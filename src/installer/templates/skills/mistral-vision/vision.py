#!/usr/bin/env python3
"""
mistral-vision — Skill für Bildanalyse via Mistral Vision API (SDK v1.x).

Funktionen:
- Bild analysieren und beschreiben
- Text aus Bildern extrahieren (OCR)
- Metadaten: Dokumententyp + Beschreibung + Konfidenz

Aufruf:
  python3 vision.py --image <pfad_oder_url> --output json|text
  python3 vision.py --image <pfad> --prompt "Was ist auf diesem Bild?"
"""

import sys
from pathlib import Path

# Auto-restart with venv python if mistralai is not available
_VENV_PY = Path(__file__).resolve().parent / ".venv" / "bin" / "python3"
if _VENV_PY.exists() and Path(sys.executable).resolve() != _VENV_PY:
    try:
        import mistralai  # noqa: F401
    except ImportError:
        import os
        os.execv(str(_VENV_PY), [str(_VENV_PY)] + sys.argv)

import argparse
import base64
import json
import os
from typing import Any

try:
    from mistralai import Mistral          # SDK v1.x
except ImportError:
    from mistralai.client import Mistral   # SDK v2.x

# --- Config ---
MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY")
# pixtral-large-latest: aktueller stabiler Alias (pixtral-12b-2409 ist deprecated)
MISTRAL_MODEL = os.getenv("MISTRAL_VISION_MODEL", "pixtral-large-latest")

client = Mistral(api_key=MISTRAL_API_KEY)


def encode_image(image_path: str) -> tuple[str, str]:
    """Bild in Base64 kodieren. Gibt (base64_data, mime_type) zurück."""
    path = Path(image_path)
    ext = path.suffix.lower()
    mime_map = {".jpg": "image/jpeg", ".jpeg": "image/jpeg",
                ".png": "image/png", ".webp": "image/webp", ".gif": "image/gif"}
    mime = mime_map.get(ext, "image/jpeg")
    with open(image_path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8"), mime


def analyze_image(image_source: str, prompt: str) -> Any:
    """Bild via Mistral Vision API analysieren. image_source = Pfad oder URL."""
    if image_source.startswith("http://") or image_source.startswith("https://"):
        image_content = {"type": "image_url", "image_url": image_source}
    else:
        b64, mime = encode_image(image_source)
        image_content = {
            "type": "image_url",
            "image_url": f"data:{mime};base64,{b64}",
        }

    messages = [
        {
            "role": "user",
            "content": [
                {"type": "text", "text": prompt},
                image_content,
            ],
        }
    ]

    response = client.chat.complete(
        model=MISTRAL_MODEL,
        messages=messages,
        max_tokens=1024,
    )

    return response.choices[0].message.content


def extract_text_and_metadata(image_source: str) -> dict[str, Any]:
    """Text + Metadaten aus Bild extrahieren. Gibt geparste JSON-Struktur zurück."""
    prompt = (
        "Analysiere dieses Dokument und gib folgende Informationen im JSON-Format zurück:\n"
        "- 'text': Der extrahierte Text (OCR).\n"
        "- 'metadata': {\n"
        "    'document_type': Typ des Dokuments (z. B. 'Rechnung', 'Vertrag', 'Foto'),\n"
        "    'description': Kurze Beschreibung (1 Satz),\n"
        "    'confidence': Konfidenzscore (0.0-1.0)\n"
        "  }\n"
        "Antworte NUR mit dem JSON-Objekt, ohne Markdown-Blöcke."
    )

    raw = analyze_image(image_source, prompt)

    raw = raw.strip()
    if raw.startswith("```"):
        lines = raw.split("\n")
        raw = "\n".join(lines[1:-1] if lines[-1] == "```" else lines[1:])

    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return {"text": raw, "metadata": {"document_type": "unknown",
                                           "description": "JSON-Parse fehlgeschlagen",
                                           "confidence": 0.0}}


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Mistral Vision Skill: Bildanalyse, OCR, Metadaten"
    )
    parser.add_argument("--image", required=True, help="Pfad oder URL zum Bild")
    parser.add_argument(
        "--output", choices=["json", "text"], default="json",
        help="Ausgabeformat (json oder text)"
    )
    parser.add_argument(
        "--prompt", default=None,
        help="Eigener Prompt statt Standard-OCR-Analyse"
    )
    args = parser.parse_args()

    if args.prompt:
        result_raw = analyze_image(args.image, args.prompt)
        print(result_raw)
        return

    result = extract_text_and_metadata(args.image)

    if args.output == "json":
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        print(f"Text:\n{result.get('text', '')}\n")
        meta = result.get("metadata", {})
        print(f"Typ: {meta.get('document_type', '?')}")
        print(f"Beschreibung: {meta.get('description', '?')}")
        print(f"Konfidenz: {meta.get('confidence', '?')}")


if __name__ == "__main__":
    main()
