"""Admin CMS: dashboard, homepage, skills, experience, projects, products, settings."""
from fastapi import APIRouter, Depends, HTTPException
from app.auth.dependencies import require_admin
from app.database import get_db, utcnow
from app.models import oid_str
from app.schemas import LeadPatch, ProjectIn
from app.services.notify import audit, notify

router = APIRouter(prefix="/api/admin")


def _slug(name: str, given: str | None) -> str:
    import re
    if given:
        return given.strip().lower()
    return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")


@router.get("/projects")
async def list_projects(status: str | None = None, email: str = Depends(require_admin)):
    db = get_db()
    q = {} if not status else {"status": status}
    cur = db["projects"].find(q).sort("display_order", 1)
    return [oid_str(d) async for d in cur]


@router.post("/projects")
async def create_project(body: ProjectIn, email: str = Depends(require_admin)):
    db = get_db()
    slug = _slug(body.name, None)
    if await db["projects"].find_one({"slug": slug}):
        raise HTTPException(400, "Slug already exists")
    doc = body.model_dump()
    doc.update({"slug": slug, "published": body.status == "published",
                "created_at": utcnow(), "updated_at": utcnow(), "source_hash": ""})
    res = await db["projects"].insert_one(doc)
    await audit(email, "PROJECT_CREATE", slug)
    return {"id": str(res.inserted_id), "slug": slug}


@router.put("/projects/{pid}")
async def update_project(pid: str, body: ProjectIn, email: str = Depends(require_admin)):
    from bson import ObjectId
    db = get_db()
    try:
        oid = ObjectId(pid)
    except Exception:
        raise HTTPException(400, "Invalid id")
    cur = await db["projects"].find_one({"_id": oid})
    if not cur:
        raise HTTPException(404, "Project not found")
    locked = set(cur.get("locked_fields", []))
    patch = {k: v for k, v in body.model_dump().items() if k not in locked}
    patch["published"] = body.status == "published"
    patch["updated_at"] = utcnow()
    await db["projects"].update_one({"_id": oid}, {"$set": patch})
    await audit(email, "PROJECT_UPDATE", cur.get("slug", pid))
    return {"ok": True}


@router.delete("/projects/{pid}")
async def archive_project(pid: str, email: str = Depends(require_admin)):
    from bson import ObjectId
    db = get_db()
    await db["projects"].update_one({"_id": ObjectId(pid)}, {"$set": {"status": "archived", "published": False}})
    await audit(email, "PROJECT_DELETE", pid)
    return {"ok": True}


@router.get("/notifications")
async def notifications(email: str = Depends(require_admin)):
    db = get_db()
    cur = db["notifications"].find().sort("created_at", -1).limit(50)
    return [oid_str(d) async for d in cur]


@router.put("/notifications/{nid}/read")
async def notif_read(nid: str, email: str = Depends(require_admin)):
    from bson import ObjectId
    db = get_db()
    await db["notifications"].update_one({"_id": ObjectId(nid)}, {"$set": {"is_read": True}})
    return {"ok": True}


@router.get("/leads")
async def leads(status: str | None = None, q: str | None = None,
                email: str = Depends(require_admin)):
    """Lead list with optional status filter + text search (name/email/company)."""
    import re as _re
    db = get_db()
    query: dict = {}
    if status:
        query["status"] = status
    if q and q.strip():
        rx = {"$regex": _re.escape(q.strip()[:100]), "$options": "i"}
        query["$or"] = [{"name": rx}, {"email": rx}, {"company_name": rx}]
    cur = db["customer_leads"].find(query).sort("created_at", -1).limit(100)
    return [_lead_out(d) async for d in cur]


@router.put("/leads/{lid}")
async def lead_status(lid: str, status: str, email: str = Depends(require_admin)):
    from bson import ObjectId
    db = get_db()
    await db["customer_leads"].update_one({"_id": ObjectId(lid)}, {"$set": {"status": status}})
    await audit(email, "LEAD_STATUS_CHANGE", lid, {"status": status})
    return {"ok": True}


def _lead_out(d: dict) -> dict:
    d = oid_str(d)
    d.pop("conversation_id", None)
    return d


