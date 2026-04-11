#!/usr/bin/env python3
import imaplib, email, os, sys
from email.header import decode_header

IMAP_HOST = "mx.rhone.ch"
IMAP_PORT = 993
EMAIL_USER = "zot@alpenblickzeneggen.ch"
EMAIL_PASS = os.environ.get("EMAIL_PASSWD", "")

def decode_str(s):
    if s is None: return ""
    parts = decode_header(s)
    decoded = []
    for part, enc in parts:
        if isinstance(part, bytes):
            decoded.append(part.decode(enc or "utf-8", errors="replace"))
        else:
            decoded.append(part)
    return " ".join(decoded)

mail = imaplib.IMAP4_SSL(IMAP_HOST, IMAP_PORT)
mail.login(EMAIL_USER, EMAIL_PASS)
mail.select("INBOX")
status, messages = mail.search(None, "UNSEEN")
msg_ids = messages[0].split()
if not msg_ids:
    status, messages = mail.search(None, "ALL")
    msg_ids = messages[0].split()

target = msg_ids[-1]
status, data = mail.fetch(target, "(RFC822)")
msg = email.message_from_bytes(data[0][1])

body = ""
if msg.is_multipart():
    for part in msg.walk():
        if part.get_content_type() == "text/plain":
            body = part.get_payload(decode=True).decode("utf-8", errors="replace")
            break
else:
    body = msg.get_payload(decode=True).decode("utf-8", errors="replace")

print(body)
mail.logout()
