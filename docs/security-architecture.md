# Security-Architektur — OpenClaw Installer

## Designphilosophie

**Ein LLM-Agent mit Shell-Zugriff ist eine kontrollierte Waffe.** Nicht die Fähigkeit ist das Problem — sondern unkontrollierte Fähigkeit. Dieses System gibt dem Agent genau so viel Macht wie er braucht, und nicht ein Byte mehr.

Wir machen keine Illusionen: Ein Agent mit Allowlist ist **nicht** unknackbar. Aber er ist *beobachtbar*, *eingeschränkt* und *auditierbar*. Das ist der Unterschied zwischen einem offenen Scheunentor und einer Tür mit Schloss, Kamera und Alarm.

---

## Schicht 1: Exec-Approvals (Allowlist-System)

### Architektur

```
exec-approvals.json
├── defaults          ← gilt für ALLE Sessions (inkl. Crons, isolated)
├── agents
│   ├── main          ← Botmaster, breiteste Rechte
│   ├── coding_bot    ← Dev-Tools, Git, Node
│   ├── buero_bot     ← nur spezifische Script-Pfade
│   └── formular_bot  ← nur spezifische Script-Pfade
```

### Prinzip: Deny-by-Default, Allowlist-Only

```json
{
  "security": "allowlist",
  "ask": "on-miss",
  "askFallback": "deny"
}
```

- **`security: allowlist`** — nur explizit gelistete Commands erlaubt. `security: full` wird nie angeboten.
- **`ask: on-miss`** — was nicht auf der Liste steht, fragt den User
- **`askFallback: deny`** — wenn kein User antwortet: verweigern

### Rechte-Tiers

| Tier | Agents | Bare Interpreter | Was erlaubt |
|------|--------|-----------------|-------------|
| **Restricted** | büro_bot, formular_bot | ❌ Kein python3, kein bash | Nur benannte Script-Pfade + Read-Tools |
| **Standard** | coding_bot | ✅ python3 + bash | Dev-Tools, Git, Node, SSH — kein systemctl, openclaw CLI |
| **Elevated** | main | ✅ python3 + bash | System-Tools, Gateway-Management — kein rm, pip3, Root |
| **Cron/Isolated** | defaults | ❌ Kein bash | python3 + Read-Tools + Health/Digest-Scripts |

### Warum kein bare Interpreter für Restricted Agents?

```json
// ❌ Zu breit — matcht JEDEN Python-Code
{"pattern": "/usr/bin/python3"}

// ✅ Präzise — nur erlaubte Scripts
{"pattern": "/data/workspace/skills/web-search/search.py"}
{"pattern": "/data/workspace/skills/email/send_mail.py"}
```

**Bekannte Limitierung:** Agents mit bare python3/bash können die Einschränkung umgehen. Sicherheit liegt bei diesen Agents in der Beobachtbarkeit (Integrity-Audit), nicht in der Einschränkung.

---

## Schicht 2: Restore-Mechanismus

**Problem:** `openclaw update` überschreibt `exec-approvals.json` mit Defaults.

**Lösung:**
```
systemd ExecStartPost → restore_exec_approvals.py
Docker ENTRYPOINT    → restore_exec_approvals.py
```

**Die Allowlist lebt im Code, nicht in der Datei.** `exec-approvals.json` ist generiert, nicht manuell editiert.

Der Installer generiert `restore_exec_approvals.py` basierend auf:
- Welche Agents konfiguriert wurden
- Welches Rechte-Tier pro Agent gewählt wurde
- Welche Skills installiert sind (→ Script-Pfade)

---

## Schicht 3: Integrity-Monitoring

### `audit_integrity.py`

```bash
python3 audit_integrity.py              # Voller Report
python3 audit_integrity.py --silent     # Nur bei Änderungen (für Health-Check)
python3 audit_integrity.py --json       # Maschinenlesbar
python3 audit_integrity.py --reset      # Baselines neu setzen (nach legitimen Änderungen)
```

| Check | Methode | Erkennt |
|-------|---------|---------|
| exec-approvals.json | SHA256-Hash vs. Baseline | Manipulation, unerwartete Updates |
| scripts/ Inventar | Dateiliste + individuelle Hashes | Neue/gelöschte/modifizierte Scripts |

**Wichtig:** Baselines werden bei Änderungen **nicht** auto-überschrieben → manuelles `--reset`.

**Exit-Codes:** 0 = OK, 1 = Änderungen, 2 = kritisch

### Integration im Health-Check

```
health_check.py → audit_integrity.py --silent → Alert via Telegram
```

---

## Schicht 4: Secret-Management

- **Secrets nur in `.env`** — nie in openclaw.json, nie im Service-File
- **systemd:** `EnvironmentFile=%h/.openclaw/.env` — nie `Environment=KEY=...`
- **Health-Check:** erkennt API-Keys im Service-File (passiert nach `openclaw update`)
- **Docker:** `.env` read-only gemountet (`:ro`)
- **Workspace-Dateien:** `.gitignore` enthält `.env`

