from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class GeneratedLesson:
    day: int
    title: str
    goal: str
    vocabulary: list[tuple[str, str]]
    phrases: list[tuple[str, str]]
    grammar: list[str]
    exercise: str
    mini_challenge: str
    source: str
    source_detail: str
