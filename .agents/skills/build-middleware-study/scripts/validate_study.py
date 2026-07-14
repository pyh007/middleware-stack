#!/usr/bin/env python3
"""Validate a middleware study curriculum against the reusable quality contract."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from urllib.parse import unquote


MODULE_PATTERN = re.compile(r"^\d{2}-[a-z0-9]+(?:-[a-z0-9]+)*$")
PLACEHOLDER_PATTERN = re.compile(
    r"\b(?:TODO|FIXME|TBD)\b|待建设|待补充|\{\{[A-Z_]+\}\}|\[PLACEHOLDER\]",
    re.IGNORECASE,
)
MARKDOWN_LINK_PATTERN = re.compile(r"\[[^\]]+\]\(([^)]+)\)")
LAB_SUFFIXES = {".sql", ".py", ".sh"}


class Validator:
    def __init__(self, study: Path, min_modules: int, max_modules: int) -> None:
        self.study = study
        self.min_modules = min_modules
        self.max_modules = max_modules
        self.errors: list[str] = []
        self.warnings: list[str] = []

    def error(self, message: str) -> None:
        self.errors.append(message)

    def warning(self, message: str) -> None:
        self.warnings.append(message)

    def validate_structure(self) -> list[Path]:
        required_files = ["README.md", "ROADMAP.md", "CHEATSHEET.md"]
        required_directories = [
            "labs",
            "cases",
            "interview",
            "review",
            "runbooks",
            "scripts",
        ]
        for relative in required_files:
            path = self.study / relative
            if not path.is_file():
                self.error(f"缺少必需文件：{relative}")
            elif len(path.read_text(encoding="utf-8").strip()) < 200:
                self.error(f"根文档内容过少：{relative}")
        for relative in required_directories:
            if not (self.study / relative).is_dir():
                self.error(f"缺少必需目录：{relative}/")

        labs = self.study / "labs"
        modules = (
            sorted(path for path in labs.iterdir() if path.is_dir())
            if labs.is_dir()
            else []
        )
        invalid_names = [path.name for path in modules if not MODULE_PATTERN.fullmatch(path.name)]
        if invalid_names:
            self.error(f"模块目录命名无效：{', '.join(invalid_names)}")
        if not self.min_modules <= len(modules) <= self.max_modules:
            self.error(
                f"模块数为 {len(modules)}，期望 {self.min_modules}～{self.max_modules} 个"
            )
        return modules

    def validate_modules(self, modules: list[Path]) -> None:
        for module in modules:
            for filename in ("README.md", "exercises.md", "answers.md"):
                path = module / filename
                if not path.is_file():
                    self.error(f"{module.name} 缺少 {filename}")
                elif len(path.read_text(encoding="utf-8").strip()) < 180:
                    self.error(f"{module.name}/{filename} 内容过少")

            artifacts = [
                path
                for path in module.rglob("*")
                if path.is_file()
                and (
                    path.suffix.lower() in LAB_SUFFIXES
                    or path.name.startswith("docker-compose")
                )
            ]
            if not artifacts:
                self.error(f"{module.name} 没有可运行实验（sql/py/sh/compose）")

    def validate_placeholders(self) -> None:
        checked_suffixes = {".md", ".json", ".py", ".sql", ".sh", ".yml", ".yaml"}
        for path in self.study.rglob("*"):
            if not path.is_file() or path.suffix.lower() not in checked_suffixes:
                continue
            content = path.read_text(encoding="utf-8", errors="replace")
            match = PLACEHOLDER_PATTERN.search(content)
            if match:
                self.error(f"发现占位内容 {match.group(0)!r}：{path.relative_to(self.study)}")

    def validate_questions(self) -> None:
        path = self.study / "interview" / "questions.json"
        if not path.is_file():
            self.error("缺少 interview/questions.json")
            return
        try:
            questions = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            self.error(f"题库 JSON 无效：{exc}")
            return
        if not isinstance(questions, list) or not questions:
            self.error("题库必须是非空数组")
            return

        required = {"topic", "question", "answer", "lab"}
        for number, question in enumerate(questions, start=1):
            if not isinstance(question, dict):
                self.error(f"题库第 {number} 项不是对象")
                continue
            missing = required - question.keys()
            if missing:
                self.error(f"题库第 {number} 项缺少字段：{sorted(missing)}")
                continue
            if not isinstance(question["answer"], list) or not question["answer"]:
                self.error(f"题库第 {number} 项 answer 必须是非空数组")
            lab = self.study / str(question["lab"])
            if not lab.exists():
                self.error(f"题库第 {number} 项关联路径不存在：{question['lab']}")

    def validate_markdown_links(self) -> None:
        for path in self.study.rglob("*.md"):
            content = path.read_text(encoding="utf-8")
            for raw_target in MARKDOWN_LINK_PATTERN.findall(content):
                target = raw_target.strip().strip("<>")
                if target.startswith(("http://", "https://", "mailto:", "#")):
                    continue
                target = unquote(target.split("#", 1)[0])
                if not target:
                    continue
                candidate = (path.parent / target).resolve()
                if not candidate.exists():
                    self.error(
                        f"断开的 Markdown 链接：{path.relative_to(self.study)} -> {raw_target}"
                    )

    def validate_supporting_content(self) -> None:
        if not list((self.study / "cases").rglob("README.md")):
            self.error("cases/ 中至少需要一个综合案例 README.md")
        if not list((self.study / "runbooks").rglob("*.md")):
            self.error("runbooks/ 中至少需要一个 Runbook")
        if not list((self.study / "scripts").glob("reset.*")):
            self.error("scripts/ 中缺少受控 reset 脚本")
        if not (self.study / "scripts" / "review.py").is_file():
            self.error("scripts/review.py 不存在")

    def validate_command_entrypoint(self) -> None:
        makefile = self.study.parent / "Makefile"
        if not makefile.is_file():
            self.error(f"缺少中间件根目录命令入口：{makefile}")
            return
        content = makefile.read_text(encoding="utf-8")
        for target in ("help", "up", "down", "reset", "review", "all"):
            if not re.search(rf"(?m)^{re.escape(target)}\s*:", content):
                self.error(f"Makefile 缺少目标：{target}")

        all_match = re.search(r"(?m)^all\s*:[^\n]*", content)
        if all_match and re.search(
            r"crash|failover|destroy|replication-down|volume-delete",
            all_match.group(0),
            re.IGNORECASE,
        ):
            self.error(f"安全 all 目标包含破坏性依赖：{all_match.group(0)}")

    def run(self) -> int:
        if not self.study.is_dir():
            self.error(f"study 目录不存在：{self.study}")
        else:
            modules = self.validate_structure()
            self.validate_modules(modules)
            self.validate_placeholders()
            self.validate_questions()
            self.validate_markdown_links()
            self.validate_supporting_content()
            self.validate_command_entrypoint()

        for warning in self.warnings:
            print(f"[WARN] {warning}")
        for error in self.errors:
            print(f"[ERROR] {error}")
        if self.errors:
            print(f"\n验证失败：{len(self.errors)} 个错误，{len(self.warnings)} 个警告")
            return 1
        print(f"验证通过：{self.study} 满足课程结构与质量门禁")
        return 0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("study", type=Path, help="待验证的 study/ 目录")
    parser.add_argument("--min-modules", type=int, default=6)
    parser.add_argument("--max-modules", type=int, default=10)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.min_modules < 1 or args.max_modules < args.min_modules:
        print("ERROR: 模块数量范围无效", file=sys.stderr)
        return 2
    return Validator(
        args.study.expanduser().resolve(), args.min_modules, args.max_modules
    ).run()


if __name__ == "__main__":
    raise SystemExit(main())
