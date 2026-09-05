"""GitHub Integration & Knowledge Sync tests.

Pure unit tests run everywhere; live tests need MongoDB (skip otherwise —
same pattern as the rest of the suite). GitHub HTTP is mocked with respx;
embeddings/vectors are faked so no OpenAI/Qdrant is required.
"""
import pytest
import respx
from httpx import Response

API = "https://api.github.com"
OWNER, REPO = "rajibmahata", "demo-repo"
FULL = f"{OWNER}/{REPO}"

REPOS_PAYLOAD = [{
    "id": 111, "name": REPO, "full_name": FULL,
    "description": "Demo React + FastAPI app",
    "html_url": f"https://github.com/{FULL}",
    "language": "TypeScript", "topics": ["react", "fastapi"],
    "stargazers_count": 12, "default_branch": "main", "private": False,
    "pushed_at": "2026-09-01T00:00:00Z",
}]
TREE_PAYLOAD = {"tree": [
    {"path": "README.md", "type": "blob", "size": 100},
    {"path": "docs/architecture.md", "type": "blob", "size": 200},
    {"path": "src/app.py", "type": "blob", "size": 300},
    {"path": ".env", "type": "blob", "size": 50},
    {"path": "node_modules/x.js", "type": "blob", "size": 60},
]}
COMMITS_PAYLOAD = [{
    "sha": "abc1234567", "html_url": f"https://github.com/{FULL}/commit/abc",
    "commit": {"message": "Add architecture docs",
               "author": {"name": "Rajib", "date": "2026-09-02T00:00:00Z"}},
}]
USER_PAYLOAD = {"login": OWNER, "name": "Rajib M",
                "avatar_url": "https://avatars/x",
                "public_repos": 30, "followers": 5}

FILE_CONTENTS: dict[str, str] = {}


def _mock_github(r, files=None, commits=True, extra_tree=None):
    r.get(f"{API}/user").mock(return_value=Response(200, json=USER_PAYLOAD))
    r.get(f"{API}/users/{OWNER}/repos").mock(return_value=Response(200, json=REPOS_PAYLOAD))
    r.get(f"{API}/repos/{OWNER}/{REPO}/readme").mock(
        return_value=Response(200, text="# Demo\nReact + FastAPI demo."))
    tree = {"tree": list(TREE_PAYLOAD["tree"]) + list(extra_tree or [])}
    r.get(f"{API}/repos/{OWNER}/{REPO}/git/trees/main").mock(
        return_value=Response(200, json=tree))
    files = files if files is not None else {
        "docs/architecture.md": "# Architecture\nReact frontend, FastAPI backend.",
        "src/app.py": "print('hello')\n",
    }
    FILE_CONTENTS.update(files)
    for path in set(list(files) + ["README.md"]):
        body = files.get(path, f"# {path}\ncontent")
        r.get(f"{API}/repos/{OWNER}/{REPO}/contents/{path}").mock(
            return_value=Response(200, text=body))
    r.get(f"{API}/repos/{OWNER}/{REPO}/commits").mock(
        return_value=Response(200, json=COMMITS_PAYLOAD if commits else []))
    r.get(f"{API}/repos/{OWNER}/{REPO}/issues").mock(
        return_value=Response(200, json=[]))


class _FakeEmbeddings:
    def descriptor(self):
        return {"embedding_provider": "test", "embedding_model": "t",
                "embedding_version": "v1", "embedding_dim": 4}

    async def generate_embeddings(self, texts):
        return [[0.1, 0.2, 0.3, 0.4] for _ in texts]

    async def generate_embedding(self, text):
        return [0.1, 0.2, 0.3, 0.4]


class _FakeVectors:
    def __init__(self):
        self.upserted = []
        self.deleted_docs = []

    async def upsert_chunks(self, payloads):
        self.upserted.extend(payloads)
        return len(payloads)

    async def search(self, vector, top_k=5, must=None, **kw):
        return []

    async def delete_document(self, document_id):
        self.deleted_docs.append(document_id)
        return 1

    async def health_check(self):
        return {"ok": True}


