# Requirements Diff — Docker Installer vs. Multi-Agent Setup
**Erstellt:** 2026-04-10  
**Von:** coding_zot  
**Basis:** tasks/2026-04-10-installer-requirements.md vs. Ist-Stand Installer

---

## Legende
- ✅ Implementiert
- ⚠️ Teilweise / Abweichung
- ❌ Fehlt
- 🔵 Designentscheid nötig

---

## 1. LLM-Tier-Variablen in `.env`

| Tier | Requirements | Implementiert |
|------|-------------|---------------|
| LLM_BUDGET | ✅ | ✅ |
| LLM_STANDARD | ✅ | ✅ |
| LLM_POWER | ✅ | ✅ |
| LLM_MEDIA | ✅ | ✅ |
| **LLM_COMPLEX** | ✅ | ❌ fehlt |
| **LLM_CODE** | ✅ (codestral) | ❌ fehlt |

**Default-Werte (state.py):**
- `llm_budget = mistral/mistral-large-latest` ✅
- `llm_standard = anthropic/claude-sonnet-4-6` ✅
- `llm_power = anthropic/claude-opus-4-6` ⚠️ (Requirements: claude-sonnet-4-6 als LLM_POWER — war das so gemeint?)
- `llm_media = mistral/mistral-large-latest` ✅

**Kritisch:** `LLM_COMPLEX` und `LLM_CODE` (codestral) fehlen in state.py, env_gen.py und dem Wizard. Der Installer-Wizard fragt nicht nach Codestral-Key.

**Fix:** 2 neue Felder in state.py, env_gen.py erweitern, Wizard-Step api_keys.py anpassen.

---

## 2. `agents.defaults.model` — Konfiguration

**Requirements:**
```json
"primary": "${LLM_BUDGET}",
"fallbacks": ["${LLM_STANDARD}", "${LLM_POWER}"]
```

**Implementiert (openclaw_json_gen.py):**
```json
"primary": state.llm_standard,   ← Abweichung!
"fallbacks": [state.llm_power]   ← nur 1 fallback
```

**Probleme:**
1. ⚠️ Default primary ist `LLM_STANDARD` statt `LLM_BUDGET` — teurer als nötig für Heartbeats/Crons
2. ⚠️ Nur 1 Fallback statt 2
3. ❌ `${LLM_*}` env-var-Referenzen nicht genutzt — Installer schreibt Werte direkt rein. Das ist eigentlich OK solange `.env` + `openclaw.json` konsistent bleiben, aber der Kommentar in der Requirements ist misleading. OpenClaw interpoliert `${VAR}` nicht aus .env in openclaw.json.

**Empfehlung:** primary auf `state.llm_budget` setzen. Fallbacks: `[llm_standard, llm_power]`.

---

## 3. Per-Agent Model-Overrides

**Requirements:**
```json
{ "id": "CODING_AGENT", "model": { "primary": "${LLM_COMPLEX}", ... } }
{ "id": "RESEARCH_AGENT", "model": { "primary": "${LLM_BUDGET}", ... } }
```

**Implementiert:** ❌ Kein Multi-Agent. Nur `main` wird generiert. Kein Wizard-Step für zusätzliche Agents.

**Scope für v1.0:** 🔵 Designentscheid — Multi-Agent-Wizard ist grössere Arbeit. Für v1.0 akzeptabel wenn das requirements-doc es als "MUSS" listet, muss ein Minimal-Multi-Agent-Setup her.

---

## 4. API Keys & Credentials

| Key | Requirements | Implementiert |
|-----|-------------|---------------|
| MISTRAL_API_KEY | ✅ | ✅ |
| ANTHROPIC_API_KEY | ✅ | ✅ |
| TELEGRAM_BOT_TOKEN | ✅ | ✅ |
| **OPENCLAW_GATEWAY_TOKEN** | ✅ auto-generated | ❌ fehlt |
| **BACKUP_ENCRYPTION_KEY** | ✅ auto-generated | ❌ fehlt |
| EMAIL_PASSWD | optional | ❌ fehlt (kein E-Mail-Skill-Wizard) |

