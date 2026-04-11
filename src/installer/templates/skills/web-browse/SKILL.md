---
name: web-browse
description: Headless browser skill via Playwright for JavaScript-heavy pages (SPAs, booking sites). Use when web_fetch or docs-summarize return empty or broken output.
metadata: {"openclaw": {"requires": {"bins": ["chromium"]}, "emoji": "🌐"}}
---

## Wann verwenden
- `web_fetch` oder `docs-summarize` liefern leeren/unbrauchbaren Output
- Booking.com, TripAdvisor, Instagram, moderne SPAs
- Dynamisch geladene Inhalte (React, Vue, Angular)

## Voraussetzungen
Playwright installieren (einmalig):
```bash
pip install playwright
# Kein 'playwright install chromium' — nutzt /usr/bin/chromium (bereits installiert)
```

## Verwendung
```bash
# Text extrahieren → stdout
python3 {baseDir}/browse.py --url "https://..."

# In Datei speichern
python3 {baseDir}/browse.py --url "https://..." --output result.md

# Screenshot
python3 {baseDir}/browse.py --url "https://..." --screenshot shot.png

# Timeout anpassen (default 30s, max 120s)
python3 {baseDir}/browse.py --url "https://..." --timeout 60
```

## Output
Extrahierter Seitentext als Markdown (Titel, URL, bereinigter Text).
Scripts, Styles, Nav, Footer werden entfernt.

## Constraints
- **Nur lesen** — kein Login, kein Formular-Submit
- **Max. 1 Instanz gleichzeitig** — RAM-Limit
- **Kein Scraping im Loop** — einzelne Anfragen, keine Batch-Crawls
