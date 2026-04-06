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
git clone https://github.com/photon78/openclaw-docker-installer.git
cd openclaw-docker-installer
```

---

## Step 4: Python Environment

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

---

## Step 5: Run Tests

```bash
pytest tests/ -v
```

All tests should pass without Docker running (mock-based).

---

## Step 6: Manual Checks (when wizard exists)

- [ ] Wizard starts without errors
- [ ] Platform detection works (Linux, correct username)
- [ ] API key input works
- [ ] docker-compose.yml generated with correct paths (no `/home/hummer`)
- [ ] .env generated correctly
- [ ] exec-approvals.json uses `Path.home()` correctly
- [ ] restore_exec_approvals.py runs without errors
- [ ] Gateway ping works after docker-compose up

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
