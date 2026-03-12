from __future__ import annotations

import json
import os
import re
import urllib.error
import urllib.request
from typing import Any

from tutor.curriculum import LessonSeed
from tutor.models import GeneratedLesson


LM_STUDIO_BASE_URL = "http://127.0.0.1:1234/v1"


def build_prompt(seed: LessonSeed) -> str:
    return f"""
Du bist ein didaktisch sauberer Italienisch-Tutor fuer absolute Anfaenger mit deutscher Muttersprache.
Erzeuge genau eine Lektion im JSON-Format ohne Markdown, ohne Erklaerung ausserhalb des JSON.

Rahmen:
- Tag: {seed.day}
- Titel: {seed.title}
- Lernziel: {seed.goal}
- Grammatikfokus: {seed.grammar_focus}
- Wortschatzthema: {seed.vocabulary_theme}
- Uebungsfokus: {seed.exercise_focus}

Regeln:
- Niveau A0, absolute Anfaenger.
- 6 Vokabeln.
- 3 alltagstaugliche Redewendungen.
- 2 kurze Grammatikpunkte in einfachem Deutsch.
- 1 kurze Uebung.
- 1 Mini-Challenge.
- Italienische Beispiele muessen einfach und natuerlich sein.
- Keine komplizierten Zeiten.
- Deutsch kurz und klar.
- ASCII only, keine Umlaute.

JSON-Schema:
{{
  "title": "string",
  "goal": "string",
  "vocabulary": [{{"italian": "string", "german": "string"}}],
  "phrases": [{{"italian": "string", "german": "string"}}],
  "grammar": ["string", "string"],
  "exercise": "string",
  "mini_challenge": "string"
}}
""".strip()


def _lm_studio_url() -> str:
    base = os.getenv("LM_STUDIO_BASE_URL", LM_STUDIO_BASE_URL).rstrip("/")
    return f"{base}/chat/completions"


def _lm_studio_model() -> str:
    return os.getenv("LM_STUDIO_MODEL", "local-model")


def _lm_studio_models_url() -> str:
    base = os.getenv("LM_STUDIO_BASE_URL", LM_STUDIO_BASE_URL).rstrip("/")
    return f"{base}/models"


def lm_studio_status() -> dict[str, str | bool]:
    req = urllib.request.Request(_lm_studio_models_url(), method="GET")
    try:
        with urllib.request.urlopen(req, timeout=4) as response:
            body = json.loads(response.read().decode("utf-8"))
        models = body.get("data", [])
        model_ids = [
            item.get("id", "").strip()
            for item in models
            if isinstance(item, dict) and item.get("id")
        ]
        loaded_models = ", ".join(model_ids)
        configured_model = _lm_studio_model()
        exact_match = configured_model in model_ids
        return {
            "ok": exact_match,
            "reachable": True,
            "message": "LM Studio erreichbar." if exact_match else "LM Studio erreichbar, aber das konfigurierte Modell ist nicht geladen.",
            "model": configured_model,
            "loaded_models": loaded_models or "Keine Modelle gemeldet.",
            "state": "green" if exact_match else "amber",
        }
    except urllib.error.HTTPError as exc:
        return {
            "ok": False,
            "reachable": False,
            "message": f"LM Studio Antwort ungueltig: HTTP {exc.code}",
            "model": _lm_studio_model(),
            "loaded_models": "",
            "state": "red",
        }
    except urllib.error.URLError as exc:
        return {
            "ok": False,
            "reachable": False,
            "message": f"LM Studio nicht erreichbar: {exc.reason}",
            "model": _lm_studio_model(),
            "loaded_models": "",
            "state": "red",
        }
    except (json.JSONDecodeError, TimeoutError) as exc:
        return {
            "ok": False,
            "reachable": False,
            "message": f"LM Studio Antwort ungueltig: {exc}",
            "model": _lm_studio_model(),
            "loaded_models": "",
            "state": "red",
        }


def request_lm_studio(seed: LessonSeed) -> GeneratedLesson:
    payload = _completion_payload(seed, use_json_mode=True)
    try:
        body = _post_completion(payload)
    except urllib.error.HTTPError as exc:
        details = exc.read().decode("utf-8", errors="replace")
        if exc.code == 400 and "response_format" in details:
            body = _post_completion(_completion_payload(seed, use_json_mode=False))
        else:
            raise_http_error(exc.code, details)

    content = extract_content(body)
    parsed = parse_json_content(content)
    return normalize_lesson(seed, parsed, source="lm_studio", source_detail="Lektion erfolgreich ueber LM Studio erzeugt.")


def _completion_payload(seed: LessonSeed, use_json_mode: bool) -> dict[str, Any]:
    payload = {
        "model": _lm_studio_model(),
        "temperature": 0.5,
        "messages": [
            {"role": "system", "content": "Return only valid JSON."},
            {"role": "user", "content": build_prompt(seed)},
        ],
    }
    if use_json_mode:
        payload["response_format"] = {"type": "json_object"}
    return payload


