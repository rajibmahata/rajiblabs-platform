"""Admin GitHub Integration: token config (masked), connection test, repo
discovery, per-repo knowledge sync, and KB lifecycle — all JWT-protected.

The PAT is stored server-side only (site_settings `github` doc, write-only
API) and never appears in responses, logs, prompts, or the index.
Knowledge flows through the single shared pipeline (rag_ingest) — there is
no separate GitHub RAG system.
"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from app.auth.dependencies import require_admin
from app.config import get_settings
from app.database import get_db, utcnow
from app.models import oid_str
from app.services import github_service
from app.services.notify import audit, log_error

router = APIRouter(prefix="/api/admin/github")


class TokenIn(BaseModel):
    token: str = ""
    owner: str | None = None


def _repo_out(d: dict) -> dict:
    d = oid_str(d)
    d.pop("readme", None)  # large; fetch per-repo when needed
    return d


@router.get("/status")
async def status(email: str = Depends(require_admin)):
    s = get_settings()
    db = get_db()
    last = await db["github_sync_runs"].find_one(sort=[("started_at", -1)])
    if last:
        last = oid_str(last)
    cfg = await github_service.token_status(db)
    return {"connected": cfg["configured"], "owner": cfg["owner"],
            "token_source": cfg["source"], "token_masked": cfg["masked"],
            "count": await db["github_repositories"].count_documents({}), "last_sync": last}


@router.get("/config")
async def get_config(email: str = Depends(require_admin)):
    """Masked token status — the full token is never returned."""
    db = get_db()
    return await github_service.token_status(db)


@router.post("/config")
async def save_config(body: TokenIn, email: str = Depends(require_admin)):
    """Store/replace the PAT (write-only). Validates shape, never echoes it."""
    token = (body.token or "").strip()
    if not token or len(token) < 8 or any(c.isspace() for c in token):
        raise HTTPException(400, "Token looks invalid (empty/too short/whitespace)")
    db = get_db()
    owner = (body.owner or "").strip() or get_settings().github_owner
    await db["site_settings"].update_one(
        {"key": github_service.CONFIG_KEY},
        {"$set": {"value": {"token": token, "owner": owner,
                            "updated_at": utcnow(), "updated_by": email},
                  "updated_at": utcnow()}},
        upsert=True)
    await audit(email, "GITHUB_TOKEN_SET", "github", {"owner": owner})
    return {**(await github_service.token_status(db)), "ok": True}


@router.delete("/config")
async def delete_config(email: str = Depends(require_admin)):
    """Revoke the stored token (env token, if set, still applies)."""
    db = get_db()
    await db["site_settings"].delete_one({"key": github_service.CONFIG_KEY})
    await audit(email, "GITHUB_TOKEN_REVOKE", "github")
    return {**(await github_service.token_status(db)), "ok": True}


@router.post("/test")
async def test_connection(body: TokenIn, email: str = Depends(require_admin)):
    """Validate a token (given or stored/env) and show account info."""
    db = get_db()
    token = (body.token or "").strip() or await github_service.resolve_github_token(db)
    if not token:
        raise HTTPException(400, "No token provided and none configured")
    try:
        info = await github_service.fetch_user(token)
    except RuntimeError as e:
        raise HTTPException(400, str(e))
    except Exception as e:
        await log_error("github_test", "GitHub connection test failed",
                        str(e)[:1000], logger="app.routers.github")
        raise HTTPException(502, f"GitHub unreachable: {e}"[:200])
    return {"ok": True, **info}


@router.post("/sync")
async def sync(email: str = Depends(require_admin)):
    try:
        result = await github_service.sync_now()
    except RuntimeError as e:
        raise HTTPException(400, str(e))
    await audit(email, "GITHUB_SYNC", "github")
    return result


@router.get("/repositories")
async def repos(tracked: bool | None = None, email: str = Depends(require_admin)):
    db = get_db()
    q = {}
    cur = db["github_repositories"].find(q).sort("stars", -1).limit(200)
    return [_repo_out(d) async for d in cur]


async def _find_repo(rid: str):
    from bson import ObjectId
    db = get_db()
    try:
        doc = await db["github_repositories"].find_one({"_id": ObjectId(rid)})
    except Exception:
        doc = None
    if doc is None:
        doc = await db["github_repositories"].find_one({"full_name": rid})
    return db, doc


@router.patch("/repositories/{rid}")
async def patch_repo(rid: str, body: dict, email: str = Depends(require_admin)):
    """Enable/disable knowledge sync (rag_enabled) and related flags."""
    db, doc = await _find_repo(rid)
    if not doc:
        raise HTTPException(404, "Repository not found")
    patch: dict = {}
    if "rag_enabled" in (body or {}):
        patch["rag_enabled"] = bool(body["rag_enabled"])
    if "classification" in (body or {}) and body["classification"]:
        patch["classification"] = str(body["classification"])[:40]
    if not patch:
        raise HTTPException(400, "Nothing to update (rag_enabled, classification)")
    await db["github_repositories"].update_one({"_id": doc["_id"]}, {"$set": patch})
    await audit(email, "GITHUB_REPO_PATCH", doc.get("full_name", rid), patch)
    return _repo_out({**doc, **patch})


@router.post("/repositories/{rid}/sync")
async def sync_repo(rid: str, email: str = Depends(require_admin)):
    """Manual per-repo knowledge sync (full incremental pipeline)."""
    from app.services import rag_ingest
    db, doc = await _find_repo(rid)
    if not doc:
        raise HTTPException(404, "Repository not found")
    full_name = doc.get("full_name", "")
    if doc.get("rag_enabled") is False:
        raise HTTPException(409, "Knowledge sync is disabled for this repository — enable it first")
    try:
        stats = await rag_ingest.ingest_github_repo(full_name)
    except RuntimeError as e:
        await db["github_repositories"].update_one(
            {"_id": doc["_id"]}, {"$set": {"rag_last_error": str(e)[:500]}})
        await log_error("github_repo_sync", f"Sync failed for {full_name}",
                        str(e)[:2000], logger="app.routers.github")
        raise HTTPException(400, str(e))
    except Exception as e:
        await db["github_repositories"].update_one(
            {"_id": doc["_id"]}, {"$set": {"rag_last_error": str(e)[:500]}})
        await log_error("github_repo_sync", f"Sync failed for {full_name}",
                        str(e)[:2000], logger="app.routers.github")
        raise HTTPException(502, f"Sync failed: {e}"[:300])
    await db["github_repositories"].update_one(
        {"_id": doc["_id"]}, {"$set": {"rag_last_error": None}})
    await audit(email, "GITHUB_REPO_SYNC", full_name,
                {k: stats.get(k, 0) for k in ("created", "updated", "unchanged", "failed")})
    return {"ok": True, "repository": full_name, **stats}


@router.get("/repositories/{rid}/knowledge")
async def repo_knowledge(rid: str, email: str = Depends(require_admin)):
    """Per-repo KB rollup: documents, chunks, last indexed, statuses."""
    db, doc = await _find_repo(rid)
    if not doc:
        raise HTTPException(404, "Repository not found")
    full_name = doc.get("full_name", "")
    docs = [oid_str(d) async for d in db["knowledge_documents"].find(
        {"repository": full_name}).sort("updated_at", -1).limit(200)]
    doc_ids = [d.get("id") for d in docs]
    chunks = await db["knowledge_chunks"].count_documents(
        {"document_id": {"$in": doc_ids}}) if doc_ids else 0
    by_status: dict[str, int] = {}
    for d in docs:
        by_status[d.get("status", "?")] = by_status.get(d.get("status", "?"), 0) + 1
    indexed = [d.get("indexed_at") for d in docs if d.get("indexed_at")]
    return {
        "repository": full_name, "rag_enabled": doc.get("rag_enabled", True),
        "sync_status": doc.get("sync_status"), "last_synced_at": doc.get("rag_last_synced_at"),
        "last_commit_sha": doc.get("rag_last_commit_sha"),
        "doc_count": len(docs), "chunk_count": chunks,
        "last_indexed_at": max(indexed) if indexed else None,
        "by_status": by_status, "docs": docs,
    }


@router.post("/repositories/{rid}/reindex")
async def reindex_repo(rid: str, email: str = Depends(require_admin)):
    """Force full re-index of one repo (clears hashes, re-runs the pipeline)."""
    from app.services import rag_ingest
    db, doc = await _find_repo(rid)
    if not doc:
        raise HTTPException(404, "Repository not found")
    full_name = doc.get("full_name", "")
    await db["knowledge_documents"].update_many(
        {"repository": full_name},
        {"$set": {"content_hash": "", "updated_at": utcnow()}})
    try:
        stats = await rag_ingest.ingest_github_repo(full_name)
    except Exception as e:
        await log_error("github_repo_sync", f"Re-index failed for {full_name}",
                        str(e)[:2000], logger="app.routers.github")
        raise HTTPException(502, f"Re-index failed: {e}"[:300])
    await audit(email, "GITHUB_REPO_REINDEX", full_name)
    return {"ok": True, "repository": full_name, **stats}


@router.post("/repositories/{rid}/disable")
async def disable_repo(rid: str, email: str = Depends(require_admin)):
    """Disable from RAG: flag off + vectors removed (docs kept as records)."""
    from app.services import rag_ingest
    db, doc = await _find_repo(rid)
    if not doc:
        raise HTTPException(404, "Repository not found")
    full_name = doc.get("full_name", "")
    await db["github_repositories"].update_one(
        {"_id": doc["_id"]}, {"$set": {"rag_enabled": False}})
    removed = 0
    async for d in db["knowledge_documents"].find({"repository": full_name}):
        try:
            if await rag_ingest.deactivate_document(str(d["_id"])):
                removed += 1
        except Exception:
            pass
    await audit(email, "GITHUB_REPO_DISABLE", full_name, {"docs_deactivated": removed})
    return {"ok": True, "repository": full_name, "docs_deactivated": removed}


@router.delete("/repositories/{rid}/knowledge")
async def delete_repo_knowledge(rid: str, email: str = Depends(require_admin)):
    """Delete all indexed knowledge for a repo (docs + vectors)."""
    from app.services import rag_ingest
    db, doc = await _find_repo(rid)
    if not doc:
        raise HTTPException(404, "Repository not found")
    full_name = doc.get("full_name", "")
    removed = 0
    async for d in db["knowledge_documents"].find({"repository": full_name}):
        try:
            if await rag_ingest.delete_document(str(d["_id"])):
                removed += 1
        except Exception:
            pass
    await audit(email, "GITHUB_REPO_KB_DELETE", full_name, {"docs_deleted": removed})
    return {"ok": True, "repository": full_name, "docs_deleted": removed}


@router.post("/repositories/{rid}/map")
async def map_repo(rid: str, project_slug: str, email: str = Depends(require_admin)):
    from bson import ObjectId
    db = get_db()
    await db["github_repositories"].update_one({"_id": ObjectId(rid)}, {"$set": {"project_slug": project_slug}})
    await audit(email, "GITHUB_MAP", rid, {"project": project_slug})
    return {"ok": True}
