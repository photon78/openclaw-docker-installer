# Contributing to openclaw-docker-installer

First: thank you. Every issue filed, every PR opened, every question asked makes this project better.

---

## Philosophy

This project exists because we believe **secure by default** is not optional — especially for tools that give AI agents shell access. If you contribute, you share that belief. We won't merge features that trade security for convenience without a very good reason.

---

## How to contribute

### Reporting bugs

Use the [Bug Report](.github/ISSUE_TEMPLATE/bug_report.md) issue template.  
Include: OS, Python version, Docker version, what you expected, what happened.

### Requesting features

Use the [Feature Request](.github/ISSUE_TEMPLATE/feature_request.md) template.  
Explain the use case, not just the feature.

### Security vulnerabilities

**Do not open a public issue.** See [SECURITY.md](SECURITY.md) for responsible disclosure.

### Code contributions

1. Fork the repo
2. Create a branch: `feature/your-thing` or `fix/your-bug`
3. Write tests for non-UI code (target: 80%+ coverage)
4. Run checks before pushing (see below)
5. Open a PR against the **active feature branch** (currently `feature/windows-compat`) — not directly against `main`

> **Why?** `main` is always releasable. New work lands in a feature branch first, gets reviewed there, then merges to `main` as a unit.

---

## Development setup

```bash
git clone https://github.com/photon78/openclaw-docker-installer
cd openclaw-docker-installer
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

### Run tests

```bash
pytest tests/ -v
```

### Linting + type checks

```bash
ruff check src/ tests/
mypy src/
```

### All checks at once

```bash
bash run_tests.sh
```

---

## Code style

- **Python 3.11+**, type hints everywhere
- **ruff** for linting (config in `pyproject.toml`)
- **mypy** for type checking
- **Google-style docstrings** for all public functions/classes
- No bare `except:` — always catch specific exceptions
- No `subprocess` with `shell=True`
- No hardcoded paths — use `platformdirs` or pass paths as arguments

---

## Branching

| Prefix | Use for |
|--------|---------|
| `feature/` | New features |
| `fix/` | Bug fixes |
| `docs/` | Documentation only |
| `refactor/` | Restructuring without new behaviour |

Merge directly into `main`. PRs require passing CI.

---

## Commit messages

```
feat: add Docker Compose generator
fix: handle missing .env on first run
docs: update security architecture
refactor: extract gateway check into own module
```

---

## DCO — Developer Certificate of Origin

By contributing, you certify that:
- The contribution is your own work, or you have the right to submit it
- You agree it may be distributed under the MIT License

No CLA required. Just be honest.

---

## Questions?

Open a Discussion or ping us in the [OpenClaw Discord](https://discord.com/invite/clawd).
