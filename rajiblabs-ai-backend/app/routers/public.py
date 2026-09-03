"""Public read-only API — published content only. GET /api/public/*"""
from fastapi import APIRouter
from app.database import get_db
from app.models import oid_str

router = APIRouter(prefix="/api/public")


@router.get("/site")
async def site():
    db = get_db()
    s = await db["site_settings"].find_one({"key": "contact"})
    return {"contact": (s or {}).get("value", {}), "url": "https://rajiblabs.com"}


@router.get("/home")
async def home():
    db = get_db()
    cur = db["homepage_content"].find({"status": "published"}).sort("display_order", 1)
    return [oid_str(d) async for d in cur]


@router.get("/skills")
async def skills():
    db = get_db()
    cur = db["skills"].find({"status": "published"}).sort("display_order", 1)
    return [oid_str(d) async for d in cur]


@router.get("/experience")
async def experience():
    db = get_db()
    cur = db["experience"].find({"status": "published"}).sort("display_order", 1)
    return [oid_str(d) async for d in cur]


@router.get("/projects")
async def projects(featured: bool | None = None):
    db = get_db()
    q: dict = {"published": True}
    if featured is not None:
        q["featured"] = featured
    cur = db["projects"].find(q).sort("display_order", 1)
    out = []
    async for d in cur:
        d = oid_str(d)
        # Never leak locked/internal fields publicly
        d.pop("locked_fields", None)
        out.append(d)
    return out


@router.get("/projects/{slug}")
async def project_detail(slug: str):
    from fastapi import HTTPException
    db = get_db()
    d = await db["projects"].find_one({"slug": slug, "published": True})
    if not d:
        raise HTTPException(404, {"code": "PROJECT_NOT_FOUND", "message": "Project not found"})
    d = oid_str(d)
    d.pop("locked_fields", None)
    links = [oid_str(l) async for l in db["project_links"].find({"project_slug": slug})]
    d["links"] = links
    return d


@router.get("/products")
async def products():
    db = get_db()
    cur = db["projects"].find({"published": True, "category": "product"}).sort("display_order", 1)
    return [oid_str(d) async for d in cur]


@router.get("/resume")
async def resume():
    db = get_db()
    d = await db["resumes"].find_one({"active": True}, sort=[("version", -1)])
    if not d:
        return {"active": False}
    d = oid_str(d)
    d.pop("stored_path", None)
    d.pop("path", None)  # legacy field, never expose disk paths
    return {**d, "download_url": "/api/public/resume/download"}


@router.get("/resume/download")
async def resume_download():
    from fastapi import HTTPException
    from fastapi.responses import FileResponse
    from pathlib import Path
    db = get_db()
    d = await db["resumes"].find_one({"active": True}, sort=[("version", -1)])
    if not d:
        raise HTTPException(404, "No active resume")
    # Canonical field is stored_path; fall back to legacy path for old docs.
    stored = d.get("stored_path") or d.get("path")
    if not stored or not Path(stored).is_file():
        raise HTTPException(404, "Resume file missing")
    return FileResponse(stored, filename=d.get("filename") or d.get("file_name") or "resume.pdf",
                        media_type="application/pdf")