**OPENCLAW_GATEWAY_TOKEN:** Wird für die Gateway-Auth benötigt. In openclaw.json nicht konfiguriert. Entweder OpenClaw generiert es selbst beim ersten Start, oder der Installer muss es setzen. Klären.

**BACKUP_ENCRYPTION_KEY:** backup_gen.py vorhanden — schreibt ein Script. Aber der Key wird nirgends generiert und nicht in .env gesetzt.

**API-Key-Validierung:** Requirements fordert Test-Call vor Fortsetzung. ❌ Nicht implementiert.

---

## 5. exec-approvals — Sicherheits-Default

**autoAllowSkills:** `state.auto_allow_skills = False` als Default ✅ — korrekt.

**ask/askFallback:** `"on-miss"` / `"deny"` ✅

**Allowlist Inhalt:**
- `/usr/bin/python3` ✅
- `/usr/bin/git` ✅ (nur main)
- Skill-Pfade (web-search, docs-summarize) ✅ (nur main)
- `check_tasks.py` ⚠️ — Script-Pfad in Allowlist, aber check_tasks.py liegt in `workspace/scripts/`, Allowlist hat `openclaw_dir/scripts/` — könnte falscher Pfad sein
- `hourly_log.py` ❌ fehlt in Allowlist
- `memory_digest.py` ❌ fehlt in Allowlist

**Multi-Agent Sections:** ❌ Nur `main` in `agents`-Sektion. CODING_AGENT, CONTENT_AGENT, RESEARCH_AGENT fehlen komplett.

**Globale Telegram-Approval-Buttons:** ⚠️ Plugin ist konfiguriert (`telegram-approval-buttons@5.1.0`), aber `approvals.exec.targets` mit Telegram-ID des Users wird nicht gesetzt. User muss das manuell nachtragen.

---

## 6. Spawning Policy

**Requirements:** `allowAgents[]` pro Agent, `maxSpawnDepth: 1`

**Implementiert:**
```json
"subagents": { "maxConcurrent": 2 }   ← in defaults
```

**Fehlt:**
- ❌ `maxSpawnDepth: 1` nicht gesetzt
- ❌ Kein `allowAgents[]` pro Agent
- ❌ Kein Wizard-Step für Spawning-Konfiguration

---

## 7. Backup

**Requirements:** BACKUP_ENCRYPTION_KEY auto-generiert, User erhält Key-Export.

**Implementiert:**
- `backup_gen.py` ✅ — generiert `daily_backup.py` Script
- `backup_mount_path` in state ✅
- Docker Volume-Mount ✅

**Fehlt:**
- ❌ BACKUP_ENCRYPTION_KEY wird nicht generiert und nicht in .env geschrieben
- ❌ Kein Key-Export / QR-Code für User

---

## 8. Workspace-Datei-Matrix

| Datei | Requirements | Implementiert |
|-------|-------------|---------------|
| SOUL.md | ✅ eigene Datei | ✅ |
| AGENTS.md | ✅ eigene Datei | ✅ |
| HEARTBEAT.md | ✅ eigene Datei | ✅ |
| IDENTITY.md | ✅ eigene Datei | ✅ |
| MEMORY.md | ✅ eigene Datei | ✅ |
| USER.md | ✅ eigene Datei | ✅ |
| BOOTSTRAP.md | ✅ eigene Datei | ✅ |
| **TOOLS.md** | ✅ eigene Datei | ❌ fehlt |
| scripts/check_tasks.py | ✅ | ✅ |

**Real copies, keine Symlinks:** ✅ korrekt umgesetzt.

---

## 9. Skill-Deployment

