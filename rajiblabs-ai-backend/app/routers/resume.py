"""Resume upload/download (validated) + public active resume."""
from pathlib import Path
import secrets
import uuid
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi.responses import FileResponse
from app.auth.dependencies import require_admin
from app.config import get_settings
from app.database import get_db, utcnow
from app.models import oid_str
from app.services.notify import audit

router = APIRouter()
ALLOWED = {".pdf": "application/pdf", ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document"}


@router.post("/api/admin/resume")
async def upload(file: UploadFile = File(...), email: str = Depends(require_admin)):
    # Canonical upload is POST /api/admin/resumes/upload (legacy). This singular
    # endpoint is kept for backward compat and now mirrors that logic exactly
    # so either path enforces single-published and unified schema.
    import hashlib as _hashlib
    s = get_settings()
    ext = Path(file.filename or "").suffix.lower()
    if ext not in (".pdf", ".docx"):
        raise HTTPException(400, "Only PDF/DOCX allowed")
    data = await file.read()
    if len(data) > s.max_resume_mb * 1024 * 1024:
        raise HTTPException(400, f"Max {s.max_resume_mb}MB")
    file_hash = _hashlib.sha256(data).hexdigest()[:16]
    db = get_db()
    existing_hash = await db["resumes"].find_one({"file_hash": file_hash})
    if existing_hash:
        from app.models import oid_str as _oid
        d = _oid(existing_hash)
        return {"id": d.get("id") or str(existing_hash["_id"]), "version": d.get("version")}
    updir = Path(s.upload_dir) / "resumes"
    updir.mkdir(parents=True, exist_ok=True)
    safe = f"{secrets.token_hex(8)}{ext}"
    try:
        (updir / safe).write_bytes(data)
    except Exception as e:
        raise HTTPException(500, f"Storage failed: {e}")
    max_ver = await db["resumes"].find_one(sort=[("version", -1)], projection={"version": 1})
    version = int((max_ver or {}).get("version", 0)) + 1
    # absolute stored_path for reliable FileResponse later
    stored_abs = str((updir / safe).resolve()) if (updir / safe).exists() else str(updir / safe)
    doc = {
        "legacy_id": uuid.uuid4().hex,
        "filename": file.filename, "file_name": file.filename,
        "stored_path": stored_abs, "stored_rel": f"uploads/resumes/{safe}",
        "content_type": file.content_type or ALLOWED.get(ext, "application/octet-stream"),
        "size_bytes": len(data), "version": version,
        "status": "published", "active": True,
        "extracted_text": "", "file_hash": file_hash,
        "uploaded_at": utcnow(), "published_at": utcnow(),
    }
    # Single-published: archive all others before insert (insert stays published)
    await db["resumes"].update_many({}, {"$set": {"status": "archived", "active": False}})
    res = await db["resumes"].insert_one(doc)
    await audit(email, "RESUME_UPLOAD", str(res.inserted_id))
    # Best-effort extraction + RAG (no duplicate processing: upsert is hash-deduped)
    # also triggers resume→project consolidation via profile agent (hash-deduped)
    try:
        from app.services.resume_text import extract_and_store
        await extract_and_store(str(res.inserted_id))
    except Exception as e:
        try:
            from app.services.notify import log_error
            await log_error("resume_upload", "Resume extraction failed", str(e)[:1000])
        except Exception:
            pass
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
