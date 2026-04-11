#!/usr/bin/env python3
"""
Mistral OCR — Text + eingebettete Bilder aus Bild/PDF extrahieren.

Die OCR-API liefert für jedes eingebettete Bild:
  - image_base64: Rohdaten (kann proprietäres Format sein)
  - top_left_x/y, bottom_right_x/y: Bounding-Box im Original (0.0–1.0)

Für Bild-Extraktion nutzen wir die Bounding-Box + Pillow,
um direkt aus dem Original-Scan zu croppen → immer valides JPEG.

Usage:
  python3 ocr.py --input <pfad_oder_url>
  python3 ocr.py --input <pfad> --extract-images [--output-dir /pfad/]
  python3 ocr.py --input <pfad> --extract-images --send [--target 8620748747]
  python3 ocr.py --input <pfad> --debug   # Rohe API-Response ausgeben
"""

import os
import sys
import argparse
import base64
import json
import shutil
import subprocess
import urllib.request
import urllib.error
from pathlib import Path

API_KEY = os.environ.get("MISTRAL_API_KEY", "")
API_URL = "https://api.mistral.ai/v1/ocr"
SHARED_OUTPUT = Path.home() / ".openclaw" / "workspace" / "shared-output"


def encode_file(path: str) -> str:
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode()


def is_url(s: str) -> bool:
    return s.startswith("http://") or s.startswith("https://")


def send_telegram(image_path: str, target: str = "8620748747") -> bool:
    """Bild via openclaw message send an Telegram schicken."""
    SHARED_OUTPUT.mkdir(parents=True, exist_ok=True)
    dest = SHARED_OUTPUT / Path(image_path).name
    if str(dest) != str(image_path):
        shutil.copy(image_path, dest)
    cmd = ["openclaw", "message", "send",
           "--channel", "telegram",
           "--target", target,
           "--media", str(dest)]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode == 0:
        print(f"✅ Telegram gesendet: {result.stdout.strip()}")
        return True
    else:
        print(f"❌ Telegram-Fehler: {result.stderr.strip()}", file=sys.stderr)
        return False


def crop_from_original(input_path: str, bbox: dict, page_dims: dict, out_path: str) -> str:
    """
    Cropped ein Bild aus dem Original-Scan anhand der Bounding-Box.
    bbox: absolute Pixelkoordinaten im OCR-verarbeiteten Raum
    page_dims: {"width": N, "height": N} — OCR-Bildgrösse
    Koordinaten werden auf die Original-Bildgrösse skaliert.
    """
    try:
        from PIL import Image
    except ImportError:
        print("❌ Pillow nicht installiert: pip install pillow", file=sys.stderr)
        sys.exit(1)

    img = Image.open(input_path)
    orig_w, orig_h = img.size

    ocr_w = page_dims.get("width", orig_w)
    ocr_h = page_dims.get("height", orig_h)

    # Skalierungsfaktor OCR → Original
    scale_x = orig_w / ocr_w
    scale_y = orig_h / ocr_h

    x1 = int(bbox.get("top_left_x", 0) * scale_x)
    y1 = int(bbox.get("top_left_y", 0) * scale_y)
    x2 = int(bbox.get("bottom_right_x", orig_w) * scale_x)
    y2 = int(bbox.get("bottom_right_y", orig_h) * scale_y)

    # Clipping
    x1, y1 = max(0, x1), max(0, y1)
    x2, y2 = min(orig_w, x2), min(orig_h, y2)

    print(f"📐 OCR-Raum: {ocr_w}x{ocr_h}px | Original: {orig_w}x{orig_h}px | Scale: {scale_x:.2f}x{scale_y:.2f}")
    print(f"📐 Crop: x1={x1}, y1={y1}, x2={x2}, y2={y2}")

    cropped = img.crop((x1, y1, x2, y2)).convert("RGB")
    cropped.save(out_path, "JPEG", quality=92)
    print(f"✅ Gespeichert: {out_path} ({cropped.size[0]}x{cropped.size[1]}px)")
    return out_path


