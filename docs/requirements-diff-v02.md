# Requirements-Diff — MAIN-Requirements vs. Installer v0.2.0

**Erstellt:** 2026-04-10  
**Zweck:** Abgleich zwischen MAIN's Requirements (`tasks/2026-04-10-installer-requirements.md`) und aktuellem Stand

---

## ✅ Implementiert (v0.2.0)

| Anforderung | Status | Anmerkung |
|-------------|--------|-----------|
| LLM-Tiers in `.env`, keine Hardcoding | ✅ | BUDGET/STANDARD/POWER/MEDIA |
| `${VAR}` in `openclaw.json` | ✅ | OpenClaw löst zur Laufzeit auf |
| `agents.defaults.model.primary` + fallbacks | ✅ | `"${LLM_BUDGET}"` etc. |
| `memorySearch` mit mistral-embed | ✅ | Auto-konfiguriert wenn Mistral-Key vorhanden |
| exec-approvals: `autoAllowSkills: false` | ✅ | Überall, keine Ausnahme |
| exec-approvals: keine Shell-Tools | ✅ | bash, ls, cat, grep, find raus |
| E-Mail No-Trust-Regel in SOUL.md/AGENTS.md | ✅ | Als Pflicht-Default in allen Templates |
| Workspace-Files als echte Kopien (kein Symlink) | ✅ | Dokumentiert + im Generator erzwungen |
| Skills in Workspace kopiert | ✅ | web-search, docs-summarize, mistral-{ocr,translate,transcribe} |
| USER.md mit Name/Timezone/Tech-Level | ✅ | Neu: Wizard-Step "About You" |
| Daily Memory Digest + Gateway Health Check (Crons) | ✅ | In Completion-Screen als CLI-Befehle |
| Spawning: `maxConcurrent: 2` | ✅ | In `openclaw.json` |

---

## ⚠️ Konflikte / abweichende Entscheidungen

### 1. LLM_COMPLEX + LLM_CODE
**MAIN will:** 6 Tiers (BUDGET, STANDARD, COMPLEX, CODE, MEDIA, POWER)  
**Installer hat:** 4 Tiers (BUDGET, STANDARD, POWER, MEDIA)

**Entscheidung (Photon, 2026-04-10):** LLM_COMPLEX und LLM_CODE fallen weg — zu granular, verwirrt User beim Setup. COMPLEX ≈ POWER, CODE ≈ BUDGET mit Codestral. Kann im `.env` nachträglich manuell ergänzt werden.

**Offen:** MAIN verwendet LLM_COMPLEX in Cron-Prompts und Agent-Configs. → MAIN muss das auf STANDARD/POWER umschreiben.

### 2. Telegram Approval Targets
**MAIN will:** `approvals.exec.targets` mit Telegram-ID in `openclaw.json`  
**Installer:** Nicht drin — User setzt manuell

**Entscheidung (Photon, 2026-04-10):** Kein Approval-Buttons-Plugin. Stattdessen Pflicht-Regel in AGENTS.md: Jeder Approval-Request als vollständiges Paket (Befehl + Was + Warum + `/approve`-ID) — auf Telegram, WebUI und Discord identisch.

---

## ❌ Noch nicht implementiert (v0.3.0+)

| Anforderung | Prio | Aufwand | Anmerkung |
|-------------|------|---------|-----------|
| `OPENCLAW_GATEWAY_TOKEN` generieren | Hoch | Klein | Token nach erstem Gateway-Start auslesen via `docker run --rm` |
| `BACKUP_ENCRYPTION_KEY` generieren | Mittel | Klein | AES-256 Key in `.env`, Key-Export für User |
| API-Key-Validierung (Test-Call) | Mittel | Mittel | Vor Wizard-Ende validieren ob Key funktioniert |
| `compaction.model` in `openclaw.json` | Mittel | Minimal | Einfach hinzufügen: `"compaction": {"model": "${LLM_BUDGET}"}` |
| Hourly Log Writer Cron | Niedrig | Klein | Zusätzlicher Cron in Completion-Screen |
| Model Watch & Logger Cron | Niedrig | Klein | Dito |
| Weekly Memory Maintenance Cron | Niedrig | Klein | Dito |
| `maxSpawnDepth: 1` | Niedrig | Minimal | Erst prüfen ob valider OpenClaw-Key |
| Multi-Agent-Wizard | Nicht in Scope | Gross | → v2.0 |

---

## 💡 Empfehlung für v0.3.0

Priorität 1 (klein, grosser Impact):
1. `compaction.model` in `openclaw_json_gen.py` — 3 Zeilen
2. `OPENCLAW_GATEWAY_TOKEN` auslesen nach Gateway-Start — bereits in Completion-Screen vorbereitet
3. Alle 5 Crons in Completion-Screen zeigen (statt 2)

Priorität 2 (mittel):
4. API-Key-Validierung (Anthropic: `curl models`, Mistral: `curl models`)
5. `BACKUP_ENCRYPTION_KEY` generieren

---

## Entschiedene Fragen (2026-04-10)

1. **`LLM_COMPLEX`** → MAIN mappt auf `LLM_STANDARD`
2. **Telegram Approval Targets** → kein Plugin, stattdessen AGENTS.md-Pflicht-Regel (vollständiges Paket)
3. **`maxSpawnDepth: 1`** → valide in unserem Setup — in `openclaw.json` aufnehmen
