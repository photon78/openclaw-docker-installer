---
name: mistral-vision
description: Analyze images using Mistral Vision API — extract text (OCR), get document type, description, and metadata. Use for understanding image content contextually.
metadata: {"openclaw": {"requires": {"env": ["MISTRAL_API_KEY"]}, "emoji": "👁️"}}
---

## Wann verwenden
- Bild analysieren, beschreiben oder Fragen dazu beantworten
- Produktfotos, Weinetiketten, Landschaftsbilder verstehen
- Unterschied zu `mistral-ocr`: Vision versteht den Bildinhalt kontextuell, OCR extrahiert nur Text

## Verwendung
```bash
python3 {baseDir}/vision.py \
  --image <pfad_oder_url> \
  --output json|text
```

## Optionen
- `--image` — Lokaler Pfad oder URL zum Bild (JPEG, PNG)
- `--output json` — JSON mit `text` + `metadata` (document_type, description, confidence)
- `--output text` — Nur Fliesstext

## Modell
`pixtral-12b-2409` (Standard, günstig) oder `pixtral-large-latest` (stärker)

## API Key
`MISTRAL_API_KEY` aus `~/.openclaw/.env`

## Beispiel
```bash
python3 {baseDir}/vision.py --image /tmp/etikett.jpg --output json
```
