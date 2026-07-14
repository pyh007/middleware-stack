"""从 MySQL 题库随机抽题，用主动回忆代替重复阅读。"""

from __future__ import annotations

import argparse
import json
import random
from pathlib import Path
from typing import Any


STUDY_ROOT = Path(__file__).resolve().parents[1]
QUESTION_BANK = STUDY_ROOT / "interview" / "questions.json"


def load_questions() -> list[dict[str, Any]]:
    with QUESTION_BANK.open(encoding="utf-8") as file:
        questions = json.load(file)

    if not isinstance(questions, list) or not questions:
        raise SystemExit(f"题库为空或格式错误：{QUESTION_BANK}")
    return questions


def parse_args(topics: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--topic", choices=topics, help="只复习指定主题")
    parser.add_argument("--count", type=int, default=3, help="抽题数量，默认 3")
    parser.add_argument("--seed", type=int, help="固定随机种子，便于复现")
    parser.add_argument(
        "--no-wait",
        action="store_true",
        help="不等待回车，直接显示参考要点；用于自动检查",
    )
    parser.add_argument(
        "--list-topics",
        action="store_true",
        help="列出题库主题和题目数量",
    )
    return parser.parse_args()


def main() -> None:
    questions = load_questions()
    topics = sorted({str(question["topic"]) for question in questions})
    args = parse_args(topics)

    if args.list_topics:
        print("可用主题：")
        for topic in topics:
            count = sum(question["topic"] == topic for question in questions)
            print(f"  {topic}: {count} 题")
        return

    if args.count < 1:
        raise SystemExit("--count 必须大于 0")

    candidates = [
        question
        for question in questions
        if args.topic is None or question["topic"] == args.topic
    ]
    random_generator = random.Random(args.seed)
    selected = random_generator.sample(candidates, min(args.count, len(candidates)))

    print(f"本轮复习：{len(selected)} 题。先口述结论、机制、边界和生产验证。")
    for number, question in enumerate(selected, start=1):
        print(f"\n[{number}/{len(selected)}] {question['question']}")
        if not args.no_wait:
            try:
                input("思考完成后按回车查看参考要点……")
            except EOFError:
                pass

        print("参考要点：")
        for point in question["answer"]:
            print(f"  - {point}")
        print(f"对应实验：mysql/study/{question['lab']}")

    print("\n复习结束：答错的问题应重跑实验，并更新 ROADMAP.md 的等级和日期。")


if __name__ == "__main__":
    main()
