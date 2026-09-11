"""Resume text extraction + RAG wiring (single published, history retained).

- Extracts PDF via pypdf (fallback to no-op if not installed/corrupt).
- Extracts DOCX via python-docx if available.
- Writes `extracted_text` to the resume doc (for profile_agent + RAG).
- Triggers RAG ingest (hash-deduped, so no duplicate processing).
- Scrubs sensitive lines before indexing.
"""
import logging
from pathlib import Path

from app.config import get_settings
from app.database import get_db, utcnow

log = logging.getLogger("rajiblabs")

def _extract_pdf_text(path: str, max_chars: int = 40000) -> str:
    try:
        # Prefer pypdf (lightweight, no system deps). Fallback to empty if not installed.
        from pypdf import PdfReader
        reader = PdfReader(path)
        texts = []
        for page in reader.pages[:20]:  # cap pages
            try:
                t = page.extract_text() or ""
                if t.strip():
                    texts.append(t)
            except Exception:
                continue
        return "\n".join(texts)[:max_chars]
    except ImportError:
        log.warning("pypdf not installed — PDF extraction skipped for %s", path)
        return ""
    except Exception as e:
        log.warning("PDF extraction failed %s: %s", path, e)
        return ""

def _extract_docx_text(path: str, max_chars: int = 40000) -> str:
    try:
        from docx import Document
        doc = Document(path)
        texts = [p.text for p in doc.paragraphs if p.text.strip()]
        return "\n".join(texts)[:max_chars]
    except ImportError:
        log.warning("python-docx not installed — DOCX extraction skipped for %s", path)
        return ""
    except Exception as e:
        log.warning("DOCX extraction failed %s: %s", path, e)
        return ""

def extract_text_for_file(path: str) -> str:
    ext = Path(path).suffix.lower()
    if ext == ".pdf":
        return _extract_pdf_text(path)
    if ext == ".docx":
        return _extract_docx_text(path)
    return ""

async def extract_and_store(resume_id: str) -> str:
    """Extract text for one resume, store `extracted_text`, and trigger RAG.

    Returns extracted text (scrubbed, truncated). Never raises to caller
    (best-effort); logs warnings instead. Hash-dedup in rag_ingest prevents
    duplicate Qdrant work.
    """
    from bson import ObjectId
    db = get_db()
    # by_id handles both ObjectId and legacy_id
    doc = None
    try:
        doc = await db["resumes"].find_one({"_id": ObjectId(resume_id)})
    except Exception:
        pass
    if not doc:
        doc = await db["resumes"].find_one({"legacy_id": resume_id})
    if not doc:
        log.warning("extract_and_store: resume not found %s", resume_id)
        return ""
    # Resolve file path (same candidates as _resume_file_path)
    candidates = [doc.get("stored_path")]
    rel = doc.get("stored_rel")
    if rel:
        # legacy.py: _resume_file_path candidates
        candidates.append(str(Path(get_settings().upload_dir).parent / rel))
        candidates.append(str(Path(get_settings().upload_dir) / "resumes" / Path(rel).name))
    file_path = next((c for c in candidates if c and Path(c).is_file()), None)
    if not file_path:
        log.warning("extract_and_store: file missing for %s", resume_id)
        # Stamp the attempt so callers (consolidate) don't retry every run —
        # a missing file is a stable outcome, not a retry signal.
        try:
            await db["resumes"].update_one(
                {"_id": doc["_id"]},
                {"$set": {"extracted_at": utcnow(), "extracted_len": 0}})
        except Exception:
            pass
        return ""
    raw = extract_text_for_file(file_path)
    # Fallback: if extraction empty but file exists, keep previous extracted_text
    if not raw.strip():
        log.warning("extract_and_store: empty extraction for %s", resume_id)
        raw = ""
    # Scrub sensitive before storing (reuse rag_ingest scrub)
    try:
        from app.services.rag_ingest import _scrub_resume_text
        scrubbed = _scrub_resume_text(raw)[:20000]
    except Exception:
        scrubbed = raw[:20000]
    # Store (preserve history: update this doc only)
    await db["resumes"].update_one(
        {"_id": doc["_id"]},
        {"$set": {"extracted_text": scrubbed, "extracted_at": utcnow()}}
    )
    # Compute content/file hash for versioning (unchanged resumes skip downstream)
    import hashlib as _hashlib
    try:
        file_hash = _hashlib.sha256(raw.encode()).hexdigest()[:16] if raw else ""
    except Exception:
        file_hash = ""
    await db["resumes"].update_one(
        {"_id": doc["_id"]},
        {"$set": {"extracted_hash": file_hash, "extracted_len": len(scrubbed)}}
    )
    # Downstream fan-out only when this extraction produced text or changed
    # the stored text. Re-extracting an unchanged empty result must NOT
    # re-fire consolidation+skills (each of which is otherwise cheap, but the
    # unconditional fan-out formed an extract→consolidate→extract loop for
    # files that yield no text).
    prev_text = doc.get("extracted_text") or ""
    downstream_needed = bool((scrubbed or "").strip()) or ((prev_text or "") != scrubbed)
    # Trigger RAG only if this resume is the currently published/active one
    # (archived resumes remain internal knowledge source but not publicly indexed;
    #  ingest_resume checks active:true, so archived will be skipped until published)
    fresh = await db["resumes"].find_one({"_id": doc["_id"]})
    if downstream_needed and fresh and fresh.get("active") and fresh.get("status") == "published":
        try:
            from app.services.rag_ingest import ingest_resume
            await ingest_resume()
        except Exception as e:
            log.warning("RAG ingest after extract failed: %s", e)
    # Resume → Projects consolidation (Profile Agent owned): extract projects from this resume
    # and merge with existing projects/portfolio (hash/versioned, no duplicate processing)
    if downstream_needed:
        try:
            from app.services.resume_projects import consolidate_resume_projects
            # Only run consolidation if this resume's extracted_hash changed or no cache
            # consolidate_resume_projects handles per-resume hash versioning internally
            await consolidate_resume_projects(db, triggered_by=f"resume:{resume_id}")
        except Exception as e:
            log.warning("resume project consolidation skipped: %s", e)
    # Resume → Skills sync (Profile Agent owned, deterministic, no LLM):
    # previously skills refreshed only on the daily agent run, so freshly
    # uploaded resume skills never appeared until 06:00. Same best-effort
    # pattern as projects above; sync_skills is hash-versioned internally.
    if downstream_needed:
        try:
            from app.services.skill_intelligence import sync_skills
            await sync_skills(triggered_by=f"resume:{resume_id}")
        except Exception as e:
            log.warning("resume skill sync skipped: %s", e)
    # Alert when the ACTIVE resume has no usable text: without extraction the
    # public resume RAG, skills and projects all silently go stale. Archived
    # resumes stay quiet (history only).
    try:
        if fresh and fresh.get("active") and not (scrubbed or "").strip():
            from app.services.notify import log_error
            await log_error("resume_extraction", "Active resume has no extracted text",
                            f"resume:{resume_id} — re-upload the PDF/DOCX or check storage. "
                            "Skills, projects and resume RAG are stale until extraction succeeds.",
                            level="warning", logger="app.services.resume_text")
    except Exception:
        pass
    return scrubbed