def _post_completion(payload: dict[str, Any]) -> dict[str, Any]:
    req = urllib.request.Request(
        _lm_studio_url(),
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=90) as response:
        return json.loads(response.read().decode("utf-8"))


def extract_content(body: dict[str, Any]) -> str:
    content = body["choices"][0]["message"]["content"]
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for item in content:
            if isinstance(item, dict) and item.get("type") == "text" and item.get("text"):
                parts.append(str(item["text"]))
        if parts:
            return "\n".join(parts)
    raise ValueError("LM Studio content field could not be parsed.")


def parse_json_content(content: str) -> dict[str, Any]:
    text = content.strip()
    if text.startswith("```"):
        match = re.search(r"```(?:json)?\s*(\{.*\})\s*```", text, flags=re.DOTALL)
        if match:
            text = match.group(1).strip()
    if not text.startswith("{"):
        match = re.search(r"(\{.*\})", text, flags=re.DOTALL)
        if match:
            text = match.group(1).strip()
    return json.loads(text)


def raise_http_error(code: int, details: str) -> None:
    raise RuntimeError(f"LM Studio HTTP-Fehler {code}: {details[:300]}")


def fallback_lesson(seed: LessonSeed, reason: str) -> GeneratedLesson:
    vocabulary = [
        ("ciao", "hallo / tschuess"),
        ("grazie", "danke"),
        ("per favore", "bitte"),
        ("si", "ja"),
        ("no", "nein"),
        ("bene", "gut"),
    ]
    phrases = [
        ("Ciao, mi chiamo Luca.", "Hallo, ich heisse Luca."),
        ("Sto bene, grazie.", "Mir geht es gut, danke."),
        ("Un caffe, per favore.", "Einen Kaffee, bitte."),
    ]
    grammar = [
        f"Fokus heute: {seed.grammar_focus}. Halte die Saetze sehr kurz.",
        "Im Italienischen reichen am Anfang oft sehr kurze Standardsaetze fuer Alltagssituationen.",
    ]
    return GeneratedLesson(
        day=seed.day,
        title=seed.title,
        goal=seed.goal,
        vocabulary=vocabulary,
        phrases=phrases,
        grammar=grammar,
        exercise=f"Uebung: {seed.exercise_focus}. Sprich die Beispiele laut und schreibe einen eigenen Satz.",
        mini_challenge=f"Mini-Challenge: Nutze das Thema '{seed.vocabulary_theme}' in 2 sehr kurzen Saetzen.",
        source="template_fallback",
        source_detail=reason,
    )


def normalize_lesson(seed: LessonSeed, parsed: dict[str, Any], source: str, source_detail: str) -> GeneratedLesson:
    vocabulary = [
        (item["italian"].strip(), item["german"].strip())
        for item in parsed.get("vocabulary", [])[:6]
        if isinstance(item, dict) and item.get("italian") and item.get("german")
    ]
    phrases = [
        (item["italian"].strip(), item["german"].strip())
        for item in parsed.get("phrases", [])[:3]
        if isinstance(item, dict) and item.get("italian") and item.get("german")
    ]
    grammar = [str(item).strip() for item in parsed.get("grammar", [])[:2] if str(item).strip()]
    if len(vocabulary) < 4 or len(phrases) < 2 or not grammar:
        raise ValueError("LM Studio returned incomplete lesson data.")
    return GeneratedLesson(
        day=seed.day,
        title=str(parsed.get("title") or seed.title).strip(),
        goal=str(parsed.get("goal") or seed.goal).strip(),
        vocabulary=vocabulary,
        phrases=phrases,
        grammar=grammar,
        exercise=str(parsed.get("exercise") or seed.exercise_focus).strip(),
        mini_challenge=str(parsed.get("mini_challenge") or "Schreibe 2 eigene Saetze.").strip(),
        source=source,
        source_detail=source_detail,
    )


def generate_lesson(seed: LessonSeed) -> GeneratedLesson:
    try:
        return request_lm_studio(seed)
    except urllib.error.URLError as exc:
        return fallback_lesson(seed, f"LM Studio nicht erreichbar: {exc.reason}")
    except TimeoutError:
        return fallback_lesson(seed, "LM Studio Zeitueberschreitung.")
    except json.JSONDecodeError as exc:
        return fallback_lesson(seed, f"LM Studio lieferte ungueltiges JSON: {exc}")
    except RuntimeError as exc:
        return fallback_lesson(seed, str(exc))
    except KeyError as exc:
        return fallback_lesson(seed, f"LM Studio Antwort hatte unerwartete Struktur: fehlendes Feld {exc}.")
    except ValueError as exc:
        return fallback_lesson(seed, f"LM Studio lieferte unvollstaendige Lektion: {exc}")
