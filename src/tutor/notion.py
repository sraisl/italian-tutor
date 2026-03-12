from __future__ import annotations

import datetime as dt
import json
import os
import urllib.error
import urllib.request

from tutor.models import GeneratedLesson


def notion_headers(token: str) -> dict[str, str]:
    return {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "Notion-Version": "2022-06-28",
    }


def notion_request(url: str, payload: dict, token: str) -> dict:
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers=notion_headers(token),
        method="POST",
    )
    with urllib.request.urlopen(req) as response:
        return json.loads(response.read().decode("utf-8"))


def paragraph_block(text: str) -> dict:
    return {
        "object": "block",
        "type": "paragraph",
        "paragraph": {
            "rich_text": [{"type": "text", "text": {"content": text[:1800]}}],
        },
    }


def bulleted_blocks(items: list[str]) -> list[dict]:
    return [
        {
            "object": "block",
            "type": "bulleted_list_item",
            "bulleted_list_item": {
                "rich_text": [{"type": "text", "text": {"content": item[:1800]}}],
            },
        }
        for item in items
    ]


def build_notion_children(lesson: GeneratedLesson) -> list[dict]:
    vocab_items = [f"{it} = {de}" for it, de in lesson.vocabulary]
    phrase_items = [f"{it} = {de}" for it, de in lesson.phrases]
    return [
        paragraph_block(f"Ziel: {lesson.goal}"),
        paragraph_block(f"Quelle: {lesson.source}"),
        {"object": "block", "type": "heading_2", "heading_2": {"rich_text": [{"type": "text", "text": {"content": "Vokabeln"}}]}},
        *bulleted_blocks(vocab_items),
        {"object": "block", "type": "heading_2", "heading_2": {"rich_text": [{"type": "text", "text": {"content": "Redewendungen"}}]}},
        *bulleted_blocks(phrase_items),
        {"object": "block", "type": "heading_2", "heading_2": {"rich_text": [{"type": "text", "text": {"content": "Grammatik"}}]}},
        *bulleted_blocks(lesson.grammar),
        {"object": "block", "type": "heading_2", "heading_2": {"rich_text": [{"type": "text", "text": {"content": "Uebung"}}]}},
        paragraph_block(lesson.exercise),
        {"object": "block", "type": "heading_2", "heading_2": {"rich_text": [{"type": "text", "text": {"content": "Mini-Challenge"}}]}},
        paragraph_block(lesson.mini_challenge),
    ]


def push_to_notion(target_date: dt.date, lesson: GeneratedLesson) -> str:
    token = os.getenv("NOTION_TOKEN")
    database_id = os.getenv("NOTION_DATABASE_ID")
    parent_page_id = os.getenv("NOTION_PARENT_PAGE_ID")
    title_property = os.getenv("NOTION_TITLE_PROPERTY", "Name")
    date_property = os.getenv("NOTION_DATE_PROPERTY", "Date")

    if not token:
        raise RuntimeError("NOTION_TOKEN fehlt.")
    if not database_id and not parent_page_id:
        raise RuntimeError("Setze NOTION_DATABASE_ID oder NOTION_PARENT_PAGE_ID.")

    title = f"Italienisch {target_date.isoformat()}: {lesson.title}"
    children = build_notion_children(lesson)

    if database_id:
        payload = {
            "parent": {"database_id": database_id},
            "properties": {
                title_property: {"title": [{"type": "text", "text": {"content": title}}]},
                date_property: {"date": {"start": target_date.isoformat()}},
            },
            "children": children,
        }
    else:
        payload = {
            "parent": {"page_id": parent_page_id},
            "properties": {
                "title": {"title": [{"type": "text", "text": {"content": title}}]},
            },
            "children": children,
        }

    try:
        response = notion_request("https://api.notion.com/v1/pages", payload, token)
    except urllib.error.HTTPError as exc:
        details = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"Notion API Fehler: {exc.code} {details}") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"Netzwerkfehler bei Notion: {exc.reason}") from exc
    return response.get("url", "https://www.notion.so/")
