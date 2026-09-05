"""RAG Knowledge System tests (20 cases, §33).

Pure-unit where possible; service boundaries faked — no network, no
secrets, no Qdrant, deterministic.
"""
import pytest

from app.services import rag_query as rq
from app.services.github_service import is_ingestible_path, prioritize_paths
from app.services.rag_chunk import chunk_text
from app.services.rag_embeddings import EmbeddingError, EmbeddingService
from app.services.rag_ingest import _scrub_resume_text, content_hash
from app.services.rag_vectors import point_id


# ── chunking (5) ──

def test_chunk_short_text_is_single_chunk():
    chunks = chunk_text("Rajib Mahata builds AI products.", max_chars=2000,
                        topic="Profile")
    assert len(chunks) == 1
    assert chunks[0]["content"].startswith("Rajib")
    assert chunks[0]["topic"] == "Profile"


def test_chunk_long_text_splits_and_grows():
    body = "\n\n".join(f"Paragraph {i} with enough words to fill space." for i in range(40))
    chunks = chunk_text(body, max_chars=400, overlap=80)
    assert len(chunks) > 2
    assert all(c["content"].strip() for c in chunks)


def test_chunk_hard_split_windows_overlap():
    # A single oversized paragraph hits the hard-split path, which slides by overlap.
    para = "abcdefghij" * 200  # 2000 chars, no whitespace
    chunks = chunk_text(para, max_chars=400, overlap=80)
    assert len(chunks) > 2
    assert chunks[1]["content"][:40] in chunks[0]["content"]


def test_chunk_code_fence_kept_whole():
    code = "```python\n" + "x = 1\n" * 30 + "```"
    chunks = chunk_text(code, max_chars=2000)
    assert len(chunks) == 1
    assert "```" in chunks[0]["content"]


def test_chunk_empty_returns_empty():
    assert chunk_text("   \n  ", max_chars=500) == []


# ── embeddings (2) + vector ids (1) ──

def test_embedding_descriptor_shape():
    d = EmbeddingService().descriptor()
    assert set(d) == {"embedding_provider", "embedding_model",
                      "embedding_version", "embedding_dim"}
    assert d["embedding_dim"] > 0


async def test_embedding_without_key_raises(monkeypatch):
    class S:
        openai_api_key = ""
        openai_enabled = False
        embedding_provider = "openai"
        embedding_model = "text-embedding-3-small"
        embedding_version = "v1"
        embedding_dim = 1536
    import app.services.rag_embeddings as emb_mod
    monkeypatch.setattr(emb_mod, "get_settings", lambda: S())
    with pytest.raises(EmbeddingError):
        await EmbeddingService().generate_embeddings(["hello"])


def test_point_id_deterministic_and_scoped():
    assert point_id("doc1", 0) == point_id("doc1", 0)
    assert point_id("doc1", 0) != point_id("doc1", 1)
    assert point_id("doc1", 0) != point_id("doc2", 0)


# ── github ingest helpers (4) ──

def test_github_secret_paths_rejected():
    for p in (".env", ".env.production", "config/credentials.json", "id_rsa",
              "deploy/secrets.yaml", "certs/key.pem", ".git/config",
              "node_modules/pkg/index.js", "dist/bundle.js"):
        assert not is_ingestible_path(p, 100), p


def test_github_binaries_rejected():
    for p in ("logo.png", "demo.mp4", "archive.zip", "doc.pdf", "app.exe",
              "model.h5", "data.parquet"):
        assert not is_ingestible_path(p, 100), p


def test_github_docs_prioritized_over_code():
    files = [{"path": "src/deep/module.py", "size": 500},
             {"path": "README.md", "size": 2000},
             {"path": "src/main.py", "size": 500},
             {"path": "docs/guide.md", "size": 1000}]
    ordered = [f["path"] for f in prioritize_paths(files, max_files=10)]
    assert ordered[0] == "README.md"  # priority names always win
    assert set(ordered) == {f["path"] for f in files}


def test_github_size_limit_and_empty():
    assert not is_ingestible_path("big.md", 600_000)
    assert not is_ingestible_path("", 10)
    assert is_ingestible_path("README.md", 5000)


