# OpenClaw Installer Notes
# Alle Optimierungen & Tweaks seit Erstinstallation
# Stand: 2026-04-05 — Raspberry Pi 5, User: hummer

---

## 0. VISION & DESIGNPHILOSOPHIE

### Warum dieses Projekt existiert
OpenClaw ist mächtig. Zu mächtig für eine Standardinstallation ohne Leitplanken.
Ein LLM-Agent mit zu vielen Rechten + ein Benutzer der nicht versteht was er aktiviert hat = Katastrophenpotenzial.

Das Schreckenszenario: Agent in kritischer Infrastruktur, Benutzer gibt ihm API-Zugriff weil es "praktisch" ist, niemand schaut mehr hin. Das ist keine Theorie — das wird passieren.

**Dieses Projekt ist die Antwort darauf: Sicherheit als First-Class-Citizen, nicht als Nachgedanke.**

### Kernprinzipien

**1. Secure by Default**
- Allowlist statt offene Rechte — `security: full` wird nicht angeboten
- Keine gefährlichen Tools in der Standard-Allowlist (kein pip3, kein rm, kein Root)
- Secrets nur in `.env`, nie in Config-Files oder Service-Files
- Approval-Mechanismus vorkonfiguriert und aktiv

**2. Wizard der schlechte Entscheidungen verhindert**
- Jede Rechte-Erweiterung erklärt was sie bedeutet und welches Risiko sie trägt
- Warnung bei zu offenen Konfigurationen — nicht nur Hinweis, sondern echte Friction
- Kein "weiter klicken ohne lesen"
- Homedir, Username, Pfade einmal abfragen — überall einsetzen (kein hardcoding)

**3. Human-in-the-Loop für irreversible Aktionen**
- Alles ausserhalb der Allowlist braucht Approval
- Audit-Trail: was hat der Agent gemacht, wann, mit welchem Ergebnis
- Restart, Deploy, externe API-Calls — nie ohne Confirmation

**4. Capability mit Guardrails — nicht Capability statt Guardrails**
Der Agent darf viel — aber der Benutzer weiss jederzeit was er tut und kann eingreifen.
Bequemlichkeit ist sekundär. Kontrolle ist primär.

### Zielgruppe
Nicht der Linux-Profi der weiss was er tut — der kann sich selbst helfen.
Sondern der **halbwissende Benutzer** der begeistert ist von den Möglichkeiten, aber die Risiken nicht überblickt. Genau dieser Benutzer braucht einen Installer der ihn schützt — auch vor sich selbst.

### Abgrenzung
- **Nicht:** eine weitere Docker-Compose-Vorlage
- **Nicht:** maximale Convenience auf Kosten der Sicherheit
- **Ja:** opinionated Setup mit klar begründeten Defaults
- **Ja:** dokumentierte Entscheidungen die der Benutzer verstehen kann

---

## 1. INSTALLATION & SYSTEMD

### Service-File bereinigen
- `openclaw gateway install` schreibt API-Keys als `Environment=` ins Service-File
- **Fix:** API-Key-Zeilen entfernen — Keys kommen bereits aus `EnvironmentFile=%h/.openclaw/.env`
- Betroffene Zeilen: `Environment=ANTHROPIC_API_KEY=...` und `Environment=MISTRAL_API_KEY=...`
- Prüfung im Health-Check automatisiert (Alarm wenn Keys wieder drin)

### ExecStartPost für exec-approvals.json
- Gateway-Restart überschreibt `exec-approvals.json` mit Defaults
- **Fix:** `ExecStartPost` im Service-File: `python3 /path/restore_exec_approvals.py`
- Restore-Script pflegt die vollständige Allowlist und schreibt sie nach jedem Restart zurück

### Autostart
- Systemd User-Service: `~/.config/systemd/user/openclaw-gateway.service`
- `loginctl enable-linger hummer` nötig damit der Service ohne Login läuft

---

## 2. OPENCLAW.JSON — WICHTIGE CONFIG-TWEAKS

