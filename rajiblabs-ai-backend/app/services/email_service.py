"""Outbound email via the configured SMTP server (stdlib only).

Used ONLY by the explicit Admin approve-and-send path — the LLM never sends
email and never sees credentials. Nothing secret is ever logged: callers log
ids and recipient domains, never bodies or passwords.
"""
import logging
import re
import smtplib
from email.message import EmailMessage

from app.config import get_settings

log = logging.getLogger("rajiblabs")

_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
MAX_SUBJECT = 200
MAX_BODY = 20000


class EmailError(Exception):
    """Raised for configuration, validation, or delivery failures."""


def is_configured(s=None) -> bool:
    s = s or get_settings()
    return bool((s.smtp_host or "").strip() and (s.smtp_user or "").strip()
                and (s.smtp_password or "").strip())


def validate_outgoing(to_email: str, subject: str, body: str) -> str:
    """Returns normalized recipient or raises EmailError. No secrets involved."""
    to_email = (to_email or "").strip().lower()
    if not _EMAIL_RE.match(to_email):
        raise EmailError("Recipient email is invalid")
    if not (subject or "").strip():
        raise EmailError("Subject is required")
    if not (body or "").strip():
        raise EmailError("Body is required")
    return to_email


def send_application_email(to_email: str, subject: str, body_text: str,
                           *, reply_to: str | None = None) -> dict:
    """Send one plain-text email through SMTP. Raises EmailError on failure."""
    s = get_settings()
    if not is_configured(s):
        raise EmailError("SMTP is not configured (smtp_host/user/password)")
    to_email = validate_outgoing(to_email, subject, body_text)
    msg = EmailMessage()
    msg["From"] = s.smtp_from or s.smtp_user
    msg["To"] = to_email
    msg["Subject"] = subject.strip()[:MAX_SUBJECT]
    if reply_to and _EMAIL_RE.match(reply_to.strip()):
        msg["Reply-To"] = reply_to.strip()
    msg.set_content(body_text.strip()[:MAX_BODY])
    try:
        if int(s.smtp_port) == 465:
            smtp: smtplib.SMTP = smtplib.SMTP_SSL(s.smtp_host, 465, timeout=30)
        else:
            smtp = smtplib.SMTP(s.smtp_host, int(s.smtp_port or 587), timeout=30)
        with smtp:
            try:
                smtp.starttls()
            except smtplib.SMTPException:
                pass  # 465/implicit-TLS servers reject STARTTLS; already encrypted
            smtp.login(s.smtp_user, s.smtp_password)
            smtp.send_message(msg)
    except EmailError:
        raise
    except Exception as e:
        raise EmailError(f"SMTP delivery failed: {type(e).__name__}")
    domain = to_email.split("@")[-1]
    return {"to_domain": domain, "subject_len": len(subject.strip())}
