# Skill: mistral-translate

## Wann verwenden
- Wenn Text übersetzt werden soll
- Dokumente, E-Mails, Website-Texte übersetzen
- Günstiger als Sonnet/Opus für reine Übersetzungsaufgaben

## Verwendung
```bash
python3 ~/.openclaw/workspace/skills/mistral-translate/translate.py --text "..." --to de [--from en]
```

Oder mit Datei:
```bash
python3 ~/.openclaw/workspace/skills/mistral-translate/translate.py --file <pfad> --to fr
```

## Unterstützte Sprachen
de, fr, en, it, es, und viele mehr (ISO 639-1 Codes)
