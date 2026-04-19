"""
extract.py — Extrahiert eingebettete Fotos aus eingescannten Dokumentseiten.

Workflow:
1. Mistral Vision erkennt Bounding-Box des eingebetteten Fotos
2. Pillow cropped das Foto aus dem Scan
3. OpenCV korrigiert die Ausrichtung (Deskewing)
4. Ausgabe als JPG + optional senden via Telegram

Aufruf:
  python3 extract.py --image <scan.jpg> [--send] [--target <telegram_chat_id>]
"""

import argparse
import base64
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import cv2
import numpy as np
from PIL import Image
from mistralai import Mistral

# --- Config ---
MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY")
MISTRAL_MODEL = "pixtral-12b-latest"
SHARED_OUTPUT = Path("/home/hummer/.openclaw/workspace/shared-output")

client = Mistral(api_key=MISTRAL_API_KEY)


def encode_image(image_path: str) -> str:
    """Bild in Base64 kodieren."""
    with open(image_path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")


def detect_photo_region(image_path: str) -> dict:
    """
    Mistral Vision erkennt die Bounding-Box des eingebetteten Fotos.
    Gibt Koordinaten als relative Werte (0.0–1.0) zurück.
    """
    b64 = encode_image(image_path)
    prompt = (
        "Dieses Bild ist eine eingescannte Buchseite. "
        "Erkenne das eingebettete Foto (nicht den Text) und gib seine Bounding-Box zurück. "
        "Antworte NUR mit einem JSON-Objekt (kein Markdown, kein Text drumherum):\n"
        '{"x": 0.0, "y": 0.0, "width": 1.0, "height": 1.0}\n'
        "Alle Werte sind relative Koordinaten (0.0 = links/oben, 1.0 = rechts/unten). "
        "x und y sind die obere linke Ecke des Fotos."
    )

    response = client.chat.complete(
        model=MISTRAL_MODEL,
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:image/jpeg;base64,{b64}"},
                    },
                ],
            }
        ],
    )

    raw = response.choices[0].message.content.strip()

    # JSON aus Antwort extrahieren (falls Mistral doch Markdown zurückgibt)
    if "```" in raw:
        raw = raw.split("```")[1].replace("json", "").strip()

    return json.loads(raw)


def crop_and_deskew(image_path: str, bbox: dict, output_path: str) -> str:
    """
    Cropped das Foto aus dem Scan und korrigiert die Ausrichtung.

    Args:
        image_path: Pfad zum Scan
        bbox: {"x": 0.0, "y": 0.0, "width": 1.0, "height": 1.0} (relative Koordinaten)
        output_path: Pfad zur Ausgabedatei

    Returns:
        Pfad zur Ausgabedatei
    """
    img = Image.open(image_path)
    w, h = img.size

    # Relative Koordinaten → absolute Pixel
    x = int(bbox["x"] * w)
    y = int(bbox["y"] * h)
    crop_w = int(bbox["width"] * w)
    crop_h = int(bbox["height"] * h)

    # Sicherheits-Clipping (keine negativen Werte)
    x = max(0, x)
    y = max(0, y)
    crop_w = min(crop_w, w - x)
    crop_h = min(crop_h, h - y)

    print(f"📐 Crop-Bereich: x={x}, y={y}, w={crop_w}, h={crop_h}")

    # Crop via Pillow
    cropped = img.crop((x, y, x + crop_w, y + crop_h))

    # Deskewing via OpenCV
    cv_img = cv2.cvtColor(np.array(cropped), cv2.COLOR_RGB2BGR)
    gray = cv2.cvtColor(cv_img, cv2.COLOR_BGR2GRAY)
    edges = cv2.Canny(gray, 50, 150, apertureSize=3)
    lines = cv2.HoughLines(edges, 1, np.pi / 180, threshold=100)

    angle = 0.0
    if lines is not None:
        angles = []
        for line in lines[:20]:
            rho, theta = line[0]
            angle_deg = np.degrees(theta) - 90
            if abs(angle_deg) < 10:  # Nur kleine Korrekturen
                angles.append(angle_deg)
        if angles:
            angle = np.median(angles)
            print(f"🔄 Deskew-Winkel: {angle:.2f}°")

    if abs(angle) > 0.5:
        ch, cw = cv_img.shape[:2]
        M = cv2.getRotationMatrix2D((cw / 2, ch / 2), angle, 1.0)
        cv_img = cv2.warpAffine(cv_img, M, (cw, ch), flags=cv2.INTER_CUBIC,
                                borderMode=cv2.BORDER_REPLICATE)

    # Zurück zu PIL + als JPG speichern
    result = Image.fromarray(cv2.cvtColor(cv_img, cv2.COLOR_BGR2RGB))
    result.save(output_path, "JPEG", quality=92)
    print(f"✅ Extrahiertes Foto gespeichert: {output_path}")
    return output_path


def send_via_telegram(image_path: str, target: str):
    """Sendet das extrahierte Foto via Telegram (openclaw message send)."""
    shared_path = SHARED_OUTPUT / Path(image_path).name
    SHARED_OUTPUT.mkdir(parents=True, exist_ok=True)
    shutil.copy(image_path, shared_path)

    cmd = [
        "openclaw", "message", "send",
        "--channel", "telegram",
        "--target", target,
        "--media", str(shared_path),
    ]
    print(f"📤 Sende via Telegram an {target}...")
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode == 0:
        print(f"✅ Gesendet! {result.stdout.strip()}")
    else:
        print(f"❌ Fehler beim Senden: {result.stderr.strip()}", file=sys.stderr)


def main():
    parser = argparse.ArgumentParser(
        description="Extrahiert eingebettete Fotos aus eingescannten Dokumentseiten."
    )
    parser.add_argument("--image", type=str, required=True, help="Pfad zum Scan (JPG/PNG)")
    parser.add_argument("--output", type=str, default=None, help="Ausgabepfad (default: extracted_<input>.jpg)")
    parser.add_argument("--send", action="store_true", help="Extrahiertes Foto via Telegram senden")
    parser.add_argument("--target", type=str, default="8620748747", help="Telegram Chat-ID (default: 8620748747)")
    args = parser.parse_args()

    if not MISTRAL_API_KEY:
        print("❌ MISTRAL_API_KEY nicht gesetzt!", file=sys.stderr)
        sys.exit(1)

    image_path = args.image
    output_path = args.output or f"extracted_{Path(image_path).stem}.jpg"

    print(f"🔍 Erkenne Foto-Bereich in: {image_path}")
    bbox = detect_photo_region(image_path)
    print(f"📦 Bounding-Box: {bbox}")

    crop_and_deskew(image_path, bbox, output_path)

    if args.send:
        send_via_telegram(output_path, args.target)


if __name__ == "__main__":
    main()