**Requirements:** Shared Volume `/openclaw/skills` → in jeden Agent-Workspace gemountet.

**Implementiert:**
- Skills liegen in `src/installer/templates/skills/` ✅
- `workspace_bootstrap.py` kopiert sie in Workspace ⚠️ — aber nur in den Haupt-Workspace, nicht als Shared Volume. Für Single-Agent OK.
- Für Multi-Agent: ❌ kein Shared-Volume-Konzept in docker-compose.yml

---

## 10. memorySearch / Semantische Suche

| Feature | Requirements | Implementiert |
|---------|-------------|---------------|
| provider: mistral | ✅ | ✅ |
| model: mistral-embed | ✅ | ✅ |
| **extraPaths** | ✅ | ❌ fehlt |

`extraPaths: ["/openclaw/workspace/memory/topics"]` erlaubt geteilte Topics zwischen Agents — macht nur Sinn bei Multi-Agent.

---

## 11. Crons

**Requirements:** 5 Cron-Templates

| Cron | Requirements | Implementiert |
|------|-------------|---------------|
| Hourly Log Writer | ✅ | ❌ |
| Daily Memory Digest | ✅ | ❌ |
| Gateway Health Check | ✅ | ❌ |
| Model Watch & Logger | ✅ | ❌ |
| Weekly Memory Maintenance | ✅ | ❌ |

**Es gibt kein `cron_gen.py`.** Keine Crons werden generiert. Das ist die grösste Lücke für ein produktives Setup.

---

## Zusammenfassung: Offene Punkte nach Priorität

### Prio 1 — Blocker für v1.0
1. **Cron-Generator fehlt komplett** — ohne Crons kein Memory-Digest, kein Health-Check
2. **LLM_COMPLEX + LLM_CODE fehlen** — Codestral-Tier nicht konfigurierbar
3. **BACKUP_ENCRYPTION_KEY** nicht generiert
4. **TOOLS.md** fehlt in workspace_bootstrap_gen.py

### Prio 2 — Wichtig aber nicht Blocker
5. **agents.defaults.model.primary** sollte LLM_BUDGET sein, nicht LLM_STANDARD
6. **OPENCLAW_GATEWAY_TOKEN** — klären ob OpenClaw das selbst generiert
7. **maxSpawnDepth: 1** fehlt in spawning config
8. **Telegram-Approval-Targets** — User-ID muss automatisch eingetragen werden
9. **hourly_log.py + memory_digest.py** fehlen in exec-approvals Allowlist

### Prio 3 — v1.0 kann warten
10. **Multi-Agent Wizard** — komplett neuer Feature-Scope
11. **Per-Agent allowAgents** — erst relevant bei Multi-Agent
12. **API-Key-Validierung** (Test-Call)
13. **extraPaths in memorySearch** — erst bei Multi-Agent relevant
14. **E-Mail-Skill / EMAIL_PASSWD** — optional

### Nicht implementierbar (Designeinschränkung)
- **`${LLM_*}` in openclaw.json** — OpenClaw interpoliert keine env-vars aus .env in JSON-Config. Der Installer muss Werte direkt einschreiben. Ist korrekt so.

---

## Offene Fragen für Photon

1. **OPENCLAW_GATEWAY_TOKEN** — generiert OpenClaw das beim ersten Start selbst, oder muss der Installer es setzen?
2. **LLM_POWER Default** — Requirements: `anthropic/claude-sonnet-4-6`. state.py hat `claude-opus-4-6` als LLM_POWER. Welches ist richtig?
3. **Multi-Agent für v1.0?** — Das ist mehrere Wochen Arbeit. Oder erst v2.0?
4. **Cron-Generator Scope** — Alle 5 Crons für v1.0, oder nur die kritischen 2 (Digest + Health)?
5. **restore_gen.py Bugfix** — altes Script hat noch Shell-Tools in Allowlist. Fix in eigenem PR oder zusammen mit neuem Feature?
