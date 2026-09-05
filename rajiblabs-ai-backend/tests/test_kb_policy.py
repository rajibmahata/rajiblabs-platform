"""KB guardrails + hallucination control tests.

Pure policy unit tests run everywhere; live tests need MongoDB (skip
otherwise). Vector/embedding backends are faked — no OpenAI/Qdrant needed.
"""
import pytest

from app.services import kb_policy as kb


async def _live_db():
    try:
        from app.database import get_db
        db = get_db()
        await db.command("ping")
        return db
    except Exception:
        pytest.skip("MongoDB not running locally")


# ── normalization / persistence shapes (pure) ──

def test_normalize_guardrails_defaults_and_clamps():
    g = kb.normalize_guardrails(None)
    assert g["public_access"] is True and g["allow_source_code"] is False
    assert g["require_source"] is True and g["blocked_fields"] == []
    g = kb.normalize_guardrails({"public_access": 0, "blocked_fields": "a, b",
                                 "allow_urls": "yes"})
    assert g["public_access"] is False and g["blocked_fields"] == ["a", "b"]
    assert g["allow_urls"] is True


def test_normalize_hallucination_defaults_and_clamps():
    h = kb.normalize_hallucination(None)
    assert h["grounded_only"] is True and h["minimum_confidence"] == 0.0
    assert h["max_unsupported_claims"] == 0 and h["on_insufficient"] == "fallback"
    assert "verified information" in h["fallback_message"]
    h = kb.normalize_hallucination({"minimum_confidence": 9,
                                    "max_unsupported_claims": -3,
                                    "on_insufficient": "maybe",
                                    "fallback_message": "x" * 5000})
    assert h["minimum_confidence"] == 1.0 and h["max_unsupported_claims"] == 0
    assert h["on_insufficient"] == "fallback" and len(h["fallback_message"]) == 2000


def test_effective_policies_default_without_migration():
    assert kb.effective_guardrails({})["public_access"] is True
    assert kb.effective_guardrails(None)["allow_source_code"] is False
    assert kb.effective_hallucination({})["grounded_only"] is True
    custom = kb.effective_hallucination(
        {"hallucination_control": {"minimum_confidence": 0.75}})
    assert custom["minimum_confidence"] == 0.75


# ── consumer gates (pure) ──

def test_consumer_matrix():
    open_doc = {"status": "active"}
    assert kb.doc_allowed_for_consumer(open_doc, "public") == (True, "ok")
    assert kb.doc_allowed_for_consumer(open_doc, "admin") == (True, "ok")
    assert kb.doc_allowed_for_consumer(open_doc, "workbench") == (True, "ok")
    assert kb.doc_allowed_for_consumer(open_doc, "rag") == (True, "ok")
    assert kb.doc_allowed_for_consumer(open_doc, "nobody")[0] is False
    assert kb.doc_allowed_for_consumer({"status": "inactive"}, "public")[0] is False
    assert kb.doc_allowed_for_consumer({"status": "inactive"}, "admin")[0] is False


def test_public_access_restriction():
    doc = {"status": "active", "guardrails": {"public_access": False}}
    assert kb.doc_allowed_for_consumer(doc, "public")[1] == "not-public"
    assert kb.doc_allowed_for_consumer(doc, "admin")[0] is True
    assert kb.doc_allowed_for_consumer(doc, "workbench")[0] is True


def test_rag_disabled_blocks_retrieval_consumers():
    doc = {"status": "active", "guardrails": {"allow_rag": False}}
    for c in ("public", "rag", "workbench"):
        assert kb.doc_allowed_for_consumer(doc, c)[0] is False, c
    assert kb.doc_allowed_for_consumer(doc, "admin")[0] is True


def test_sensitive_blocked_everywhere_except_admin():
    doc = {"status": "active",
           "guardrails": {"contains_sensitive_data": True}}
    for c in ("public", "rag", "workbench"):
        assert kb.doc_allowed_for_consumer(doc, c)[1] == "sensitive", c
    assert kb.doc_allowed_for_consumer(doc, "admin")[0] is True


def test_source_code_rule():
    code = {"status": "active", "file_path": "src/app.py"}
    assert kb.doc_allowed_for_consumer(code, "public")[1] == "source-code"
    assert kb.doc_allowed_for_consumer(code, "admin")[0] is True
    allowed = {"status": "active", "file_path": "src/app.py",
               "guardrails": {"allow_source_code": True}}
    assert kb.doc_allowed_for_consumer(allowed, "public")[0] is True
    docs = {"status": "active", "file_path": "docs/a.md"}
    assert kb.doc_allowed_for_consumer(docs, "public")[0] is True


