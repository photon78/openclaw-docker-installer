# VM Test Environment Setup

> For manual integration testing of the installer on a clean system.
> Internal reference — not for end users.

---

## Goal

Test the installer on a fresh system without any assumptions about the host environment.
Catches issues that don't appear on the Pi setup (hardcoded paths, missing dependencies, etc.).

---

## Recommended VM Specs

| Item | Recommendation |
|------|---------------|
| OS | Ubuntu 24.04 LTS or Debian 12 (Bookworm) |
| RAM | 2 GB minimum, 4 GB recommended |
| Disk | 20 GB |
| User | Any username — NOT `hummer` (intentional!) |
| Network | Bridged or NAT (internet access needed) |

---

## Step 1: Base System

```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y git python3 python3-pip python3-venv curl
```

---

## Step 2: Docker

```bash
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER
newgrp docker

# Verify
docker --version
docker compose version
```

---

## Step 3: Clone Installer

```bash
git clone git@github-installer:photon78/openclaw-docker-installer.git
cd openclaw-docker-installer
git checkout feature/prototype-docker-check
```

> **Note:** Deploy key required for private repo. See [GitHub Deploy Keys](https://docs.github.com/en/authentication/connecting-to-github-with-ssh/managing-deploy-keys).

---

## Step 4: Python Environment

```bash
python3 -m venv .venv --copies
source .venv/bin/activate
# Editable install may fail on Ubuntu 24.04 due to setuptools — use direct install instead:
pip install typer rich questionary httpx psutil platformdirs docker jinja2 pytest
```

---

## Step 5: Run Tests

```bash
pytest tests/ -v
```

All tests should pass without Docker running (mock-based).

---

## Step 6: Run Wizard

```bash
python src/main.py install
```

Durchklicken mit echten oder Test-Credentials.

---

## Step 7: Start Gateway

```bash
docker compose -f ~/.openclaw/docker-compose.yml up -d
docker compose -f ~/.openclaw/docker-compose.yml logs -f
```

---

## Step 8: Clean für neuen Testlauf

```bash
./scripts/clean.sh        # mit Bestätigung
./scripts/clean.sh --yes  # ohne Rückfrage
```

Entfernt: Container, Image (`ghcr.io/openclaw/openclaw:*`), `~/.openclaw/`.

---

## Manuelle Checks

- [ ] Wizard startet ohne Fehler
- [ ] Platform Detection: korrekter Username (nicht `hummer`)
- [ ] API Key Input funktioniert
- [ ] `docker-compose.yml` generiert mit korrekten Pfaden (kein `/home/hummer`)
- [ ] `.env` korrekt, keine Duplikate, keine `+`-Zeilen
- [ ] `openclaw.json` valid — `models` ist Dict von ID→Objekt
- [ ] `exec-approvals.json` verwendet `Path.home()` korrekt
- [ ] Gateway startet ohne Config-Errors
- [ ] Completion-Screen zeigt korrekten `docker compose`-Befehl

---

## What to Watch For

- Any hardcoded `/home/hummer` in generated files → bug
- Any assumption about username → bug
- Missing Python dependencies → add to pyproject.toml
- Docker permission issues → document workaround

---

## Reporting Issues

Open a GitHub issue with label `bug` and tag `vm-test`.
Include: OS version, username, exact error message.
