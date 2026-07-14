#!/usr/bin/env python3
"""随机抽取 Kubernetes 主动回忆题。"""

from __future__ import annotations

import argparse
import json
import random
from pathlib import Path


QUESTIONS = Path(__file__).resolve().parents[1] / "interview" / "questions.json"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--count", type=int, default=3, help="抽取题数")
    parser.add_argument("--list-topics", action="store_true", help="列出主题及题数")
    parser.add_argument("--seed", type=int, help="固定随机种子，便于复现")
    parser.add_argument("--no-wait", action="store_true", help="直接显示答案，用于自动检查")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    questions = json.loads(QUESTIONS.read_text(encoding="utf-8"))
    if args.list_topics:
        counts: dict[str, int] = {}
        for item in questions:
            counts[item["topic"]] = counts.get(item["topic"], 0) + 1
        for topic, count in sorted(counts.items()):
            print(f"{topic}: {count} 题")
        return 0

    if args.count < 1:
        raise SystemExit("--count 必须大于 0")
    rng = random.Random(args.seed)
    chosen = rng.sample(questions, min(args.count, len(questions)))
    for number, item in enumerate(chosen, start=1):
        print(f"\n[{number}] {item['topic']}：{item['question']}")
        if not args.no_wait:
            try:
                input("先口述答案，按回车查看参考要点...")
            except EOFError:
                pass
        for point in item["answer"]:
            print(f"  - {point}")
        print(f"  关联证据：study/{item['lab']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
