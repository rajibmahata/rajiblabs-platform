"""Admin notifications + audit log + failure-log helpers."""
from app.database import get_db, utcnow


def _truncate(text: str, limit: int = 2000) -> str:
    """Cap stored log text so one failure can't bloat the DB."""
    text = text or ""
    return text if len(text) <= limit else text[:limit] + "…(truncated)"


async def notify(ntype: str, title: str, message: str = "", entity_type: str = "", entity_id: str = "") -> None:
    db = get_db()
    await db["notifications"].insert_one({
        "type": ntype, "title": title, "message": message,
        "entity_type": entity_type, "entity_id": entity_id,
        "is_read": False, "created_at": utcnow()})


async def audit(actor: str, action: str, entity: str = "", metadata: dict | None = None) -> None:
    db = get_db()
    await db["audit_logs"].insert_one({
        "actor": actor, "action": action, "entity": entity,
        "metadata": metadata or {}, "created_at": utcnow()})


async def log_error(source: str, message: str, details: str = "", level: str = "error") -> None:
    """Record a failure for the admin System Logs section.

    Retention is enforced by a MongoDB TTL index on ``created_at``
    (see ``ensure_indexes`` + ``LOG_RETENTION_DAYS``) — entries older
    than the retention window are deleted automatically.
    """
    db = get_db()
    await db["error_logs"].insert_one({
        "level": level if level in ("error", "warning") else "error",
        "source": _truncate(source, 120), "message": _truncate(message, 500),
        "details": _truncate(details, 2000), "created_at": utcnow()})
