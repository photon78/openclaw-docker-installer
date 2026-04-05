# openclaw-docker-installer

> OpenClaw in a Box — vollständige, produktionsreife OpenClaw-Instanz in wenigen Minuten.

## Status
🚧 Work in progress — Frühe Entwicklungsphase

## Vision

> *Ein LLM-Agent mit Shell-Zugriff ist eine kontrollierte Waffe. Nicht die Fähigkeit ist das Problem — sondern unkontrollierte Fähigkeit. Dieses System gibt dem Agent genau so viel Macht wie er braucht, und nicht ein Byte mehr.*

OpenClaw ist mächtig. Zu mächtig für eine ungesicherte Standardinstallation.

Dieser Installer setzt nicht einfach eine OpenClaw-Instanz auf — er setzt eine **sichere** auf. By default. Ohne dass der Nutzer wissen muss was `exec-approvals`, Allowlists oder Security-Levels bedeuten.

**Prinzipien:**
- **Security by Default** — restriktive Allowlist, kein Root-Zugriff, keine gefährlichen Tools
- **Human in the Loop** — Approval-Mechanismus vorkonfiguriert, irreversible Aktionen brauchen Bestätigung
- **Guardrails vor Convenience** — der Wizard erklärt was jede Entscheidung bedeutet
- **Headless-tauglich** — läuft auf Raspberry Pi ohne Display
- **Saubere Trennung** — Kern-Logik ist UI-unabhängig, TUI ist Überbau

## Features (geplant v1)
- Docker-Verfügbarkeitscheck
- API-Key-Eingabe (Anthropic, optional Mistral/Telegram)
- Modellauswahl
- `docker-compose.yml` + `.env` Generierung
- Workspace-Bootstrapping (AGENTS.md, SOUL.md, MEMORY.md)
- Post-Install Gateway-Check

## Requirements
- Python 3.11+
- Docker + Docker Compose

## Stack
- TUI: `rich` + `questionary` (oder `textual`)
- Docker: Python docker SDK
- System: `psutil`, `httpx`, `platformdirs`
- Config: TOML (`tomllib` Stdlib)
- Templates: Jinja2
- Packaging: pyinstaller → single binary

## Struktur
```
src/
  main.py              ← Einstiegspunkt
  tui/
    wizard.py          ← Haupt-Wizard
    steps/             ← Je ein Schritt als Modul
  docker/
    compose_gen.py     ← docker-compose + .env Generator
    templates/         ← Jinja2-Templates
  bootstrap/
    workspace.py       ← Workspace-Struktur anlegen
    templates/         ← AGENTS.md, SOUL.md, MEMORY.md
  checks/
    docker_check.py    ← Docker verfügbar?
    gateway_check.py   ← Ping nach Install
tests/
```

## Lizenz
MIT — frei zu nutzen, zu modifizieren und weiterzugeben.

Wenn dir dieses Projekt das Leben erleichtert: Der Autor freut sich über ein Glas guten Walliser Rotwein. 🍷
