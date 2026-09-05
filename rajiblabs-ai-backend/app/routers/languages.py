"""Public language + translation API — cache-first, never waits for an LLM.

- GET /api/public/languages → enabled languages for the selector.
- GET /api/public/translations/{language} → valid translated strings (key → text).
- POST /api/public/translate → explicit on-demand translation (rate-limited,
  orchestrator-billed once, then cached for everyone).
"""
import time
from fastapi import APIRouter, HTTPException, Request
from app.database import get_db
from app.schemas import TranslateIn
from app.services import lang_service
from app.services.translation_service import TranslationService, source_hash

router = APIRouter(prefix="/api/public")
_HITS: dict[str, list[float]] = {}


def _limit(ip: str, limit: int = 20, window: int = 60):
    now = time.time()
    hits = [t for t in _HITS.get(ip, []) if now - t < window]
    if len(hits) >= limit:
        raise HTTPException(429, "Slow down — try again shortly.")
    hits.append(now)
    _HITS[ip] = hits


@router.get("/languages")
async def public_languages():
    langs = await lang_service.enabled_languages()
    return [{"code": l["code"], "name": l.get("name", l["code"]),
             "native_name": l.get("native_name", l["code"]),
             "direction": l.get("direction", "ltr"),
             "is_default": bool(l.get("is_default")),
             "sort_order": l.get("sort_order", 100)} for l in langs]


@router.get("/translations/{language}")
async def public_translations(language: str):
    """Currently-valid translated strings (key → text), hash-checked live."""
    db = get_db()
    target = await lang_service.resolve(language, db)
    default = await lang_service.default_code(db)
    if target == default:
        return {"language": target, "direction": "ltr", "strings": {}, "count": 0}
    strings: dict[str, str] = {}
    try:
        current = {u["key"]: source_hash(u["source_text"])
                   for u in await TranslationService.universe(db)}
        cur = db["translations"].find(
            {"target_language": target, "status": {"$in": ["approved", "generated"]}}
        ).limit(2000)
        async for r in cur:
            if r.get("key") in current and r.get("source_hash") == current[r["key"]]:
                strings[r["key"]] = r.get("translated_text", "")
    except Exception:
        strings = {}
    return {"language": target, "direction": await lang_service.direction_of(target, db),
            "strings": strings, "count": len(strings)}


@router.post("/translate")
async def public_translate(body: TranslateIn, request: Request):
    """On-demand translation: cache-first, single orchestrator call on miss."""
    ip = request.client.host if request.client else "unknown"
    _limit(ip)
    target = await lang_service.resolve(body.target_language)
    default = await lang_service.default_code()
    if target == default:
        return {"text": body.text, "target": target, "status": "source", "cached": True}
    key = f"adhoc.{source_hash(body.source_language + body.text)[:12]}"
    try:
        text, status = await TranslationService.get_text(
            key, body.text, target, context=body.context[:400],
            source_lang=body.source_language, generate=True)
    except ValueError as e:
        raise HTTPException(400, str(e))
    except Exception as e:
        raise HTTPException(502, f"Translation unavailable: {e}"[:200])
    return {"text": text, "target": target, "status": status,
            "cached": status in ("approved", "generated", "cached")}
