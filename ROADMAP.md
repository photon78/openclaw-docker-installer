# OpenClaw Installer — Roadmap

> Stand: 2026-04-05  
> Prinzip: Jede Version ist in sich stabil. Secure by Default. Alles Python.

---

## v0.1.0 — "First Light" 🔦
*Single Agent, Docker, funktioniert.*

### Infrastruktur
- [ ] Python-Projekt-Struktur (pyproject.toml, src/, tests/)
- [ ] CLI-Grundgerüst (typer): install / status / start / stop / uninstall
- [ ] CI: Linting (ruff), Type-Check (mypy), Docker Build Test

### Wizard
- [ ] Interaktiver Wizard (questionary + rich)
- [ ] Willkommen + Plattform-Erkennung
- [ ] API-Key(s) abfragen (Anthropic, optional Mistral)
- [ ] Channel wählen (Telegram / Discord / Signal)
- [ ] Channel-Credentials abfragen (Bot-Token, etc.)
- [ ] Security-Profil: Strict / Standard / Custom

### Generierung
- [ ] docker-compose.yml (Bind Mounts, .env + scripts read-only)
- [ ] .env (API-Keys, LLM Tiers)
- [ ] openclaw.json (bootstrapMaxChars, subagents, sessions)
- [ ] exec-approvals.json (aus Security-Profil, per-Agent Tiers)
- [ ] restore_exec_approvals.py (aus Wizard-Config)
- [ ] Workspace-Bootstrapping (AGENTS.md, SOUL.md, IDENTITY.md, MEMORY.md Templates)

### Security-Baseline
- [ ] health_check.py bundlen
- [ ] audit_integrity.py bundlen + Baselines setzen
- [ ] API-Keys nur in .env, nie in Service-File

### Post-Install
- [ ] docker-compose up via CLI
- [ ] Gateway-Ping (Health-Check)
- [ ] Zusammenfassung + nächste Schritte

### Docs & Community
- [ ] README.md (Vision, Quick Start, Screenshots)
- [ ] LICENSE (MIT)
- [ ] CHANGELOG.md (Keep a Changelog)
- [ ] CONTRIBUTING.md (DCO, Code Style, PR-Prozess)
- [ ] CODE_OF_CONDUCT.md (Contributor Covenant)
- [ ] SECURITY.md (Responsible Disclosure)
- [ ] GitHub Issue-Templates (Bug / Feature / Security Report)

---

## v0.2.0 — "The Pack" 🐺
*Multi-Agent, Extended Memory, Telegram Topics.*

### Multi-Agent
- [ ] Wizard: "Wie viele Agents?" + Rollen definieren
- [ ] Pro Agent: Name, Emoji, Workspace, Rechte-Tier
- [ ] Telegram-Gruppe + Topic-Bindings generieren
- [ ] Per-Agent Allowlist generieren
- [ ] Symlinks automatisch anlegen

### Extended Memory (Opt-in)
- [ ] Wizard-Prompt: Basic vs. Extended
- [ ] Topics-Ordner + _template.md + index.md generieren
- [ ] daily_digest.py generieren (atomares Schreiben)
- [ ] Cron-Jobs: Log Writer (stündlich), Weekly Maintenance (Fr)
- [ ] extraPaths für Cross-Agent Memory
- [ ] HEARTBEAT.md mit Guards (Zeilenlimit, Log-Kompaktheit, Digest-Alter)

### LLM Tiers
- [ ] Budget / Standard / Power / Media in .env
- [ ] openclaw.json mit ${LLM_*} Variablen

### Agent-Management
- [ ] openclaw-installer add-agent (nachträglich)
- [ ] openclaw-installer remove-agent

---

## v0.3.0 — "Unleash the Beast" 🐧
*Native Linux, systemd, kein Docker.*

### Native-Installation
- [ ] Wizard: Native vs. Docker Auswahl
- [ ] Node.js prüfen / installieren (fnm)
- [ ] openclaw via npm global installieren
- [ ] systemd User-Service generieren
- [ ] ExecStartPost für restore_exec_approvals.py
- [ ] loginctl enable-linger
- [ ] sudoers-Eintrag generieren (spezifisch, nicht wildcard)

### System-Integration
- [ ] FTS5-Check (Node + SQLite)
- [ ] Crontab generieren (statt Docker-interne Crons)
- [ ] Backup-Script generieren (daily_backup.py)
- [ ] Morning Briefing generieren
- [ ] openclaw-installer doctor (Diagnose)

---

## v0.4.0 — "Shape Shifter" 🔄
*Migration, Updates, Portabilität.*

- [ ] openclaw-installer migrate docker-to-native
- [ ] openclaw-installer migrate native-to-docker
- [ ] openclaw-installer update (Version prüfen, Backup vor Update, Post-Update Check)
- [ ] openclaw-installer backup / restore
- [ ] platformdirs Integration (kein hardcoded ~/...)

---

## v0.5.0 — "All Platforms" 🌐
*macOS + Windows Support.*

- [ ] macOS: launchd Service (~/Library/LaunchAgents/)
- [ ] macOS: Docker Desktop Integration
- [ ] Windows: NSSM Service Manager
- [ ] Windows: Docker Desktop Integration
- [ ] PyInstaller Binaries (kein Python auf Host nötig)
- [ ] Cross-Platform Tests (GitHub Actions Matrix)

---

## Backlog / Langfrist

- [ ] Web-UI für Wizard (Textual TUI oder Browser-based)
- [ ] Plugin-System (Skills installieren via Wizard)
- [ ] Auto-Discovery: vorhandene OpenClaw-Installation erkennen
- [ ] Telemetrie (opt-in, anonymisiert): Install-Erfolgsrate
- [ ] Community Skills Repository Integration (ClaWHub)
- [ ] Cluster-Mode (mehrere Server)

---

## Prinzipien

1. **Jede Version ist in sich stabil** — kein "geht nur mit v0.3"
2. **Secure by Default** — jede Version, jedes Feature
3. **Rückwärtskompatibel** — Config aus v0.1 funktioniert in v0.5
4. **Wizard verhindert schlechte Entscheidungen** — Friction bei Risiko
5. **Alles Python** — Wizard, Scripts, Skills, Tests
6. **Docker first, Native second** — aber Native ist First-Class, kein Afterthought