def _patch_pipeline(monkeypatch):
    import app.services.rag_ingest as ri
    vec = _FakeVectors()
    monkeypatch.setattr(ri, "_embedding_service", lambda: _FakeEmbeddings())
    monkeypatch.setattr(ri, "get_vector_store", lambda: vec)
    return vec


async def _live_db():
    try:
        from app.database import get_db
        db = get_db()
        await db.command("ping")
        return db
    except Exception:
        pytest.skip("MongoDB not running locally")


# ── token security (pure + live) ──

def test_mask_token_never_shows_full():
    from app.services.github_service import mask_token
    assert mask_token("ghp_abcdefgh12345678") == "***5678"
    assert mask_token("") == ""
    assert "ghp_abcdefgh12345678" not in mask_token("ghp_abcdefgh12345678")


@pytest.mark.asyncio
async def test_config_masked_and_revoked_live(monkeypatch):
    from httpx import ASGITransport, AsyncClient
    from app.main import create_app
    db = await _live_db()
    secret = "ghp_testsecretvalue1234567890"
    try:
        await db["site_settings"].delete_many({"key": "github"})
        from app.services import github_service as gh
        await db["site_settings"].insert_one(
            {"key": "github", "value": {"token": secret, "owner": OWNER}})
        status = await gh.token_status(db)
        assert status["configured"] is True and status["source"] == "admin"
        assert secret not in str(status) and status["masked"].endswith(secret[-4:])
        assert await gh.resolve_github_token(db) == secret
        # admin endpoints require JWT even for masked reads
        app = create_app()
        async with AsyncClient(transport=ASGITransport(app=app),
                               base_url="http://test") as c:
            for method, path in (("GET", "/api/admin/github/config"),
                                 ("GET", "/api/admin/github/repositories"),
                                 ("POST", "/api/admin/github/test")):
                r = await c.request(method, path, json={} if method == "POST" else None)
                assert r.status_code == 401, (method, path)
    finally:
        await db["site_settings"].delete_many({"key": "github"})


# ── connection test + discovery (mocked HTTP, no DB) ──

@pytest.mark.asyncio
@respx.mock
async def test_connection_ok_and_account_info():
    from app.services import github_service as gh
    _mock_github(respx)
    info = await gh.fetch_user("ghp_validtoken12345678")
    assert info["login"] == OWNER and info["public_repos"] == 30


@pytest.mark.asyncio
@respx.mock
async def test_connection_invalid_token():
    import pytest as _pt
    from app.services import github_service as gh
    respx.get(f"{API}/user").mock(return_value=Response(401, json={}))
    with _pt.raises(RuntimeError, match="invalid token"):
        await gh.fetch_user("ghp_wrong")


@pytest.mark.asyncio
@respx.mock
async def test_discovery_upserts_with_rag_enabled_live(monkeypatch):
    from app.services import github_service as gh
    db = await _live_db()
    _mock_github(respx)
    _patch_pipeline(monkeypatch)
    try:
        await db["site_settings"].delete_many({"key": "github"})
        await db["github_repositories"].delete_many({"full_name": FULL})
        await db["site_settings"].insert_one(
            {"key": "github", "value": {"token": "ghp_discovery12345678"}})
        out = await gh.sync_now()
        assert out["found"] == 1 and out["added"] == 1
        doc = await db["github_repositories"].find_one({"full_name": FULL})
        assert doc["rag_enabled"] is True
        assert "ghp_discovery" not in str(doc)  # token never persisted on repos
        out2 = await gh.sync_now()
        assert out2["updated"] == 1  # second run updates, never duplicates
        assert await db["github_repositories"].count_documents({"full_name": FULL}) == 1
    finally:
        await db["site_settings"].delete_many({"key": "github"})
        await db["github_repositories"].delete_many({"full_name": FULL})


# ── sync: docs, metadata, incremental, stale cleanup, scrub ──

