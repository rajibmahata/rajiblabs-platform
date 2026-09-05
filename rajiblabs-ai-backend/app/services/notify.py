"""Admin notifications + audit log + failure-log helpers."""
import re
from datetime import datetime, timedelta
from app.database import get_db, utcnow

LOG_LEVELS = ("info", "warning", "error")

# Req: never persist secrets/tokens/passwords in logs, even if a caller
# passes them by mistake (tracebacks and service errors often embed them).
_SCRUB_PATTERNS = [
    # key=value / key: value assignments (passwords, tokens, secrets, keys)
    (re.compile(r"(?i)(password|passwd|pwd|secret|api[_-]?key|auth[_-]?token|access[_-]?token)\s*[:=]\s*\S+"),
     r"\1=***"),
    # Bearer / Basic auth headers
    (re.compile(r"(?i)\b(bearer|basic)\s+[A-Za-z0-9\-._~+/]+=*"), r"\1 ***"),
    # Well-known token prefixes (OpenAI, GitHub, Slack, generic)
    (re.compile(r"\b(sk-[A-Za-z0-9\-_]{8,}|ghp_[A-Za-z0-9]{8,}|github_pat_[A-Za-z0-9_]{8,}|xox[bap]-[A-Za-z0-9\-]{8,})"),
     "***token***"),
    # MongoDB / Postgres / Redis URIs with embedded credentials
    (re.compile(r"(?i)\b((?:mongodb|postgres|postgresql|redis)(?:\+srv)?://[^/\s:]+:)[^/\s@]+@"), r"\1***@"),
]


def _truncate(text: str, limit: int = 2000) -> str:
    """Cap stored log text so one failure can't bloat the DB."""
    text = text or ""
    return text if len(text) <= limit else text[:limit] + "…(truncated)"


def scrub_text(text: str) -> str:
    """Redact secrets/tokens/passwords from free-form log text."""
    out = text or ""
    for pat, repl in _SCRUB_PATTERNS:
        out = pat.sub(repl, out)
    return out


def normalize_level(level: str) -> str:
    return level if level in LOG_LEVELS else "error"


def retention_cutoff(days: int, now: datetime | None = None) -> datetime:
    """Oldest timestamp still inside the visible/retained window."""
    return (now or utcnow()) - timedelta(days=max(1, days))


async def notify(ntype: str, title: str, message: str = "", entity_type: str = "", entity_id: str = "") -> None:
    db = get_db()
    await db["notifications"].insert_one({
        "type": ntype, "title": title, "message": message,
        "entity_type": entity_type, "entity_id": entity_id,
        "is_read": False, "created_at": utcnow()})


async def audit(actor: str, action: str, entity: str = "", metadata: dict | None = None,
                *, event_type: str | None = None, session_id: str | None = None,
                lead_id: str | None = None) -> None:
    """Append an audit entry. New callers pass explicit event_type/session_id/
    lead_id (queryable top-level fields per the lead-system spec); legacy
    callers keep working — event_type defaults to the action name."""
    db = get_db()
    meta = dict(metadata or {})
    # Never persist secrets, even if a caller passes them by mistake.
    for k in list(meta.keys()):
        kl = k.lower()
        if any(s in kl for s in ("password", "secret", "token", "api_key", "apikey")):
            meta[k] = "***redacted***"
    await db["audit_logs"].insert_one({
        "actor": actor, "action": action, "entity": entity,
        "event_type": event_type or action,
        "session_id": session_id, "lead_id": lead_id,
        "metadata": meta, "created_at": utcnow()})


async def log_error(source: str, message: str, details: str = "", level: str = "error",
                  *, logger: str | None = None, path: str | None = None,
                  stack_trace: str | None = None) -> None:
    """Record a failure for the admin System Logs section.

    All free text is scrubbed for secrets before persisting. Retention is
    enforced by a MongoDB TTL index on ``created_at`` (see
    ``ensure_indexes`` + ``LOG_RETENTION_DAYS``) plus a daily scheduled
    sweep (see ``purge_old_logs``) — entries older than the window are
    deleted automatically. Extra fields (logger/path/stack_trace) are
    optional so old callers keep working and old docs still read fine.
    """
    db = get_db()
    await db["error_logs"].insert_one({
        "level": normalize_level(level),
        "source": _truncate(scrub_text(source), 120),
        "logger": _truncate(scrub_text(logger or ""), 160) or None,
        "path": _truncate(scrub_text(path or ""), 250) or None,
        "message": _truncate(scrub_text(message), 500),
        "details": _truncate(scrub_text(details), 2000),
        "stack_trace": _truncate(scrub_text(stack_trace or ""), 4000) or None,
        "created_at": utcnow()})


async def purge_old_logs(db=None, days: int | None = None) -> int:
    """Scheduled-cleanup counterpart to the TTL index: delete entries older
    than the retention window. Returns the deleted count. Safe to run often
    (only touches ``error_logs`` with a strict ``$lt`` cutoff)."""
    from app.config import get_settings
    db = get_db() if db is None else db
    if days is None:
        days = get_settings().log_retention_days
    res = await db["error_logs"].delete_many(
        {"created_at": {"$lt": retention_cutoff(days)}})
    return res.deleted_count or 0
