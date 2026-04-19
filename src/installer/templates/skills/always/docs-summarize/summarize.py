#!/usr/bin/env python3
"""
docs-summarize — Erstellt eine strukturierte Working Reference aus API/Framework-Docs.

Usage:
  python3 summarize.py <url-oder-pfad> [--permanent] [--task <name>] [--name <name>] [--model <model>]

Beispiele:
  python3 summarize.py https://docs.example.com/api --permanent --name myapi
  python3 summarize.py /home/user/docs/manual.md --task myproject
"""

import os
import sys
import argparse
import json
import re
from datetime import date
from pathlib import Path

try:
    import requests
except ImportError:
    print("FEHLER: 'requests' nicht verfügbar. Bitte sicherstellen dass requests installiert ist.", file=sys.stderr)
    sys.exit(1)

# ── Konfiguration ────────────────────────────────────────────────
MISTRAL_API_URL = "https://api.mistral.ai/v1/chat/completions"
DEFAULT_MODEL = os.environ.get("LLM_BUDGET", "mistral/mistral-large-latest").replace("mistral/", "")
MAX_CONTENT_CHARS = 40000  # Mistral context limit buffer

WORKSPACE = Path(os.environ.get("OPENCLAW_WORKSPACE", Path.home() / ".openclaw/workspace"))

SUMMARY_PROMPT = """Du bist ein technischer Dokumentations-Analyst. 
Analysiere die folgende Dokumentation und erstelle eine kompakte, strukturierte Working Reference.

Halte dich GENAU an dieses Schema:

# Docs Reference: <Tool/Framework Name>
## Scope
- Version: (falls bekannt, sonst "unbekannt")
- Quelle: <URL oder Dateiname>
- Datum: {today}

## Core Commands / Endpoints
(Die wichtigsten Befehle/Endpoints — max 15, mit kurzer Beschreibung)

## Parameters
| Name | Typ | Pflicht | Default | Beschreibung |
|------|-----|---------|---------|--------------|
(Wichtigste Parameter — max 20)

## Supported Patterns
(Typische Anwendungsmuster — 3-7 Punkte)

## Gotchas & Known Limits
(Fallstricke, Einschränkungen, häufige Fehler — 3-7 Punkte)

## Minimal Examples
```
(2-4 minimale, funktionierende Beispiele)
```

## Source Sections
(Welche Abschnitte der Originaldoku wurden verarbeitet)

---
Dokumentation:

{content}
"""


def fetch_url(url: str) -> str:
    """Holt Inhalt einer URL."""
    print(f"Lade URL: {url}", file=sys.stderr)
    try:
        resp = requests.get(url, timeout=30, headers={"User-Agent": "docs-summarize/1.0"})
        resp.raise_for_status()
        # Einfaches HTML-Stripping für HTML-Seiten
        content = resp.text
        if resp.headers.get("content-type", "").startswith("text/html"):
            content = re.sub(r"<script[^>]*>.*?</script>", "", content, flags=re.DOTALL)
            content = re.sub(r"<style[^>]*>.*?</style>", "", content, flags=re.DOTALL)
            content = re.sub(r"<[^>]+>", " ", content)
            content = re.sub(r"\s{3,}", "\n\n", content)
        return content
    except requests.RequestException as e:
        print(f"FEHLER beim Laden der URL: {e}", file=sys.stderr)
        sys.exit(1)


def read_file(path: str) -> str:
    """Liest lokale Datei."""
    p = Path(path)
    if not p.exists():
        print(f"FEHLER: Datei nicht gefunden: {path}", file=sys.stderr)
        sys.exit(1)
    print(f"Lese Datei: {p}", file=sys.stderr)
    try:
        return p.read_text(encoding="utf-8")
    except Exception as e:
        print(f"FEHLER beim Lesen der Datei: {e}", file=sys.stderr)
        sys.exit(1)


def call_mistral(content: str, model: str) -> str:
    """Ruft Mistral API auf und gibt Summary zurück."""
    api_key = os.environ.get("MISTRAL_API_KEY")
    if not api_key:
        print("FEHLER: MISTRAL_API_KEY nicht gesetzt.", file=sys.stderr)
        sys.exit(1)

    # Content kürzen falls nötig
    if len(content) > MAX_CONTENT_CHARS:
        print(f"WARN: Content auf {MAX_CONTENT_CHARS} Zeichen gekürzt (Original: {len(content)})", file=sys.stderr)
        content = content[:MAX_CONTENT_CHARS] + "\n\n[... gekürzt ...]"

    prompt = SUMMARY_PROMPT.format(content=content, today=date.today().isoformat())

    payload = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.2,
        "max_tokens": 4096,
    }

    print(f"Rufe Mistral API auf (Modell: {model})...", file=sys.stderr)
    try:
        resp = requests.post(
            MISTRAL_API_URL,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json=payload,
            timeout=240,
        )
        resp.raise_for_status()
        data = resp.json()
        return data["choices"][0]["message"]["content"]
    except requests.RequestException as e:
        print(f"FEHLER bei Mistral API: {e}", file=sys.stderr)
        if hasattr(e, "response") and e.response is not None:
            print(f"Response: {e.response.text}", file=sys.stderr)
        sys.exit(1)
    except (KeyError, json.JSONDecodeError) as e:
        print(f"FEHLER beim Parsen der API-Antwort: {e}", file=sys.stderr)
        sys.exit(1)


def derive_name(source: str) -> str:
    """Leitet einen Dateinamen aus URL oder Pfad ab."""
    # URL: letztes Pfadsegment oder Domain
    if source.startswith("http"):
        path_part = source.rstrip("/").split("/")[-1] or source.split("/")[2].split(".")[0]
        name = re.sub(r"[^a-z0-9-]", "-", path_part.lower())
    else:
        name = Path(source).stem.lower()
    name = re.sub(r"-+", "-", name).strip("-")
    return name or "docs"


def determine_output_path(name: str, permanent: bool, task: str | None) -> Path:
    """Bestimmt den Ausgabepfad."""
    if task:
        out = WORKSPACE / "work" / task / "docs-summary.md"
    elif permanent:
        out = WORKSPACE / "memory" / "docs" / f"docs-{name}.md"
    else:
        out = WORKSPACE / f"docs-{name}.md"
    return out


def main():
    parser = argparse.ArgumentParser(description="Docs summarizer via Mistral API")
    parser.add_argument("source", help="URL oder Dateipfad zur Dokumentation")
    parser.add_argument("--permanent", action="store_true", help="In memory/topics/ speichern")
    parser.add_argument("--task", metavar="NAME", help="In work/<name>/ speichern")
    parser.add_argument("--name", metavar="NAME", help="Output-Dateiname überschreiben")
    parser.add_argument("--model", default=DEFAULT_MODEL, help=f"Mistral Modell (default: {DEFAULT_MODEL})")
    args = parser.parse_args()

    # Inhalt laden
    if args.source.startswith("http://") or args.source.startswith("https://"):
        content = fetch_url(args.source)
    else:
        content = read_file(args.source)

    if not content.strip():
        print("FEHLER: Inhalt ist leer.", file=sys.stderr)
        sys.exit(1)

    # Mistral aufrufen
    summary = call_mistral(content, args.model)

    # Ausgabepfad bestimmen
    name = args.name or derive_name(args.source)
    out_path = determine_output_path(name, args.permanent, args.task)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    # Schreiben
    out_path.write_text(summary, encoding="utf-8")
    print(f"✅ Summary gespeichert: {out_path}", file=sys.stderr)

    # Auch auf stdout für direktes Pipen
    print(summary)


if __name__ == "__main__":
    main()
