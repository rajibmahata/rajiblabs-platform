"""RAG ingestion — MongoDB content, resume, and GitHub sources → chunks → vectors.

MongoDB is the source of truth; Qdrant holds a derived, versioned index.
content_hash dedup means unchanged content is never re-embedded (§5, §27).
Secrets can never enter the index: every source passes through an
allowlist of public fields, and GitHub ingestion skips private repos,
secret paths and binaries (§4, §29).
"""
import hashlib
import logging
from datetime import datetime, timezone

from app.config import get_settings as _get_settings
from app.database import get_db, utcnow


def get_settings_local():
    return _get_settings()
from app.schemas import RAG_SOURCE_TYPES
from app.services.notify import audit, notify
from app.services.rag_chunk import chunk_text
from app.services.rag_embeddings import EmbeddingError, EmbeddingService
from app.services.rag_vectors import VectorStoreError, get_vector_store, point_id

log = logging.getLogger("rajiblabs")


def content_hash(*parts: str) -> str:
    return hashlib.sha256("|".join(p or "" for p in parts).encode()).hexdigest()


def _embedding_service() -> EmbeddingService:
    from app.services import rag_embeddings
    return rag_embeddings.EmbeddingService()


async def upsert_document(source_type: str, source_id: str, title: str,
                          content: str, url: str | None = None,
                          repository: str | None = None,
                          language: str | None = None,
                          tags: list | None = None,
                          branch: str | None = None,
                          file_path: str | None = None,
                          commit_sha: str | None = None,
                          guardrails: dict | None = None,
                          hallucination_control: dict | None = None) -> dict:
    """Create/update one knowledge document + its vectors.

    Returns {document_id, status} where status is created|updated|unchanged.
    Raises ValueError on invalid source_type; EmbeddingError/VectorStoreError
    leave a failed record and re-raise for the caller to count.
    branch/file_path/commit_sha are GitHub provenance (None for other types).
    guardrails/hallucination_control are normalized server-side; when omitted
    on update, the existing stored policies are preserved.
    """
    from app.services import kb_policy as _kb
    if source_type not in RAG_SOURCE_TYPES:
        raise ValueError(f"unknown source_type: {source_type}")
    content = (content or "").strip()
    if not content:
        raise ValueError("empty content")
    db = get_db()
    now = utcnow()
    chash = content_hash(source_type, source_id, content)
    existing = await db["knowledge_documents"].find_one(
        {"source_type": source_type, "source_id": source_id})
    if existing and existing.get("content_hash") == chash \
            and existing.get("status") == "active":
        return {"document_id": str(existing["_id"]), "status": "unchanged"}
    version = int((existing or {}).get("version", 0)) + 1
    doc = {
        "source_type": source_type, "source_id": source_id,
        "title": title[:200], "content": content,
        "url": url, "repository": repository, "language": language,
        "branch": branch, "file_path": file_path, "commit_sha": commit_sha,
        "tags": tags or [], "visibility": "public",
        "guardrails": _kb.normalize_guardrails(
            guardrails if guardrails is not None
            else (existing or {}).get("guardrails")),
        "hallucination_control": _kb.normalize_hallucination(
            hallucination_control if hallucination_control is not None
            else (existing or {}).get("hallucination_control")),
        "status": "active", "content_hash": chash, "version": version,
        "created_at": (existing or {}).get("created_at", now),
        "updated_at": now, "indexed_at": None,
    }
    if existing:
        await db["knowledge_documents"].update_one(
            {"_id": existing["_id"]}, {"$set": doc})
        doc_id = existing["_id"]
    else:
        res = await db["knowledge_documents"].insert_one(doc)
        doc_id = res.inserted_id
    doc["_id"] = doc_id
    try:
        await _index_chunks(str(doc_id), doc)
    except (EmbeddingError, VectorStoreError) as e:
        await db["knowledge_documents"].update_one(
            {"_id": doc_id},
            {"$set": {"status": "failed", "error": str(e)[:500]}})
        raise
    await db["knowledge_documents"].update_one(
        {"_id": doc_id}, {"$set": {"status": "active", "indexed_at": utcnow()}})
    return {"document_id": str(doc_id),
            "status": "updated" if existing else "created"}


