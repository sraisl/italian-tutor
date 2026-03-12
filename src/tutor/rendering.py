from __future__ import annotations

import datetime as dt
import json
import re
from dataclasses import asdict
from pathlib import Path

from tutor.config import OUTPUT_DIR
from tutor.models import GeneratedLesson


def slugify(value: str) -> str:
    cleaned = re.sub(r"[^a-zA-Z0-9]+", "-", value.lower()).strip("-")
    return cleaned or "lesson"


def lesson_markdown(target_date: dt.date, lesson: GeneratedLesson) -> str:
    vocab_lines = "\n".join(f"- **{it}**: {de}" for it, de in lesson.vocabulary)
    phrase_lines = "\n".join(f"- **{it}**: {de}" for it, de in lesson.phrases)
    grammar_lines = "\n".join(f"- {point}" for point in lesson.grammar)
    source_line = "LM Studio" if lesson.source == "lm_studio" else "Template fallback"
    return f"""# Italienisch Lektion {lesson.day}: {lesson.title}

**Datum:** {target_date.isoformat()}
**Niveau:** Absolute Anfaenger
**Ziel:** {lesson.goal}
**Quelle:** {source_line}
**Details:** {lesson.source_detail}

## Vokabeln
{vocab_lines}

## Redewendungen
{phrase_lines}

## Ein wenig Grammatik
{grammar_lines}

## Uebung
{lesson.exercise}

## Mini-Challenge
{lesson.mini_challenge}
"""


def save_markdown(target_date: dt.date, lesson: GeneratedLesson) -> Path:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    filename = f"{target_date.isoformat()}-{slugify(lesson.title)}.md"
    path = OUTPUT_DIR / filename
    path.write_text(lesson_markdown(target_date, lesson), encoding="utf-8")
    return path


def save_json(target_date: dt.date, lesson: GeneratedLesson) -> Path:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    filename = f"{target_date.isoformat()}-{slugify(lesson.title)}.json"
    path = OUTPUT_DIR / filename
    path.write_text(json.dumps(asdict(lesson), ensure_ascii=True, indent=2), encoding="utf-8")
    return path
