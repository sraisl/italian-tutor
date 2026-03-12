# Taegliche Italienisch-Lektionen

Kleines `uv`-Projekt fuer taegliche Italienisch-Lektionen auf Anfaenger-Niveau.

Das System arbeitet jetzt hybrid:

- ein fester Kursplan bestimmt Thema, Ziel und Grammatikfokus
- LM Studio erzeugt daraus die konkrete Tageslektion
- wenn LM Studio nicht erreichbar ist, faellt die App auf ein lokales Template zurueck
- Lektionen koennen lokal gespeichert und optional nach Notion geschickt werden

## CLI

```bash
uv run italian-lesson
```

Wenn `uv` bei dir wegen Hardlinks warnt, kannst du optional so starten:

```bash
UV_LINK_MODE=copy uv run italian-lesson
```

Fuer ein bestimmtes Datum:

```bash
uv run italian-lesson --date 2026-03-12
```

Mit Notion-Export:

```bash
cp .env.example .env
uv run italian-lesson --push-notion
```

## Webinterface

```bash
uv run italian-web
```

Dann im Browser:

```text
http://127.0.0.1:8765
```

Im Webinterface kannst du:

- eine Lektion fuer ein Datum generieren
- sie lokal als Markdown und JSON speichern
- sie direkt nach Notion senden

## LM Studio einrichten

1. Starte in LM Studio einen lokalen Server im OpenAI-kompatiblen Modus.
2. Pruefe, dass der Endpoint `http://127.0.0.1:1234/v1` erreichbar ist.
3. Trage optional `LM_STUDIO_BASE_URL` und `LM_STUDIO_MODEL` in `.env` ein.

Standardwerte:

```env
LM_STUDIO_BASE_URL=http://127.0.0.1:1234/v1
LM_STUDIO_MODEL=local-model
```

Wichtig:

- `local-model` ist nur ein Platzhalter.
- Falls dein LM-Studio-Server einen konkreten Modellnamen erwartet, setze ihn in `.env`.

## Notion einrichten

1. Erstelle in Notion eine Integration und kopiere das Secret in `NOTION_TOKEN`.
2. Teile die Ziel-Datenbank oder Ziel-Seite mit dieser Integration.
3. Trage entweder `NOTION_DATABASE_ID` oder `NOTION_PARENT_PAGE_ID` in `.env` ein.
4. Wenn du eine Datenbank nutzt und die Spalten nicht `Name` und `Date` heissen, passe `NOTION_TITLE_PROPERTY` und `NOTION_DATE_PROPERTY` an.

## Taeglich automatisch ausfuehren

Beispiel mit `launchd` auf macOS:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
  <dict>
    <key>Label</key>
    <string>com.sraisl.italianlesson</string>
    <key>ProgramArguments</key>
    <array>
      <string>/opt/homebrew/bin/uv</string>
      <string>run</string>
      <string>italian-lesson</string>
      <string>--push-notion</string>
    </array>
    <key>WorkingDirectory</key>
    <string>/Volumes/480GB External/Code/tutor</string>
    <key>StartCalendarInterval</key>
    <dict>
      <key>Hour</key>
      <integer>7</integer>
      <key>Minute</key>
      <integer>30</integer>
    </dict>
    <key>StandardOutPath</key>
    <string>/tmp/italian-lesson.out</string>
    <key>StandardErrorPath</key>
    <string>/tmp/italian-lesson.err</string>
  </dict>
</plist>
```

Danach laden mit:

```bash
launchctl load ~/Library/LaunchAgents/com.sraisl.italianlesson.plist
```

## Hinweise

- Der Kurs rotiert aktuell ueber 14 Anfaenger-Lektionen.
- Die CLI wurde lokal mit `uv run italian-lesson --date 2026-03-13` verifiziert.
- Der Webserver startet lokal mit `uv run italian-web`.
- Wenn du willst, kann ich als naechstes Auto-Save nach Notion oder eine Verlaufsliste im Webinterface einbauen.
