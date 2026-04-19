# Skill: mistral-vision

## Wann verwenden
- Bild analysieren, beschreiben oder Fragen dazu beantworten
- Produktfotos, Weinetiketten, Landschaftsbilder verstehen
- Unterschied zu `mistral-ocr`: Vision versteht den Bildinhalt kontextuell, OCR extrahiert nur Text

## Verwendung
```bash
python3 ~/.openclaw/workspace/skills/mistral-vision/vision.py \
  --image <pfad_oder_url> \
  --output json|text
```

## Parameter — NUR DIESE EXISTIEREN
| Parameter | Pflicht | Werte | Beschreibung |
|-----------|---------|-------|--------------|
| `--image` | ✅ ja | Pfad oder URL | Lokales Bild (JPEG, PNG) oder URL |
| `--output` | nein | `json` / `text` | `json` = Text + Metadaten; `text` = nur Fliesstext (Default: text) |
| `--prompt` | nein | String | Eigene Frage an das Bild |

## VERBOTEN — Diese Parameter gibt es NICHT
- `--extract-images` — existiert nicht
- `--output-dir` — existiert nicht
- `--format` — existiert nicht
- `--lang` — existiert nicht

Keine anderen Parameter erfinden.

## Modell
`pixtral-large-latest` (Standard, aktueller stabiler Alias — pixtral-12b-2409 ist deprecated)
Override via Env-Var: `MISTRAL_VISION_MODEL=pixtral-large-latest`

## API Key
`MISTRAL_API_KEY` aus `~/.openclaw/.env`

## Beispiel
```bash
python3 vision.py --image /tmp/etikett.jpg --output json
```
