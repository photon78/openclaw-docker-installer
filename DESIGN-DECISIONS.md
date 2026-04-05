# Design Decisions — openclaw-docker-installer

This document records key design decisions — why things are the way they are.
Not for the user. For us, when we ask in six months: "Why did we do it this way?"

---

## Design Philosophy (Landing Page — First Sentence)

> *An LLM agent with shell access is a controlled weapon. The issue isn't the capability — it's uncontrolled capability. This system gives the agent exactly as much power as it needs, and not a byte more.*

— Photon, 2026-04-05

---

## DD-001: Allowlist — "You can do anything, but not all at once"

**Decision:** The installer configures `security: allowlist` with explicitly approved binaries. No `security: full`.

**Core Problem:**
Every approved binary runs without approval. But `ls | grep foo` = `bash -c "ls | grep foo"` = Bash compound = Bash must be on the allowlist. If you want pipes, you must write a Python script that encapsulates the pipe internally — then only the script path is on the allowlist.

**Consequence for the User:**
> *"You can do anything, but not all at once."*

**Why This Is a Feature, Not a Bug:**
- Forces logic to be encapsulated in scripts rather than inline chains
- Scripts are testable, versionable, traceable
- Inline pipe chains are not
- The user always sees exactly what is approved

**What the Installer Does:**
- Explains this behavior explicitly in the "Security & Allowlist" wizard step
- Shows which binaries are pre-approved and why
- Warns if someone tries to enable `bash` with a wildcard or `security: full`

**Source:** Photon + coding_zot, 2026-04-05

---

## DD-002: Security by Default, Not Security by Choice

**Decision:** The installer does not offer an "I know what I'm doing, open everything" option in the standard installation.

**Reasoning:**
An inexperienced user in a chemical plant control room would click "open everything" because it's more convenient. This scenario is not theoretical.

**What the Installer Does:**
- Restrictive defaults, no wildcard option in the MVP
- Those who want more must manually edit `exec-approvals.json` — a conscious decision, not a click

**Source:** Photon + coding_zot, 2026-04-05

---

## DD-003: TUI Instead of GUI

**Decision:** Terminal UI (`rich` + `questionary`), no GUI framework.

**Reasoning:**
- Runs on headless Raspberry Pi without a display
- No PyInstaller overhead from Qt/Tk
- More robust cross-platform
- Core logic remains UI-independent — TUI is just a layer on top

**Source:** Photon + coding_zot, 2026-04-05

---

## DD-004: Core API Layer Is UI-Independent

**Decision:** `checks/`, `docker/`, `bootstrap/`, `security/` have no UI dependencies. The TUI calls the core, not the other way around.

**Reasoning:**
- Enables future web UI, CLI-only mode, or other frontends
- Core is testable without UI
- Headless operation (e.g., CI/CD) possible

**Source:** Photon (voice message), 2026-04-05

---

## DD-005: Extended Memory — Opt-in, Not Default

**Decision:** The three-layer memory system always runs. Semantic vector search (Mistral embeddings) is opt-in.

**Standard (No Mistral Key):**
- SQLite + FTS5 full-text search
- Works, finds exact terms
- Zero additional costs

**Opt-in "Extended Memory" (With Mistral Key):**
- SQLite + FTS5 + Mistral `mistral-embed` (1024 dims) + sqlite-vec
- Hybrid search: BM25 (0.3) + vector (0.7)
- Finds semantically related terms — "accommodation" matches "hotel room"
- Costs Mistral API calls for each embedding index build

**Wizard Text:**
> *"Without Mistral: Full-text search — finds exactly what you enter.
> With Mistral: Semantic search — also finds related terms.
> Recommendation: Enter a Mistral key if available. Can be activated later."*

**Source:** Photon, 2026-04-05
