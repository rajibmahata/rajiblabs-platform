"""LanguageService — language master reads + guards (multilingual framework).

English (`en`) is the default. Only enabled languages reach the public
selector. The default language can never be disabled or deleted, and a
language with translation records is "in use" and cannot be deleted.
"""
import logging
import time

from app.database import get_db, utcnow

log = logging.getLogger("rajiblabs")

DEFAULT_CODE = "en"

# Short-lived process cache; admin writes invalidate it immediately.
_cache: dict = {"at": 0.0, "languages": []}
CACHE_TTL = 60.0


def invalidate_cache() -> None:
    _cache["at"] = 0.0
    _cache["languages"] = []


async def all_languages(db=None) -> list[dict]:
    """Every language in sort order (admin view)."""
    db = db if db is not None else get_db()
    cur = db["languages"].find({}).sort("sort_order", 1)
    return [{**d, "_id": str(d["_id"])} async for d in cur]


async def enabled_languages(db=None) -> list[dict]:
    """Enabled languages for the public selector (cached 60s)."""
    now = time.monotonic()
    if _cache["languages"] and now - _cache["at"] < CACHE_TTL:
        return _cache["languages"]
    db = db if db is not None else get_db()
    try:
        cur = db["languages"].find({"enabled": True}).sort("sort_order", 1)
        out = [{**d, "_id": str(d["_id"])} async for d in cur]
    except Exception as e:
        log.warning("language list fallback: %s", e)
        out = []
    if not out or not any(l.get("is_default") for l in out):
        # DB empty/unreachable: English-only safe fallback (never break the site).
        out = [{"code": DEFAULT_CODE, "name": "English", "native_name": "English",
                "enabled": True, "is_default": True, "direction": "ltr", "sort_order": 1}]
    _cache["at"], _cache["languages"] = now, out
    return out


async def default_code(db=None) -> str:
    try:
        langs = await enabled_languages(db)
        for l in langs:
            if l.get("is_default"):
                return l["code"]
    except Exception:
        pass
    return DEFAULT_CODE


async def resolve(requested: str | None, db=None) -> str:
    """Map any request to an enabled language code, else the default."""
    if not requested:
        return await default_code(db)
    want = requested.strip().replace("_", "-")
    langs = await enabled_languages(db)
    codes = {l["code"]: l["code"] for l in langs}
    if want in codes:
        return want
    base = want.split("-")[0].lower()
    for code in codes:
        if code.split("-")[0].lower() == base:
            return code
    # e.g. browser sends "zh" → prefer zh-CN when enabled
    for code in codes:
        if code.lower().startswith(base + "-"):
            return code
    return await default_code(db)


async def direction_of(code: str, db=None) -> str:
    for l in await enabled_languages(db):
        if l["code"] == code:
            return l.get("direction", "ltr")
    return "ltr"


async def language_name(code: str, db=None) -> str:
    """English display name for prompts ('Bengali', 'Arabic', ...)."""
    for l in await all_languages(db):
        if l["code"] == code:
            return l.get("name", code)
    return code


def guard_status_change(doc: dict, enabled: bool) -> None:
    if doc.get("is_default") and not enabled:
        raise ValueError("The default language cannot be disabled")


async def guard_delete(db, doc: dict) -> None:
    if doc.get("is_default"):
        raise ValueError("The default language cannot be deleted")
    used = await db["translations"].count_documents({"target_language": doc["code"]})
    used += await db["translation_cache"].count_documents({"target_language": doc["code"]})
    if used:
        raise ValueError(f"Language '{doc['code']}' is in use by {used} translation records")


async def touch(db, code: str, patch: dict) -> None:
    patch = {**patch, "updated_at": utcnow()}
    await db["languages"].update_one({"code": code}, {"$set": patch})
    invalidate_cache()


async def response_instruction(requested: str | None, db=None) -> tuple[str, str]:
    """(code, instruction). Empty instruction for the default language.

    Same RAG knowledge is retrieved regardless of language — only the final
    response language changes (no per-language RAG index)."""
    code = await resolve(requested, db)
    if code == await default_code(db):
        return code, ""
    name = await language_name(code, db)
    return code, (
        f"Respond ENTIRELY in {name} ({code}), including any structured reply text. "
        f"Do not mix in English except for brand names (RajibLabs, Rajib Mahata), "
        f"technology names, URLs, emails and code, which stay exactly as-is.")