@router.get("/leads/{lid}")
async def lead_detail(lid: str, email: str = Depends(require_admin)):
    """Lead + ideas + sessions + activity for the admin detail view."""
    from bson import ObjectId
    db = get_db()
    try:
        oid = ObjectId(lid)
    except Exception:
        raise HTTPException(400, "Invalid id")
    lead = await db["customer_leads"].find_one({"_id": oid})
    if not lead:
        raise HTTPException(404, "Lead not found")
    ideas = [oid_str(d) async for d in
             db["ideas"].find({"$or": [{"lead_id": oid}, {"lead_id": str(oid)}]})
             .sort("updated_at", -1)]
    sessions = []
    async for s in db["customer_conversations"].find(
            {"$or": [{"lead_id": str(oid)},
                     {"session_token": {"$in": lead.get("session_ids", [])}}]}
    ).sort("last_activity_at", -1):
        s = oid_str(s)
        s["message_count"] = await db["customer_messages"].count_documents(
            {"session_token": s.get("session_token")})
        s.pop("ip_hash", None)
        sessions.append(s)
    return {"lead": _lead_out(lead), "ideas": ideas, "sessions": sessions}


@router.patch("/leads/{lid}")
async def lead_patch(lid: str, body: LeadPatch, email: str = Depends(require_admin)):
    """Partial lead update with status validation (PUT ?status= kept for compat)."""
    from bson import ObjectId
    from app.services import leads as rules
    db = get_db()
    try:
        oid = ObjectId(lid)
    except Exception:
        raise HTTPException(400, "Invalid id")
    if not await db["customer_leads"].find_one({"_id": oid}):
        raise HTTPException(404, "Lead not found")
    patch: dict = {}
    data = body.model_dump(exclude_unset=True)
    for key in ("name", "company_name", "industry"):
        if data.get(key) is not None:
            patch[key] = (data[key] or "").strip()[:200]
    if data.get("email") is not None:
        em = rules.normalize_email(data["email"])
        if em and not rules.valid_email(em):
            raise HTTPException(400, "Invalid email")
        patch["email"] = em
    if data.get("phone") is not None:
        ph = rules.normalize_phone(data["phone"])
        if ph and not rules.valid_phone(ph):
            raise HTTPException(400, "Invalid phone")
        patch["phone"] = ph
    if data.get("status") is not None:
        patch["status"] = data["status"]
    if not patch:
        raise HTTPException(400, "Nothing to update")
    patch["updated_at"] = utcnow()
    # Admin edits lock those fields against future chat overwrites.
    locked = set((await db["customer_leads"].find_one(
        {"_id": oid}, {"locked_fields": 1}) or {}).get("locked_fields") or [])
    locked |= {k for k in patch if k not in ("status", "updated_at")}
    patch["locked_fields"] = sorted(locked)
    await db["customer_leads"].update_one({"_id": oid}, {"$set": patch})
    await audit(email, "LEAD_STATUS_CHANGE" if set(patch) == {"status", "updated_at"}
                else "LEAD_UPDATED", lid, {"fields": sorted(patch.keys())})
    return {"ok": True}


@router.get("/leads/{lid}/sessions")
async def lead_sessions(lid: str, email: str = Depends(require_admin)):
    from bson import ObjectId
    db = get_db()
    try:
        oid = ObjectId(lid)
    except Exception:
        raise HTTPException(400, "Invalid id")
    lead = await db["customer_leads"].find_one({"_id": oid})
    if not lead:
        raise HTTPException(404, "Lead not found")
    out = []
    async for s in db["customer_conversations"].find(
            {"$or": [{"lead_id": str(oid)},
                     {"session_token": {"$in": lead.get("session_ids", [])}}]}
    ).sort("last_activity_at", -1):
        s = oid_str(s)
        s["message_count"] = await db["customer_messages"].count_documents(
            {"session_token": s.get("session_token")})
        s.pop("ip_hash", None)
        out.append(s)
    return out


@router.get("/leads/{lid}/ideas")
async def lead_ideas(lid: str, email: str = Depends(require_admin)):
    from bson import ObjectId
    db = get_db()
    try:
        oid = ObjectId(lid)
    except Exception:
        raise HTTPException(400, "Invalid id")
    if not await db["customer_leads"].find_one({"_id": oid}):
        raise HTTPException(404, "Lead not found")
    return [oid_str(d) async for d in
            db["ideas"].find({"$or": [{"lead_id": oid}, {"lead_id": str(oid)}]})
            .sort("updated_at", -1)]


@router.get("/chat/sessions/{sid}/messages")
async def session_messages(sid: str, email: str = Depends(require_admin)):
    """Full chronological conversation for the admin chat view (read-only)."""
    db = get_db()
    sess = await db["customer_conversations"].find_one({"session_token": sid})
    if not sess:
        raise HTTPException(404, "Session not found")
    cur = db["customer_messages"].find({"session_token": sid}).sort("created_at", 1).limit(500)
    out = []
    async for m in cur:
        out.append({"sender": m.get("sender", "user"), "message": m.get("message", ""),
                    "created_at": m.get("created_at"),
                    "ai_model": m.get("ai_model")})
    return {"session_id": sid, "messages": out}
