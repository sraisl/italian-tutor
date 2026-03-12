from __future__ import annotations

import argparse
import datetime as dt
import json
from dataclasses import asdict
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from tutor.config import load_env_file
from tutor.curriculum import lesson_seed_for_date
from tutor.generator import generate_lesson, lm_studio_status
from tutor.notion import push_to_notion
from tutor.rendering import save_json, save_markdown


HTML = """<!doctype html>
<html lang="de">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Italian Tutor</title>
  <style>
    :root {
      --bg: #f4efe6;
      --panel: #fffaf2;
      --ink: #2d241d;
      --muted: #746659;
      --accent: #1e7a5c;
      --accent-2: #c6512d;
      --line: #e4d7c5;
    }
    * { box-sizing: border-box; }
    body {
      margin: 0;
      font-family: Georgia, "Times New Roman", serif;
      color: var(--ink);
      background:
        radial-gradient(circle at top left, rgba(198,81,45,0.15), transparent 28%),
        radial-gradient(circle at right, rgba(30,122,92,0.18), transparent 22%),
        linear-gradient(180deg, #f7f1e8 0%, var(--bg) 100%);
    }
    .wrap {
      max-width: 1080px;
      margin: 0 auto;
      padding: 32px 18px 56px;
    }
    .hero {
      background: rgba(255,250,242,0.88);
      border: 1px solid var(--line);
      border-radius: 24px;
      padding: 28px;
      box-shadow: 0 18px 50px rgba(72, 44, 21, 0.08);
      backdrop-filter: blur(10px);
    }
    h1 {
      margin: 0 0 8px;
      font-size: clamp(2.3rem, 5vw, 4rem);
      line-height: 0.95;
      letter-spacing: -0.04em;
    }
    .sub {
      margin: 0;
      max-width: 760px;
      color: var(--muted);
      font-size: 1.05rem;
    }
    .grid {
      display: grid;
      grid-template-columns: 320px 1fr;
      gap: 20px;
      margin-top: 20px;
    }
    .card {
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 22px;
      padding: 20px;
      box-shadow: 0 12px 28px rgba(72, 44, 21, 0.06);
    }
    label {
      display: block;
      font-size: 0.9rem;
      margin-bottom: 6px;
      color: var(--muted);
    }
    input {
      width: 100%;
      padding: 12px 14px;
      border-radius: 14px;
      border: 1px solid #d8c7b4;
      background: #fffefb;
      font: inherit;
      margin-bottom: 12px;
    }
    button {
      width: 100%;
      border: 0;
      border-radius: 999px;
      padding: 13px 16px;
      font: inherit;
      cursor: pointer;
      transition: transform 140ms ease, opacity 140ms ease;
      margin-bottom: 10px;
    }
    button:hover { transform: translateY(-1px); }
    .primary { background: var(--accent); color: white; }
    .secondary { background: var(--accent-2); color: white; }
    .ghost { background: #efe2d1; color: var(--ink); }
    .meta {
      display: flex;
      gap: 10px;
      flex-wrap: wrap;
      margin: 12px 0 18px;
    }
    .pill {
      padding: 8px 12px;
      border-radius: 999px;
      background: #f0e3d2;
      color: var(--muted);
      font-size: 0.9rem;
    }
    .status {
      min-height: 24px;
      color: var(--muted);
      font-size: 0.95rem;
    }
    .lm-status {
      display: flex;
      align-items: center;
      gap: 10px;
      padding: 12px 14px;
      margin-bottom: 14px;
      border-radius: 16px;
      background: #f7ebdd;
      border: 1px solid var(--line);
    }
    .dot {
      width: 14px;
      height: 14px;
      border-radius: 999px;
      background: #b9aa99;
      box-shadow: 0 0 0 4px rgba(185, 170, 153, 0.18);
      flex: 0 0 auto;
    }
    .dot.green {
      background: #2f8f56;
      box-shadow: 0 0 0 4px rgba(47, 143, 86, 0.18);
    }
    .dot.red {
      background: #c6512d;
      box-shadow: 0 0 0 4px rgba(198, 81, 45, 0.18);
    }
    .dot.amber {
      background: #cf8a1c;
      box-shadow: 0 0 0 4px rgba(207, 138, 28, 0.18);
    }
    .lm-copy {
      min-width: 0;
    }
    .lm-copy strong {
      display: block;
      font-size: 0.92rem;
    }
    .lm-copy span {
      display: block;
      color: var(--muted);
      font-size: 0.82rem;
      margin-top: 2px;
      overflow-wrap: anywhere;
    }
    .section {
      margin-top: 20px;
      padding-top: 18px;
      border-top: 1px solid var(--line);
    }
    .section h2 {
      font-size: 1.1rem;
      margin: 0 0 10px;
    }
    ul { padding-left: 20px; }
    li { margin: 6px 0; }
    .hidden { display: none; }
    @media (max-width: 860px) {
      .grid { grid-template-columns: 1fr; }
    }
  </style>
</head>
<body>
  <div class="wrap">
    <section class="hero">
      <h1>Italian Tutor</h1>
      <p class="sub">Taegliche Lektionen fuer absolute Anfaenger. Die Struktur kommt aus einem festen Kursplan, die konkrete Lektion aus LM Studio. Wenn LM Studio nicht erreichbar ist, faellt die App kontrolliert auf ein Template zurueck.</p>
    </section>
    <div class="grid">
      <aside class="card">
        <div class="lm-status">
          <div class="dot amber" id="lm-dot"></div>
          <div class="lm-copy">
            <strong id="lm-label">LM Studio wird geprueft...</strong>
            <span id="lm-detail">Noch kein Status.</span>
          </div>
        </div>
        <label for="date">Datum</label>
        <input id="date" type="date">
        <button class="primary" id="generate">Lektion generieren</button>
        <button class="ghost" id="save" disabled>Lokal speichern</button>
        <button class="secondary" id="notion" disabled>Nach Notion senden</button>
        <div class="status" id="status"></div>
      </aside>
      <main class="card">
        <div id="empty">Noch keine Lektion geladen.</div>
        <div id="lesson" class="hidden">
          <h2 id="title"></h2>
          <div class="meta">
            <span class="pill" id="lesson-date"></span>
            <span class="pill" id="lesson-day"></span>
            <span class="pill" id="lesson-source"></span>
          </div>
          <p id="goal"></p>
          <div class="section">
            <h2>Vokabeln</h2>
            <ul id="vocabulary"></ul>
          </div>
          <div class="section">
            <h2>Redewendungen</h2>
            <ul id="phrases"></ul>
          </div>
          <div class="section">
            <h2>Ein wenig Grammatik</h2>
            <ul id="grammar"></ul>
          </div>
          <div class="section">
            <h2>Uebung</h2>
            <p id="exercise"></p>
          </div>
          <div class="section">
            <h2>Mini-Challenge</h2>
            <p id="challenge"></p>
          </div>
        </div>
      </main>
    </div>
  </div>
  <script>
    const dateInput = document.getElementById("date");
    const statusEl = document.getElementById("status");
    const emptyEl = document.getElementById("empty");
    const lessonEl = document.getElementById("lesson");
    const saveBtn = document.getElementById("save");
    const notionBtn = document.getElementById("notion");
    const lmDot = document.getElementById("lm-dot");
    const lmLabel = document.getElementById("lm-label");
    const lmDetail = document.getElementById("lm-detail");
    let lessonState = null;

    dateInput.value = new Date().toISOString().slice(0, 10);

    function setStatus(text) {
      statusEl.textContent = text;
    }

    function renderLmStatus(payload) {
      lmDot.className = `dot ${payload.state || (payload.ok ? "green" : "red")}`;
      if (payload.state === "green") {
        lmLabel.textContent = "LM Studio bereit";
      } else if (payload.state === "amber") {
        lmLabel.textContent = "LM Studio teils bereit";
      } else {
        lmLabel.textContent = "LM Studio offline";
      }
      const parts = [payload.message];
      if (payload.model) parts.push(`Konfiguriertes Modell: ${payload.model}`);
      if (payload.loaded_models) parts.push(`Server meldet: ${payload.loaded_models}`);
      lmDetail.textContent = parts.join(" | ");
    }

    function renderList(id, items, format) {
      const ul = document.getElementById(id);
      ul.innerHTML = "";
      items.forEach((item) => {
        const li = document.createElement("li");
        li.textContent = format(item);
        ul.appendChild(li);
      });
    }

    function renderLesson(payload) {
      const lesson = payload.lesson;
      lessonState = payload;
      emptyEl.classList.add("hidden");
      lessonEl.classList.remove("hidden");
      document.getElementById("title").textContent = lesson.title;
      document.getElementById("lesson-date").textContent = payload.date;
      document.getElementById("lesson-day").textContent = `Tag ${lesson.day}`;
      document.getElementById("lesson-source").textContent = lesson.source === "lm_studio" ? "LM Studio" : "Template fallback";
      document.getElementById("goal").textContent = lesson.goal;
      document.getElementById("exercise").textContent = lesson.exercise;
      document.getElementById("challenge").textContent = lesson.mini_challenge;
      renderList("vocabulary", lesson.vocabulary, ([it, de]) => `${it} = ${de}`);
      renderList("phrases", lesson.phrases, ([it, de]) => `${it} = ${de}`);
      renderList("grammar", lesson.grammar, (text) => text);
      saveBtn.disabled = false;
      notionBtn.disabled = false;
    }

    async function postJson(url, payload) {
      const response = await fetch(url, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
      });
      if (!response.ok) {
        const text = await response.text();
        throw new Error(text || `HTTP ${response.status}`);
      }
      return response.json();
    }

    async function refreshLmStatus() {
      lmDot.className = "dot amber";
      lmLabel.textContent = "LM Studio wird geprueft...";
      lmDetail.textContent = "Verbindung wird getestet.";
      try {
        const payload = await fetch("/api/status/lm-studio");
        if (!payload.ok) {
          throw new Error(`HTTP ${payload.status}`);
        }
        renderLmStatus(await payload.json());
      } catch (error) {
        renderLmStatus({
          ok: false,
          reachable: false,
          message: `Statuscheck fehlgeschlagen: ${error.message}`,
          model: "",
          loaded_models: "",
          state: "red"
        });
      }
    }

    document.getElementById("generate").addEventListener("click", async () => {
      setStatus("Generiere Lektion...");
      try {
        await refreshLmStatus();
        const payload = await postJson("/api/generate", { date: dateInput.value });
        renderLesson(payload);
        setStatus(payload.lesson.source === "lm_studio" ? payload.lesson.source_detail : `Fallback aktiv: ${payload.lesson.source_detail}`);
      } catch (error) {
        setStatus(`Fehler: ${error.message}`);
      }
    });

    saveBtn.addEventListener("click", async () => {
      if (!lessonState) return;
      setStatus("Speichere lokal...");
      try {
        const payload = await postJson("/api/save", lessonState);
        setStatus(`Gespeichert: ${payload.markdown_path}`);
      } catch (error) {
        setStatus(`Fehler: ${error.message}`);
      }
    });

    notionBtn.addEventListener("click", async () => {
      if (!lessonState) return;
      setStatus("Sende zu Notion...");
      try {
        const payload = await postJson("/api/notion", lessonState);
        setStatus(`Notion: ${payload.url}`);
      } catch (error) {
        setStatus(`Fehler: ${error.message}`);
      }
    });

    refreshLmStatus();
  </script>
</body>
</html>
"""


