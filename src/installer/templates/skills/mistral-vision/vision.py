#!/usr/bin/env python3
"""
mistral-vision — Skill für Bildanalyse und OCR via Mistral Vision API.

Funktionen:
- OCR: Text aus Bildern extrahieren (z. B. Rechnungen, Formulare).
- Metadaten: Dokumententyp + Beschreibung generieren.
- Barcode/QR-Code: Optional (via pyzbar).

Aufruf:
  python3 vision.py --image <path/url> --output json|text
"""

import argparse
import base64
import json
import os
from pathlib import Path
from typing import Optional, Dict, Any

import httpx
from PIL import Image
from mistralai.client import MistralClient
from mistralai.models.chat_completion import ChatMessage

# --- Config ---
MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY")
MISTRAL_MODEL = "mistral-large-latest"  # Vision-fähig

client = MistralClient(api_key=MISTRAL_API_KEY)


def encode_image(image_path: str) -> str:
    """Bild in Base64 kodieren."""
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")


def analyze_image(image_path: str, prompt: str) -> Dict[str, Any]:
    """Bild via Mistral Vision API analysieren."""
    base64_image = encode_image(image_path)

    messages = [
        ChatMessage(
            role="user",
            content=[
                {"type": "text", "text": prompt},
                {
                    "type": "image_url",
                    "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"},
                },
            ],
        )
    ]

    response = client.chat_completion(
        model=MISTRAL_MODEL,
        messages=messages,
        max_tokens=1024,
    )

    return json.loads(response.choices[0].message.content)


def extract_text_and_metadata(image_path: str) -> Dict[str, Any]:
    """Text + Metadaten aus Bild extrahieren."""
    prompt = (
        "Analysiere dieses Dokument und gib folgende Informationen im JSON-Format zurück:\n"
        "- 'text': Der extrahierte Text (OCR).\n"
        "- 'metadata': {\n"
        "    'document_type': Typ des Dokuments (z. B. 'Rechnung', 'Vertrag'),\n"
        "    'description': Kurze Beschreibung (1 Satz),\n"
        "    'confidence': Konfidenzscore (0.0-1.0)\n"
        "  }"
    )

    return analyze_image(image_path, prompt)


def main():
    parser = argparse.ArgumentParser(description="Mistral Vision Skill: OCR + Metadaten-Extraktion")
    parser.add_argument("--image", type=str, required=True, help="Pfad oder URL zum Bild")
    parser.add_argument(
        "--output",
        type=str,
        choices=["json", "text"],
        default="json",
        help="Ausgabeformat (json oder text)",
    )
    args = parser.parse_args()

    result = extract_text_and_metadata(args.image)

    if args.output == "json":
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        print(f"Text:\n{result['text']}\n")
        print(f"Metadaten:\n{json.dumps(result['metadata'], indent=2, ensure_ascii=False)}")


if __name__ == "__main__":
    main()
