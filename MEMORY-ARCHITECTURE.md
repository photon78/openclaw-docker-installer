# Memory-Architektur — openclaw-docker-installer

> Referenz für den Installer: Was wird aufgebaut, warum, und wie.

---

## Konzept: Dreischichtiges Memory-System

Alles Markdown, kein externes Backend, kein Vektor-Datenbank-Setup nötig.
Die Memory-Engine (SQLite + FTS5 + Mistral-Embeddings) läuft automatisch im Gateway.

---

## Schicht 1: MEMORY.md — Langzeitgedächtnis

```
~/.openclaw/workspace/MEMORY.md
```

- Max 30 Zeilen, nur stabile Fakten und Regeln
- Wird bei jedem Session-Start vollständig in den Context geladen → jede Zeile kostet Tokens
- Nie aufblähen — Details gehören in `memory/topics/`
- Heartbeat darf nur kürzen wenn ≥25 Zeilen, nie ergänzen

**Was der Installer anlegt:** Ein minimales Template mit Name, Rolle, Nutzer-Infos — Rest füllt der Agent selbst.

---

## Schicht 2: Daily Logs — Rohmaterial

```
~/.openclaw/workspace/memory/YYYY-MM-DD.md
```

- Was heute passiert ist — Entscheidungen, offene Punkte
- Format: `## HH:MM — Thema` + Stichpunkte
- Max 5 Zeilen pro Stunde — kompakt halten
- Today + Yesterday werden automatisch in den Context geladen → kosten Tokens bei jedem Call
- Bei Mistral (kein Prompt-Caching): voller Preis → umso wichtiger kurz zu bleiben

**Was der Installer anlegt:** Leeres Log für heute. Der Agent schreibt ab dem ersten Gespräch.

---

## Schicht 3: Topics — Verdichtetes Wissen

```
~/.openclaw/workspace/memory/topics/
  _template.md      ← Template für neue Topics
  index.md          ← Übersicht aller Topics
```

- Strukturiertes Wissen pro Thema
- Inhalt: Kurzfassung, Status, Relevanztrigger, Kernwissen, Entscheidungen
- Weekly Maintenance Cron verdichtet Daily Logs → Topics (Freitag 04:00)

**Was der Installer anlegt:** `_template.md` + leeres `index.md`. Topics entstehen im Betrieb.

---

## Memory Engine (automatisch durch Gateway)

| Komponente | Detail |
|---|---|
| Storage | SQLite + FTS5 + sqlite-vec |
| Embeddings | Mistral (`mistral-embed`, 1024 dims) |
| Hybrid-Search | BM25 (Gewicht 0.3) + Vektor (Gewicht 0.7) |
| Index | `~/.openclaw/memory/<agentId>.sqlite` |
| `memory_search` | Semantische Suche über alle `.md` im Workspace |
| `memory_get` | Gezielt Zeilen aus Treffern lesen |

**Voraussetzung:** Mistral API-Key nötig für Embeddings. Ohne Mistral: nur FTS5 (Volltext), keine Vektor-Suche.

---

## Cross-Agent Memory: Sub-Agent liest Main-Topics

Sub-Agents haben eigene Workspaces — sie sehen Main-Topics NICHT automatisch.

**Lösung 1: `extraPaths` in `openclaw.json`**

```json
"agents": {
  "list": [
    {
      "id": "coding_bot",
      "memorySearch": {
        "extraPaths": ["~/.openclaw/workspace/memory/topics"]
      }
    }
  ]
}
```

Damit indiziert `coding_bot` die Main-Topics in seinen eigenen Memory-Index.
`memory_search` findet Treffer aus beiden Quellen — eigener Workspace + Main-Topics.

**Lösung 2: Daily Digest als Flat-File-Fallback**

`daily_digest.py` schreibt `memory/digest-latest.md` in alle Sub-Workspaces:
- 3× täglich (03:05, 11:05, 18:05)
- Kein LLM, kein API-Call, null Kosten
- Atomares Schreiben via `os.replace()` (Race-Condition-sicher)

Beide Lösungen ergänzen sich — `extraPaths` für strukturiertes Wissen, Digest für tagesaktuelles.

---

## Automation (Cron-Jobs)

| Zeit | Job | Modell | Was |
|---|---|---|---|
| Stündlich :05 | Log Writer | — | Daily Log schreiben |
| 03:05, 11:05, 18:05 | `daily_digest.py` | kein LLM | Digest in alle Sub-Workspaces |
| Freitag 04:00 | Weekly Maintenance | Mistral | Daily Logs → Topics verdichten |
| Täglich 07:45 | Health Check | Mistral | Silent on success |
| Täglich 07:55 | Morning Briefing | Mistral | Immer senden |

---

## Wichtige Regeln (für AGENTS.md Template)

1. `memory_search` vor jeder Antwort die auf frühere Arbeit, Entscheidungen oder Projekte referenziert
2. Treffer → `memory_get` für die relevanten Zeilen
3. MEMORY.md slim halten — ≤30 Zeilen, sonst wird der Bootstrap teuer
4. Daily Logs kompakt — max 5 Zeilen/h, nur Entscheidungen und offene Punkte
5. Nach Fortschritten: Topic-Datei updaten, nicht Daily Log aufblähen
6. Spawned Sub-Agents (`sessions_spawn`) haben KEIN `memory_search` — nur persistente Agents mit eigener `agentId`

---

## Was der Installer konkret anlegt

```
~/.openclaw/workspace/
  MEMORY.md                    ← Template (slim, ≤10 Zeilen initial)
  AGENTS.md                    ← Pflicht-Regeln inkl. Memory-Workflow
  SOUL.md                      ← Vom Nutzer konfiguriert via Wizard
  IDENTITY.md                  ← Name, Emoji, Vibe
  USER.md                      ← Vom Wizard ausgefüllt
  HEARTBEAT.md                 ← Heartbeat-Verhalten
  TOOLS.md                     ← Leer, für Nutzer
  memory/
    YYYY-MM-DD.md              ← Leeres Log für heute
    digest-latest.md           ← Leer, wird von Digest-Cron gefüllt
    topics/
      _template.md             ← Topic-Template
      index.md                 ← Leer, wächst im Betrieb
```

Für Sub-Agents zusätzlich:
```
~/.openclaw/workspace-<name>/
  SOUL.md                      ← Eigener Charakter
  IDENTITY.md                  ← Eigener Name
  memory/
    digest-latest.md           ← Wird von Digest-Cron befüllt
    topics/                    ← Leer
  AGENTS.md -> ../workspace/AGENTS.md    (Symlink)
  USER.md -> ../workspace/USER.md        (Symlink)
  HEARTBEAT.md -> ../workspace/HEARTBEAT.md (Symlink)
  skills/ -> ../workspace/skills/        (Symlink)
```
