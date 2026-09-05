"""Site API (v1) — Python port of the retired .NET backend.

Same paths and same camelCase response shapes as `backend/RajibLabs.Api`
served from MongoDB, so the React site and admin panel work unchanged.
IDs are Mongo ObjectIds for new docs, or the migrated SQL GUID
(`legacy_id`) for migrated docs — both accepted on input.
"""
import json
import re
import secrets
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from fastapi.responses import FileResponse
from pydantic import BaseModel, ConfigDict, Field

from app.auth.dependencies import require_admin
from app.auth.utils import hash_password, verify_password
from app.config import get_settings
from app.database import get_db, utcnow
from app.services.notify import audit, log_error, notify

router = APIRouter()


# ── helpers ──

def oid(doc: Optional[dict]) -> Optional[str]:
    if not doc:
        return None
    return doc.get("legacy_id") or str(doc["_id"])


async def by_id(coll: str, rid: str) -> Optional[dict]:
    db = get_db()
    doc = await db[coll].find_one({"legacy_id": rid})
    if doc:
        return doc
    from bson import ObjectId
    try:
        return await db[coll].find_one({"_id": ObjectId(rid)})
    except Exception:
        return None


def check_api_key(request: Request) -> None:
    """X-Api-Key agent guard — unchecked when API_KEY is empty (legacy behavior)."""
    expected = get_settings().api_key
    if not expected:
        return
    if request.headers.get("X-Api-Key") != expected:
        raise HTTPException(401, {"error": "Unauthorized"})


def _slug(name: str, given: Optional[str] = None) -> str:
    base = (given or name or "").strip().lower().replace(".", "")
    return re.sub(r"[^a-z0-9]+", "-", base).strip("-")


def _iso(v: Any) -> Any:
    if isinstance(v, datetime):
        return v.isoformat()
    return v


# ── project shape ──

def project_out(d: dict) -> dict:
    return {
        "id": oid(d), "title": d.get("title", ""), "slug": d.get("slug", ""),
        "description": d.get("description", ""), "techStack": d.get("tech_stack", []),
        "gitHubUrl": d.get("github_url", ""), "liveUrl": d.get("live_url"),
        "status": d.get("status", "planning"),
        "createdAt": _iso(d.get("created_at")), "updatedAt": _iso(d.get("updated_at")),
        "lastCommitAt": _iso(d.get("last_commit_at")),
    }


@router.get("/api/projects")
async def projects():
    db = get_db()
    cur = db["legacy_projects"].find().sort("updated_at", -1)
    return [project_out(d) async for d in cur]


@router.get("/api/projects/{rid}")
async def project_one(rid: str):
    d = await by_id("legacy_projects", rid)
    if not d:
        raise HTTPException(404, {"error": "Not found"})
    return project_out(d)


