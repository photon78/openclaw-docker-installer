# Design Decisions — openclaw-docker-installer

Dieses Dokument hält wichtige Designentscheide fest — warum etwas so ist wie es ist.
Nicht für den Nutzer. Für uns, wenn wir in 6 Monaten fragen: "Warum haben wir das so gemacht?"

---

## Designphilosophie (Landing Page — erster Satz)

> *Ein LLM-Agent mit Shell-Zugriff ist eine kontrollierte Waffe. Nicht die Fähigkeit ist das Problem — sondern unkontrollierte Fähigkeit. Dieses System gibt dem Agent genau so viel Macht wie er braucht, und nicht ein Byte mehr.*

— Photon, 2026-04-05

---

## DD-001: Allowlist — "Du kannst alles, aber nicht gleichzeitig"

**Entscheid:** Der Installer konfiguriert `security: allowlist` mit explizit genehmigten Binaries. Kein `security: full`.

**Kernproblem:**
Jede genehmigte Binary läuft ohne Approval. Aber `ls | grep foo` = `bash -c "ls | grep foo"` = Bash-Compound = Bash muss in der Allowlist stehen. Wer Pipes will, muss ein Python-Script schreiben das die Pipe intern kapselt — dann steht nur der Script-Pfad in der Allowlist.

**Konsequenz für den Nutzer:**
> "Du kannst alles, aber nicht gleichzeitig."

**Warum das Feature ist, nicht Bug:**
- Zwingt dazu, Logik in Scripts zu kapseln statt als Inline-Chains
- Scripts sind testbar, versionierbar, nachvollziehbar
- Inline-Pipe-Chains sind es nicht
- Der Nutzer sieht immer genau was genehmigt ist

**Was der Installer tut:**
- Erklärt dieses Verhalten explizit im Wizard-Schritt "Sicherheit & Allowlist"
- Zeigt welche Binaries vorinstalliert genehmigt sind und warum
- Warnt wenn jemand `bash` mit Wildcard oder `security: full` aktivieren will

**Quelle:** Photon + coding_zot, 2026-04-05

---

## DD-002: Security by Default, nicht Security by Choice

**Entscheid:** Der Installer bietet keine "Ich weiss was ich tue, alles aufmachen"-Option in der Standard-Installation.

**Begründung:**
Ein unbedarfter Nutzer in einer Messwarte eines Chemiebetriebs würde "alles aufmachen" klicken weil es bequemer ist. Das Szenario ist nicht theoretisch.

**Was der Installer tut:**
- Restriktive Defaults, keine Wildcard-Option im MVP
- Wer mehr will, muss manuell in `exec-approvals.json` eingreifen — bewusste Entscheidung, nicht Klick

**Quelle:** Photon + coding_zot, 2026-04-05

---

## DD-003: TUI statt GUI

**Entscheid:** Terminal-UI (`rich` + `questionary`), kein GUI-Framework.

**Begründung:**
- Läuft auf Headless Raspberry Pi ohne Display
- Kein PyInstaller-Overhead durch Qt/Tk
- Cross-platform robuster
- Kern-Logik bleibt UI-unabhängig — TUI ist Überbau

**Quelle:** Photon + coding_zot, 2026-04-05

---

## DD-005: Extended Memory — Opt-in, nicht Default

**Entscheid:** Das dreischichtige Memory-System läuft immer. Semantische Vektorsuche (Mistral-Embeddings) ist Opt-in.

**Standard (kein Mistral-Key):**
- SQLite + FTS5 Volltext-Suche
- Funktioniert, findet exakte Begriffe
- Null Zusatzkosten

**Opt-in "Extended Memory" (mit Mistral-Key):**
- SQLite + FTS5 + Mistral `mistral-embed` (1024 dims) + sqlite-vec
- Hybrid-Search: BM25 (0.3) + Vektor (0.7)
- Findet semantisch verwandte Begriffe — "Unterkunft" trifft "Hotelzimmer"
- Kostet Mistral API-Calls für jeden Embedding-Index-Aufbau

**Wizard-Text:**
> "Ohne Mistral: Volltext-Suche — findet exakt was du eingibst.  
> Mit Mistral: semantische Suche — findet auch verwandte Begriffe.  
> Empfehlung: Mistral-Key eingeben wenn vorhanden. Kann später aktiviert werden."

**Quelle:** Photon, 2026-04-05

---

## DD-004: Kern-API-Schicht ist UI-unabhängig

**Entscheid:** `checks/`, `docker/`, `bootstrap/`, `security/` haben keine UI-Abhängigkeit. TUI ruft den Kern an, nicht umgekehrt.

**Begründung:**
- Ermöglicht später Web-UI, CLI-only Modus, oder andere Frontends
- Kern ist testbar ohne UI
- Headless-Betrieb (z.B. CI/CD) möglich

**Quelle:** Photon (Sprachnachricht), 2026-04-05
