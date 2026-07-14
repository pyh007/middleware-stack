#!/usr/bin/env python3
"""从 Redis 题库随机抽题，先回忆再显示参考要点。"""

from __future__ import annotations

import argparse
import json
import random
from pathlib import Path
from typing import Any


STUDY_ROOT = Path(__file__).resolve().parents[1]
QUESTION_BANK = STUDY_ROOT / "interview" / "questions.json"


def load_questions() -> list[dict[str, Any]]:
    questions = json.loads(QUESTION_BANK.read_text(encoding="utf-8"))
    if not isinstance(questions, list) or not questions:
        raise SystemExit(f"题库为空，请先完成：{QUESTION_BANK}")
    return questions


def main() -> None:
    questions = load_questions()
    topics = sorted({str(question["topic"]) for question in questions})
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--topic", choices=topics)
    parser.add_argument("--count", type=int, default=3)
    parser.add_argument("--seed", type=int)
    parser.add_argument("--no-wait", action="store_true")
    parser.add_argument("--list-topics", action="store_true")
    args = parser.parse_args()

    if args.list_topics:
        for topic in topics:
            count = sum(question["topic"] == topic for question in questions)
            print(f"{topic}: {count} 题")
        return

    candidates = [
        question
        for question in questions
        if args.topic is None or question["topic"] == args.topic
    ]
    selected = random.Random(args.seed).sample(
        candidates, min(max(args.count, 1), len(candidates))
    )

    for number, question in enumerate(selected, start=1):
        print(f"\n[{number}/{len(selected)}] {question['question']}")
        if not args.no_wait:
            try:
                input("思考完成后按回车查看参考要点……")
            except EOFError:
                pass
        for point in question["answer"]:
            print(f"  - {point}")
        print(f"关联材料：{question['lab']}")


if __name__ == "__main__":
    main()