def ocr(input_path, pages=None, extract_images=False, output_dir=None,
        send=False, target="8620748747", debug=False):
    if not API_KEY:
        print("ERROR: MISTRAL_API_KEY nicht gesetzt", file=sys.stderr)
        sys.exit(1)

    # Dokument aufbauen
    if is_url(input_path):
        doc = {"type": "document_url", "document_url": input_path} \
              if input_path.lower().endswith(".pdf") \
              else {"type": "image_url", "image_url": input_path}
    else:
        ext = input_path.lower().split(".")[-1]
        data = encode_file(input_path)
        if ext == "pdf":
            doc = {"type": "document_url",
                   "document_url": f"data:application/pdf;base64,{data}"}
        else:
            mime = "image/jpeg" if ext in ("jpg", "jpeg") else f"image/{ext}"
            doc = {"type": "image_url",
                   "image_url": f"data:{mime};base64,{data}"}

    payload = {
        "model": "mistral-ocr-latest",
        "document": doc,
        "include_image_base64": False,
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
    except urllib.error.HTTPError as e:
        print(f"API Fehler {e.code}: {e.read().decode()}", file=sys.stderr)
        sys.exit(1)

    if debug:
        print(json.dumps(result, indent=2, ensure_ascii=False))
        return []

    for page in result.get("pages", []):
        print(page.get("markdown", ""))

    if extract_images:
        out_dir = Path(output_dir) if output_dir else SHARED_OUTPUT
        out_dir.mkdir(parents=True, exist_ok=True)
        extracted = []

        for page_idx, page in enumerate(result.get("pages", [])):
            images = page.get("images", [])
            if not images:
                print(f"ℹ️ Seite {page_idx}: Keine eingebetteten Bilder.", file=sys.stderr)
                continue

            for img_meta in images:
                img_id = img_meta.get("id", f"img_{page_idx}")
                safe_name = img_id.replace("/", "_").replace(":", "_")
                if not safe_name.lower().endswith((".jpg", ".jpeg", ".png")):
                    safe_name += ".jpg"
                out_path = str(out_dir / safe_name)

                bbox = {
                    "top_left_x":     img_meta.get("top_left_x", 0),
                    "top_left_y":     img_meta.get("top_left_y", 0),
                    "bottom_right_x": img_meta.get("bottom_right_x", 9999),
                    "bottom_right_y": img_meta.get("bottom_right_y", 9999),
                }
                page_dims = page.get("dimensions", {})

                if not is_url(input_path):
                    crop_from_original(input_path, bbox, page_dims, out_path)
                    extracted.append(out_path)
                    if send:
                        send_telegram(out_path, target)
                else:
                    print("⚠️ Crop aus URL nicht unterstützt — nutze --input mit lokalem Pfad.")

        if not extracted:
            print("ℹ️ Keine Bilder extrahiert.")
        return extracted

    return []


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Mistral OCR — Text + Bilder aus Dokumenten extrahieren"
    )
    parser.add_argument("--input", required=True, help="Pfad oder URL zu Bild/PDF")
    parser.add_argument("--pages", type=int, help="Anzahl Seiten (optional)")
    parser.add_argument("--extract-images", action="store_true",
                        help="Eingebettete Bilder via Bounding-Box aus Original croppen")
    parser.add_argument("--output-dir", help="Ausgabeverzeichnis (default: shared-output)")
    parser.add_argument("--send", action="store_true",
                        help="Extrahierte Bilder via Telegram senden")
    parser.add_argument("--target", default="8620748747", help="Telegram Chat-ID")
    parser.add_argument("--debug", action="store_true",
                        help="Rohe API-Response ausgeben (für Debugging)")
    args = parser.parse_args()

    ocr(
        args.input,
        pages=args.pages,
        extract_images=args.extract_images,
        output_dir=args.output_dir,
        send=args.send,
        target=args.target,
        debug=args.debug,
    )
