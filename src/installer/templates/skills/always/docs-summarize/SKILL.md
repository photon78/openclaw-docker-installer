---
name: docs-summarize
description: >
  Summarize API/framework documentation into a structured Working Reference.
  Use when an agent needs to efficiently process external docs (URL or local file)
  without reading them incrementally multiple times. Produces a compact, reusable
  reference in memory/topics/ or a task-local work/ directory.
when_to_use:
  - Agent needs to understand a new API, CLI tool, or framework
  - Documentation is too long to read inline (>2000 tokens)
  - A reusable reference should be saved for future sessions
  - Quick lookup of commands, parameters, or patterns is needed
usage: |
  python3 ~/.openclaw/workspace/skills/docs-summarize/summarize.py <url-or-path> [options]

  Options:
    --permanent          Save to memory/docs/docs-<name>.md (default: workspace root)
    --task <name>        Save to work/<name>/docs-summary.md (task-local)
    --name <name>        Override output filename (default: derived from URL/path)
    --model <model>      Mistral model to use (default: mistral-large-latest)

  Examples:
    python3 summarize.py https://docs.example.com/api --permanent --name myapi
    python3 summarize.py /home/hummer/docs/manual.md --task myproject
    python3 summarize.py https://api.example.com/openapi.json --name openapi
---

# Skill: docs-summarize

Reads a URL or local file and produces a structured Working Reference via Mistral API.

## Output Schema

```
# Docs Reference: <Tool/Framework>
## Scope (Version, Quelle, Datum)
## Core Commands / Endpoints
## Parameters (Tabelle: Name | Typ | Pflicht | Default)
## Supported Patterns
## Gotchas & Known Limits
## Minimal Examples
## Source Sections
```

## Requirements

- `MISTRAL_API_KEY` environment variable must be set
- `requests` Python package (system default, no install needed)
- Python 3.8+
