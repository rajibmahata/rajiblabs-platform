"""Admin RAG console (§20): dashboard, knowledge CRUD, reindex, evaluate.

All routes require admin JWT. Knowledge edits re-index automatically so the
vector store can never drift from MongoDB.
"""
from fastapi import APIRouter, Depends, HTTPException
from app.auth.dependencies import require_admin
from app.config import get_settings
from app.database import get_db, utcnow
from app.models import oid_str
from app.schemas import KnowledgeDocumentIn, RagEvaluateIn
from app.services.notify import audit

router = APIRouter(prefix="/api/admin/rag")


def _oid(pid: str):
    from bson import ObjectId
    try:
        return ObjectId(pid)
    except Exception:
        raise HTTPException(400, "Invalid id")


@router.get("/dashboard")
async def rag_dashboard(email: str = Depends(require_admin)):
    """Source coverage, doc health, Qdrant status, recent query telemetry."""
    from app.services.rag_vectors import get_vector_store
    db = get_db()
    by_source = {}
    async for row in db["knowledge_documents"].aggregate([
            {"$group": {"_id": {"t": "$source_type", "s": "$status"},
                        "n": {"$sum": 1}}}]):
        by_source.setdefault(row["_id"]["t"], {})[row["_id"]["s"]] = row["n"]
    failed = [oid_str(d) async for d in db["knowledge_documents"].find(
        {"status": "failed"}).sort("updated_at", -1).limit(20)]
    recent = []
    async for a in db["audit_logs"].find(
            {"action": {"$in": ["RAG_QUERY", "RAG_ANSWER"]}}).sort("created_at", -1).limit(30):
        recent.append(oid_str(a))
    repos = [oid_str(r) async for r in db["github_repositories"].find(
        {}, {"full_name": 1, "private": 1, "rag_last_synced_at": 1,
             "rag_last_commit_sha": 1, "rag_doc_count": 1}).limit(100)]
    # health_check() never raises, but stay defensive.
    try:
        qdrant: dict = await get_vector_store().health_check()
    except Exception as e:
        qdrant = {"ok": False, "error": str(e)[:200]}
    s = get_settings()
    return {
        "enabled": s.rag_enabled, "by_source": by_source,
        "chunks": await db["knowledge_chunks"].count_documents({}),
        "failed": failed, "recent_queries": recent,
        "github_repos": repos, "qdrant": qdrant,
        "config": {"provider": s.ai_provider, "chat_model": s.openai_model,
                   "embedding_model": s.embedding_model,
                   "embedding_dim": s.embedding_dim,
                   "top_k": s.rag_top_k, "min_score": s.rag_min_score,
                   "chunk_size": s.rag_chunk_size,
                   "max_files": s.github_rag_max_files,
                   "max_bytes": s.github_rag_max_bytes,
                   "allowlist": s.github_rag_repos},
    }


@router.get("/documents")
async def list_documents(source_type: str | None = None, status: str | None = None,
                         search: str | None = None, repository: str | None = None,
                         limit: int = 50,
                         email: str = Depends(require_admin)):
    db = get_db()
    q: dict = {}
    if source_type:
        q["source_type"] = source_type
    if status:
        q["status"] = status
    if repository:
        q["repository"] = repository
    if search:
        q["$or"] = [{"title": {"$regex": search[:80], "$options": "i"}},
                    {"source_id": {"$regex": search[:80], "$options": "i"}}]
    cur = db["knowledge_documents"].find(
        q, {"content": 0}).sort("updated_at", -1).limit(min(limit, 200))
    return [oid_str(d) async for d in cur]


@router.get("/github-sources")
async def github_sources(email: str = Depends(require_admin)):
    """Knowledge-source tree for synced GitHub repos: docs, chunks, index
    and sync state per repository (powers the KB Admin GitHub group)."""
    db = get_db()
    agg = [d async for d in db["knowledge_documents"].aggregate([
        {"$match": {"source_type": {"$regex": "^github_"}}},
        {"$group": {"_id": "$repository",
                    "docs": {"$sum": 1},
                    "by_status": {"$push": "$status"},
                    "last_indexed": {"$max": "$indexed_at"},
                    "last_updated": {"$max": "$updated_at"}}}])]
    out = []
    for row in agg:
        repo = row["_id"] or "(unknown)"
        doc_ids = [str(d["_id"]) async for d in db["knowledge_documents"].find(
            {"repository": repo}, {"_id": 1}).limit(2000)]
        chunks = await db["knowledge_chunks"].count_documents(
            {"document_id": {"$in": doc_ids}}) if doc_ids else 0
        by_status: dict[str, int] = {}
        for st in row.get("by_status") or []:
            by_status[st or "?"] = by_status.get(st or "?", 0) + 1
        tracked = await db["github_repositories"].find_one({"full_name": repo})
        out.append({
            "repository": repo,
            "repository_url": (tracked or {}).get("html_url"),
            "doc_count": row.get("docs", 0), "chunk_count": chunks,
            "by_status": by_status,
            "last_indexed_at": row.get("last_indexed"),
            "last_updated_at": row.get("last_updated"),
            "rag_enabled": (tracked or {}).get("rag_enabled", True),
            "sync_status": (tracked or {}).get("sync_status"),
            "last_synced_at": (tracked or {}).get("rag_last_synced_at"),
            "last_commit_sha": (tracked or {}).get("rag_last_commit_sha"),
        })
    out.sort(key=lambda r: r["repository"].lower())
    return out


