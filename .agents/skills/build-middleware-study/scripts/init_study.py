#!/usr/bin/env python3
"""Initialize a middleware study curriculum from the bundled templates."""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from pathlib import Path


SKILL_ROOT = Path(__file__).resolve().parents[1]
TEMPLATE_ROOT = SKILL_ROOT / "assets" / "study-template"
SLUG_PATTERN = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


@dataclass(frozen=True)
class Module:
    number: int
    slug: str
    title: str

    @property
    def directory_name(self) -> str:
        return f"{self.number:02d}-{self.slug}"


def parse_modules(raw_modules: str, allow_nonstandard_count: bool) -> list[Module]:
    modules: list[Module] = []
    for number, item in enumerate(raw_modules.split(","), start=1):
        item = item.strip()
        if not item or ":" not in item:
            raise ValueError(
                "模块必须使用 slug:标题 格式，并以逗号分隔，例如 data-model:数据建模"
            )
        slug, title = (part.strip() for part in item.split(":", 1))
        if not SLUG_PATTERN.fullmatch(slug):
            raise ValueError(f"非法模块 slug：{slug}")
        if not title:
            raise ValueError(f"模块 {slug} 缺少标题")
        modules.append(Module(number, slug, title))

    slugs = [module.slug for module in modules]
    if len(slugs) != len(set(slugs)):
        raise ValueError("模块 slug 不能重复")
    if not allow_nonstandard_count and not 6 <= len(modules) <= 10:
        raise ValueError("课程默认需要 6～10 个模块；确有理由时使用 --allow-nonstandard-count")
    return modules


def render(template_name: str, values: dict[str, str]) -> str:
    template_path = TEMPLATE_ROOT / template_name
    content = template_path.read_text(encoding="utf-8")
    for key, value in values.items():
        content = content.replace(f"{{{{{key}}}}}", value)
    unresolved = sorted(set(re.findall(r"\{\{[A-Z_]+\}\}", content)))
    if unresolved:
        raise ValueError(f"模板 {template_name} 存在未解析变量：{unresolved}")
    return content


def write_file(path: Path, content: str, merge: bool, executable: bool = False) -> str:
    if path.exists():
        if merge:
            return f"SKIP {path}"
        raise FileExistsError(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    if executable:
        path.chmod(path.stat().st_mode | 0o111)
    return f"CREATE {path}"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--middleware", required=True, help="中间件显示名称，例如 Redis")
    parser.add_argument(
        "--target",
        required=True,
        type=Path,
        help="中间件根目录；脚本会在其下创建 study/",
    )
    parser.add_argument(
        "--modules",
        required=True,
        help="逗号分隔的 slug:标题 列表",
    )
    parser.add_argument(
        "--merge",
        action="store_true",
        help="只创建缺失文件，不覆盖已有内容",
    )
    parser.add_argument(
        "--allow-nonstandard-count",
        action="store_true",
        help="允许少于 6 个或多于 10 个模块",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        modules = parse_modules(args.modules, args.allow_nonstandard_count)
    except ValueError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    target = args.target.expanduser().resolve()
    study = target / "study"
    if study.exists() and any(study.iterdir()) and not args.merge:
        print(f"ERROR: {study} 已有内容；使用 --merge 仅补充缺失文件", file=sys.stderr)
        return 2

    target.mkdir(parents=True, exist_ok=True)
    module_list = "\n".join(
        f"{module.number}. [{module.title}](labs/{module.directory_name}/README.md)"
        for module in modules
    )
    roadmap_rows = "\n".join(
        f"| {module.number} | {module.title} | L0 | - | - | - |"
        for module in modules
    )
    cheatsheet_sections = "\n\n".join(
        f"## {module.title}\n\n- TODO：写入最重要的机制、边界和证据。"
        for module in modules
    )
    common = {
        "MIDDLEWARE": args.middleware,
        "MIDDLEWARE_LOWER": args.middleware.lower(),
        "MODULE_LIST": module_list,
        "ROADMAP_ROWS": roadmap_rows,
        "CHEATSHEET_SECTIONS": cheatsheet_sections,
        "STUDY_RELATIVE": f"{target.name}/study",
    }

    operations: list[str] = []
    root_templates = {
        "README.md.tpl": study / "README.md",
        "ROADMAP.md.tpl": study / "ROADMAP.md",
        "CHEATSHEET.md.tpl": study / "CHEATSHEET.md",
        "review-README.md.tpl": study / "review" / "README.md",
        "review.py.tpl": study / "scripts" / "review.py",
        "questions.json.tpl": study / "interview" / "questions.json",
        "case-README.md.tpl": study / "cases" / "production-incident" / "README.md",
        "runbook.md.tpl": study / "runbooks" / "diagnosis.md",
    }
    try:
        for template_name, destination in root_templates.items():
            operations.append(
                write_file(
                    destination,
                    render(template_name, common),
                    args.merge,
                    executable=destination.name == "review.py",
                )
            )

        for module in modules:
            values = {
                **common,
                "MODULE_NUMBER": f"{module.number:02d}",
                "MODULE_SLUG": module.slug,
                "MODULE_TITLE": module.title,
            }
            module_dir = study / "labs" / module.directory_name
            for template_name, filename in (
                ("module-README.md.tpl", "README.md"),
                ("exercises.md.tpl", "exercises.md"),
                ("answers.md.tpl", "answers.md"),
            ):
                operations.append(
                    write_file(
                        module_dir / filename,
                        render(template_name, values),
                        args.merge,
                    )
                )
    except (FileExistsError, OSError, ValueError) as exc:
        print(f"ERROR: 初始化失败：{exc}", file=sys.stderr)
        return 1

    for operation in operations:
        print(operation)
    print(f"\n已生成脚手架：{study}")
    if not (target / "Makefile").exists():
        print("NEXT: 创建中间件根目录 Makefile，并接入 help/up/down/reset/review/all。")
    print("NEXT: 替换 TODO、实现真实实验和题库，然后运行 validate_study.py。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