async def _index_chunks(doc_id: str, doc: dict) -> int:
    """Replace all vectors for a document (versioning — no stale entries).

    Mongo rows are written first so every vector payload carries the
    resolvable ``mongo_chunk_id`` (Qdrant point IDs are UUIDv5, not ObjectIds).
    Vector failure rolls the Mongo rows back and marks the doc failed.
    """
    db = get_db()
    store = get_vector_store()
    s = get_settings_local()
    chunks = chunk_text(doc["content"], max_chars=s.rag_chunk_size,
                        overlap=s.rag_chunk_overlap,
                        topic=doc.get("title", ""))
    await db["knowledge_chunks"].delete_many({"document_id": doc_id})
    if not chunks:
        return 0
    emb = _embedding_service()
    vectors = await emb.generate_embeddings([c["content"] for c in chunks])
    res = await db["knowledge_chunks"].insert_many([{
        "document_id": doc_id, "chunk_index": i,
        "content": c["content"],
        "metadata": {"topic": c.get("topic", ""),
                     "source_type": doc["source_type"]},
        "embedding_id": point_id(doc_id, i),
        "created_at": utcnow()} for i, c in enumerate(chunks)])
    payloads = []
    for i, (oid, (c, v)) in enumerate(zip(res.inserted_ids, zip(chunks, vectors))):
        payloads.append({
            "point_id": point_id(doc_id, i), "vector": v,
            "payload": {
                "chunk_id": str(oid), "mongo_chunk_id": str(oid),
                "document_id": doc_id,
                "source_type": doc["source_type"],
                "repository": doc.get("repository"),
                "title": doc.get("title", ""),
                "url": doc.get("url"),
                "language": doc.get("language"),
                "branch": doc.get("branch"),
                "file_path": doc.get("file_path"),
                "commit_sha": doc.get("commit_sha"),
                "topic": c.get("topic", ""),
                **emb.descriptor(),
            }})
    try:
        await store.upsert_chunks(payloads)
    except Exception:
        await db["knowledge_chunks"].delete_many({"document_id": doc_id})
        raise
    return len(payloads)


async def deactivate_document(document_id: str) -> bool:
    """Unpublish: remove from retrieval (vectors + status), keep the record."""
    from bson import ObjectId
    db = get_db()
    try:
        oid = ObjectId(document_id)
    except Exception:
        return False
    doc = await db["knowledge_documents"].find_one({"_id": oid})
    if not doc:
        return False
    try:
        await get_vector_store().delete_document(str(oid))
    except VectorStoreError as e:
        log.warning("vector delete failed for %s: %s", document_id, e)
    await db["knowledge_documents"].update_one(
        {"_id": oid}, {"$set": {"status": "inactive", "updated_at": utcnow()}})
    await db["knowledge_chunks"].delete_many({"document_id": str(oid)})
    return True


async def delete_document(document_id: str) -> bool:
    from bson import ObjectId
    db = get_db()
    try:
        oid = ObjectId(document_id)
    except Exception:
        return False
    await deactivate_document(document_id)
    res = await db["knowledge_documents"].delete_one({"_id": oid})
    return res.deleted_count > 0


# ── MongoDB content ingestion (§12: published records only) ──

def _profile_text(p: dict) -> str:
    lines = [f"{p.get('full_name', '')} — {p.get('title', '')}".strip(" —"),
             (p.get("bio") or "").strip()]
    skills = p.get("skills") or []
    if skills:
        lines.append("Skills: " + ", ".join(skills))
    for c in p.get("career") or []:
        lines.append(f"{c.get('role','')} at {c.get('company','')} ({c.get('period','')})".strip())
        for a in (c.get("achievements") or [])[:6]:
            lines.append(f"- {a}")
        if c.get("tech_stack"):
            lines.append("Technologies: " + ", ".join(c["tech_stack"]))
    if p.get("social_links"):
        links = p["social_links"]
        lines.append("Links: " + ", ".join(
            f"{k}: {v}" for k, v in links.items() if v and k in ("github", "linkedin")))
    return "\n".join(l for l in lines if l)


