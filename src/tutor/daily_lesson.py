from __future__ import annotations

import argparse
import datetime as dt
import sys

from tutor.config import load_env_file
from tutor.curriculum import lesson_seed_for_date
from tutor.generator import generate_lesson
from tutor.notion import push_to_notion
from tutor.rendering import save_json, save_markdown


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Create a daily hybrid Italian lesson.")
    parser.add_argument("--date", help="Lesson date in YYYY-MM-DD format. Defaults to today.")
    parser.add_argument("--push-notion", action="store_true", help="Push the lesson to Notion.")
    return parser.parse_args()


def resolve_date(raw_date: str | None) -> dt.date:
    if raw_date:
        return dt.date.fromisoformat(raw_date)
    return dt.date.today()


def main() -> int:
    load_env_file()
    args = parse_args()
    target_date = resolve_date(args.date)
    seed = lesson_seed_for_date(target_date)
    lesson = generate_lesson(seed)

    markdown_path = save_markdown(target_date, lesson)
    json_path = save_json(target_date, lesson)
    print(f"Markdown gespeichert: {markdown_path}")
    print(f"JSON gespeichert: {json_path}")
    print(f"Quelle: {lesson.source}")

    if args.push_notion:
        notion_url = push_to_notion(target_date, lesson)
        print(f"Nach Notion exportiert: {notion_url}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
