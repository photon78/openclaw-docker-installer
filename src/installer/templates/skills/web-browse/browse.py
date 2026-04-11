#!/usr/bin/env python3
"""
web-browse/browse.py — Headless Browser Skill via Playwright
Rendert JavaScript-lastige Seiten (SPAs, Booking.com, TripAdvisor, etc.)
Nutzt System-Chromium (/usr/bin/chromium) — kein Playwright-eigenes Binary nötig.

Verwendung:
  python3 browse.py --url "https://www.booking.com/hotel/..."
  python3 browse.py --url "https://..." --output result.md
  python3 browse.py --url "https://..." --screenshot screenshot.png
  python3 browse.py --url "https://..." --timeout 60

Constraints:
  - Nur lesen (kein Login, kein Formular-Submit)
  - Maximal eine Browser-Instanz gleichzeitig (RAM-Limit)
  - Timeout: 30s default, max 120s
"""
import argparse
import sys
import os
from pathlib import Path

# System-Chromium (bereits installiert)
SYSTEM_CHROMIUM = "/usr/bin/chromium"

def check_playwright() -> bool:
    """Prüft ob playwright installiert ist."""
    try:
        import playwright  # noqa: F401
        return True
    except ImportError:
        return False


def browse(url: str, timeout: int = 30, screenshot_path: str | None = None) -> str:
    """
    Ruft URL auf, rendert JS, gibt Text/Markdown zurück.
    Returns: Extrahierter Seiteninhalt als Text
    """
    from playwright.sync_api import sync_playwright

    # System-Chromium verwenden wenn verfügbar
    chromium_path = SYSTEM_CHROMIUM if Path(SYSTEM_CHROMIUM).exists() else None

    with sync_playwright() as p:
        launch_kwargs = {
            "args": [
                "--no-sandbox",
                "--disable-setuid-sandbox",
                "--disable-dev-shm-usage",
                "--disable-gpu",
                "--single-process",
                "--memory-pressure-off",
            ],
            "timeout": timeout * 1000,
        }
        if chromium_path:
            launch_kwargs["executable_path"] = chromium_path

        browser = p.chromium.launch(**launch_kwargs)
        context = browser.new_context(
            viewport={"width": 1280, "height": 800},
            user_agent=(
                "Mozilla/5.0 (X11; Linux aarch64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            ),
        )
        page = context.new_page()

        try:
            page.goto(url, wait_until="networkidle", timeout=timeout * 1000)
        except Exception:
            # Fallback: load statt networkidle
            page.goto(url, wait_until="load", timeout=timeout * 1000)

        # Screenshot wenn gewünscht
        if screenshot_path:
            page.screenshot(path=screenshot_path, full_page=True)

        # Text extrahieren
        content = page.evaluate("""
            () => {
                // Entfernt Scripts, Styles, Nav, Footer
                const remove = ['script', 'style', 'nav', 'footer', 'header',
                                'noscript', 'iframe', 'svg', 'button', 'form'];
                remove.forEach(tag => {
                    document.querySelectorAll(tag).forEach(el => el.remove());
                });
                return document.body ? document.body.innerText : '';
            }
        """)

        title = page.title()
        browser.close()

    # Text aufräumen
    lines = [line.strip() for line in content.splitlines()]
    cleaned = []
    prev_empty = False
    for line in lines:
        if not line:
            if not prev_empty:
                cleaned.append("")
            prev_empty = True
        else:
            cleaned.append(line)
            prev_empty = False

    result = "\n".join(cleaned).strip()
    return f"# {title}\n\nURL: {url}\n\n---\n\n{result}"


def main() -> None:
    parser = argparse.ArgumentParser(description="Headless browser — rendert JS-Seiten")
    parser.add_argument("--url", required=True, help="URL zum Laden")
    parser.add_argument("--output", help="Ausgabe-Datei (Markdown), default: stdout")
    parser.add_argument("--screenshot", help="Screenshot-Pfad (.png)")
    parser.add_argument(
        "--timeout", type=int, default=30,
        help="Timeout in Sekunden (default: 30, max: 120)"
    )
    args = parser.parse_args()

    # Playwright-Check
    if not check_playwright():
        print(
            "❌ playwright nicht installiert.\n"
            "Installation: pip install playwright\n"
            "Kein 'playwright install chromium' nötig — System-Chromium wird genutzt.",
            file=sys.stderr,
        )
        sys.exit(1)

    timeout = min(max(args.timeout, 5), 120)

    try:
        content = browse(args.url, timeout=timeout, screenshot_path=args.screenshot)
    except Exception as e:
        print(f"❌ Browse-Fehler: {e}", file=sys.stderr)
        sys.exit(1)

    if args.output:
        out = Path(args.output)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(content)
        lines = content.count("\n")
        print(f"✅ Gespeichert: {args.output} ({lines} Zeilen)")
        if args.screenshot:
            print(f"   Screenshot: {args.screenshot}")
    else:
        print(content)


if __name__ == "__main__":
    main()
