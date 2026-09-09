"""Admin Skills — full CRUD with evidence, search/filter/pagination."""
import re
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from typing import Optional
from bson import ObjectId

from app.auth.dependencies import require_admin
from app.database import get_db, utcnow
from app.models import oid_str

router = APIRouter(prefix="/api/admin/skills")

class SkillIn(BaseModel):
    name: str = Field(..., min_length=1, max_length=80)
    category: str = Field(..., min_length=1, max_length=40)
    status: Optional[str] = Field(default="published", max_length=20)
    display_order: Optional[int] = None
    featured: Optional[bool] = None

class SkillPatch(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=80)
    category: Optional[str] = Field(None, min_length=1, max_length=40)
    status: Optional[str] = None
    display_order: Optional[int] = None
    featured: Optional[bool] = None
    confidence: Optional[float] = None

def _norm(name: str) -> str:
    return re.sub(r"\s+", " ", name.strip().lower())

def _slug(name: str) -> str:
    s = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
    return re.sub(r"-{2,}", "-", s)[:80] or "skill"

def _public_view(d: dict) -> dict:
    # Hide internal backend-only fields from admin list? Admin needs evidence, so keep it
    return oid_str(d)

@router.get("")
async def list_skills(
    q: Optional[str] = Query(None, max_length=100),
    category: Optional[str] = Query(None, max_length=40),
    status: Optional[str] = Query(None, max_length=20),
    sort: Optional[str] = Query(None, max_length=20),
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=200),
    email: str = Depends(require_admin),
):
    db = get_db()
    query: dict = {}
    if status:
        query["status"] = status
    if category:
        query["category"] = category
    if q and q.strip():
        rx = {"$regex": re.escape(q.strip()[:80]), "$options": "i"}
        query["$or"] = [{"name": rx}, {"category": rx}, {"normalized_name": rx}]
    total = await db["skills"].count_documents(query)
    # Sorting: name, category, confidence, display_order, updated_at
    sort_map = {
        "name": [("name", 1)],
        "category": [("category", 1), ("name", 1)],
        "confidence": [("confidence", -1)],
        "display_order": [("display_order", 1)],
        "updated": [("updated_at", -1)],
    }
    sort_spec = sort_map.get(sort or "", [("display_order", 1), ("name", 1)])
    cur = db["skills"].find(query).sort(sort_spec).skip((page - 1) * page_size).limit(page_size)
    items = [_public_view(d) async for d in cur]
    return {"items": items, "total": total, "page": page, "page_size": page_size}

@router.get("/{skill_id}")
async def get_skill(skill_id: str, email: str = Depends(require_admin)):
    db = get_db()
    try:
        oid = ObjectId(skill_id)
    except Exception:
        raise HTTPException(400, "Invalid id")
    d = await db["skills"].find_one({"_id": oid})
    if not d:
        raise HTTPException(404, "Skill not found")
    return _public_view(d)

@router.post("", status_code=201)
async def create_skill(body: SkillIn, email: str = Depends(require_admin)):
    db = get_db()
    norm = _norm(body.name)
    # Duplicate prevention via normalized_name
    existing = await db["skills"].find_one({"normalized_name": norm})
    if existing:
        raise HTTPException(400, f"Skill '{existing['name']}' already exists (normalized match)")
    slug = _slug(norm)
    # Ensure slug unique
    if await db["skills"].find_one({"slug": slug}):
        slug = f"{slug}-{str(ObjectId())[:6]}"
    now = utcnow()
    doc = {
        "name": body.name.strip(),
        "normalized_name": norm,
        "slug": slug,
        "category": body.category.strip(),
        "status": body.status or "published",
        "display_order": body.display_order if body.display_order is not None else 999,
        "featured": bool(body.featured) if body.featured is not None else False,
        "evidence": {"sources": [{"type": "manual", "id": email}]},
        "evidence_count": 1,
        "confidence": 1.0,
        "version": 1,
        "first_detected": now,
        "last_used": now,
        "last_validated": now,
        "created_at": now,
        "updated_at": now,
        "content_hash": _slug(norm + str(now.timestamp())),
    }
    res = await db["skills"].insert_one(doc)
    doc["_id"] = res.inserted_id
    # Keep profiles.skills cache in sync (published only)
    try:
        cur = db["skills"].find({"status": "published"}).sort([("confidence", -1), ("display_order", 1)])
        names = [d["name"] async for d in cur]
        await db["profiles"].update_one({}, {"$set": {"skills": names, "updated_at": now}})
    except Exception:
        pass
    # RAG sync for this skill
    try:
        from app.services import rag_ingest
        await rag_ingest.upsert_document("profile", f"skill:{slug}", f"Skill — {doc['name']}", f"Skill: {doc['name']} (Category: {doc['category']})", tags=["skill", doc["category"]])
    except Exception:
        pass
    from app.services.notify import audit
    try:
        await audit(email, "SKILL_CREATE", slug, {"name": doc["name"]})
    except Exception:
        pass
    return _public_view(doc)