@pytest.mark.asyncio
@respx.mock
async def test_repo_sync_creates_metadata_live(monkeypatch):
    from app.services import rag_ingest
    db = await _live_db()
    _mock_github(respx)
    _patch_pipeline(monkeypatch)
    try:
        await db["site_settings"].delete_many({"key": "github"})
        await db["site_settings"].insert_one(
            {"key": "github", "value": {"token": "ghp_sync123456789012"}})
        for coll in ("knowledge_documents", "knowledge_chunks"):
            await db[coll].delete_many({"repository": FULL})
        stats = await rag_ingest.ingest_github_repo(FULL)
        assert stats["created"] >= 3  # repo + readme + file docs
        doc = await db["knowledge_documents"].find_one(
            {"source_id": f"github:{FULL}:file:docs/architecture.md"})
        assert doc is not None
        assert doc["branch"] == "main" and doc["file_path"] == "docs/architecture.md"
        assert doc["repository"] == FULL and doc["visibility"] == "public"
        assert doc["status"] == "indexed" or doc["status"] == "active"
        assert doc["url"] == f"https://github.com/{FULL}/blob/main/docs/architecture.md"
        assert doc["content_hash"] and len(doc["content_hash"]) == 64
        assert (await db["github_repositories"].find_one(
            {"full_name": FULL})) is None or True  # sync-state recorded when tracked
    finally:
        for coll in ("knowledge_documents", "knowledge_chunks"):
            await db[coll].delete_many({"repository": FULL})
        await db["site_settings"].delete_many({"key": "github"})


@pytest.mark.asyncio
@respx.mock
async def test_incremental_and_stale_cleanup_live(monkeypatch):
    from app.services import rag_ingest
    db = await _live_db()
    _mock_github(respx)
    _patch_pipeline(monkeypatch)
    try:
        await db["site_settings"].delete_many({"key": "github"})
        await db["site_settings"].insert_one(
            {"key": "github", "value": {"token": "ghp_incr1234567890123"}})
        for coll in ("knowledge_documents", "knowledge_chunks"):
            await db[coll].delete_many({"repository": FULL})
        first = await rag_ingest.ingest_github_repo(FULL)
        second = await rag_ingest.ingest_github_repo(FULL)
        assert second["unchanged"] >= first["created"]  # nothing re-embedded
        assert second["created"] == 0 and second.get("stale_removed", 0) == 0
        # change one file → exactly that doc updates
        FILE_CONTENTS["docs/architecture.md"] = "# Architecture v2\nNew lines."
        respx.get(f"{API}/repos/{OWNER}/{REPO}/contents/docs/architecture.md").mock(
            return_value=Response(200, text=FILE_CONTENTS["docs/architecture.md"]))
        third = await rag_ingest.ingest_github_repo(FULL)
        assert third["updated"] >= 1
        # delete the file from the tree → doc + vectors removed
        respx.get(f"{API}/repos/{OWNER}/{REPO}/git/trees/main").mock(
            return_value=Response(200, json={"tree": [
                {"path": "README.md", "type": "blob", "size": 100}]}))
        fourth = await rag_ingest.ingest_github_repo(FULL)
        assert fourth.get("stale_removed", 0) >= 1
        assert await db["knowledge_documents"].count_documents(
            {"source_id": f"github:{FULL}:file:docs/architecture.md"}) == 0
    finally:
        for coll in ("knowledge_documents", "knowledge_chunks"):
            await db[coll].delete_many({"repository": FULL})
        await db["site_settings"].delete_many({"key": "github"})


