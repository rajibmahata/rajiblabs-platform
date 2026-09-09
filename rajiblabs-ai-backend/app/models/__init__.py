"""Mongo document helpers (no ORM — Motor + Pydantic schemas in app/schemas)."""
from datetime import datetime, timezone


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def oid_str(doc: dict | None) -> dict | None:
    if doc is None:
        return None
    try:
        from bson import ObjectId
    except Exception:
        ObjectId = None  # type: ignore
    d = dict(doc)
    if "_id" in d:
        try:
            d["id"] = str(d.pop("_id"))
        except Exception:
            d.pop("_id", None)
    # Convert any remaining ObjectId values (e.g. path_id, lead_id) to strings for JSON
    for k, v in list(d.items()):
        if ObjectId is not None and isinstance(v, ObjectId):
            d[k] = str(v)
        # also handle lists containing ObjectIds (unlikely for top-level)
        elif isinstance(v, list) and v and ObjectId is not None and isinstance(v[0], ObjectId):
            d[k] = [str(x) if isinstance(x, ObjectId) else x for x in v]
    return d