async def ingest_mongodb() -> dict:
    """Read every published record, normalize, dedup by hash, index changes."""
    db = get_db()
    stats = {"created": 0, "updated": 0, "unchanged": 0, "failed": 0, "errors": []}

    async def one(source_type, source_id, title, content, **kw):
        try:
            r = await upsert_document(source_type, source_id, title, content, **kw)
            stats[r["status"]] += 1
        except Exception as e:
            stats["failed"] += 1
            stats["errors"].append(f"{source_type}:{source_id}: {e}"[:200])
            log.warning("ingest failed %s %s: %s", source_type, source_id, e)

    # profile → professional identity (public fields only)
    prof = await db["profiles"].find_one()
    if prof:
        await one("profile", f"profile:{prof.get('_id')}",
                  f"{prof.get('full_name', 'Rajib Mahata')} — Professional Profile",
                  _profile_text(prof),
                  url="https://rajiblabs.com/#about",
                  tags=["profile", "rajib", "career", "skills"])
    # skills grouped
    cur = db["skills"].find({"status": "published"})
    grouped: dict[str, list] = {}
    async for sk in cur:
        grouped.setdefault(sk.get("category", "General"), []).append(sk.get("name", ""))
    if grouped:
        await one("profile", "skills:all", "Rajib — Technical Skills",
                  "\n".join(f"{cat}: {', '.join(names)}" for cat, names in grouped.items()),
                  url="https://rajiblabs.com/#about", tags=["skills", "rajib"])
    # experience entries
    async for ex in db["experience"].find({"status": "published"}):
        await one("profile", f"experience:{ex.get('_id')}",
                  f"{ex.get('role_title', ex.get('role', ''))} — {ex.get('company', '')}",
                  "\n".join(filter(None, [
                      f"{ex.get('role_title', ex.get('role', ''))} at {ex.get('company', '')} "
                      f"({ex.get('date_range', ex.get('period', ''))})".strip(),
                      ex.get("description", "")])),
                  tags=["experience", "career", "rajib"])
    # projects / products (published only, no internal fields)
    async for p in db["projects"].find({"published": True}):
        tech = ", ".join(p.get("technologies", []) or [])
        body = "\n".join(filter(None, [
            p.get("short_description", "") or p.get("description", ""),
            f"Technologies: {tech}" if tech else "",
            f"Status: {p.get('status', '')}",
            f"Live: {p['live_url']}" if p.get("live_url") else "",
            f"GitHub: {p['github_url']}" if p.get("github_url") else "",
        ]))
        await one("project" if p.get("category") != "product" else "product",
                  f"project:{p.get('slug', p.get('_id'))}",
                  p.get("name", "Untitled project"), body,
                  url=f"https://rajiblabs.com/portfolio/{p.get('slug', '')}",
                  language=(p.get("technologies") or [None])[0],
                  tags=["project", p.get("category", ""), p.get("status", "")])
    # homepage + website content (published only)
    async for h in db["homepage_content"].find({"status": "published"}):
        body = h.get("subtitle", "")
        if isinstance(h.get("body"), dict):
            body += "\n" + "\n".join(
                f"{k}: {v}" for k, v in h["body"].items()
                if isinstance(v, str) and v.strip())[:2000]
        elif isinstance(h.get("body"), str) and h["body"].strip():
            body += "\n" + h["body"][:2000]
        await one("website_content", f"homepage:{h.get('section_key', h.get('_id'))}",
                  h.get("title", "RajibLabs"), body,
                  url="https://rajiblabs.com/", tags=["homepage", "rajiblabs"])
    async for w in db["website_contents"].find({}):
        await one("website_content", f"site:{w.get('key', w.get('_id'))}",
                  w.get("title", "RajibLabs"), str(w.get("body", ""))[:4000],
                  url="https://rajiblabs.com/", tags=["website", "rajiblabs"])
    # services are curated in code (single source of truth with the site)
    for slug, title, desc in (
            ("architecture", "Software Architecture",
             "Enterprise software architecture: .NET 8 microservices, event-driven systems, "
             "CQRS, domain-driven design, Azure cloud-native platforms."),
            ("ai-products", "AI Products & GenAI",
             "AI product engineering: RAG pipelines, LLM integration, vector search, "
             "AI chat assistants, document intelligence."),
            ("saas", "SaaS Development",
             "Multi-tenant SaaS platforms: subscriptions, payments, white-label APIs, "
             "PWA frontends with React and TypeScript.")):
        await one("service", f"service:{slug}", title, desc,
                  url="https://rajiblabs.com/#services",
                  tags=["service", "rajiblabs"])
    return stats


