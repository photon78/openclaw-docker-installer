#!/usr/bin/env python3
"""
Mistral OCR — Text aus Bild/PDF extrahieren
Usage: python3 ocr.py --input <pfad_oder_url> [--pages N]
"""

import os
import sys
import argparse
import base64
import json
import urllib.request
import urllib.error

API_KEY = os.environ.get("MISTRAL_API_KEY", "")
API_URL = "https://api.mistral.ai/v1/ocr"

def encode_file(path):
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode()

def is_url(s):
    return s.startswith("http://") or s.startswith("https://")

def ocr(input_path, pages=None):
    if not API_KEY:
        print("ERROR: MISTRAL_API_KEY nicht gesetzt", file=sys.stderr)
        sys.exit(1)

    # Document aufbauen
    if is_url(input_path):
        if input_path.lower().endswith(".pdf"):
            doc = {"type": "document_url", "document_url": input_path}
        else:
            doc = {"type": "image_url", "image_url": input_path}
    else:
        # Lokale Datei
        ext = input_path.lower().split(".")[-1]
        data = encode_file(input_path)
        if ext == "pdf":
            doc = {"type": "document_url", "document_url": f"data:application/pdf;base64,{data}"}
        else:
            mime = "image/jpeg" if ext in ("jpg", "jpeg") else f"image/{ext}"
            doc = {"type": "image_url", "image_url": f"data:{mime};base64,{data}"}

    payload = {
        "model": "mistral-ocr-latest",
        "document": doc
    }
    if pages:
        payload["pages"] = list(range(pages))

    req = urllib.request.Request(
        API_URL,
        data=json.dumps(payload).encode(),
        headers={
            "Authorization": f"Bearer {API_KEY}",
            "Content-Type": "application/json"
        }
    )

    try:
        with urllib.request.urlopen(req) as resp:
            result = json.loads(resp.read())
        for page in result.get("pages", []):
            print(page.get("markdown", ""))
    except urllib.error.HTTPError as e:
        print(f"API Fehler {e.code}: {e.read().decode()}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Mistral OCR")
    parser.add_argument("--input", required=True, help="Pfad oder URL zu Bild/PDF")
    parser.add_argument("--pages", type=int, help="Anzahl Seiten (optional)")
    args = parser.parse_args()
    ocr(args.input, args.pages)