def test_filter_hits_fail_closed():
    hits = [{"document_id": "d1"}, {"document_id": "missing"}]
    kept = kb.filter_hits(hits, {"d1": {"status": "active"}}, "public")
    assert [h["document_id"] for h in kept] == ["d1"]  # orphan dropped


def test_strip_blocked_fields():
    doc = {"title": "t", "internal_notes": "x",
           "guardrails": {"blocked_fields": ["internal_notes"]}}
    out = kb.strip_blocked_fields(doc)
    assert "internal_notes" not in out and out["title"] == "t"


# ── hallucination validation (pure, no LLM) ──

EV = ["RajibLabs builds React frontends with FastAPI backends in Kolkata."]


def test_missing_knowledge_falls_back():
    ok, reason = kb.validate_grounding("Anything here?", [], None)
    assert (ok, reason) == (False, "no-evidence")


def test_low_confidence_falls_back():
    pol = {"minimum_confidence": 0.75}
    ok, reason = kb.validate_grounding("RajibLabs builds React frontends.", EV, pol, 0.4)
    assert (ok, reason) == (False, "low-confidence")
    ok, _ = kb.validate_grounding("RajibLabs builds React frontends.", EV, pol, 0.9)
    assert ok is True


def test_unsupported_claims_blocked_by_default():
    reply = ("RajibLabs builds React frontends. "
             "It won seventeen international awards last Tuesday.")
    ok, reason = kb.validate_grounding(reply, EV, None, 0.9)
    assert (ok, reason) == (False, "unsupported-claims")


def test_supported_answer_passes():
    reply = ("What does RajibLabs build? RajibLabs builds React frontends "
             "with FastAPI backends in Kolkata.")
    ok, reason = kb.validate_grounding(reply, EV, None, 0.9)
    assert (ok, reason) == (True, "ok")


def test_url_gate_uses_verified_only():
    cleaned, removed = kb.validate_reply_urls(
        "See https://rajiblabs.com and https://evil.example/x.",
        {"https://rajiblabs.com"})
    assert removed == 1 and "evil.example" not in cleaned


# ── admin API surface (no DB needed for auth gates + schema gate) ──

@pytest.mark.asyncio
async def test_policy_endpoints_require_auth():
    from httpx import ASGITransport, AsyncClient
    from app.main import create_app
    app = create_app()
    async with AsyncClient(transport=ASGITransport(app=app),
                           base_url="http://test") as c:
        assert (await c.get("/api/admin/rag/guardrail-schema")).status_code == 401
        assert (await c.post("/api/admin/rag/documents", json={})).status_code in (401, 422)


def test_schema_shape():
    from app.services.kb_policy import FIELD_META, DEFAULT_GUARDRAILS, DEFAULT_HALLUCINATION
    assert set(FIELD_META) == {"guardrails", "hallucination_control"}
    assert set(DEFAULT_GUARDRAILS) >= {"public_access", "allow_rag", "allow_source_code",
                                       "require_source", "blocked_fields"}
    assert set(DEFAULT_HALLUCINATION) >= {"grounded_only", "minimum_confidence",
                                          "max_unsupported_claims", "fallback_message",
                                          "on_insufficient"}


# ── live: persistence, no-reindex saves, enforcement ──

class _FakeEmb:
    def descriptor(self):
        return {"embedding_provider": "t", "embedding_model": "t",
                "embedding_version": "v1", "embedding_dim": 4}

    async def generate_embeddings(self, texts):
        return [[0.1] * 4 for _ in texts]

    async def generate_embedding(self, text):
        return [0.1] * 4


class _FakeVec:
    async def upsert_chunks(self, payloads):
        return len(payloads)

    async def search(self, vector, top_k=5, must=None, **kw):
        return []

    async def delete_document(self, document_id):
        return 1