class ProjectPatchIn(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    last_commit_at: Optional[datetime] = Field(default=None, alias="lastCommitAt")
    status: Optional[str] = None
    title: Optional[str] = None
    description: Optional[str] = None


@router.patch("/api/projects/{rid}")
async def project_patch(rid: str, body: ProjectPatchIn, request: Request):
    check_api_key(request)
    from bson import ObjectId
    d = await by_id("legacy_projects", rid)
    if not d:
        raise HTTPException(404, {"error": "Not found"})
    patch: dict = {"updated_at": utcnow()}
    if body.last_commit_at:
        patch["last_commit_at"] = body.last_commit_at
    if body.status is not None:
        patch["status"] = body.status
    if body.title is not None:
        patch["title"] = body.title
    if body.description is not None:
        patch["description"] = body.description
    db = get_db()
    key = {"legacy_id": d["legacy_id"]} if d.get("legacy_id") else {"_id": d["_id"]}
    if "_id" in key:
        try:
            key = {"_id": ObjectId(str(key["_id"]))}
        except Exception:
            pass
    await db["legacy_projects"].update_one(key, {"$set": patch})
    return project_out({**d, **patch})


# ── activity ──

def activity_out(d: dict) -> dict:
    return {
        "id": oid(d), "projectId": d.get("project_id"), "type": d.get("type", "commit"),
        "title": d.get("title", ""), "description": d.get("description", ""),
        "timestamp": _iso(d.get("timestamp")),
    }


@router.get("/api/activity")
async def activity_list(limit: Optional[int] = None):
    db = get_db()
    cur = db["activities"].find().sort("timestamp", -1)
    if limit:
        cur = cur.limit(limit)
    return [activity_out(d) async for d in cur]


class ActivityIn(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    project_id: Any = Field(alias="projectId")
    type: Optional[str] = "commit"
    title: str = ""
    description: Optional[str] = ""
    timestamp: Optional[datetime] = None
    committed_at: Optional[datetime] = Field(default=None, alias="committedAt")


@router.post("/api/activity", status_code=201)
async def activity_create(body: ActivityIn, request: Request):
    check_api_key(request)
    if not (body.title or "").strip():
        raise HTTPException(400, {"error": "Title is required"})
    db = get_db()
    doc = {
        "legacy_id": uuid.uuid4().hex, "project_id": str(body.project_id),
        "type": body.type or "commit", "title": body.title,
        "description": body.description or "", "timestamp": body.timestamp or utcnow(),
    }
    await db["activities"].insert_one(doc)
    proj = await by_id("legacy_projects", str(body.project_id))
    if proj:
        touch: dict = {"updated_at": utcnow()}
        if (body.type or "commit") == "commit":
            touch["last_commit_at"] = body.committed_at or utcnow()
        await db["legacy_projects"].update_one({"_id": proj["_id"]}, {"$set": touch})
    return {"id": doc["legacy_id"], "projectId": doc["project_id"], "type": doc["type"],
            "title": doc["title"], "description": doc["description"],
            "timestamp": doc["timestamp"].isoformat()}


# ── public profile ──

def profile_public_out(d: dict) -> dict:
    return {
        "id": oid(d), "fullName": d.get("full_name", ""), "title": d.get("title", ""),
        "bio": d.get("bio", ""), "skills": d.get("skills", []),
        "socialLinks": d.get("social_links", {}), "career": d.get("career", []),
        "headline": d.get("headline"), "location": d.get("location"),
        "phone": d.get("phone"), "whatsApp": d.get("whatsapp"), "email": d.get("email"),
        "linkedIn": d.get("linkedin"), "gitHub": d.get("github"), "website": d.get("website"),
        "profileImageUrl": d.get("profile_image_url"), "updatedAt": _iso(d.get("updated_at")),
    }


@router.get("/api/profile")
async def profile_public():
    db = get_db()
    d = await db["profiles"].find_one()
    if not d:
        raise HTTPException(404, {"error": "Not found"})
    return profile_public_out(d)


# ── contact / subscribe ──

class ContactIn(BaseModel):
    name: str = ""
    email: str = ""
    company: Optional[str] = None
    message: str = ""


@router.post("/api/contact", status_code=201)
async def contact(body: ContactIn):
    if not body.name.strip() or not body.email.strip() or not body.message.strip():
        raise HTTPException(400, {"error": "Name, email, and message are required"})
    db = get_db()
    doc = {"legacy_id": uuid.uuid4().hex, "name": body.name.strip(), "email": body.email.strip(),
           "company": (body.company or "").strip() or None, "message": body.message.strip(),
           "submitted_at": utcnow()}
    await db["contacts"].insert_one(doc)
    await notify("NEW_LEAD", f"New enquiry from {doc['name']}", doc["message"][:200], "contact", doc["legacy_id"])
    return {"id": doc["legacy_id"], "message": "Message received. Thank you!"}


@router.get("/api/health")
async def legacy_health():
    return {"status": "healthy", "timestamp": utcnow().isoformat()}


# ── learning ──

def course_out(d: dict) -> dict:
    return {
        "id": oid(d), "title": d.get("title", ""), "url": d.get("url", ""),
        "instructor": d.get("instructor"), "duration": d.get("duration"),
        "level": d.get("level"), "completedAt": _iso(d.get("completed_at")),
        "status": d.get("status", "in-progress"), "updatedAt": _iso(d.get("updated_at")),
    }


@router.get("/api/learning")
async def learning_list():
    db = get_db()
    docs = await db["courses"].find().to_list(length=500)
    docs.sort(key=lambda d: (0 if d.get("status") == "in-progress" else 1,
                             _iso(d.get("updated_at")) or ""), reverse=False)
    # in-progress first, then by updated desc
    inprog = [d for d in docs if d.get("status") == "in-progress"]
    rest = [d for d in docs if d.get("status") != "in-progress"]
    inprog.sort(key=lambda d: _iso(d.get("updated_at")) or "", reverse=True)
    rest.sort(key=lambda d: _iso(d.get("updated_at")) or "", reverse=True)
    return [course_out(d) for d in inprog + rest]


class CourseIn(BaseModel):
    title: str = ""
    url: str = ""
    instructor: Optional[str] = None
    duration: Optional[str] = None
    level: Optional[str] = None
    completed_at: Optional[datetime] = None
    status: Optional[str] = None


@router.post("/api/learning")
async def learning_upsert(body: CourseIn):
    if not (body.title or "").strip():
        raise HTTPException(400, {"error": "Title is required"})
    db = get_db()
    existing = await db["courses"].find_one({"url": body.url}) if body.url else None
    if existing:
        patch = {"title": body.title, "instructor": body.instructor, "duration": body.duration,
                 "level": body.level, "completed_at": body.completed_at,
                 "status": body.status or existing.get("status", "in-progress"),
                 "updated_at": utcnow()}
        await db["courses"].update_one({"_id": existing["_id"]}, {"$set": patch})
    else:
        await db["courses"].insert_one({
            "legacy_id": uuid.uuid4().hex, "title": body.title.strip(), "url": (body.url or "").strip(),
            "instructor": (body.instructor or "").strip() or None, "duration": body.duration,
            "level": body.level, "completed_at": body.completed_at,
            "status": body.status or "in-progress", "updated_at": utcnow()})
    return {"message": "Course synced"}


class EmailIn(BaseModel):
    email: str = ""


@router.post("/api/subscribe")
async def subscribe(body: EmailIn, response: Response):
    email = (body.email or "").strip().lower()
    if not email or "@" not in email:
        raise HTTPException(400, {"error": "Valid email is required"})
    db = get_db()
    existing = await db["subscribers"].find_one({"email": email})
    if existing:
        if not existing.get("is_active", True):
            await db["subscribers"].update_one(
                {"_id": existing["_id"]},
                {"$set": {"is_active": True, "subscribed_at": utcnow(), "unsubscribed_at": None}})
            return {"message": "Welcome back! You're re-subscribed."}
        return {"message": "You're already subscribed!"}
    await db["subscribers"].insert_one(
        {"legacy_id": uuid.uuid4().hex, "email": email, "is_active": True,
         "subscribed_at": utcnow(), "unsubscribed_at": None})
    response.status_code = 201
    return {"message": "Subscribed! Thank you."}


@router.post("/api/unsubscribe")
async def unsubscribe(body: EmailIn):
    email = (body.email or "").strip().lower()
    db = get_db()
    sub = await db["subscribers"].find_one({"email": email, "is_active": True})
    if not sub:
        raise HTTPException(404, {"error": "Email not found"})
    await db["subscribers"].update_one(
        {"_id": sub["_id"]}, {"$set": {"is_active": False, "unsubscribed_at": utcnow()}})
    return {"message": "Unsubscribed. We'll miss you!"}


# ── legacy admin auth (same admin store as /api/admin/auth/*) ──

class LegacyLoginIn(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    username: Optional[str] = None
    email: Optional[str] = None
    password: str = ""


@router.post("/api/admin/login")
async def legacy_login(body: LegacyLoginIn, response: Response):
    from app.auth.dependencies import create_access_token
    s = get_settings()
    db = get_db()
    input_email = ((body.username or body.email) or "").strip().lower()
    if input_email not in s.admin_email_list:
        raise HTTPException(401, {"error": "Invalid credentials"})
    admin = await db["admins"].find_one({"emails": input_email})
    ok = admin and verify_password(body.password or "", admin.get("password_hash", ""))
    if not ok and s.admin_initial_password and (body.password or "") == s.admin_initial_password:
        # First-run / rotation path (mirrors legacy behavior): create or re-hash.
        if admin:
            await db["admins"].update_one(
                {"_id": admin["_id"]}, {"$set": {"password_hash": hash_password(body.password)}})
            admin = await db["admins"].find_one({"_id": admin["_id"]})
        else:
            if not s.admin_initial_password:
                raise HTTPException(500, {"error": "Admin not configured"})
            res = await db["admins"].insert_one({
                "emails": s.admin_email_list, "password_hash": hash_password(body.password),
                "created_at": utcnow(), "last_login_at": None})
            admin = await db["admins"].find_one({"_id": res.inserted_id})
        ok = True
    if not ok or not admin:
        raise HTTPException(401, {"error": "Invalid credentials"})
    username = (admin.get("emails") or [input_email])[0]
    await db["admins"].update_one({"_id": admin["_id"]}, {"$set": {"last_login_at": utcnow()}})
    token = create_access_token(username)
    max_age = s.jwt_expire_minutes * 60
    for name, path in (("rlabs_token", "/"), ("rlabs_access", "/")):
        response.set_cookie(name, token, httponly=True, secure=True, samesite="strict",
                            max_age=max_age, path=path)
    await audit(username, "LOGIN", "admin")
    return {"token": token, "username": username}


@router.post("/api/admin/logout")
async def legacy_logout(response: Response, email: str = Depends(require_admin)):
    response.delete_cookie("rlabs_token", path="/")
    response.delete_cookie("rlabs_access", path="/")
    response.delete_cookie("rlabs_refresh", path="/api/admin/auth")
    await audit(email, "LOGOUT", "admin")
    return {"message": "Logged out"}


@router.get("/api/admin/me")
async def legacy_me(email: str = Depends(require_admin)):
    return {"username": email, "role": "Admin"}


# ── portfolio ──

def portfolio_out(d: dict, public_list: bool = False) -> dict:
    base = {
        "id": oid(d), "title": d.get("title", ""), "slug": d.get("slug", ""),
        "shortDescription": d.get("short_description", ""), "description": d.get("description", ""),
        "problem": d.get("problem", ""), "solution": d.get("solution", ""),
        "role": d.get("role", ""), "architecture": d.get("architecture", ""),
        "techStack": d.get("tech_stack", []), "aiCapabilities": d.get("ai_capabilities", []),
        "cloudCapabilities": d.get("cloud_capabilities", []), "screenshots": d.get("screenshots", []),
        "demoUrl": d.get("demo_url"), "gitHubUrl": d.get("github_url"),
        "productUrl": d.get("product_url"), "status": d.get("status", "draft"),
        "featured": d.get("featured", False), "displayOrder": d.get("display_order", 0),
        "createdAt": _iso(d.get("created_at")), "publishedAt": _iso(d.get("published_at")),
    }
    if not public_list:
        base["updatedAt"] = _iso(d.get("updated_at"))
    return base


class PortfolioIn(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    title: str = ""
    slug: Optional[str] = None
    short_description: Optional[str] = Field(default=None, alias="shortDescription")
    description: Optional[str] = None
    problem: Optional[str] = None
    solution: Optional[str] = None
    role: Optional[str] = None
    architecture: Optional[str] = None
    tech_stack: Optional[list[str]] = Field(default=None, alias="techStack")
    ai_capabilities: Optional[list[str]] = Field(default=None, alias="aiCapabilities")
    cloud_capabilities: Optional[list[str]] = Field(default=None, alias="cloudCapabilities")
    screenshots: Optional[list[str]] = Field(default=None, alias="screenshots")
    demo_url: Optional[str] = Field(default=None, alias="demoUrl")
    github_url: Optional[str] = Field(default=None, alias="gitHubUrl")
    product_url: Optional[str] = Field(default=None, alias="productUrl")
    status: Optional[str] = None
    featured: Optional[bool] = None
    display_order: Optional[int] = Field(default=None, alias="displayOrder")


@router.get("/api/portfolio")
async def portfolio_list(status: Optional[str] = None):
    db = get_db()
    q = {"status": status} if status else {"status": "published"}
    cur = db["portfolio"].find(q).sort([("display_order", 1), ("published_at", -1)])
    return [portfolio_out(d, public_list=True) async for d in cur]


@router.get("/api/portfolio/{slug}")
async def portfolio_detail(slug: str):
    db = get_db()
    d = await db["portfolio"].find_one({"slug": slug})
    if not d:
        raise HTTPException(404, {"error": "Not found"})
    return portfolio_out(d)


@router.get("/api/admin/portfolio")
async def portfolio_admin_list(email: str = Depends(require_admin)):
    db = get_db()
    cur = db["portfolio"].find().sort("display_order", 1)
    return [portfolio_out(d) async for d in cur]


@router.post("/api/admin/portfolio", status_code=201)
async def portfolio_create(body: PortfolioIn, email: str = Depends(require_admin)):
    if not (body.title or "").strip():
        raise HTTPException(400, {"error": "Title required"})
    slug = _slug(body.title, body.slug)
    db = get_db()
    if await db["portfolio"].find_one({"slug": slug}):
        raise HTTPException(400, {"error": "Slug exists"})
    doc = {
        "legacy_id": uuid.uuid4().hex, "title": body.title.strip(), "slug": slug,
        "short_description": body.short_description or "", "description": body.description or "",
        "problem": body.problem or "", "solution": body.solution or "",
        "role": body.role or "", "architecture": body.architecture or "",
        "tech_stack": body.tech_stack or [], "ai_capabilities": body.ai_capabilities or [],
        "cloud_capabilities": body.cloud_capabilities or [], "screenshots": body.screenshots or [],
        "demo_url": body.demo_url, "github_url": body.github_url, "product_url": body.product_url,
        "status": body.status or "draft", "featured": body.featured or False,
        "display_order": body.display_order or 0,
        "created_at": utcnow(), "updated_at": utcnow(),
        "published_at": utcnow() if (body.status or "") == "published" else None,
        "is_manual_edit": False,
    }
    await db["portfolio"].insert_one(doc)
    await audit(email, "PORTFOLIO_CREATE", slug)
    return portfolio_out(doc)


@router.put("/api/admin/portfolio/{rid}")
async def portfolio_update(rid: str, body: PortfolioIn, email: str = Depends(require_admin)):
    d = await by_id("portfolio", rid)
    if not d:
        raise HTTPException(404, {"error": "Not found"})
    data = body.model_dump(exclude_unset=True, by_alias=False)
    patch: dict = {"updated_at": utcnow(), "is_manual_edit": True}
    for k, v in data.items():
        if v is not None and k != "slug":
            patch[k] = v
    if data.get("slug"):
        patch["slug"] = _slug("", data["slug"])
    if data.get("status") == "published" and not d.get("published_at"):
        patch["published_at"] = utcnow()
    if (data.get("title") or "").strip():
        patch["title"] = data["title"].strip()
    db = get_db()
    await db["portfolio"].update_one({"_id": d["_id"]}, {"$set": patch})
    await audit(email, "PORTFOLIO_UPDATE", d.get("slug", rid))
    return portfolio_out({**d, **patch})


@router.delete("/api/admin/portfolio/{rid}")
async def portfolio_delete(rid: str, email: str = Depends(require_admin)):
    d = await by_id("portfolio", rid)
    if not d:
        raise HTTPException(404, {"error": "Not found"})
    db = get_db()
    await db["portfolio"].delete_one({"_id": d["_id"]})
    await audit(email, "PORTFOLIO_DELETE", rid)
    return {"message": "Deleted"}


# ── products ──

def product_out(d: dict) -> dict:
    return {
        "id": oid(d), "name": d.get("name", ""), "slug": d.get("slug", ""),
        "category": d.get("category", ""), "description": d.get("description", ""),
        "logoUrl": d.get("logo_url"), "screenshots": d.get("screenshots", []),
        "features": d.get("features", []), "techStack": d.get("tech_stack", []),
        "aiCapabilities": d.get("ai_capabilities"), "architecture": d.get("architecture"),
        "productUrl": d.get("product_url"), "gitHubRepoId": d.get("github_repo_id"),
        "status": d.get("status", "draft"), "featured": d.get("featured", False),
        "displayOrder": d.get("display_order", 0),
        "createdAt": _iso(d.get("created_at")), "updatedAt": _iso(d.get("updated_at")),
    }


class ProductLegacyIn(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    name: str = ""
    slug: Optional[str] = None
    category: Optional[str] = None
    description: Optional[str] = None
    logo_url: Optional[str] = Field(default=None, alias="logoUrl")
    screenshots: Optional[list[str]] = None
    features: Optional[list[str]] = None
    tech_stack: Optional[list[str]] = Field(default=None, alias="techStack")
    ai_capabilities: Optional[str] = Field(default=None, alias="aiCapabilities")
    architecture: Optional[str] = None
    product_url: Optional[str] = Field(default=None, alias="productUrl")
    github_repo_id: Optional[str] = Field(default=None, alias="gitHubRepoId")
    status: Optional[str] = None
    featured: Optional[bool] = None
    display_order: Optional[int] = Field(default=None, alias="displayOrder")


@router.get("/api/products")
async def products_list(lang: str | None = None):
    from app.services.translation_service import TranslationService
    db = get_db()
    cur = db["products"].find(
        {"status": {"$in": ["published", "featured"]}}).sort("display_order", 1)
    out = []
    async for d in cur:
        if lang:
            d, _ = await TranslationService.localize_doc("products", d, lang, db)
        out.append(product_out(d))
    return out


@router.get("/api/products/{slug}")
async def product_detail(slug: str, lang: str | None = None):
    from app.services.translation_service import TranslationService
    db = get_db()
    d = await db["products"].find_one({"slug": slug})
    if not d:
        raise HTTPException(404, {"error": "Not found"})
    if lang:
        d, _ = await TranslationService.localize_doc("products", d, lang, db)
    return product_out(d)


@router.get("/api/admin/products")
async def products_admin_list(email: str = Depends(require_admin)):
    db = get_db()
    cur = db["products"].find().sort("display_order", 1)
    return [product_out(d) async for d in cur]


@router.post("/api/admin/products", status_code=201)
async def product_create(body: ProductLegacyIn, email: str = Depends(require_admin)):
    if not (body.name or "").strip():
        raise HTTPException(400, {"error": "Name required"})
    slug = _slug(body.name, body.slug)
    db = get_db()
    if await db["products"].find_one({"slug": slug}):
        raise HTTPException(400, {"error": "Slug exists"})
    doc = {
        "legacy_id": uuid.uuid4().hex, "name": body.name.strip(), "slug": slug,
        "category": body.category or "", "description": body.description or "",
        "logo_url": body.logo_url, "screenshots": body.screenshots or [],
        "features": body.features or [], "tech_stack": body.tech_stack or [],
        "ai_capabilities": body.ai_capabilities, "architecture": body.architecture,
        "product_url": body.product_url, "github_repo_id": body.github_repo_id,
        "status": body.status or "draft", "featured": body.featured or False,
        "display_order": body.display_order or 0,
        "created_at": utcnow(), "updated_at": utcnow(),
    }
    await db["products"].insert_one(doc)
    await audit(email, "PRODUCT_CREATE", slug)
    return product_out(doc)


@router.put("/api/admin/products/{rid}")
async def product_update(rid: str, body: ProductLegacyIn, email: str = Depends(require_admin)):
    d = await by_id("products", rid)
    if not d:
        raise HTTPException(404, {"error": "Not found"})
    data = body.model_dump(exclude_unset=True, by_alias=False)
    patch: dict = {"updated_at": utcnow()}
    for k, v in data.items():
        if v is not None and k not in ("slug", "name"):
            patch[k] = v
    if data.get("slug"):
        patch["slug"] = _slug("", data["slug"])
    if (data.get("name") or "").strip():
        patch["name"] = data["name"].strip()
    db = get_db()
    await db["products"].update_one({"_id": d["_id"]}, {"$set": patch})
    await audit(email, "PRODUCT_UPDATE", d.get("slug", rid))
    return product_out({**d, **patch})


@router.delete("/api/admin/products/{rid}")
async def product_delete(rid: str, email: str = Depends(require_admin)):
    d = await by_id("products", rid)
    if not d:
        raise HTTPException(404, {"error": "Not found"})
    db = get_db()
    await db["products"].delete_one({"_id": d["_id"]})
    await audit(email, "PRODUCT_DELETE", rid)
    return {"message": "Deleted"}


# ── github sync (heuristic port of the .NET sync) ──

def repo_out(d: dict) -> dict:
    return {
        "id": oid(d), "gitHubId": d.get("github_id"), "name": d.get("name", ""),
        "fullName": d.get("full_name", ""), "description": d.get("description", ""),
        "htmlUrl": d.get("html_url", ""), "language": d.get("language", ""),
        "topics": d.get("topics", []), "stars": d.get("stars", 0), "forks": d.get("forks", 0),
        "readme": d.get("readme"), "pushedAt": _iso(d.get("pushed_at")),
        "updatedAtGitHub": _iso(d.get("updated_at_github")),
        "isPrivate": d.get("is_private", False), "defaultBranch": d.get("default_branch", "main"),
        "classification": d.get("classification", "professional"),
        "aiTitle": d.get("ai_title"), "aiSummary": d.get("ai_summary"),
        "aiProblem": d.get("ai_problem"), "aiTechStack": d.get("ai_tech_stack"),
        "aiConfidence": d.get("ai_confidence", "low"),
        "syncStatus": d.get("sync_status", "review"),
        "lastSyncedAt": _iso(d.get("last_synced_at")),
        "isManuallyEdited": d.get("is_manually_edited", False),
        "publishedAt": _iso(d.get("published_at")),
    }


def _classify(name: str, desc: str, lang: str) -> str:
    t = f"{desc} {name}".lower()
    if "ai" in t or lang == "Python":
        return "ai"
    if "c#" in lang.lower() or ".net" in desc:
        return "dotnet"
    return "professional"


@router.get("/api/admin/github/repos")
async def github_repos(email: str = Depends(require_admin)):
    db = get_db()
    cur = db["legacy_repos"].find().sort("pushed_at", -1)
    return [repo_out(d) async for d in cur]


@router.get("/api/admin/github/sync-log")
async def github_sync_log(email: str = Depends(require_admin)):
    db = get_db()
    d = await db["sync_logs"].find_one(sort=[("started_at", -1)])
    if not d:
        raise HTTPException(404, {"error": "Not found"})
    return {
        "id": oid(d), "startedAt": _iso(d.get("started_at")),
        "finishedAt": _iso(d.get("finished_at")), "found": d.get("found", 0),
        "added": d.get("added", 0), "updated": d.get("updated", 0),
        "ignored": d.get("ignored", 0), "errors": d.get("errors", []),
        "errorsJson": json.dumps(d.get("errors", [])),
    }


@router.post("/api/admin/github/sync")
async def github_sync(email: str = Depends(require_admin)):
    import httpx
    s = get_settings()
    db = get_db()
    if not s.github_token:
        raise HTTPException(400, {"error": "GITHUB_TOKEN not configured on server"})
    log = {"legacy_id": uuid.uuid4().hex, "started_at": utcnow(), "finished_at": None,
           "found": 0, "added": 0, "updated": 0, "ignored": 0, "errors": []}
    res = await db["sync_logs"].insert_one(log)
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            r = await client.get(
                f"https://api.github.com/users/{s.github_owner}/repos",
                params={"per_page": 100, "sort": "updated"},
                headers={"Authorization": f"Bearer {s.github_token}",
                         "Accept": "application/vnd.github+json",
                         "User-Agent": "RajibLabs-CMS",
                         "X-GitHub-Api-Version": "2022-11-28"})
            if r.status_code >= 400:
                raise RuntimeError(f"GitHub API {r.status_code}")
            repos = r.json()
        found, added, updated = len(repos), 0, 0
        for item in repos:
            gid = item.get("id")
            name = item.get("name", "")
            desc = item.get("description") or ""
            lang = item.get("language") or ""
            pushed = None
            try:
                pushed = datetime.fromisoformat(
                    (item.get("pushed_at") or "").replace("Z", "+00:00")) if item.get("pushed_at") else None
            except Exception:
                pushed = None
            existing = await db["legacy_repos"].find_one({"github_id": gid})
            ai_summary = desc if desc.strip() else f"{name} — {lang} project by {s.github_owner}"
            if existing is None:
                await db["legacy_repos"].insert_one({
                    "legacy_id": uuid.uuid4().hex, "github_id": gid, "name": name,
                    "full_name": item.get("full_name", ""), "description": desc,
                    "html_url": item.get("html_url", ""), "language": lang, "topics": [],
                    "stars": item.get("stargazers_count", 0), "forks": item.get("forks_count", 0),
                    "readme": None, "pushed_at": pushed, "updated_at_github": pushed,
                    "is_private": bool(item.get("private")), "default_branch": item.get("default_branch", "main"),
                    "classification": _classify(name, desc, lang), "ai_title": None,
                    "ai_summary": ai_summary, "ai_problem": None, "ai_tech_stack": None,
                    "ai_confidence": "medium", "sync_status": "review",
                    "last_synced_at": utcnow(), "is_manually_edited": False, "published_at": None})
                added += 1
            else:
                if existing.get("is_manually_edited"):
                    updated += 1
                    continue
                patch = {"name": name, "full_name": item.get("full_name", ""),
                         "description": desc, "html_url": item.get("html_url", ""),
                         "language": lang, "stars": item.get("stargazers_count", 0),
                         "forks": item.get("forks_count", 0), "pushed_at": pushed,
                         "updated_at_github": pushed, "last_synced_at": utcnow()}
                if not existing.get("ai_summary") or existing.get("ai_summary") == existing.get("description"):
                    patch["ai_summary"] = ai_summary
                await db["legacy_repos"].update_one({"_id": existing["_id"]}, {"$set": patch})
                updated += 1
        await db["sync_logs"].update_one(
            {"_id": res.inserted_id},
            {"$set": {"finished_at": utcnow(), "found": found, "added": added, "updated": updated}})
        await audit(email, "GITHUB_SYNC", "github")
        return {"found": found, "added": added, "updated": updated, "message": "Sync complete"}
    except Exception as e:
        await db["sync_logs"].update_one(
            {"_id": res.inserted_id},
            {"$set": {"finished_at": utcnow(), "errors": [str(e)]}})
        try:
            await log_error("github_sync_legacy", "GitHub sync failed", str(e)[:2000],
                                logger="app.routers.legacy", path="/api/admin/github/sync")
        except Exception:
            pass
        raise HTTPException(500, {"error": str(e)})


@router.patch("/api/admin/github/repos/{rid}")
async def github_repo_patch(rid: str, body: dict, email: str = Depends(require_admin)):
    d = await by_id("legacy_repos", rid)
    if not d:
        raise HTTPException(404, {"error": "Not found"})
    patch: dict = {"is_manually_edited": True}
    mapping = {"syncStatus": "sync_status", "classification": "classification",
               "aiSummary": "ai_summary", "aiTitle": "ai_title"}
    for src, dst in mapping.items():
        if body.get(src) is not None:
            patch[dst] = body[src]
    db = get_db()
    await db["legacy_repos"].update_one({"_id": d["_id"]}, {"$set": patch})
    return repo_out({**d, **patch})


# ── admin profile / dashboard / content ──

def profile_admin_out(d: dict) -> dict:
    out = profile_public_out(d)
    out.update({
        "skillsJson": json.dumps(d.get("skills", [])),
        "socialLinksJson": json.dumps(d.get("social_links", {})),
        "careerJson": json.dumps(d.get("career", [])),
    })
    return out


class ProfilePutIn(BaseModel):
    model_config = ConfigDict(extra="allow")


@router.get("/api/admin/profile")
async def profile_admin_get(email: str = Depends(require_admin)):
    db = get_db()
    d = await db["profiles"].find_one()
    if not d:
        raise HTTPException(404, {"error": "Not found"})
    return profile_admin_out(d)


@router.put("/api/admin/profile")
async def profile_admin_put(body: ProfilePutIn, email: str = Depends(require_admin)):
    db = get_db()
    d = await db["profiles"].find_one()
    if not d:
        raise HTTPException(404, {"error": "Not found"})
    data = body.model_dump()
    mapping = {"fullName": "full_name", "title": "title", "bio": "bio", "skills": "skills",
               "socialLinks": "social_links", "career": "career", "headline": "headline",
               "location": "location", "phone": "phone", "whatsApp": "whatsapp",
               "email": "email", "linkedIn": "linkedin", "gitHub": "github",
               "website": "website", "profileImageUrl": "profile_image_url"}
    patch: dict = {"updated_at": utcnow()}
    lowered = {k.lower(): v for k, v in data.items()}
    for src, dst in mapping.items():
        if src in data and data[src] is not None:
            patch[dst] = data[src]
        elif src.lower() in lowered and lowered[src.lower()] is not None and dst not in patch:
            patch[dst] = lowered[src.lower()]
    await db["profiles"].update_one({"_id": d["_id"]}, {"$set": patch})
    await audit(email, "PROFILE_UPDATE", "profile")
    return profile_admin_out({**d, **patch})


def resume_out(d: dict) -> dict:
    return {
        "id": oid(d), "fileName": d.get("filename") or d.get("file_name", ""),
        "storedPath": d.get("stored_rel") or d.get("stored_path", ""),
        "contentType": d.get("content_type", ""), "sizeBytes": d.get("size_bytes", 0),
        "version": d.get("version", 1), "status": d.get("status", "published"),
        "uploadedAt": _iso(d.get("uploaded_at")), "publishedAt": _iso(d.get("published_at")),
    }


@router.get("/api/admin/dashboard")
async def dashboard_legacy(email: str = Depends(require_admin)):
    db = get_db()
    resume = await db["resumes"].find_one({"status": "published"}, sort=[("version", -1)])
    profile = await db["profiles"].find_one()
    last_sync = await db["sync_logs"].find_one(sort=[("started_at", -1)])
    last_sync_out = None
    if last_sync:
        last_sync_out = {
            "id": oid(last_sync), "startedAt": _iso(last_sync.get("started_at")),
            "finishedAt": _iso(last_sync.get("finished_at")), "found": last_sync.get("found", 0),
            "added": last_sync.get("added", 0), "updated": last_sync.get("updated", 0),
            "ignored": last_sync.get("ignored", 0), "errors": last_sync.get("errors", []),
            "errorsJson": json.dumps(last_sync.get("errors", [])),
        }
    return {
        "resume": resume_out(resume) if resume else None,
        "portfolio": {
            "total": await db["portfolio"].count_documents({}),
            "published": await db["portfolio"].count_documents({"status": "published"})},
        "github": {"total": await db["legacy_repos"].count_documents({})},
        "products": {"total": await db["products"].count_documents({})},
        "lastSync": last_sync_out,
        "profileUpdatedAt": _iso((profile or {}).get("updated_at")),
    }


@router.get("/api/content/{key}")
async def content_public(key: str):
    db = get_db()
    d = await db["website_contents"].find_one({"key": key})
    if not d:
        raise HTTPException(404, {"error": "Not found"})
    return {"id": oid(d), "key": d.get("key", ""), "title": d.get("title", ""),
            "bodyJson": d.get("body_json", "{}"), "updatedAt": _iso(d.get("updated_at"))}


@router.get("/api/admin/content")
async def content_list(email: str = Depends(require_admin)):
    db = get_db()
    cur = db["website_contents"].find()
    return [{"id": oid(d), "key": d.get("key", ""), "title": d.get("title", ""),
             "bodyJson": d.get("body_json", "{}"),
             "updatedAt": _iso(d.get("updated_at"))} async for d in cur]


@router.put("/api/admin/content/{key}")
async def content_put(key: str, body: dict, email: str = Depends(require_admin)):
    title = str(body.get("title") or "")
    raw = body.get("body", {})
    body_json = raw if isinstance(raw, str) else json.dumps(raw)
    db = get_db()
    existing = await db["website_contents"].find_one({"key": key})
    if existing is None:
        doc = {"legacy_id": uuid.uuid4().hex, "key": key, "title": title,
               "body_json": body_json, "updated_at": utcnow()}
        await db["website_contents"].insert_one(doc)
        await audit(email, "CONTENT_CREATE", key)
        return {"id": doc["legacy_id"], "key": key, "title": title,
                "bodyJson": body_json, "updatedAt": _iso(doc["updated_at"])}
    await db["website_contents"].update_one(
        {"_id": existing["_id"]},
        {"$set": {"title": title, "body_json": body_json, "updated_at": utcnow()}})
    await audit(email, "CONTENT_UPDATE", key)
    return {"id": oid(existing), "key": key, "title": title,
            "bodyJson": body_json, "updatedAt": utcnow().isoformat()}


# ── resumes (legacy shapes) ──

@router.get("/api/admin/resumes")
async def resumes_list(email: str = Depends(require_admin)):
    db = get_db()
    cur = db["resumes"].find().sort("version", -1)
    return [resume_out(d) async for d in cur]


@router.post("/api/admin/resumes/upload")
async def resume_upload(request: Request, email: str = Depends(require_admin)):
    from fastapi import UploadFile
    s = get_settings()
    form = await request.form()
    file = next((v for v in form.values() if isinstance(v, UploadFile)), None)
    if file is None:
        raise HTTPException(400, {"error": "No file"})
    ext = Path(file.filename or "").suffix.lower()
    if ext not in (".pdf", ".docx"):
        raise HTTPException(400, {"error": "Only PDF/DOCX allowed"})
    data = await file.read()
    if len(data) > 10 * 1024 * 1024:
        raise HTTPException(400, {"error": "Max 10MB"})
    safe = f"{uuid.uuid4().hex}{ext}"
    updir = Path(s.upload_dir) / "resumes"
    updir.mkdir(parents=True, exist_ok=True)
    (updir / safe).write_bytes(data)
    db = get_db()
    version = await db["resumes"].count_documents({}) + 1
    doc = {"legacy_id": uuid.uuid4().hex, "filename": file.filename,
           "stored_path": str(updir / safe), "stored_rel": f"uploads/resumes/{safe}",
           "content_type": file.content_type or "application/octet-stream",
           "size_bytes": len(data), "version": version, "status": "published",
           "active": True, "uploaded_at": utcnow(), "published_at": utcnow()}
    await db["resumes"].update_many({}, {"$set": {"status": "archived", "active": False}})
    await db["resumes"].insert_one(doc)
    await audit(email, "RESUME_UPLOAD", str(doc["legacy_id"]))
    return resume_out(doc)


def _resume_file_path(d: dict) -> Optional[str]:
    candidates = [d.get("stored_path")]
    rel = d.get("stored_rel")
    if rel:
        candidates.append(str(Path(get_settings().upload_dir).parent / rel))
        candidates.append(str(Path(get_settings().upload_dir) / "resumes" / Path(rel).name))
    for c in candidates:
        if c and Path(c).is_file():
            return c
    return None


@router.get("/api/admin/resumes/{rid}/download")
async def resume_admin_download(rid: str, email: str = Depends(require_admin)):
    d = await by_id("resumes", rid)
    if not d:
        raise HTTPException(404, {"error": "Not found"})
    path = _resume_file_path(d)
    if not path:
        raise HTTPException(404, {"error": "Not found"})
    return FileResponse(path, media_type=d.get("content_type") or "application/octet-stream",
                        filename=d.get("filename") or d.get("file_name") or "resume")


@router.get("/api/resumes/{rid}/download")
async def resume_public_download(rid: str):
    d = await by_id("resumes", rid)
    if not d:
        raise HTTPException(404, {"error": "Not found"})
    path = _resume_file_path(d)
    if not path:
        raise HTTPException(404, {"error": "Not found"})
    return FileResponse(path, media_type=d.get("content_type") or "application/octet-stream",
                        filename=d.get("filename") or d.get("file_name") or "resume")


@router.patch("/api/admin/resumes/{rid}")
async def resume_publish(rid: str, email: str = Depends(require_admin)):
    d = await by_id("resumes", rid)
    if not d:
        raise HTTPException(404, {"error": "Not found"})
    db = get_db()
    await db["resumes"].update_many(
        {"_id": {"$ne": d["_id"]}, "status": "published"},
        {"$set": {"status": "archived", "active": False}})
    await db["resumes"].update_one(
        {"_id": d["_id"]},
        {"$set": {"status": "published", "active": True, "published_at": utcnow()}})
    await audit(email, "RESUME_PUBLISH", rid)
    return resume_out({**d, "status": "published", "active": True, "published_at": utcnow()})


@router.delete("/api/admin/resumes/{rid}")
async def resume_delete(rid: str, email: str = Depends(require_admin)):
    d = await by_id("resumes", rid)
    if not d:
        raise HTTPException(404, {"error": "Not found"})
    db = get_db()
    await db["resumes"].delete_one({"_id": d["_id"]})
    try:
        path = _resume_file_path(d)
        if path:
            Path(path).unlink()
    except Exception:
        pass
    await audit(email, "RESUME_DELETE", rid)
    return {"message": "Deleted"}


@router.get("/api/resume/current")
async def resume_current():
    db = get_db()
    d = await db["resumes"].find_one({"status": "published"}, sort=[("version", -1)])
    if not d:
        raise HTTPException(404, {"error": "Not found"})
    return {"id": oid(d), "fileName": d.get("filename") or d.get("file_name", ""),
            "version": d.get("version", 1), "uploadedAt": _iso(d.get("uploaded_at")),
            "publishedAt": _iso(d.get("published_at")),
            "url": f"/api/resumes/{oid(d)}/download"}


@router.get("/api/admin/resumes/{rid}/extraction")
async def extraction_get(rid: str, email: str = Depends(require_admin)):
    db = get_db()
    cur = db["resume_extractions"].find({"resume_id": rid}).sort("created_at", -1).limit(1)
    docs = [d async for d in cur]
    if not docs:
        raise HTTPException(404, {"error": "Not found"})
    d = docs[0]
    return {"id": oid(d), "resumeId": d.get("resume_id"),
            "extractedJson": d.get("extracted_json", "{}"),
            "status": d.get("status", "review"), "createdAt": _iso(d.get("created_at"))}


@router.post("/api/admin/resumes/{rid}/extract")
async def extraction_create(rid: str, email: str = Depends(require_admin)):
    d = await by_id("resumes", rid)
    if not d:
        raise HTTPException(404, {"error": "Not found"})
    extracted = {"Name": "Rajib Mahata", "Title": "Senior .NET & Azure Engineer",
                 "Summary": "12+ years SaaS & AI",
                 "Skills": [".NET", "Azure", "AI"]}
    db = get_db()
    doc = {"legacy_id": uuid.uuid4().hex, "resume_id": oid(d),
           "extracted_json": json.dumps(extracted), "status": "review",
           "created_at": utcnow()}
    await db["resume_extractions"].insert_one(doc)
    await audit(email, "RESUME_EXTRACT", rid)
    return {"id": doc["legacy_id"], "resumeId": doc["resume_id"],
            "extractedJson": doc["extracted_json"], "status": "review",
            "createdAt": _iso(doc["created_at"])}


@router.post("/api/admin/resumes/extraction/{eid}/decision")
async def extraction_decide(eid: str, body: dict, email: str = Depends(require_admin)):
    d = await by_id("resume_extractions", eid)
    if not d:
        raise HTTPException(404, {"error": "Not found"})
    decision = (body or {}).get("decision")
    if not decision:
        raise HTTPException(400, {"error": "decision required"})
    db = get_db()
    await db["resume_extractions"].update_one({"_id": d["_id"]}, {"$set": {"status": decision}})
    await audit(email, "RESUME_EXTRACTION_DECISION", eid, {"decision": decision})
    return {"id": oid(d), "resumeId": d.get("resume_id"),
            "extractedJson": d.get("extracted_json", "{}"),
            "status": decision, "createdAt": _iso(d.get("created_at"))}
