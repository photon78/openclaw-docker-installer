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
| **Restricted** | büro_bot, formular_bot | ❌ Kein python3, kein bash | Nur benannte Script-Pfade + Read-Tools (ls, cat, grep, etc.) |
| **Standard** | coding_bot | ✅ python3 + bash | Dev-Tools, Git, Node, SSH, aber kein systemctl, kein openclaw CLI |
| **Elevated** | main | ✅ python3 + bash | System-Tools, Gateway-Management, aber kein rm, kein pip3, kein Root |
| **Cron/Isolated** | defaults | ❌ Kein bash | python3 + Read-Tools + Health/Digest-Scripts |

### Warum kein bare Interpreter für Restricted Agents?

`/usr/bin/python3` in der Allowlist bedeutet: der Agent kann **jedes** Python ausführen — `python3 -c "import os; os.system('rm -rf /')"` matcht. Für Agents die nur Skills ausführen sollen, listen wir stattdessen die konkreten Script-Pfade:

```json
// ❌ Zu breit
{"pattern": "/usr/bin/python3"}

// ✅ Präzise
{"pattern": "/home/user/.openclaw/workspace/skills/web-search/search.py"}
{"pattern": "/home/user/.openclaw/workspace/skills/email/send_mail.py"}
```

**Bekannte Limitierung:** Agents mit bare python3 oder bash können diese Einschränkung umgehen. Das ist ein bewusster Kompromiss — Dev-Agents *brauchen* generellen Interpreter-Zugriff. Die Sicherheit liegt hier in der Beobachtbarkeit (Integrity-Audit), nicht in der Einschränkung.

---

## Schicht 2: Restore-Mechanismus

### Das Problem

`openclaw gateway install` und `openclaw update` können `exec-approvals.json` mit Defaults überschreiben. Alle manuellen Anpassungen wären verloren.

### Die Lösung

```
systemd ExecStartPost → restore_exec_approvals.py
```

Nach jedem Gateway-Start:
1. 2 Sekunden warten (Socket muss bereit sein)
2. Komplette Allowlist aus dem Python-Script schreiben
3. Log-Eintrag in `logs/restore-exec-approvals.log`

**Die Allowlist lebt im Code, nicht in der Datei.** `exec-approvals.json` ist generiert, nicht manuell editiert. Änderungen gehören ins Restore-Script.

### Installer-Kontext

Der Wizard generiert `restore_exec_approvals.py` basierend auf:
- Welche Agents konfiguriert wurden
- Welches Rechte-Tier pro Agent gewählt wurde
- Welche Skills installiert sind (→ Script-Pfade)

---

## Schicht 3: Integrity-Monitoring

### `audit_integrity.py` — eigenständiges Audit-Script

```bash
python3 audit_integrity.py              # Voller Report
python3 audit_integrity.py --silent     # Nur bei Änderungen
python3 audit_integrity.py --json       # Maschinenlesbar
python3 audit_integrity.py --reset      # Baselines neu setzen
```

**Was geprüft wird:**

| Check | Methode | Erkennt |
|-------|---------|---------|
| exec-approvals.json | SHA256-Hash vs. Baseline | Manipulation, unerwartete Updates |
| scripts/ Inventar | Dateiliste + individuelle Hashes | Neue Scripts, gelöschte Scripts, modifizierte Scripts |

**Wichtig:** Baselines werden bei erkannten Änderungen **nicht** automatisch überschrieben. Erfordert bewusstes `--reset` nach legitimen Änderungen. Ein Angreifer der die Baseline überschreibt, müsste dafür `audit_integrity.py --reset` ausführen — was im Script-Inventar wiederum auffällt.

**Exit-Codes:** 0 = OK, 1 = Änderungen, 2 = kritisch (Dateien fehlen)

### Integration im Health-Check

```
health_check.py
├── Disk, Gateway, Backup          ← System
├── Errors, Pakete, Logins         ← Security
├── API-Keys im Service-File       ← Secret-Leak-Detection
└── audit_integrity.py --silent    ← Integrity
```

Läuft täglich 07:45 via Crontab. Bei Änderungen: Alert via Telegram.

---

## Schicht 4: Secret-Management

### Prinzip: Secrets nur in `.env`, nirgendwo sonst

```
~/.openclaw/.env          ← einziger Ort für Secrets
├── ANTHROPIC_API_KEY
├── MISTRAL_API_KEY
├── EMAIL_PASSWD
├── TELEGRAM_BOT_TOKEN
└── LLM_BUDGET / LLM_STANDARD / LLM_POWER / LLM_MEDIA
```

- **systemd:** `EnvironmentFile=%h/.openclaw/.env` — nie `Environment=KEY=...` im Service-File
- **Health-Check:** prüft bei jedem Lauf ob API-Keys im Service-File stehen
- **`openclaw update`** kann Keys zurück ins Service-File schreiben → Health-Check erkennt das
- **Workspace-Dateien:** nie Secrets committen. `.gitignore` enthält `.env`

### Docker-Kontext

```yaml
volumes:
  - ${OPENCLAW_DATA}/.env:/data/.env:ro    # ← read-only!
```

`.env` ist read-only gemountet. Der Agent kann Secrets lesen (braucht er für API-Calls), aber nicht überschreiben.

---

## Schicht 5: Prozess-Isolation (Docker)

