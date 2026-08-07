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
python3 vision.py --image test_images/document.jpg --output json

# Nur Text
python3 vision.py --image test_images/document.jpg --output text
```

## Beispielausgabe (JSON)
```json
{
  "text": "Invoice No. 2026-4711\nAmount: 1,200 USD\nDate: 2026-04-11",
  "metadata": {
    "document_type": "invoice",
    "description": "Sample invoice for a renovation project",
    "confidence": 0.95
  }
}
```

## Testbilder
- `test_images/document.jpg`: Beispiel-Dokument (fiktiv).
- `test_images/formular.png`: Beispiel-Formular.