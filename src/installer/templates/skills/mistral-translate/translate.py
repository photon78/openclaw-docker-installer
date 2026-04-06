#!/usr/bin/env python3
"""
Mistral Translation via Chat Completions
Usage: python3 translate.py --text "..." --to de [--from en]
       python3 translate.py --file <pfad> --to fr
"""

import os
import sys
import argparse
import json
import urllib.request
import urllib.error

API_KEY = os.environ.get("MISTRAL_API_KEY", "")
API_URL = "https://api.mistral.ai/v1/chat/completions"
DEFAULT_MODEL = os.environ.get("LLM_BUDGET", "mistral/mistral-large-latest").replace("mistral/", "")

LANG_NAMES = {
    "de": "German", "fr": "French", "en": "English",
    "it": "Italian", "es": "Spanish", "pt": "Portuguese",
    "nl": "Dutch", "pl": "Polish", "ru": "Russian",
    "ja": "Japanese", "zh": "Chinese"
}

def translate(text, to_lang, from_lang=None):
    if not API_KEY:
        print("ERROR: MISTRAL_API_KEY nicht gesetzt", file=sys.stderr)
        sys.exit(1)

    to_name = LANG_NAMES.get(to_lang, to_lang)
    if from_lang:
        from_name = LANG_NAMES.get(from_lang, from_lang)
        system = f"You are a professional translator. Translate the following text from {from_name} to {to_name}. Output only the translated text, nothing else."
    else:
        system = f"You are a professional translator. Translate the following text to {to_name}. Output only the translated text, nothing else."

    payload = {
        "model": DEFAULT_MODEL,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": text}
        ],
        "temperature": 0.1
    }

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
        print(result["choices"][0]["message"]["content"])
    except urllib.error.HTTPError as e:
        print(f"API Fehler {e.code}: {e.read().decode()}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Mistral Translation")
    parser.add_argument("--text", help="Text zum Übersetzen")
    parser.add_argument("--file", help="Datei zum Übersetzen")
    parser.add_argument("--to", required=True, help="Zielsprache (z.B. de, fr, en)")
    parser.add_argument("--from", dest="from_lang", help="Quellsprache (optional)")
    args = parser.parse_args()

    if args.file:
        with open(args.file, "r", encoding="utf-8") as f:
            text = f.read()
    elif args.text:
        text = args.text
    else:
        text = sys.stdin.read()

    translate(text, args.to, args.from_lang)