### Bind Mounts: read-write vs. read-only

```yaml
volumes:
  # Read-Write (Agent braucht Schreibzugriff)
  - ${OPENCLAW_DATA}/workspace:/data/workspace
  - ${OPENCLAW_DATA}/workspace-coding:/data/workspace-coding
  - ${OPENCLAW_DATA}/logs:/data/logs
  - ${OPENCLAW_DATA}/memory:/data/memory

  # Read-Only (Agent darf nicht ändern)
  - ${OPENCLAW_DATA}/scripts:/data/scripts:ro
  - ${OPENCLAW_DATA}/.env:/data/.env:ro
  - ${OPENCLAW_DATA}/openclaw.json:/data/openclaw.json:ro
```

**Warum Bind Mounts statt Named Volumes?** Backup, Migration (`openclaw-installer migrate`), manuelle Inspektion — alles funktioniert ohne Docker-Umwege.

**Warum scripts read-only?** Wenn der Agent ein neues Script anlegen könnte und es in der Allowlist steht, wäre die Allowlist wertlos. Scripts werden nur vom Installer oder vom User geändert — nie vom Agent zur Laufzeit.

### Native-Installation (Linux)

Kein Container = keine Prozess-Isolation. Die Sicherheit liegt vollständig in:
- Allowlist (was darf ausgeführt werden)
- User-Separation (Agent läuft als dedizierter User, nicht als root)
- Integrity-Monitoring (was hat sich verändert)
- Approval-Mechanismus (User bestätigt unbekannte Commands)

---

## Threat Model — ehrlich

### Was das System verhindert

✅ Agent führt willkürliche destructive Commands aus (`rm`, `dd`)
✅ Agent installiert Pakete (`pip3`, `apt`)
✅ Agent eskaliert zu Root
✅ Agent ändert seine eigene Allowlist (Docker: scripts read-only)
✅ Unbemerkte Allowlist-Manipulation (Integrity-Audit)
✅ Secret-Leaks ins Service-File (Health-Check)
✅ Allowlist-Verlust nach Gateway-Update (Restore-Script)

### Was das System NICHT verhindert

⚠️ **Agent mit bash/python3 kann Code generieren und ausführen** — die Allowlist schützt nur den Interpreter-Pfad, nicht den Inhalt. Ein Agent mit `python3` in der Allowlist kann theoretisch alles was der User kann.

⚠️ **Agent kann alle Dateien lesen auf die der User Zugriff hat** — `read`-Tool ist immer verfügbar, unabhängig von der Allowlist. Secrets die im Filesystem liegen, sind lesbar.

⚠️ **Social Engineering** — der Agent könnte den User dazu bringen, Commands zu approven die schädlich sind. Der Approval-Mechanismus schützt nur wenn der User versteht was er approved.

⚠️ **Datenexfiltration via API-Calls** — der Agent hat API-Keys und kann Daten an LLM-Provider senden. Das ist by Design (er braucht die Keys), aber ein kompromittierter Agent könnte sensible Daten in Prompts einbetten.

### Bewusste Kompromisse

| Kompromiss | Warum |
|-----------|-------|
| bash/python3 für Dev-Agents | Dev-Arbeit ohne Interpreter ist nicht praktikabel |
| `read`-Tool immer verfügbar | Agent braucht Dateizugriff für seine Kernfunktion |
| Approval-UI statt automatische Blockierung | Human-in-the-Loop > automatische Entscheidungen |
| Secrets in `.env` lesbar für Agent | Agent braucht API-Keys für Funktionalität |

---

## Installer-Wizard: Security-Setup

```
🔒 Security-Profil wählen:

  [Strict]    Empfohlen. Allowlist für alle Agents.
              Nur benannte Scripts, kein bare Interpreter
              für Nicht-Dev-Agents.

  [Standard]  Allowlist mit bare python3/bash für alle Agents.
              Mehr Flexibilität, weniger Isolation.

  [Custom]    Pro Agent einzeln konfigurieren.
              Für erfahrene User.

  ⚠️ "Full Access" wird bewusst nicht angeboten.
```

Bei **Strict:**
- Wizard fragt pro Agent: "Braucht dieser Agent Programmiersprachen-Zugriff?"
- Nein → nur Script-Pfade (Restricted Tier)
- Ja → python3 + bash (Standard/Elevated Tier)
- Integrity-Monitoring automatisch aktiv
- `scripts/` read-only im Docker

Bei **Standard:**
- Alle Agents bekommen python3 + bash
- Integrity-Monitoring aktiv
- Warnung: "Agents mit Interpreter-Zugriff können beliebigen Code ausführen"

---

## Checkliste für den Installer

```
[ ] exec-approvals.json generiert (pro Agent, pro Tier)
[ ] restore_exec_approvals.py generiert (aus Wizard-Config)
[ ] systemd ExecStartPost / Docker ENTRYPOINT konfiguriert
[ ] audit_integrity.py installiert + Baselines gesetzt
[ ] health_check.py mit Audit-Integration
[ ] .env angelegt (Secrets, LLM Tiers)
[ ] .env read-only gemountet (Docker)
[ ] scripts/ read-only gemountet (Docker)
[ ] Service-File ohne API-Keys
[ ] sudoers-Eintrag (nur spezifische Commands via NOPASSWD)
[ ] Approval-Buttons aktiv (Telegram/Discord)
```