```json
"agents": {
  "defaults": {
    "bootstrapMaxChars": 8000,
    "bootstrapTotalMaxChars": 30000,
    "subagents": { "maxConcurrent": 2 }
  }
}

"tools": {
  "sessions": { "visibility": "all" }
}

"model": {
  "primary": "${LLM_STANDARD}",
  "fallbacks": ["${LLM_POWER}", "${LLM_BUDGET}"]
}

"web": { "search": { "enabled": false } }

"execApprovals": { "target": "both" }

"requireMention": false
```

---

## 3. MODELL-STRATEGIE

| Task | Modell | Warum |
|------|--------|-------|
| Alltag, Chat, Code | Sonnet | Günstig, Prompt-Caching |
| Schwere Analyse, Security-Audit | Opus | Qualität wenn nötig |
| Sub-Agent Tasks, Crons, Compaction | Mistral | Günstig, kein Caching nötig |
| Bild-Analyse, OCR | Mistral Subagent | Günstig |

**Wichtig:** Mistral hat KEIN Prompt-Caching. Anthropic cached automatisch (bis 90% Rabatt).
→ Schlanke Bootstraps sparen vor allem bei Mistral.

---

## 4. EXEC-APPROVALS / ALLOWLIST-SYSTEM

### Architektur
- `exec-approvals.json` — aktive Allowlist
- `restore_exec_approvals.py` — Restore nach Gateway-Restart
- Jeder Agent hat eigene `agents.<agentId>.allowlist`
- `defaults.allowlist` gilt für alle Sessions inkl. isolated (Crons)

### Wichtige Erkenntnisse
- **Pipes** (`|`), Umleitungen (`2>&1`), `&&` → bash-Compound-Commands → brauchen Approval
- **Lösung:** Scripts statt Inline-Commands — Script in Allowlist, alles intern
- `isolated` Sessions (Crons) erben NICHT die Main-Allowlist → `defaults.allowlist` nötig
- `sudo` ohne Passwort für spezifische Befehle: `/etc/sudoers.d/` (z.B. journalctl)

### Allowlist-Strategie (4 Tiers)
- **Elevated (main):** Read/Analyse-Tools + System + Dev (git, python3, bash) + Node. Kein rm, pip3, Root.
- **Standard (coding_bot):** wie Elevated + ssh, chmod, crontab, astro. Minus systemctl, openclaw CLI.
- **Restricted (büro_bot, formular_bot):** Nur spezifische Script-Pfade. Kein bare python3/bash.
- **Cron/Isolated (defaults):** Kein bash. python3 + Read-Tools + Health/Digest-Scripts.
- **Nie:** rm, pip3, dd, chmod 777, Root-Shell-Interpreter, sudo generell.
- **Prinzip:** Bare Interpreter nur für Agents die sie wirklich brauchen. Alle anderen: spezifische Script-Pfade.

---

## 5. MULTI-AGENT SETUP

### Persistente Agents vs. Spawned Sub-Agents

**Persistente Agents:** Eigener Workspace, eigene Session, eigener Memory-Index. Volles `memory_search`/`memory_get`. Permanent laufend. Konfiguriert in `openclaw.json`.