@router.get("/documents/{doc_id}")
async def get_document(doc_id: str, email: str = Depends(require_admin)):
    db = get_db()
    doc = await db["knowledge_documents"].find_one({"_id": _oid(doc_id)})
    if not doc:
        raise HTTPException(404, "Document not found")
    chunks = [oid_str(c) async for c in db["knowledge_chunks"].find(
        {"document_id": doc_id}).sort("chunk_index", 1).limit(50)]
    doc = oid_str(doc)
    doc["chunks"] = chunks
    return doc


@router.get("/guardrail-schema")
async def guardrail_schema(email: str = Depends(require_admin)):
    """Field metadata driving the Admin Guardrails/Hallucination form."""
    from app.services import kb_policy as _kb
    return {"guardrails": _kb.DEFAULT_GUARDRAILS,
            "hallucination_control": _kb.DEFAULT_HALLUCINATION,
            "fields": _kb.FIELD_META}


@router.post("/documents")
async def create_document(body: KnowledgeDocumentIn, email: str = Depends(require_admin)):
    """Manual knowledge entry → indexed immediately (§21)."""
    from app.services import rag_ingest
    import hashlib
    import re
    source_id = (body.source_id or "").strip()
    if not source_id:
        slug = re.sub(r"[^a-z0-9]+", "-", body.title.lower()).strip("-")[:60]
        digest = hashlib.sha256(body.title.encode()).hexdigest()[:8]
        source_id = f"admin:{slug or 'doc'}-{digest}"
    try:
        res = await rag_ingest.upsert_document(
            body.source_type, source_id, body.title, body.content,
            url=body.url, repository=body.repository,
            language=body.language, tags=body.tags,
            guardrails=body.guardrails,
            hallucination_control=body.hallucination_control)
    except ValueError as e:
        raise HTTPException(400, str(e))
    except Exception as e:
        raise HTTPException(502, f"Indexing failed: {e}"[:300])
    await audit(email, "RAG_DOC_CREATE", res["document_id"],
                {"source_type": body.source_type, "status": res["status"]})
    return res


@router.put("/documents/{doc_id}")
async def update_document(doc_id: str, body: KnowledgeDocumentIn,
                          email: str = Depends(require_admin)):
    """Edit → version bump + full re-index (stale vectors deleted first).

    Metadata/policy-only saves (same content/title/url/tags) skip
    re-indexing: policies $set directly, no version bump, no embedding cost.
    """
    from app.services import rag_ingest
    from app.services import kb_policy as _kb
    db = get_db()
    cur = await db["knowledge_documents"].find_one({"_id": _oid(doc_id)})
    if not cur:
        raise HTTPException(404, "Document not found")
    new_title = body.title or cur.get("title", "")
    new_content = body.content
    new_url = body.url if body.url is not None else cur.get("url")
    new_tags = body.tags or cur.get("tags", [])
    content_changed = (new_title != cur.get("title", "")
                       or new_content != cur.get("content", "")
                       or new_url != cur.get("url")
                       or new_tags != cur.get("tags", [])
                       or (body.repository or cur.get("repository")) != cur.get("repository")
                       or (body.language or cur.get("language")) != cur.get("language"))
    policy_patch = {
        "guardrails": _kb.normalize_guardrails(
            body.guardrails if body.guardrails is not None else cur.get("guardrails")),
        "hallucination_control": _kb.normalize_hallucination(
            body.hallucination_control if body.hallucination_control is not None
            else cur.get("hallucination_control")),
        "updated_at": utcnow(),
    }
    if not content_changed:
        await db["knowledge_documents"].update_one(
            {"_id": cur["_id"]}, {"$set": policy_patch})
        await audit(email, "RAG_DOC_POLICY_UPDATE", doc_id, {"reindexed": False})
        return {"document_id": doc_id, "status": "metadata-updated"}
    try:
        res = await rag_ingest.upsert_document(
            cur["source_type"], cur["source_id"], new_title, new_content,
            url=new_url, repository=cur.get("repository"), language=cur.get("language"),
            tags=new_tags, guardrails=policy_patch["guardrails"],
            hallucination_control=policy_patch["hallucination_control"])
    except ValueError as e:
        raise HTTPException(400, str(e))
    except Exception as e:
        raise HTTPException(502, f"Re-indexing failed: {e}"[:300])
    await audit(email, "RAG_DOC_UPDATE", doc_id, {"status": res["status"]})
    return res