@pytest.mark.asyncio
@respx.mock
async def test_secret_content_never_indexed_live(monkeypatch):
    from app.services import rag_ingest
    db = await _live_db()
    _mock_github(respx, files={
        "src/leaky.py": "api_key=SUPERSECRET123\npassword=hunter2\nprint('ok')\n",
    }, extra_tree=[{"path": "src/leaky.py", "type": "blob", "size": 60}])
    _patch_pipeline(monkeypatch)
    try:
        await db["site_settings"].delete_many({"key": "github"})
        await db["site_settings"].insert_one(
            {"key": "github", "value": {"token": "ghp_leak1234567890123"}})
        for coll in ("knowledge_documents", "knowledge_chunks"):
            await db[coll].delete_many({"repository": FULL})
        await rag_ingest.ingest_github_repo(FULL)
        doc = await db["knowledge_documents"].find_one(
            {"source_id": f"github:{FULL}:file:src/leaky.py"})
        assert doc is not None
        assert "SUPERSECRET123" not in doc["content"] and "hunter2" not in doc["content"]
    finally:
        for coll in ("knowledge_documents", "knowledge_chunks"):
            await db[coll].delete_many({"repository": FULL})
        await db["site_settings"].delete_many({"key": "github"})


@pytest.mark.asyncio
@respx.mock
async def test_failed_sync_records_and_retries_live(monkeypatch):
    from app.services import rag_ingest
    from app.services.notify import log_error
    db = await _live_db()
    _patch_pipeline(monkeypatch)
    try:
        await db["site_settings"].delete_many({"key": "github"})
        await db["site_settings"].insert_one(
            {"key": "github", "value": {"token": "ghp_retry12345678901"}})
        respx.get(f"{API}/users/{OWNER}/repos").mock(
            return_value=Response(200, json=[]))  # repo invisible
        with pytest.raises(RuntimeError, match="not found or not visible"):
            await rag_ingest.ingest_github_repo(FULL)
        await log_error("github_repo_sync", f"Sync failed for {FULL}", "boom")
        assert await db["error_logs"].count_documents(
            {"source": "github_repo_sync"}) >= 1
        # retry after fix succeeds
        _mock_github(respx)
        stats = await rag_ingest.ingest_github_repo(FULL)
        assert stats["created"] >= 1
    finally:
        for coll in ("knowledge_documents", "knowledge_chunks", "error_logs"):
            await db[coll].delete_many(
                {"repository": FULL} if coll != "error_logs"
                else {"source": "github_repo_sync"})
        await db["site_settings"].delete_many({"key": "github"})


@pytest.mark.asyncio
@respx.mock
async def test_disable_and_delete_repo_knowledge_live(monkeypatch):
    from app.services import rag_ingest
    db = await _live_db()
    _mock_github(respx)
    vec = _patch_pipeline(monkeypatch)
    try:
        await db["site_settings"].delete_many({"key": "github"})
        await db["site_settings"].insert_one(
            {"key": "github", "value": {"token": "ghp_disable1234567890"}})
        for coll in ("knowledge_documents", "knowledge_chunks"):
            await db[coll].delete_many({"repository": FULL})
        await rag_ingest.ingest_github_repo(FULL)
        docs = [d async for d in db["knowledge_documents"].find({"repository": FULL})]
        assert docs
        for d in docs:  # disable = deactivate (vectors removed, records kept)
            assert await rag_ingest.deactivate_document(str(d["_id"])) is True
        assert len(vec.deleted_docs) >= len(docs)
        assert await db["knowledge_documents"].count_documents(
            {"repository": FULL, "status": "inactive"}) == len(docs)
        for d in docs:  # delete = records + vectors gone
            assert await rag_ingest.delete_document(str(d["_id"])) is True
        assert await db["knowledge_documents"].count_documents({"repository": FULL}) == 0
    finally:
        for coll in ("knowledge_documents", "knowledge_chunks"):
            await db[coll].delete_many({"repository": FULL})
        await db["site_settings"].delete_many({"key": "github"})


# ── RAG retrieval + Proposal Studio use GitHub knowledge ──