class TutorHandler(BaseHTTPRequestHandler):
    server_version = "TutorHTTP/0.1"

    def do_GET(self) -> None:
        if self.path == "/api/status/lm-studio":
            self.respond_json(lm_studio_status())
            return
        if self.path != "/":
            self.send_error(HTTPStatus.NOT_FOUND)
            return
        body = HTML.encode("utf-8")
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self) -> None:
        length = int(self.headers.get("Content-Length", "0"))
        raw_body = self.rfile.read(length)
        try:
            payload = json.loads(raw_body.decode("utf-8") or "{}")
        except json.JSONDecodeError:
            self.respond_json({"error": "Invalid JSON."}, HTTPStatus.BAD_REQUEST)
            return

        try:
            if self.path == "/api/generate":
                self.handle_generate(payload)
                return
            if self.path == "/api/save":
                self.handle_save(payload)
                return
            if self.path == "/api/notion":
                self.handle_notion(payload)
                return
        except RuntimeError as exc:
            self.respond_json({"error": str(exc)}, HTTPStatus.BAD_REQUEST)
            return
        except Exception as exc:
            self.respond_json({"error": str(exc)}, HTTPStatus.INTERNAL_SERVER_ERROR)
            return

        self.send_error(HTTPStatus.NOT_FOUND)

    def handle_generate(self, payload: dict) -> None:
        target_date = dt.date.fromisoformat(payload.get("date") or dt.date.today().isoformat())
        seed = lesson_seed_for_date(target_date)
        lesson = generate_lesson(seed)
        self.respond_json({"date": target_date.isoformat(), "lesson": asdict(lesson)})

    def handle_save(self, payload: dict) -> None:
        target_date, lesson = parse_payload(payload)
        markdown_path = save_markdown(target_date, lesson)
        json_path = save_json(target_date, lesson)
        self.respond_json({"markdown_path": str(markdown_path), "json_path": str(json_path)})

    def handle_notion(self, payload: dict) -> None:
        target_date, lesson = parse_payload(payload)
        url = push_to_notion(target_date, lesson)
        self.respond_json({"url": url})

    def respond_json(self, payload: dict, status: HTTPStatus = HTTPStatus.OK) -> None:
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format: str, *args) -> None:
        return


def parse_payload(payload: dict):
    from tutor.models import GeneratedLesson

    target_date = dt.date.fromisoformat(payload["date"])
    lesson_data = payload["lesson"]
    lesson = GeneratedLesson(
        day=int(lesson_data["day"]),
        title=str(lesson_data["title"]),
        goal=str(lesson_data["goal"]),
        vocabulary=[(str(a), str(b)) for a, b in lesson_data["vocabulary"]],
        phrases=[(str(a), str(b)) for a, b in lesson_data["phrases"]],
        grammar=[str(item) for item in lesson_data["grammar"]],
        exercise=str(lesson_data["exercise"]),
        mini_challenge=str(lesson_data["mini_challenge"]),
        source=str(lesson_data["source"]),
        source_detail=str(lesson_data.get("source_detail", "")),
    )
    return target_date, lesson


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the local web UI for the Italian tutor.")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    return parser.parse_args()


def main() -> int:
    load_env_file()
    args = parse_args()
    server = ThreadingHTTPServer((args.host, args.port), TutorHandler)
    print(f"Web UI running at http://{args.host}:{args.port}")
    server.serve_forever()
    return 0