@router.post("/documents/{doc_id}/unpublish")
async def unpublish_document(doc_id: str, email: str = Depends(require_admin)):
    from app.services import rag_ingest
    if not await rag_ingest.deactivate_document(doc_id):
        raise HTTPException(404, "Document not found")
    await audit(email, "RAG_DOC_UNPUBLISH", doc_id)
    return {"ok": True}


@router.delete("/documents/{doc_id}")
async def remove_document(doc_id: str, email: str = Depends(require_admin)):
    from app.services import rag_ingest
    if not await rag_ingest.delete_document(doc_id):
        raise HTTPException(404, "Document not found")
    await audit(email, "RAG_DOC_DELETE", doc_id)
    return {"ok": True}


@router.post("/documents/{doc_id}/reindex")
async def reindex_document(doc_id: str, email: str = Depends(require_admin)):
    """Force re-index of one document (clears hash so content is re-embedded)."""
    from app.services import rag_ingest
    db = get_db()
    cur = await db["knowledge_documents"].find_one({"_id": _oid(doc_id)})
    if not cur:
        raise HTTPException(404, "Document not found")
    await db["knowledge_documents"].update_one(
        {"_id": cur["_id"]}, {"$set": {"content_hash": "", "updated_at": utcnow()}})
    try:
        res = await rag_ingest.upsert_document(
            cur["source_type"], cur["source_id"], cur.get("title", ""),
            cur.get("content", ""), url=cur.get("url"),
            repository=cur.get("repository"), language=cur.get("language"),
            tags=cur.get("tags", []))
    except Exception as e:
        raise HTTPException(502, f"Re-indexing failed: {e}"[:300])
    await audit(email, "RAG_DOC_REINDEX", doc_id, {"status": res["status"]})
    return res


@router.post("/reindex")
async def reindex_all(source: str = "mongodb", email: str = Depends(require_admin)):
    """Full-source re-ingest. Hash dedup keeps it cheap; audit the outcome."""
    from app.services import rag_ingest
    s = get_settings()
    combined = {"created": 0, "updated": 0, "unchanged": 0, "failed": 0, "errors": []}
    repos: list[str] = []

    def _merge(stats: dict):
        for k in ("created", "updated", "unchanged", "failed"):
            combined[k] += stats.get(k, 0)
        combined["errors"].extend(stats.get("errors", [])[:10])

    try:
        if source in ("mongodb", "all"):
            _merge(await rag_ingest.ingest_mongodb())
            _merge(await rag_ingest.ingest_resume())
        if source in ("github", "all"):
            # github_rag_repos is a comma-separated allowlist; empty means
            # every tracked public repo.
            allow = [r.strip() for r in (s.github_rag_repos or "").split(",")
                     if r.strip()]
            db = get_db()
            if not allow:
                async for t in db["github_repositories"].find(
                        {"private": {"$ne": True}}, {"full_name": 1}):
                    if t.get("full_name"):
                        allow.append(t["full_name"])
            if not allow:
                combined["errors"].append(
                    "no GitHub repos: set GITHUB_RAG_REPOS or sync GitHub first")
            for full in allow:
                try:
                    _merge(await rag_ingest.ingest_github_repo(full))
                except Exception as e:
                    combined["failed"] += 1
                    combined["errors"].append(f"{full}: {e}"[:200])
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(502, f"Re-ingest failed: {e}"[:300])
    await audit(email, "RAG_REINDEX", source,
                {k: v for k, v in combined.items() if k != "errors"})
    try:
        from app.services.notify import notify
        await notify("RAGReindexed",
                     f"RAG re-ingest ({source}): "
                     f"{combined['created']} new, {combined['updated']} updated, "
                     f"{combined['unchanged']} unchanged, {combined['failed']} failed",
                     "", "rag", "")
    except Exception:
        pass
    return combined


@router.post("/evaluate")
async def evaluate(body: RagEvaluateIn, email: str = Depends(require_admin)):
    """Golden-question check (§23): keyword coverage over retrieved chunks."""
    from app.services import rag_query as rq
    results = []
    for item in body.items[:25]:
        chunks = await rq.retrieve(item.question, top_k=item.top_k or 5)
        haystack = "\n".join(c.get("content", "").lower() for c in chunks)
        hits = [kw for kw in item.expected_keywords if kw.lower() in haystack]
        passed = bool(hits) and len(hits) >= max(1, len(item.expected_keywords) // 2)
        results.append({"question": item.question, "intent": item.intent_hint,
                        "retrieved": len(chunks),
                        "top_score": (chunks[0].get("score") if chunks else 0),
                        "matched": hits,
                        "expected": item.expected_keywords, "passed": passed})
    summary = {"total": len(results),
               "passed": sum(1 for r in results if r["passed"]),
               "pass_rate": round(sum(1 for r in results if r["passed"])
                                  / max(1, len(results)), 3)}
    await audit(email, "RAG_EVALUATE", "", summary)
    return {"summary": summary, "results": results}