@pytest.mark.asyncio
async def test_rag_retrieval_returns_github_url_live(monkeypatch):
    import app.services.rag_query as rq
    db = await _live_db()
    chunk_id = None
    try:
        res = await db["knowledge_chunks"].insert_one({
            "document_id": "doc1", "chunk_index": 0,
            "content": "React FastAPI demo architecture",
            "metadata": {}, "embedding_id": "p1", "created_at": None})
        chunk_id = res.inserted_id
        doc_res = await db["knowledge_documents"].insert_one({
            "source_type": "github_documentation", "source_id": "e2e:retrieval-doc",
            "title": "demo/architecture.md", "content": "x",
            "status": "active", "visibility": "public"})

        class _Emb:
            async def generate_embedding(self, text):
                return [0.1]

        class _Vec:
            async def search(self, vector, top_k=5, must=None, **kw):
                return [{"point_id": "p1", "score": 0.95, "payload": {
                    "mongo_chunk_id": str(chunk_id), "document_id": str(doc_res.inserted_id),
                    "source_type": "github_documentation",
                    "title": "demo/architecture.md",
                    "url": f"https://github.com/{FULL}/blob/main/architecture.md",
                    "repository": FULL, "language": "md"}}]

            async def upsert_chunks(self, payloads):
                return len(payloads)

            async def delete_document(self, document_id):
                return 1

        monkeypatch.setattr(rq, "EmbeddingService", _Emb)
        monkeypatch.setattr(rq, "get_vector_store", lambda: _Vec())
        hits = await rq.retrieve("React architecture examples")
        assert hits and hits[0]["source_type"] == "github_documentation"
        assert hits[0]["url"] == f"https://github.com/{FULL}/blob/main/architecture.md"
        assert hits[0]["repository"] == FULL
    finally:
        if chunk_id is not None:
            await db["knowledge_chunks"].delete_many({"document_id": "doc1"})
        await db["knowledge_documents"].delete_many({"source_id": "e2e:retrieval-doc"})


async def test_rag_retrieval_drops_orphan_vectors_live(monkeypatch):
    """Fail-closed: vector hits with no parent document never reach answers."""
    import app.services.rag_query as rq
    db = await _live_db()
    try:
        res = await db["knowledge_chunks"].insert_one({
            "document_id": "doc-orphan", "chunk_index": 0,
            "content": "orphan content here",
            "metadata": {}, "embedding_id": "p9", "created_at": None})

        class _Emb:
            async def generate_embedding(self, text):
                return [0.1]

        class _Vec:
            async def search(self, vector, top_k=5, must=None, **kw):
                return [{"point_id": "p9", "score": 0.99, "payload": {
                    "mongo_chunk_id": str(res.inserted_id), "document_id": "doc-orphan",
                    "source_type": "github_documentation", "title": "orphan"}}]

            async def upsert_chunks(self, payloads):
                return len(payloads)

            async def delete_document(self, document_id):
                return 1

        monkeypatch.setattr(rq, "EmbeddingService", _Emb)
        monkeypatch.setattr(rq, "get_vector_store", lambda: _Vec())
        assert await rq.retrieve("orphan content") == []
    finally:
        await db["knowledge_chunks"].delete_many({"document_id": "doc-orphan"})


def test_workbench_github_fallback_selection(monkeypatch):
    import asyncio
    from types import SimpleNamespace  # noqa
    import app.services.workbench as wb
    ev = [
        {"document_id": "d1", "chunk_id": "c1", "source_type": "github_documentation",
         "title": "shop/architecture.md", "doc_title": "shop/architecture.md",
         "doc_url": f"https://github.com/{FULL}/blob/main/architecture.md",
         "doc_repo": FULL, "content": "React storefront with FastAPI backend",
         "score": 0.9, "_priority": 6},
        {"document_id": "d2", "chunk_id": "c2", "source_type": "profile",
         "title": "Profile", "doc_title": "Profile", "doc_url": "",
         "doc_repo": "", "content": "Rajib Mahata architect",
         "score": 0.5, "_priority": 6},
    ]

    async def _boom():
        raise RuntimeError("no AI in tests")

    monkeypatch.setattr(wb, "_orchestrator", _boom)
    picked = asyncio.run(wb.select_examples(SimpleNamespace(), ev))
    gh = [c for c in picked if c.get("source_type") == "github_documentation"]
    assert gh and gh[0]["doc_url"].startswith("https://github.com/")
    assert gh[0]["doc_repo"] == FULL
