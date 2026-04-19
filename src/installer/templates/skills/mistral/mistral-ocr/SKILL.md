# Skill: mistral-ocr

## Wann verwenden
- Text aus Bild oder PDF extrahieren (OCR)
- Eingebettete Bilder aus einem Scan croppen und speichern
- Kombiniert: durchsuchbares Dokument + Bilder extrahieren

## Parameter — NUR DIESE EXISTIEREN
| Parameter | Pflicht | Beschreibung |
|-----------|---------|-------------|
| `--input` | ✅ ja | Lokaler Pfad oder URL zu Bild/PDF |
| `--extract-images` | nein | Eingebettete Bilder via Bounding-Box aus Original croppen und speichern |
| `--output-dir` | nein | Ausgabeverzeichnis für extrahierte Bilder (default: shared-output/) |
| `--send` | nein | Extrahierte Bilder via Telegram senden |
| `--target` | nein | Telegram Chat-ID (default: 8620748747) |
| `--pages` | nein | Anzahl Seiten (für PDFs) |
| `--debug` | nein | Rohe API-Response ausgeben |

## Output
- **Stdout:** Extrahierter Text als Markdown
- **Dateien:** Extrahierte Bilder im `--output-dir` (nur bei `--extract-images`)

## Typischer Workflow: Scan → durchsuchbares PDF

```bash
# 1. Text + Bilder extrahieren
python3 ~/.openclaw/workspace/skills/mistral-ocr/ocr.py \
  --input /pfad/zum/scan.jpg \
  --extract-images \
  --output-dir /ausgabe/verzeichnis/ > text.md

# 2. Markdown mit Bildpfaden erstellen (Bilder aus output-dir einbetten)
# 3. PDF rendern via pdf_render.py
```

## Wichtig
- Bilder werden als valide JPEGs gespeichert (via Pillow-Crop aus Original)
- `--output-dir` muss existieren oder wird automatisch erstellt
- Bildnamen basieren auf der OCR-internen ID (z.B. `img-0.jpg`)
