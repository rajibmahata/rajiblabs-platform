"""Admin notifications + audit log helpers."""
from app.database import get_db, utcnow


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
