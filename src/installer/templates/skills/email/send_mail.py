#!/usr/bin/env python3
"""
SMTP Email Sender — zot@alpenblickzeneggen.ch
Usage: python3 send_mail.py --to <addr> --subject <subject> --body <text>
"""

import smtplib
import os
import sys
import argparse
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

SMTP_HOST = "mx.rhone.ch"
SMTP_PORT = 587
EMAIL_USER = "zot@alpenblickzeneggen.ch"
EMAIL_PASS = os.environ.get("EMAIL_PASSWD", "")

def send_mail(to, subject, body):
    if not EMAIL_PASS:
        print("ERROR: EMAIL_PASSWD nicht gesetzt", file=sys.stderr)
        sys.exit(1)

    msg = MIMEMultipart()
    msg["From"] = f"Zot ⚡ <{EMAIL_USER}>"
    msg["To"] = to
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "plain", "utf-8"))

    try:
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.ehlo()
            server.starttls()
            server.login(EMAIL_USER, EMAIL_PASS)
            server.sendmail(EMAIL_USER, to, msg.as_string())
        print(f"✅ Mail an {to} gesendet.")
    except Exception as e:
        print(f"SMTP Fehler: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--to", required=True)
    parser.add_argument("--subject", required=True)
    parser.add_argument("--body", required=True)
    args = parser.parse_args()
    send_mail(args.to, args.subject, args.body)
