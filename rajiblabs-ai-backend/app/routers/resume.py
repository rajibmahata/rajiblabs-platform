"""Resume upload/download (validated) + public active resume."""
from pathlib import Path
import secrets
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi.responses import FileResponse
from app.auth.dependencies import require_admin
from app.config import get_settings
from app.database import get_db, utcnow
from app.models import oid_str
from app.services.notify import audit

router = APIRouter()
ALLOWED = {".pdf": "application/pdf", ".png": "image/png", ".jpg": "image/jpeg",
           ".jpeg": "image/jpeg", ".webp": "image/webp"}


@router.post("/api/admin/resume")
async def upload(file: UploadFile = File(...), email: str = Depends(require_admin)):
    s = get_settings()
    ext = Path(file.filename or "").suffix.lower()
    if ext not in (".pdf", ".docx", ".png", ".jpg", ".jpeg", ".webp"):
        raise HTTPException(400, "Only PDF/DOCX/PNG/JPG/WEBP allowed")
    data = await file.read()
    max_mb = s.max_resume_mb if ext in (".pdf", ".docx") else s.max_image_mb
    if len(data) > max_mb * 1024 * 1024:
        raise HTTPException(400, f"Max {max_mb}MB")
    updir = Path(s.upload_dir) / "resumes"
    updir.mkdir(parents=True, exist_ok=True)
    safe = f"{secrets.token_hex(8)}{ext}"
    (updir / safe).write_bytes(data)
    db = get_db()
    count = await db["resumes"].count_documents({})
    doc = {"filename": file.filename, "stored_path": str(updir / safe),
           "content_type": file.content_type or ALLOWED.get(ext, "application/octet-stream"),
           "size_bytes": len(data), "version": count + 1, "active": True,
           "uploaded_at": utcnow()}
    await db["resumes"].update_many({}, {"$set": {"active": False}})
    res = await db["resumes"].insert_one(doc)
    await audit(email, "RESUME_UPLOAD", str(res.inserted_id))
    return {"id": str(res.inserted_id), "version": doc["version"]}


@router.get("/api/admin/resume")
async def list_resumes(email: str = Depends(require_admin)):
    db = get_db()
    cur = db["resumes"].find().sort("version", -1).limit(20)
    out = []
    async for d in cur:
        d = oid_str(d)
        d.pop("stored_path", None)
        d.pop("path", None)  # legacy field, never expose disk paths
        out.append(d)
    return out