# ── intent (5) ──

def test_intent_recruiter_rule():
    assert rq.classify_intent_rule("We are hiring — is Rajib open to roles?") == "RECRUITER"


def test_intent_github_rule():
    assert rq.classify_intent_rule("Show me your GitHub repositories") == "GITHUB_INFORMATION"


def test_intent_business_rule():
    assert rq.classify_intent_rule("I need to build an app for my pharmacy business") == "BUSINESS_INQUIRY"


def test_intent_unknown_returns_none():
    assert rq.classify_intent_rule("asdkjasd qwe qwe") is None


async def test_classify_intent_rule_method():
    intent, method = await rq.classify_intent("Tell me about Rajib's skills and profile")
    assert intent == "ABOUT_RAJIB" and method == "rule"


# ── ingest utils + pipeline contract (3) ──

def test_resume_scrub_removes_sensitive_lines():
    text = "Rajib Mahata — Architect\nPassport: X123\nAadhaar: 1234\nSkills: Python"
    scrubbed = _scrub_resume_text(text)
    assert "Passport" not in scrubbed and "Aadhaar" not in scrubbed
    assert "Skills: Python" in scrubbed


def test_content_hash_stable_and_sensitive():
    assert content_hash("a", "b") == content_hash("a", "b")
    assert content_hash("a", "b") != content_hash("a", "c")


async def test_answer_without_knowledge_is_ungrounded(monkeypatch):
    class S:
        rag_enabled = False
        rag_top_k = 5
        rag_min_score = 0.35
        openai_api_key = ""
        openai_enabled = False
    monkeypatch.setattr(rq, "get_settings", lambda: S())

    async def _noop(*a, **k):
        return None
    monkeypatch.setattr(rq, "audit", _noop)
    ans = await rq.answer_question("Show me your GitHub repositories",
                                   session_id="test-session")
    assert ans.grounded is False and ans.sources == []
    assert ans.intent == "GITHUB_INFORMATION"
    assert "verified information" in ans.answer


# ── qdrant wiring (regression: client must be installed + server configured) ──

def test_requirements_include_qdrant_client():
    from pathlib import Path
    req = (Path(__file__).resolve().parent.parent / "requirements.txt").read_text()
    assert "qdrant-client" in req


def test_qdrant_import_available():
    import qdrant_client  # noqa: F401  (ImportError = dashboard shows DOWN)
    from qdrant_client import AsyncQdrantClient
    assert AsyncQdrantClient is not None


async def test_qdrant_health_never_raises(monkeypatch):
    """Unreachable server → {ok: False}, never an exception (dashboard stays up)."""
    class S:
        qdrant_url = "http://127.0.0.1:9"
        qdrant_api_key = ""
        qdrant_collection = "rajiblabs_knowledge"
        embedding_dim = 1536
    import app.services.rag_vectors as vec_mod
    monkeypatch.setattr(vec_mod, "get_settings", lambda: S())
    res = await vec_mod.QdrantVectorStore().health_check()
    assert res["ok"] is False and "error" in res


async def test_qdrant_live_roundtrip():
    """Real server round-trip (skips when Qdrant isn't running locally)."""
    import httpx
    try:
        async with httpx.AsyncClient(timeout=5) as c:
            r = await c.get("http://localhost:6333/")
            assert r.status_code == 200
    except Exception:
        pytest.skip("Qdrant not running locally")
    from app.services.rag_vectors import QdrantVectorStore, point_id
    store = QdrantVectorStore()
    doc_id = "e2e-health-doc"
    try:
        n = await store.upsert_chunks([{
            "point_id": point_id(doc_id, 0), "vector": [0.1] * 1536,
            "payload": {"document_id": doc_id, "source_type": "test"}}])
        assert n == 1
        hits = await store.search([0.1] * 1536, top_k=1)
        assert hits and hits[0]["payload"]["document_id"] == doc_id
        health = await store.health_check()
        assert health["ok"] is True and health["points_count"] >= 1
    finally:
        await store.delete_document(doc_id)