**Spawned Sub-Agents** (via `sessions_spawn`): Temporär. `memory_search`/`memory_get` default-denied (GitHub #16214). Nur `read`-Tool für Dateizugriff. Betrifft auch isolierte Cron-Jobs.

### Workspace-Struktur
```
~/.openclaw/workspace/          ← main
~/.openclaw/workspace-coding/   ← coding_bot
~/.openclaw/workspace-buero/    ← buero_bot
~/.openclaw/workspace-formular/ ← formular_bot
```

### Shared Files via Symlinks (Pflicht in jedem Sub-Workspace)
```bash
ln -s ~/.openclaw/workspace/AGENTS.md AGENTS.md
ln -s ~/.openclaw/workspace/USER.md USER.md
ln -s ~/.openclaw/workspace/HEARTBEAT.md HEARTBEAT.md
ln -s ~/.openclaw/workspace/skills skills
```

### Topic-Bindings in openclaw.json
```json
"sessions": [
  { "agentId": "coding_bot", "channel": "telegram", "peer": { "kind": "group", "id": "-GROUPID:topic:3" }},
  { "agentId": "buero_bot",  "channel": "telegram", "peer": { "kind": "group", "id": "-GROUPID:topic:4" }},
  { "agentId": "formular_bot","channel": "telegram","peer": { "kind": "group", "id": "-GROUPID:topic:5" }}
]
```

---

## 6. WORKSPACE-DATEIEN (Bootstrap-Struktur)

### Pflichtdateien (alle Agents via Symlink)
- `AGENTS.md` — Workflow-Regeln, Kommunikationsformat, Memory-Workflow
- `SOUL.md` — Charakter, Rollen, Grenzen
- `USER.md` — Über den Benutzer
- `IDENTITY.md` — Name, Avatar, Vibe
- `HEARTBEAT.md` — Heartbeat-Verhalten

### Nur main
- `MEMORY.md` — Langzeitgedächtnis (≤30 Zeilen, nur stabile Fakten)
- `TOOLS.md` — Externe Tools/Zugänge

### Bootstrap-Grösse optimieren
- Total Bootstrap <12'000 Zeichen
- Topics und Daily Logs nicht im Bootstrap — on-demand via `memory_search`

---

## 7. MEMORY-ARCHITEKTUR

### Struktur
```
memory/
  MEMORY.md              ← Langzeitgedächtnis (slim, ≤30 Zeilen)
  YYYY-MM-DD.md          ← Daily Logs (Raw-Material)
  topics/
    _template.md
    index.md
    ...
  digest-latest.md       ← Flat-File Fallback (von daily_digest.py)
```

### Memory Engine
- SQLite + FTS5 + Embeddings (Mistral 1024 dims) + sqlite-vec
- Hybrid-Search: BM25 (0.3) + Vektor (0.7)
- Workspace-isoliert — Agents sehen nur ihren eigenen Workspace

### Cross-Agent Memory-Zugriff
- **Primär: `extraPaths`** — Sub-Agents indizieren Main-Topics direkt:
  ```json
  "memorySearch": { "extraPaths": ["/data/workspace/memory/topics"] }
  ```
  Docker: Container-Pfade! Nie `~/` oder Host-Pfade.
- **Sekundär: Daily Digest** — `daily_digest.py` schreibt `digest-latest.md` in alle Workspaces. Atomares Schreiben via `os.replace()`.
- **Spawned Sub-Agents:** `memory_search` default-denied → nur `read`-Tool.

### Daily Log Kompaktheit
- Today + yesterday automatisch im Context → kosten Tokens bei jedem Call
- Max 5 Zeilen/Stunde, nur Entscheidungen + offene Punkte
- Anthropic: yesterday gecached (90% Rabatt). Mistral: voller Preis → kurz halten.

### MEMORY.md Schutz
- Max 30 Zeilen. Heartbeat darf nur kürzen (nie ergänzen) wenn ≥25 Zeilen.

### Installer Wizard: Basic vs. Extended Memory (Opt-in)

**Basic (Default):** MEMORY.md + Daily Logs. Out of the box, kein LLM-Overhead.

**Extended (Opt-in):** Topics + Digest + Crons + extraPaths + HEARTBEAT Guards (~$0.02/Tag).

**Wizard-Prompt:**
```
🧠 Extended Memory System aktivieren?
  - Stündliche Logs → wöchentliche Topic-Zusammenfassungen
  - Cross-Agent Memory-Zugriff (wenn Multi-Agent aktiv)
  - Kostet ~$0.02/Tag (Mistral Cron-Jobs)
  [Ja, aktivieren]  [Nein, Basic reicht]
```

**Docker:** Crontab-Jobs → OpenClaw Cron (agentTurn). Alle Pfade = Container-Pfade (`/data/...`).

---

## 8. SKILLS

### web-search
- DDG via `ddgs` — `query=` statt `keywords=` (API geändert!)
- Script: `skills/web-search/search.py`

### docs-summarize
- Script: `skills/docs-summarize/summarize.py`

### email
- SMTP: port 587 (STARTTLS), IMAP: port 993 (SSL)
- Passwort in `.env` als `EMAIL_PASSWD`
- `.env` laden via Python `partition("=")`, nie `source`

---

## 9. AUTOMATION / CRONS

### Zeitplan
| Zeit | Mechanismus | Job |
|------|-------------|-----|
| 03:05, 11:05, 18:05 | Crontab | Daily Memory Digest (kein LLM) |
| 04:00 (Fr) | OpenClaw Cron | Weekly Memory Maintenance (LLM) |
| 04:10 täglich | Crontab | Backup |
| 07:45 täglich | Crontab | Health Check |
| 07:55 täglich | Crontab | Morning Briefing |

### Crontab-Einträge (Native Linux)
```
PATH=/usr/local/bin:/usr/bin:/bin
10 4 * * * /usr/bin/python3 ~/.openclaw/scripts/daily_backup.py >> ~/.openclaw/logs/daily-backup.log 2>&1
5 3,11,18 * * * /usr/bin/python3 ~/.openclaw/scripts/daily_digest.py >> ~/.openclaw/logs/daily-digest.log 2>&1
45 7 * * * /usr/bin/python3 ~/.openclaw/scripts/run_and_notify.py ~/.openclaw/scripts/health_check.py --silent >> ~/.openclaw/logs/health-check.log 2>&1
55 7 * * * /usr/bin/python3 ~/.openclaw/scripts/run_and_notify.py ~/.openclaw/scripts/morning_briefing.py >> ~/.openclaw/logs/morning-briefing.log 2>&1
```

### Cron-Prinzipien
- Nie zur vollen Stunde
- Health/Digest/Backup: direkt via Crontab — kein LLM
- Nur wenn LLM nötig: OpenClaw agentTurn Cron
- Silent on success
- **Warnung:** Mistral-Crons ohne "Keine Subagents" spawnen Sonnet-Subagents → teuer

---

## 10. BACKUP-SYSTEM

- rsync auf `/mnt/sdcard` (Bind Mount im Docker: Volume)
- Alle Workspaces täglich
- Sonntag: Vollbackup mit Versionierung
- Rolling 30 Tage via `shutil.rmtree` (nie `rm`)
- Script: `daily_backup.py`

---

## 11. HEALTH CHECK

### Script: `health_check.py`
- Disk, Gateway, Backup, System Errors, Pakete, Einbruchsversuche, SSH-Logins, API-Keys, Gateway-Restarts, Pi-Reboots, exec-approvals Integrity, Scripts-Inventar
- `--silent`: nur bei Problemen ausgeben
- `psutil.boot_time()` für Pi-Reboots
- Paket-Änderungen aus `/var/log/dpkg.log` (nicht journald)
- Ruft `audit_integrity.py --silent` auf

### audit_integrity.py
- SHA256-Checksum exec-approvals.json + Scripts-Inventar
- `--silent`, `--json`, `--reset` Flags
- Exit: 0=OK, 1=Änderungen, 2=kritisch
- Baselines bei Änderungen NICHT auto-updaten → manuelles `--reset` nötig

---

## 12. SICHERHEIT

Siehe `SECURITY-ARCHITECTURE.md` für vollständiges Threat Model.

### Kurzfassung
- `security: allowlist` für alle Agents (nie `full`)
- `trash` statt `rm`
- API-Keys nur in `.env`
- sudoers: spezifische Befehle, kein Wildcard
- Docker: `.env`, `scripts/`, `openclaw.json` read-only gemountet

---

## 13. BEKANNTE GOTCHAS

1. **Pipes in exec = Approval** — Lösung: Scripts statt Inline-Commands
2. **exec-approvals.json wird überschrieben** — restore_exec_approvals.py via ExecStartPost
3. **isolated Session ≠ Main-Allowlist** — defaults.allowlist nötig
4. **openclaw update** kann API-Keys zurück ins Service-File schreiben
5. **Mistral kein Prompt-Caching** — kurze Bootstraps sparen Geld
6. **ddgs: `query=` nicht `keywords=`** — API geändert
7. **`source .env` bricht bei Nicht-KEY=VAL-Zeilen** — Python partition() verwenden
8. **agentTurn-Crons können nicht `sessionTarget: main`** — nur `systemEvent`
9. **`2>&1` in exec = Approval** — in Scripts kapseln
10. **Paket-Änderungen nicht in journald** — `/var/log/dpkg.log`
11. **Mistral spawnt Sonnet-Subagents ohne explizites Verbot**
12. **Backup-Log heisst `daily-backup.log`** (nicht `backup.log`)
13. **Timestamp-Regex: `YYYY-MM-DD HH:MM:SS`** nicht ISO-T-Format
14. **Hardcodierte Pfade** — `OPENCLAW_USER_HOME` im Installer abfragen
15. **Gateway-Restart killt laufende Session** — Script verwenden (`gateway_restart.py`)
16. **`${LLM_VAR}` in openclaw.json** — Env-Variablen werden interpoliert
17. **FTS5 auf Node 22+ prüfen** — Installer-Check nötig. Node 24 auf Pi 5: FTS5 ✅
18. **`memory_search` default-denied bei spawned Sub-Agents** — GitHub #16214
19. **Daily Logs heute+gestern immer im Context** — kompakt halten (<5 Zeilen/h)
20. **`extraPaths` für Cross-Agent Memory** — immer absolute Container-Pfade, nie `~/`
21. **Atomares Schreiben bei Digest** — `os.replace()` statt `write_text()`

---

## 14. LLM TIERS

```
LLM_BUDGET=mistral/mistral-large-latest       # Crons, Maintenance, Routine
LLM_STANDARD=anthropic/claude-sonnet-4-6      # Daily Chat, Sub-Agents
LLM_POWER=anthropic/claude-opus-4-6           # Komplexe Analyse
LLM_MEDIA=mistral/mistral-large-latest        # Bilder, OCR, Audio
```

Mistral-API erwartet Modell-Name ohne Provider-Prefix → `.replace("mistral/", "")` in Python-Skills.

---

## 15. CODING AGENT — PROJEKT-WORKFLOW

- Pflicht-Kickoff-Dokument vor jedem Projekt
- Kein Code ohne Kickoff, kein Feature ohne User Story
- Kein Merge ohne: läuft lokal + Kern-Tests grün

---

## 16. TECH-STACK ENTSCHEIDUNGEN

### Sprache
- **Python — everywhere.** Scripts + Wizard + Skills + Tests
- Bash nur noch im Docker-Container intern toleriert (Linux guaranteed)
- **Migration abgeschlossen (2026-04-05):** alle Scripts in `~/.openclaw/scripts/` sind Python

### Key Libraries
| Kategorie | Library |
|-----------|---------|
| Prozesse | `psutil` |
| Trash | `send2trash` |
| Plattform-Pfade | `platformdirs` |
| HTTP | `httpx` |
| Wizard-UI | `questionary` + `rich` |
| CLI | `typer` |
| Templates | Jinja2 |
| Service-Manager | systemd / launchd / NSSM (Adapter-Pattern) |

### Docker → Native Migration
- Bind Mounts (nicht Named Volumes) — direkt im Filesystem, migrierbar
- `OPENCLAW_CONFIG_DIR` Env-Variable überschreibbar
- `openclaw-installer migrate` Sub-Command

### Cross-Platform Fallstricke
1. Python nicht vorinstalliert auf Windows → PyInstaller oder `uv`
2. `SIGTERM` funktioniert auf Windows nicht → `process.terminate()`
3. `/tmp` auf Windows nicht → `tempfile.gettempdir()`
4. Encoding: immer `encoding="utf-8"` bei `open()`
5. Case-sensitivity: Windows ≠ Linux
