#!/usr/bin/env python3
"""
Mistral Audio Transcription — Voxtral
Usage: python3 transcribe.py --input <pfad> [--lang de]
"""

import os
import sys
import argparse
import json
import urllib.request
import urllib.error

API_KEY = os.environ.get("MISTRAL_API_KEY", "")
API_URL = "https://api.mistral.ai/v1/audio/transcriptions"

def transcribe(input_path, lang=None):
    if not API_KEY:
        print("ERROR: MISTRAL_API_KEY nicht gesetzt", file=sys.stderr)
        sys.exit(1)

    # Multipart form-data bauen
    boundary = "----ZotBoundary"
    ext = input_path.lower().split(".")[-1]
    mime_map = {
        "mp3": "audio/mpeg",
        "wav": "audio/wav",
        "ogg": "audio/ogg",
        "m4a": "audio/mp4",
        "webm": "audio/webm",
        "flac": "audio/flac"
    }
    mime = mime_map.get(ext, "audio/mpeg")

    with open(input_path, "rb") as f:
        file_data = f.read()

    filename = os.path.basename(input_path)

    body = (
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="model"\r\n\r\n'
        f"voxtral-mini-2507\r\n"
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="file"; filename="{filename}"\r\n'
        f"Content-Type: {mime}\r\n\r\n"
    ).encode() + file_data + f"\r\n--{boundary}".encode()

    if lang:
        body += (
            f"\r\nContent-Disposition: form-data; name=\"language\"\r\n\r\n{lang}\r\n"
            f"--{boundary}"
        ).encode()

    body += b"--\r\n"

    req = urllib.request.Request(
        API_URL,
        data=body,
        headers={
            "Authorization": f"Bearer {API_KEY}",
            "Content-Type": f"multipart/form-data; boundary={boundary}"
        }
    )

    try:
        with urllib.request.urlopen(req) as resp:
            result = json.loads(resp.read())
        print(result.get("text", ""))
    except urllib.error.HTTPError as e:
        print(f"API Fehler {e.code}: {e.read().decode()}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Mistral Audio Transcription")
    parser.add_argument("--input", required=True, help="Pfad zur Audio-Datei")
    parser.add_argument("--lang", help="Sprache (z.B. de, fr, en) optional")
    args = parser.parse_args()
    transcribe(args.input, args.lang)