@router.put("/{skill_id}")
async def update_skill(skill_id: str, body: SkillPatch, email: str = Depends(require_admin)):
    db = get_db()
    try:
        oid = ObjectId(skill_id)
    except Exception:
        raise HTTPException(400, "Invalid id")
    existing = await db["skills"].find_one({"_id": oid})
    if not existing:
        raise HTTPException(404, "Skill not found")
    patch: dict = {}
    if body.name is not None:
        norm = _norm(body.name)
        # Check duplicate if name changed
        if norm != existing.get("normalized_name"):
            dup = await db["skills"].find_one({"normalized_name": norm, "_id": {"$ne": oid}})
            if dup:
                raise HTTPException(400, f"Skill '{dup['name']}' already exists")
            patch["name"] = body.name.strip()
            patch["normalized_name"] = norm
            patch["slug"] = _slug(norm)
    if body.category is not None:
        patch["category"] = body.category.strip()
    if body.status is not None:
        if body.status not in ("published", "archived", "draft", "disabled"):
            raise HTTPException(400, "Invalid status")
        patch["status"] = body.status
    if body.display_order is not None:
        patch["display_order"] = int(body.display_order)
    if body.featured is not None:
        patch["featured"] = bool(body.featured)
    if body.confidence is not None:
        patch["confidence"] = float(max(0, min(1, body.confidence)))
    if not patch:
        raise HTTPException(400, "No fields to update")
    patch["updated_at"] = utcnow()
    patch["last_validated"] = utcnow()
    patch["version"] = int(existing.get("version", 1)) + 1
    await db["skills"].update_one({"_id": oid}, {"$set": patch})
    # Sync profiles.skills if status changed
    if "status" in patch or "name" in patch:
        try:
            cur = db["skills"].find({"status": "published"}).sort([("confidence", -1), ("display_order", 1)])
            names = [d["name"] async for d in cur]
            await db["profiles"].update_one({}, {"$set": {"skills": names, "updated_at": utcnow()}})
        except Exception:
            pass
        # RAG: deactivate if archived
        if patch.get("status") == "archived":
            try:
                from app.services import rag_ingest
                kd = await db["knowledge_documents"].find_one({"source_id": f"skill:{existing['slug']}"})
                if kd:
                    await rag_ingest.deactivate_document(str(kd["_id"]))
            except Exception:
                pass
        elif patch.get("status") == "published":
            try:
                from app.services import rag_ingest
                await rag_ingest.upsert_document("profile", f"skill:{existing['slug']}", f"Skill — {patch.get('name', existing['name'])}", f"Skill: {patch.get('name', existing['name'])} (Category: {patch.get('category', existing['category'])})", tags=["skill", patch.get("category", existing["category"])])
            except Exception:
                pass
    from app.services.notify import audit
    try:
        await audit(email, "SKILL_UPDATE", skill_id, {"fields": list(patch.keys())})
    except Exception:
        pass
    updated = await db["skills"].find_one({"_id": oid})
    return _public_view(updated)

@router.delete("/{skill_id}")
async def delete_skill(skill_id: str, email: str = Depends(require_admin)):
    db = get_db()
    try:
        oid = ObjectId(skill_id)
    except Exception:
        raise HTTPException(400, "Invalid id")
    doc = await db["skills"].find_one({"_id": oid})
    if not doc:
        raise HTTPException(404, "Skill not found")
    await db["skills"].delete_one({"_id": oid})
    # Sync profiles.skills
    try:
        cur = db["skills"].find({"status": "published"}).sort([("confidence", -1), ("display_order", 1)])
        names = [d["name"] async for d in cur]
        await db["profiles"].update_one({}, {"$set": {"skills": names, "updated_at": utcnow()}})
    except Exception:
        pass
    # Deactivate RAG
    try:
        from app.services import rag_ingest
        kd = await db["knowledge_documents"].find_one({"source_id": f"skill:{doc['slug']}"})
        if kd:
            await rag_ingest.deactivate_document(str(kd["_id"]))
    except Exception:
        pass
    from app.services.notify import audit
    try:
        await audit(email, "SKILL_DELETE", skill_id, {"name": doc.get("name")})
    except Exception:
        pass
    return {"ok": True}

@router.get("/{skill_id}/evidence")
async def skill_evidence(skill_id: str, email: str = Depends(require_admin)):
    db = get_db()
    try:
        oid = ObjectId(skill_id)
    except Exception:
        raise HTTPException(400, "Invalid id")
    d = await db["skills"].find_one({"_id": oid})
    if not d:
        raise HTTPException(404, "Skill not found")
    # Resolve related projects/repos for display
    evidence = d.get("evidence", {})
    # Expand project details
    projects = []
    for pid in evidence.get("projects", [])[:5]:
        p = await db["projects"].find_one({"slug": pid, "published": True})
        if not p:
            p = await db["portfolio"].find_one({"slug": pid, "status": "published"})
        if p:
            projects.append({"slug": p.get("slug"), "name": p.get("name") or p.get("title"), "technologies": p.get("technologies") or p.get("tech_stack", [])})
    github_repos = []
    for fid in evidence.get("github_repositories", [])[:5]:
        r = await db["github_repositories"].find_one({"full_name": fid})
        if r:
            github_repos.append({"full_name": r.get("full_name"), "language": r.get("language"), "stars": r.get("stars")})
        else:
            github_repos.append({"full_name": fid})
    return {
        "skill": _public_view(d),
        "evidence": evidence,
        "projects": projects,
        "github_repositories": github_repos,
        "resume_versions": evidence.get("resume_versions", [])[:5],
    }
