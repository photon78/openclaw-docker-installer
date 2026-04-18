# Workspace File Management — OpenClaw Multi-Agent Setup

**Datum:** 2026-04-08 | **Quelle:** Produktionserfahrung (Alpenblick Pi, 2 Wochen Betrieb)

---

## Problem: OpenClaw folgt keine Symlinks

OpenClaw's **Project Context Injection** (automatisches Einlesen der Workspace-Dateien in den System-Prompt) folgt **keine symbolischen Links**. Symlinkte Dateien werden als `[MISSING]` gemeldet und **nicht in den Agent-Kontext injiziert**.

**Auswirkung:** Agent läuft ohne AGENTS.md, USER.md etc. im Kontext — Regeln, Persona, User-Infos fehlen im System-Prompt.

**Wichtig:** Das `read`-Tool folgt Symlinks auf OS-Ebene. Agents können Symlink-Inhalte via explizitem `read`-Aufruf lesen — aber das ist unsicher und inkonsequent.

---

## Lösung: Echte Dateikopien pro Workspace

Jeder Agent-Workspace braucht **echte Kopien** aller relevanten Dateien — keine Symlinks.

### Pflichtdateien pro Workspace

| Datei | Inhalt | Workspace-spezifisch? |
|-------|--------|----------------------|
| `AGENTS.md` | Regeln, Tool-Verhalten, Kommunikation | Ja — Agent-Name, spezifische Regeln |
| `USER.md` | Photon-Profil, Timezone, Kommunikationsstil | Nein — identisch in allen Workspaces |
| `SOUL.md` | Persona, Rolle, Charakter | Ja — je nach Agent-Funktion |
| `IDENTITY.md` | Name, Emoji, Avatar | Ja — je nach Agent |
| `HEARTBEAT.md` | Heartbeat-Verhalten, Pfade | Ja — workspace-spezifische Pfade |
| `MEMORY.md` | Langzeitgedächtnis | Ja — agent-spezifisch |
| `BOOTSTRAP.md` | Bootstrap-Infos | Je nach Setup |

### Symlinks die ERLAUBT sind

| Element | Typ | Warum OK |
|---------|-----|----------|
| `skills/` | Verzeichnis-Symlink | Wird nicht als Datei injiziert — nur vom Agent via `read` genutzt |

---

## Installer-Aufgabe

Beim Setup eines neuen Agents:

```python
# Echte Dateien kopieren, KEINE Symlinks
for filename in ["AGENTS.md", "USER.md", "SOUL.md", "IDENTITY.md", "HEARTBEAT.md"]:
    src = main_workspace / filename
    dst = agent_workspace / filename
    if src.exists():
        shutil.copy2(src, dst)
        # NICHT: dst.symlink_to(src)

# skills/ als Symlink ist OK
skills_link = agent_workspace / "skills"
if not skills_link.exists():
    skills_link.symlink_to(main_workspace / "skills")
```

---

## Sync-Regel (Betrieb)

Wenn gemeinsame Inhalte (z.B. `USER.md`, geteilte Regeln in `AGENTS.md`) geändert werden:

1. Datei im main-Workspace editieren
2. Änderungen in alle Agent-Workspaces propagieren
3. Workspace-spezifische Teile (Agent-Name, Pfade) beibehalten

**Vorgehen:** Zot (main) übernimmt die Synchronisation wenn Photon Änderungen anordnet.

---

## Aktueller Stand (Alpenblick Pi, 2026-04-08)

| Workspace | AGENTS.md | USER.md | SOUL.md | HEARTBEAT.md |
|-----------|-----------|---------|---------|--------------|
| `workspace/` (main) | ✅ Original | ✅ Original | ✅ Original | ✅ Original |
| `workspace-coding/` | ✅ Kopie | ✅ Kopie | ✅ eigene Datei | ✅ Kopie |
| `workspace-research/` | ✅ Kopie | ✅ eigene Datei | ✅ eigene Datei | ✅ eigene Datei |

---

## Verwandte Themen

- `AGENTS-ARCHITECTURE.md` — Agent-Rollen und Workspace-Struktur
- `MEMORY-ARCHITECTURE.md` — Memory-System und Topics