@pytest.mark.asyncio
async def test_policy_persistence_and_no_reindex_save_live(monkeypatch):
    import app.services.rag_ingest as ri
    monkeypatch.setattr(ri, "_embedding_service", lambda: _FakeEmb())
    monkeypatch.setattr(ri, "get_vector_store", lambda: _FakeVec())
    db = await _live_db()
    try:
        r = await ri.upsert_document(
            "admin_knowledge", "e2e:policy-doc", "E2E Policy Doc",
            "RajibLabs builds React frontends for clients in Kolkata, India.",
            guardrails={"public_access": False},
            hallucination_control={"minimum_confidence": 0.75})
        assert r["status"] == "created"
        doc = await db["knowledge_documents"].find_one(
            {"source_id": "e2e:policy-doc"})
        assert doc["guardrails"]["public_access"] is False
        assert doc["hallucination_control"]["minimum_confidence"] == 0.75
        assert doc["guardrails"]["allow_rag"] is True  # defaults filled
        v0, h0 = doc["version"], doc["content_hash"]
        # metadata-only update via the same path the admin PUT uses
        from app.services import kb_policy as _kbp
        await db["knowledge_documents"].update_one(
            {"_id": doc["_id"]},
            {"$set": {"guardrails": _kbp.normalize_guardrails({"public_access": True})}})
        doc2 = await db["knowledge_documents"].find_one({"_id": doc["_id"]})
        assert doc2["version"] == v0 and doc2["content_hash"] == h0  # no re-index
        assert doc2["guardrails"]["public_access"] is True
    finally:
        await db["knowledge_documents"].delete_many({"source_id": "e2e:policy-doc"})


@pytest.mark.asyncio
async def test_public_consumer_cannot_see_restricted_live(monkeypatch):
    import app.services.rag_ingest as ri
    import app.services.rag_query as rq
    monkeypatch.setattr(ri, "_embedding_service", lambda: _FakeEmb())
    monkeypatch.setattr(ri, "get_vector_store", lambda: _FakeVec())
    db = await _live_db()
    try:
        await ri.upsert_document(
            "admin_knowledge", "e2e:restricted-doc", "E2E Restricted",
            "Zebra printing division internal costing spreadsheet data here.",
            guardrails={"public_access": False})
        doc = await db["knowledge_documents"].find_one(
            {"source_id": "e2e:restricted-doc"})
        chunk = await db["knowledge_chunks"].find_one(
            {"document_id": str(doc["_id"])})
        assert chunk is not None  # real Mongo chunk row exists

        class _VecHit(_FakeVec):
            async def search(self, vector, top_k=5, must=None, **kw):
                return [{"point_id": "p", "score": 0.99, "payload": {
                    "mongo_chunk_id": str(chunk["_id"]),
                    "document_id": str(doc["_id"]),
                    "source_type": "admin_knowledge", "title": "E2E Restricted"}}]

        import app.services.rag_query as rqmod

        class _Emb(_FakeEmb):
            async def generate_embedding(self, text):
                return [0.1] * 4

        monkeypatch.setattr(rqmod, "EmbeddingService", _Emb)
        monkeypatch.setattr(rqmod, "get_vector_store", lambda: _VecHit())
        assert await rq.retrieve("zebra printing", consumer="public") == []
        admin_hits = await rq.retrieve("zebra printing", consumer="admin")
        assert len(admin_hits) == 1 and "Zebra" in admin_hits[0]["content"]
    finally:
        await db["knowledge_documents"].delete_many({"source_id": "e2e:restricted-doc"})
        await db["knowledge_chunks"].delete_many({"document_id": {"$exists": True},
                                                  "content": {"$regex": "Zebra"}})


@pytest.mark.asyncio
async def test_concierge_complies_with_kb_policy_live(monkeypatch):
    import app.services.rag_ingest as ri
    from app.services import concierge as cg
    monkeypatch.setattr(ri, "_embedding_service", lambda: _FakeEmb())
    monkeypatch.setattr(ri, "get_vector_store", lambda: _FakeVec())
    db = await _live_db()
    token = None
    try:
        await ri.upsert_document(
            "admin_knowledge", "e2e:concierge-pol", "E2E Pol Doc",
            "RajibLabs builds React frontends for clients in Kolkata, India.",
            guardrails={"public_access": False})
        # restricted doc must not ground a public answer → fallback, no leak
        r = await cg.run_concierge_turn(
            db, "Tell me about the E2E Pol Doc zebra printing division", None, "127.0.0.1")
        assert "Zebra" not in r["reply"] and "zebra" not in r["reply"].lower()
        token = r["session_token"]
    finally:
        await db["knowledge_documents"].delete_many({"source_id": "e2e:concierge-pol"})
        if token:
            await db["customer_messages"].delete_many({"session_token": token})
            await db["customer_conversations"].delete_many({"session_token": token})