# ── Resume ingestion (§13: public professional info only) ──

SENSITIVE_RESUME_KEYS = (
    "passport", "dob", "date_of_birth", "birth", "marital", "religion",
    "national_id", "aadhaar", "pan_", "bank", "account", "salary",
    "address", "phone_personal",
)


def _scrub_resume_text(text: str) -> str:
    lines = []
    for line in (text or "").splitlines():
        low = line.lower()
        if any(k in low for k in SENSITIVE_RESUME_KEYS):
            continue
        lines.append(line)
    return "\n".join(lines).strip()


async def ingest_resume() -> dict:
    """Index approved public resume info (never private/sensitive fields)."""
    db = get_db()
    stats = {"created": 0, "updated": 0, "unchanged": 0, "failed": 0, "errors": []}
    prof = await db["profiles"].find_one()
    if prof:
        text = _scrub_resume_text(_profile_text(prof))
        if text:
            try:
                r = await upsert_document(
                    "resume", "resume:approved-public",
                    f"{prof.get('full_name', 'Rajib Mahata')} — Resume (public)",
                    text, url="https://rajiblabs.com/#about",
                    tags=["resume", "career", "rajib"])
                stats[r["status"]] += 1
            except Exception as e:
                stats["failed"] += 1
                stats["errors"].append(str(e)[:200])
    # approved resume file text, when an extraction exists
    try:
        cur = db["resumes"].find({"active": True}).limit(1)
        async for resume in cur:
            extracted = (resume.get("extracted_text") or "").strip()
            if extracted:
                try:
                    r = await upsert_document(
                        "resume", f"resume:file:{resume.get('_id')}",
                        "Rajib Mahata — Resume document (public)",
                        _scrub_resume_text(extracted)[:20000],
                        tags=["resume", "document"])
                    stats[r["status"]] += 1
                except Exception as e:
                    stats["failed"] += 1
                    stats["errors"].append(str(e)[:200])
    except Exception as e:
        log.warning("resume file ingest skipped: %s", e)
    return stats


# ── GitHub ingestion (§9–§11) ──

