# Mistral Vision Skill

Skill für Bildanalyse und OCR via Mistral Vision API.

## Funktionen
- **OCR**: Text aus Bildern extrahieren (z. B. Rechnungen, Formulare).
- **Metadaten**: Dokumententyp + Beschreibung generieren.
- **Barcode/QR-Code**: Optional (via `pyzbar`).

## Installation
```bash
pip install -r requirements.txt
```

## Nutzung
```bash
# JSON-Ausgabe (OCR + Metadaten)
python3 vision.py --image test_images/rechnung.jpg --output json

# Nur Text
python3 vision.py --image test_images/rechnung.jpg --output text
```

## Beispielausgabe (JSON)
```json
{
  "text": "Rechnung Nr. 2026-4711\nBetrag: 1.200 CHF\nDatum: 11.04.2026",
  "metadata": {
    "document_type": "Rechnung",
    "description": "Rechnung für Zimmerrenovierung Alpenblick",
    "confidence": 0.95
  }
}
```

## Testbilder
- `test_images/rechnung.jpg`: Beispiel-Rechnung (fiktiv).
- `test_images/formular.png`: Beispiel-Formular.