```
.env
├── ANTHROPIC_API_KEY
├── MISTRAL_API_KEY
├── TELEGRAM_BOT_TOKEN
└── LLM_BUDGET / LLM_STANDARD / LLM_POWER / LLM_MEDIA
```

---

## Schicht 5: Prozess-Isolation (Docker)

```yaml
volumes:
  # Read-Write (Agent braucht Schreibzugriff)
  - ${OPENCLAW_DATA}/workspace:/data/workspace
  - ${OPENCLAW_DATA}/logs:/data/logs

  # Read-Only (Agent darf nicht ändern)
  - ${OPENCLAW_DATA}/scripts:/data/scripts:ro
  - ${OPENCLAW_DATA}/.env:/data/.env:ro
  - ${OPENCLAW_DATA}/openclaw.json:/data/openclaw.json:ro
```

**Warum scripts read-only?** Agent könnte sonst neues Script anlegen und ausführen → Allowlist wäre wertlos.

**Warum Bind Mounts?** Backup, Migration (`openclaw-installer migrate`), manuelle Inspektion ohne Docker-Umwege.

---

## Threat Model — ehrlich

### Was das System verhindert

✅ Willkürliche destructive Commands (`rm`, `dd`)
✅ Paket-Installation (`pip3`, `apt`)
✅ Root-Eskalation
✅ Allowlist-Selbstmodifikation (Docker: scripts read-only)
✅ Unbemerkte Allowlist-Manipulation (Integrity-Audit)
✅ Secret-Leaks ins Service-File (Health-Check)
✅ Allowlist-Verlust nach Gateway-Update (Restore-Script)

### Was das System NICHT verhindert

⚠️ **Agents mit bash/python3** können beliebigen Code ausführen — Allowlist prüft nur den Interpreter-Pfad
⚠️ **Alle Dateien lesbar** — `read`-Tool ist immer verfügbar, unabhängig von der Allowlist
⚠️ **Social Engineering** — Approval-Mechanismus schützt nur wenn der User versteht was er approved
⚠️ **Datenexfiltration via API-Calls** — Agent hat API-Keys und könnte sensible Daten in Prompts einbetten

### Bewusste Kompromisse

| Kompromiss | Warum |
|-----------|-------|
| bash/python3 für Dev-Agents | Dev-Arbeit ohne Interpreter nicht praktikabel |
| `read`-Tool immer verfügbar | Agent braucht Dateizugriff für Kernfunktion |
| Approval-UI statt Auto-Blockierung | Human-in-the-Loop > automatische Entscheidungen |
| Secrets lesbar für Agent | Agent braucht API-Keys für Funktionalität |

---

## Installer-Wizard: Security-Setup

```
🔒 Security-Profil wählen:

  [Strict]    Empfohlen.
              Nur benannte Scripts für Nicht-Dev-Agents.
              Integrity-Monitoring aktiv.

  [Standard]  python3 + bash für alle Agents.
              Mehr Flexibilität, weniger Isolation.

  [Custom]    Pro Agent konfigurieren.

  ⚠️ "Full Access" wird bewusst nicht angeboten.
```

---

## Agent-zu-Agent-Kommunikation: Task-Files statt Message-Kanäle

**Direktes A2A-Messaging ist ein Sicherheitsrisiko.**

Wenn Agents direkt miteinander kommunizieren (z.B. via sessions_send mit strukturierten Daten), können sensible Informationen — API-Keys, Nutzerdaten, interner State — unkontrolliert in fremde LLM-Kontexte gelangen. Das LLM auf der Empfängerseite sieht alles was gesendet wird, und das ist nicht immer was gewünscht ist.

**Die Alternative: Task-Files.**

Agents kommunizieren über strukturierte Dateien in `workspace/tasks/YYYY-MM-DD-<name>.md`:
- Jeder Agent liest nur was er braucht, wann er es braucht
- Keine Daten überqueren unbeabsichtigt die Kontextgrenze
- Die Kommunikation ist asynchron, auditierbar und im Dateisystem nachvollziehbar
- Der sendende Agent schreibt den Task — der empfangende Agent liest ihn via `check_tasks.py`

```
# Faustregel
Kein direktes A2A-Messaging für strukturierte Aufgaben.
Task-Files statt Message-Kanäle.

# sessions_send ist erlaubt für:
- Kurze Status-Updates ("Task erledigt")
- Eskalationen an den Operator
- Nicht für: strukturierte Daten, interne State, Credentials
```

---

## Installer-Checkliste

```
[ ] exec-approvals.json generiert (pro Agent, pro Tier)
[ ] restore_exec_approvals.py generiert
[ ] systemd ExecStartPost / Docker ENTRYPOINT konfiguriert
[ ] audit_integrity.py installiert + Baselines gesetzt
[ ] health_check.py mit Audit-Integration
[ ] .env angelegt + read-only gemountet (Docker)
[ ] scripts/ read-only gemountet (Docker)
[ ] Service-File ohne API-Keys
[ ] sudoers-Eintrag (spezifische Commands, kein Wildcard)
[ ] Approval-Buttons aktiv (Telegram/Discord)
```
