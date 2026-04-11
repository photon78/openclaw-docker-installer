#!/usr/bin/env python3
"""
IMAP Email Checker — zot@alpenblickzeneggen.ch
Prüft auf ungelesene Mails und gibt eine Zusammenfassung aus.
Usage: python3 check_mail.py [--all] [--mark-read] [--max N]
"""

import imaplib
import email
import os
import sys
import argparse
from pathlib import Path
from email.header import decode_header

IMAP_HOST = "mx.rhone.ch"
IMAP_PORT = 993
EMAIL_USER = "zot@alpenblickzeneggen.ch"

def load_password():
    # Erst aus Umgebungsvariable
    pwd = os.environ.get("EMAIL_PASSWD", "")
    if pwd:
        return pwd
    # Fallback: .env lesen
    env_path = Path.home() / ".openclaw" / ".env"
    try:
        with open(env_path) as f:
            for line in f:
                if line.startswith("EMAIL_PASSWD="):
                    return line.split("=", 1)[1].strip().strip("\"'")
    except Exception as e:
        print(f"ERROR: Konnte {env_path} nicht lesen: {e}", file=sys.stderr)
        sys.exit(1)
    print(f"ERROR: EMAIL_PASSWD nicht in {env_path} gefunden", file=sys.stderr)
    sys.exit(1)

EMAIL_PASS = load_password()

def decode_str(s):
    if s is None:
        return ""
    parts = decode_header(s)
    decoded = []
    for part, enc in parts:
        if isinstance(part, bytes):
            decoded.append(part.decode(enc or "utf-8", errors="replace"))
        else:
            decoded.append(part)
    return " ".join(decoded)

def get_body(msg):
    body = ""
    attachments = []
    if msg.is_multipart():
        for part in msg.walk():
            ct = part.get_content_type()
            cd = str(part.get("Content-Disposition", ""))
            if "attachment" in cd:
                attachments.append(part.get_filename() or "unbekannt")
            elif ct == "text/plain" and not body:
                body = part.get_payload(decode=True).decode("utf-8", errors="replace")
    else:
        body = msg.get_payload(decode=True).decode("utf-8", errors="replace")
    return body.strip(), attachments

def check_mail(mark_read=False, max_results=10, show_all=False):
    if not EMAIL_PASS:
        print("ERROR: EMAIL_PASSWD nicht gesetzt", file=sys.stderr)
        sys.exit(1)

    try:
        mail = imaplib.IMAP4_SSL(IMAP_HOST, IMAP_PORT)
        mail.login(EMAIL_USER, EMAIL_PASS)
        mail.select("INBOX")

        criteria = "ALL" if show_all else "UNSEEN"
        status, messages = mail.search(None, criteria)
        if status != "OK":
            print("Keine Mails gefunden.")
            return

        msg_ids = messages[0].split()
        if not msg_ids:
            print("Keine ungelesenen Mails." if not show_all else "Inbox leer.")
            mail.logout()
            return

        label = "Mail(s)" if show_all else "ungelesene Mail(s)"
        print(f"📬 {len(msg_ids)} {label}:\n")

        for msg_id in msg_ids[-max_results:]:
            status, data = mail.fetch(msg_id, "(RFC822)")
            if status != "OK":
                continue

            msg = email.message_from_bytes(data[0][1])
            subject = decode_str(msg.get("Subject", "(kein Betreff)"))
            sender  = decode_str(msg.get("From", "unbekannt"))
            date    = msg.get("Date", "")
            body, attachments = get_body(msg)
            body_preview = body[:300].replace("\n", " ")

            print(f"Von:     {sender}")
            print(f"Betreff: {subject}")
            print(f"Datum:   {date}")
            if attachments:
                print(f"Anhänge: {', '.join(attachments)}")
            print(f"Preview: {body_preview}")
            print("-" * 60)

            if mark_read:
                mail.store(msg_id, "+FLAGS", "\\Seen")

        mail.logout()

    except imaplib.IMAP4.error as e:
        print(f"IMAP Fehler: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Fehler: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Check Mails via IMAP")
    parser.add_argument("--all", action="store_true", help="Alle Mails anzeigen (nicht nur ungelesene)")
    parser.add_argument("--mark-read", action="store_true", help="Mails als gelesen markieren")
    parser.add_argument("--max", type=int, default=10, help="Max. Anzahl Mails (default: 10)")
    args = parser.parse_args()
    check_mail(mark_read=args.mark_read, max_results=args.max, show_all=args.all)
