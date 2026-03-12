from __future__ import annotations

import datetime as dt
from dataclasses import dataclass


LESSON_START_DATE = dt.date(2026, 3, 12)


@dataclass(frozen=True)
class LessonSeed:
    day: int
    title: str
    goal: str
    grammar_focus: str
    vocabulary_theme: str
    exercise_focus: str


CURRICULUM: list[LessonSeed] = [
    LessonSeed(1, "Begruessung und Vorstellen", "Hallo sagen und sich vorstellen", "mi chiamo, io sono", "Begruessungen und Hoeflichkeit", "Mini-Dialog zur Begruessung"),
    LessonSeed(2, "Befinden und Reaktionen", "nach dem Befinden fragen und antworten", "stare im Praesens: sto, stai", "Gefuehle und einfache Antworten", "3 kurze Antworten auf Come stai?"),
    LessonSeed(3, "Ja, nein und W-Fragen", "sehr einfache Rueckfragen bilden", "chi, cosa, dove", "Fragewoerter", "zwei sehr kurze Fragen schreiben"),
    LessonSeed(4, "Zahlen 1 bis 10", "Zaehlen und einfache Zahlen erkennen", "Zahlen im Alltag", "Zahlen und Mengen", "laut zaehlen und 3 Zahlen notieren"),
    LessonSeed(5, "Artikel il und la", "erste Nomen mit Artikel lernen", "bestimmte Artikel Singular", "Alltagsnomen", "Nomen sortieren"),
    LessonSeed(6, "Essere", "erste Saetze mit sein bilden", "sono, sei, e", "Nationalitaeten und Adjektive", "3 Ich-Saetze schreiben"),
    LessonSeed(7, "Avere", "sagen, was man hat", "ho, hai, ha", "Hunger, Durst, Zeit", "einen Mini-Dialog mit avere"),
    LessonSeed(8, "Alltagsobjekte", "einfache Dinge benennen", "c'e / ci sono Einstieg", "Gegenstaende zuhause", "5 Dinge im Zimmer benennen"),
    LessonSeed(9, "Familie", "nahe Familienmitglieder benennen", "mein/dein ohne Tiefgang", "madre, padre, sorella, fratello", "Mini-Vorstellung einer Familie"),
    LessonSeed(10, "Farben", "Grundfarben im Alltag nutzen", "Adjektive nach Nomen", "Farben", "3 Dinge mit Farbe beschreiben"),
    LessonSeed(11, "Im Cafe bestellen", "etwas sehr einfach bestellen", "vorhoefliche Bitten mit vorrei", "Getraenke und Snacks", "Mini-Bestellung"),
    LessonSeed(12, "Tageszeiten", "ueber morgens, mittags, abends sprechen", "a + Tageszeit", "mattina, pomeriggio, sera", "3 Tageszeiten nennen"),
    LessonSeed(13, "Wochentage", "einfache Verabredungen verstehen", "oggi, domani, lunedi...", "Kalender und Termine", "Frage nach einem Tag"),
    LessonSeed(14, "Orte in der Stadt", "einfache Ortswoerter verstehen", "dove, qui, la", "bar, stazione, casa, scuola", "2 Ortsfragen schreiben"),
]


def lesson_seed_for_date(target_date: dt.date) -> LessonSeed:
    delta = (target_date - LESSON_START_DATE).days
    if delta < 0:
        return CURRICULUM[0]
    return CURRICULUM[delta % len(CURRICULUM)]
