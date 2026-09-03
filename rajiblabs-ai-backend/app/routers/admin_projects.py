"""Admin CMS: dashboard, homepage, skills, experience, projects, products, settings."""
from fastapi import APIRouter, Depends, HTTPException
from app.auth.dependencies import require_admin
from app.database import get_db, utcnow
from app.models import oid_str
from app.schemas import ProjectIn
from app.services.notify import audit, notify

router = APIRouter(prefix="/api/admin")


@router.get("/dashboard")
async def dashboard(email: str = Depends(require_admin)):
    db = get_db()
    return {
        "projects": await db["projects"].count_documents({}),
        "featured": await db["projects"].count_documents({"featured": True, "published": True}),
        "products": await db["projects"].count_documents({"category": "product", "published": True}),
        "skills": await db["skills"].count_documents({}),
        "repos": await db["github_repositories"].count_documents({}),
        "leads_new": await db["customer_leads"].count_documents({"status": "new"}),
        "unread": await db["notifications"].count_documents({"is_read": False}),
        "last_sync": await db["github_sync_runs"].find_one(sort=[("started_at", -1)]),
        "last_agent": await db["agent_runs"].find_one(sort=[("started_at", -1)]),
        "github": "connected" if (await db["github_repositories"].count_documents({})) >= 0 else "unknown",
    }


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
async def leads(email: str = Depends(require_admin)):
    db = get_db()
    cur = db["customer_leads"].find().sort("created_at", -1).limit(100)
    return [oid_str(d) async for d in cur]


@router.put("/leads/{lid}")
async def lead_status(lid: str, status: str, email: str = Depends(require_admin)):
    from bson import ObjectId
    db = get_db()
    await db["customer_leads"].update_one({"_id": ObjectId(lid)}, {"$set": {"status": status}})
    await audit(email, "LEAD_STATUS_CHANGE", lid, {"status": status})
    return {"ok": True}