async def ingest_github_repo(full_name: str, max_files: int = 40,
                             max_bytes: int = 200000) -> dict:
    """Incremental per-repo sync: skip unchanged repos/files via hashes.

    Honors the per-repo ``rag_enabled`` flag (disabled repos raise).
    Files removed from the tree have their documents (+vectors) deleted.
    File content is secret-scrubbed before indexing — tokens/keys in code
    can never enter the knowledge base.
    """
    from app.services import github_service as gh
    from app.services.notify import scrub_text
    s = get_settings_local()
    db = get_db()
    token = await gh.resolve_github_token(db)
    owner_cfg = await gh.resolve_github_owner(db)
    if not token:
        raise RuntimeError("GITHUB_TOKEN not configured")
    max_files = max_files or s.github_rag_max_files
    max_bytes = max_bytes or s.github_rag_max_bytes
    owner, _, repo = full_name.partition("/")
    stats = {"created": 0, "updated": 0, "unchanged": 0, "failed": 0, "errors": []}

    async def one(source_type, source_id, title, content, **kw):
        try:
            r = await upsert_document(source_type, source_id, title, content, **kw)
            stats[r["status"]] += 1
        except Exception as e:
            stats["failed"] += 1
            stats["errors"].append(f"{source_type}:{source_id}: {e}"[:200])

    # repo metadata (public repos only — never private content)
    repos = await gh.fetch_repos(owner_cfg, token)
    meta = next((r for r in repos
                 if r.get("full_name", "").lower() == full_name.lower()), None)
    if not meta:
        raise RuntimeError(f"repository not found or not visible: {full_name}")
    if meta.get("private"):
        raise RuntimeError(f"refusing to index private repository: {full_name}")
    tracked = await db["github_repositories"].find_one({"full_name": full_name})
    if tracked and tracked.get("rag_enabled") is False:
        raise RuntimeError(f"knowledge sync is disabled for repository: {full_name}")
    branch = meta.get("default_branch", "main") or "main"
    lang = meta.get("language") or ""
    topics = meta.get("topics", []) or []
    await one("github_repository", f"github:{full_name.lower()}",
              meta.get("name", full_name),
              "\n".join(filter(None, [
                  meta.get("description") or "",
                  f"Language: {lang}" if lang else "",
                  f"Topics: {', '.join(topics)}" if topics else "",
                  f"Stars: {meta.get('stargazers_count', 0)}",
                  f"Default branch: {branch}",
              ])),
              url=meta.get("html_url"), repository=full_name, language=lang,
              branch=branch, tags=["github", "repository"] + topics[:5])

    # README (hash-deduped inside upsert_document)
    readme = await gh.fetch_readme(owner_cfg, repo, token)
    if readme.strip():
        await one("github_readme", f"github:{full_name.lower()}:readme",
                  f"{repo} — README", scrub_text(readme[:20000]),
                  url=f"{meta.get('html_url')}#readme", repository=full_name,
                  language=lang, branch=branch, tags=["github", "readme"])

    # file tree → prioritized source files
    tree = await gh.fetch_tree(owner_cfg, repo, token, branch)
    files = [t for t in tree
             if gh.is_ingestible_path(t.get("path", ""), t.get("size", 0))]
    used_bytes = len(readme)
    seen_source_ids = {
        f"github:{full_name.lower()}",
        f"github:{full_name.lower()}:readme",
        f"github:{full_name.lower()}:commits",
        f"github:{full_name.lower()}:issues",
    }
    for f in gh.prioritize_paths(files, max_files=max_files):
        if used_bytes >= max_bytes:
            break
        text = await gh.fetch_file(owner_cfg, repo, f["path"], token, branch)
        if not text.strip():
            continue
        used_bytes += len(text)
        ext = f["path"].rsplit(".", 1)[-1].lower() if "." in f["path"] else ""
        source_id = f"github:{full_name.lower()}:file:{f['path']}"
        seen_source_ids.add(source_id)
        await one("github_documentation", source_id,
                  f"{repo}/{f['path']}", scrub_text(text[:15000]),
                  url=f"{meta.get('html_url')}/blob/{branch}/{f['path']}",
                  repository=full_name, language=ext, branch=branch,
                  file_path=f["path"],
                  tags=["github", "code" if ext not in ("md", "mdx", "rst", "txt") else "docs"])

    # recent commits digest (messages only)
    commits = await gh.fetch_commits(owner_cfg, repo, token, limit=10)
    head_sha = (commits[0].get("sha") or "") if commits else ""
    if commits:
        digest = "\n".join(
            f"{c['sha']} {c['date'][:10]} {c['author']}: {c['message'].splitlines()[0] if c['message'] else ''}"
            for c in commits)
        await one("github_commit", f"github:{full_name.lower()}:commits",
                  f"{repo} — recent activity", digest,
                  url=f"{meta.get('html_url')}/commits", repository=full_name,
                  branch=branch, commit_sha=head_sha,
                  tags=["github", "activity"])

    # public issues digest (public repos only — verified above)
    issues = await gh.fetch_issues(owner_cfg, repo, token, limit=10)
    if issues:
        digest = "\n".join(
            f"#{i['number']} [{i['state']}] {i['title']}" for i in issues)
        await one("github_issue", f"github:{full_name.lower()}:issues",
                  f"{repo} — tracked issues", digest,
                  url=f"{meta.get('html_url')}/issues", repository=full_name,
                  branch=branch, tags=["github", "issues"])

    # stale cleanup: documents for files gone from the tree are deleted
    # (vectors removed first) so changed/deleted content never lingers.
    stale = 0
    async for stale_doc in db["knowledge_documents"].find({
            "repository": full_name,
            "source_type": "github_documentation",
            "source_id": {"$nin": sorted(seen_source_ids)}}):
        try:
            if await delete_document(str(stale_doc["_id"])):
                stale += 1
        except Exception as e:
            stats["failed"] += 1
            stats["errors"].append(f"github:{full_name.lower()}:stale-cleanup: {e}"[:200])
    stats["stale_removed"] = stale

    # record sync state for incremental runs (§11)
    await db["github_repositories"].update_one(
        {"full_name": full_name},
        {"$set": {"rag_last_synced_at": utcnow(),
                  "rag_last_commit_sha": head_sha or None,
                  "rag_doc_count": stats["created"] + stats["updated"]}},
        upsert=False)
    return stats
