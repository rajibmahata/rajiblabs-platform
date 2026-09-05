"""Admin language + translation management (JWT required, all actions audited).

Languages: GET /api/admin/languages, POST, PUT /{code}, PATCH /{code}/status,
DELETE /{code} (default protected; delete only when unused).
Translations: GET /api/admin/translations, POST /generate, PUT /{id} (manual
edit → approved), POST /{id}/approve, POST /{id}/regenerate, DELETE /{id},
GET /translations/coverage.
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from app.auth.dependencies import require_admin
from app.database import get_db, utcnow
from app.models import oid_str
from app.schemas import (
    LanguageIn, LanguagePatch, LanguageStatusIn, TranslationEditIn,
    TranslationGenerateIn,
)
from app.services import lang_service
from app.services.notify import audit
from app.services.translation_service import TranslationService, source_hash

router = APIRouter(prefix="/api/admin")


def _oid(pid: str):
    from bson import ObjectId
    try:
        return ObjectId(pid)
    except Exception:
        raise HTTPException(400, "Invalid id")


async def _audit(email: str, action: str, entity: str = "", meta: dict | None = None):
    try:
        await audit(email, action, entity, meta or {}, event_type=action)
    except Exception:
        pass


# ── languages ──

@router.get("/languages")
async def list_languages(email: str = Depends(require_admin)):
    return await lang_service.all_languages()


@router.post("/languages")
async def create_language(body: LanguageIn, email: str = Depends(require_admin)):
    db = get_db()
    code = body.code.strip().replace("_", "-")
    if await db["languages"].find_one({"code": code}):
        raise HTTPException(409, "Language code already exists")
    now = utcnow()
    await db["languages"].insert_one({
        "code": code, "name": body.name.strip(), "native_name": body.native_name.strip(),
        "enabled": body.enabled, "is_default": False, "direction": body.direction,
        "sort_order": body.sort_order, "created_at": now, "updated_at": now})
    lang_service.invalidate_cache()
    await _audit(email, "LANG_CREATE", code)
    return {"code": code}


@router.put("/languages/{code}")
async def update_language(code: str, body: LanguagePatch,
                          email: str = Depends(require_admin)):
    db = get_db()
    doc = await db["languages"].find_one({"code": code})
    if not doc:
        raise HTTPException(404, "Language not found")
    patch = {k: v for k, v in
             {"name": body.name, "native_name": body.native_name,
              "direction": body.direction, "sort_order": body.sort_order}.items()
             if v is not None}
    if patch:
        await lang_service.touch(db, code, patch)
    await _audit(email, "LANG_UPDATE", code, patch)
    return {"ok": True}


@router.patch("/languages/{code}/status")
async def language_status(code: str, body: LanguageStatusIn,
                          email: str = Depends(require_admin)):
    db = get_db()
    doc = await db["languages"].find_one({"code": code})
    if not doc:
        raise HTTPException(404, "Language not found")
    try:
        lang_service.guard_status_change(doc, body.enabled)
    except ValueError as e:
        raise HTTPException(400, str(e))
    await lang_service.touch(db, code, {"enabled": body.enabled})
    await _audit(email, "LANG_STATUS", code, {"enabled": body.enabled})
    return {"ok": True, "enabled": body.enabled}


@router.delete("/languages/{code}")
async def delete_language(code: str, email: str = Depends(require_admin)):
    db = get_db()
    doc = await db["languages"].find_one({"code": code})
    if not doc:
        raise HTTPException(404, "Language not found")
    try:
        await lang_service.guard_delete(db, doc)
    except ValueError as e:
        raise HTTPException(400, str(e))
    await db["languages"].delete_one({"code": code})
    lang_service.invalidate_cache()
    await _audit(email, "LANG_DELETE", code)
    return {"ok": True}


# ── translations ──

@router.get("/translations")
async def list_translations(target: str | None = None, status: str | None = None,
                            search: str | None = None, limit: int = Query(100, ge=1, le=500),
                            email: str = Depends(require_admin)):
    db = get_db()
    q: dict = {}
    if target:
        q["target_language"] = target
    if status:
        q["status"] = status
    if search:
        rx = {"$regex": search[:80], "$options": "i"}
        q["$or"] = [{"key": rx}, {"translated_text": rx}, {"source_text": rx}]
    cur = db["translations"].find(q).sort("updated_at", -1).limit(limit)
    return [oid_str(d) async for d in cur]


@router.get("/translations/coverage")
async def translations_coverage(target: str | None = None,
                                email: str = Depends(require_admin)):
    """Per-language status counts + missing/stale keys (admin dashboard)."""
    db = get_db()
    targets = [target] if target else \
        [l["code"] for l in await lang_service.all_languages(db) if not l.get("is_default")]
    return [await TranslationService.coverage(t, db) for t in targets[:25]]


@router.post("/translations/generate")
async def generate_translations(body: TranslationGenerateIn,
                                email: str = Depends(require_admin)):
    """Generate missing translations for a language (bounded, synchronous,
    admin-initiated — the only bulk LLM path). Never re-bills valid records."""
    from app.services import lead_ai
    db = get_db()
    target = await lang_service.resolve(body.target_language, db)
    uni = await TranslationService.universe(db)
    if body.keys:
        wanted = set(body.keys)
        uni = [u for u in uni if u["key"] in wanted]
    done, billed, skipped, errors = [], 0, 0, []
    for u in uni[:body.limit]:
        rec = await db["translations"].find_one(
            {"key": u["key"], "target_language": target})
        if rec and rec.get("source_hash") == source_hash(u["source_text"]) \
                and not body.force:
            skipped += 1
            continue
        try:
            text, status = await TranslationService.get_text(
                u["key"], u["source_text"], target,
                context=f"{u['collection']} {u['field']}", generate=True)
            done.append({"key": u["key"], "status": status})
            if status in ("generated", "needs_review"):
                billed += 1
        except (lead_ai.AIError, ValueError) as e:
            errors.append(f"{u['key']}: {e}"[:160])
            if "not configured" in str(e).lower():
                break
        except Exception as e:
            errors.append(f"{u['key']}: {e}"[:160])
    await _audit(email, "TRANSLATIONS_GENERATE", target,
                 {"done": len(done), "billed": billed, "skipped": skipped,
                  "errors": len(errors)})
    return {"target": target, "done": done, "billed": billed,
            "skipped": skipped, "errors": errors[:20]}


@router.put("/translations/{tid}")
async def edit_translation(tid: str, body: TranslationEditIn,
                           email: str = Depends(require_admin)):
    """Manual edit → approved (human wins over machine, version+1)."""
    db = get_db()
    rec = await db["translations"].find_one({"_id": _oid(tid)})
    if not rec:
        raise HTTPException(404, "Translation not found")
    now = utcnow()
    await db["translations"].update_one(
        {"_id": rec["_id"]},
        {"$set": {"translated_text": body.translated_text, "status": "approved",
                  "reviewed": True, "updated_at": now,
                  "version": int(rec.get("version", 0)) + 1}})
    # Keep the hot cache consistent with the human edit.
    await db["translation_cache"].update_one(
        {"source_hash": rec.get("source_hash"),
         "target_language": rec.get("target_language")},
        {"$set": {"translated_text": body.translated_text, "updated_at": now}})
    await _audit(email, "TRANSLATION_EDIT", rec.get("key", tid))
    return {"ok": True, "status": "approved"}


@router.post("/translations/{tid}/approve")
async def approve_translation(tid: str, email: str = Depends(require_admin)):
    db = get_db()
    rec = await db["translations"].find_one({"_id": _oid(tid)})
    if not rec:
        raise HTTPException(404, "Translation not found")
    await db["translations"].update_one(
        {"_id": rec["_id"]},
        {"$set": {"status": "approved", "reviewed": True, "updated_at": utcnow()}})
    await _audit(email, "TRANSLATION_APPROVE", rec.get("key", tid))
    return {"ok": True, "status": "approved"}


@router.post("/translations/{tid}/regenerate")
async def regenerate_translation(tid: str, email: str = Depends(require_admin)):
    db = get_db()
    rec = await db["translations"].find_one({"_id": _oid(tid)})
    if not rec:
        raise HTTPException(404, "Translation not found")
    try:
        # Bypass the valid-record shortcut: force a fresh LLM pass.
        await db["translations"].delete_one({"_id": rec["_id"]})
        text, status = await TranslationService.get_text(
            rec["key"], rec.get("source_text", ""), rec.get("target_language", ""),
            generate=True)
    except Exception as e:
        raise HTTPException(502, f"Regeneration failed: {e}"[:200])
    await _audit(email, "TRANSLATION_REGENERATE", rec.get("key", tid), {"status": status})
    return {"ok": True, "status": status, "text": text}


@router.delete("/translations/{tid}")
async def delete_translation(tid: str, email: str = Depends(require_admin)):
    db = get_db()
    rec = await db["translations"].find_one_and_delete({"_id": _oid(tid)})
    if not rec:
        raise HTTPException(404, "Translation not found")
    await _audit(email, "TRANSLATION_DELETE", rec.get("key", tid))
    return {"ok": True}
