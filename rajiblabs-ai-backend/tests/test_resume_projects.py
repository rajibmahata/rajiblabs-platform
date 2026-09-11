"""Resume → Projects consolidation tests (Profile Agent owned).

No network, no LLM, no live Mongo: a minimal fake DB stands in for Motor,
extraction is stubbed, RAG sync and audit are no-ops.
"""
import pytest

from app.services import resume_projects as rp


# ── fake Mongo boundary ──

import copy as _copy


def _match(doc: dict, q: dict) -> bool:
    for k, v in (q or {}).items():
        if isinstance(v, dict):
            if "$in" in v and doc.get(k) not in v["$in"]:
                return False
            if "$ne" in v and doc.get(k) == v["$ne"]:
                return False
            continue
        if doc.get(k) != v:
            return False
    return True


class FakeCursor:
    def __init__(self, docs):
        self.docs = list(docs)

    def sort(self, *a, **k):
        key = a[0] if a else None
        if key:
            reverse = (len(a) > 1 and a[1] < 0) or k.get("direction", 1) < 0
            self.docs.sort(key=lambda d: d.get(key, 0), reverse=reverse)
        return self

    def limit(self, n):
        self.docs = self.docs[:n]
        return self

    def __aiter__(self):
        async def gen():
            # Motor returns snapshot copies — caller mutation must not leak
            # back into the collection (matters for prev-vs-new comparisons).
            for d in self.docs:
                yield _copy.deepcopy(d)
        return gen()


class FakeColl:
    def __init__(self, docs=None):
        self.docs = docs or []

    def find(self, q=None, *a, **k):
        return FakeCursor([d for d in self.docs if _match(d, q or {})])

    async def find_one(self, q=None, *a, **k):
        for d in self.docs:
            if _match(d, q or {}):
                return _copy.deepcopy(d)
        return None

    async def update_one(self, filt, update, upsert=False):
        for d in self.docs:
            if _match(d, filt):
                d.update(update.get("$set", {}))
                return
        if upsert:
            doc = dict(filt)
            doc.update(update.get("$set", {}))
            self.docs.append(doc)

    async def insert_one(self, doc):
        import copy
        stored = copy.deepcopy(dict(doc))
        stored.setdefault("_id", f"fake-{len(self.docs)}")
        self.docs.append(stored)

        class R:
            inserted_id = stored["_id"]
        return R()

    async def delete_many(self, filt):
        self.docs = [d for d in self.docs if not _match(d, filt)]

    async def count_documents(self, q=None):
        return sum(1 for d in self.docs if _match(d, q or {}))


class FakeDB(dict):
    def __getitem__(self, name):
        if name not in self:
            self[name] = FakeColl()
        return dict.__getitem__(self, name)


@pytest.fixture
def fakedb(monkeypatch):
    db = FakeDB()

    async def _noop(*a, **k):
        return None

    monkeypatch.setattr("app.services.notify.audit", _noop)
    monkeypatch.setattr("app.services.resume_projects.audit", _noop)
    monkeypatch.setattr("app.services.rag_ingest.upsert_document", _noop)
    return db


@pytest.fixture
def canned(monkeypatch):
    """Stub extraction: two projects, one repeated across versions."""
    extracted = [
        {"name": "PestFlow", "short_description": "Enterprise pest control SaaS platform with microservices on Azure",
         "technologies": ["React", ".NET"], "client": "ABC Corp", "period": "2022-2024"},
        {"name": "Tiny Tool", "short_description": "Small internal tool",
         "technologies": ["Python"], "client": "", "period": ""},
    ]

    async def _fake(text):
        return [dict(e) for e in extracted]

    monkeypatch.setattr(rp, "extract_projects_from_text", _fake)


def _resume(version, text="x" * 200):
    return {"_id": f"r{version}", "version": version, "extracted_text": text,
            "status": "published" if version == 2 else "archived",
            "active": version == 2}


# ── pure unit tests ──

def test_portfolio_score_rewards_evidence_scale():
    high = rp._portfolio_score(
        "PestFlow", "Enterprise pest control SaaS platform with microservices on Azure",
        ["React", ".NET", "Azure", "Kubernetes"], 3, True, True, "ABC Corp")
    low = rp._portfolio_score("Tiny", "Small tool", ["Python"], 1, False, False, "")
    assert high >= 50 and low < 50


async def test_criteria_defaults_match_codebase_gates(fakedb):
    criteria = await rp.get_portfolio_criteria(fakedb)
    assert criteria == {"score_threshold": 50, "auto_create_draft": False}


def test_merge_evidence_dedupes_and_caps():
    out = rp._merge_evidence(
        [{"source": "resume", "label": "Resume"}],
        [{"source": "resume", "label": "Resume"},
         {"source": "github", "label": "u/r", "url": "https://github.com/u/r"}])
    assert [(e["source"], e["label"]) for e in out] == [("resume", "Resume"), ("github", "u/r")]


def test_normalize_slug():
    assert rp._slug("ReturnGuard AI - Omnichannel") == "returnguard-ai-omnichannel"


# ── consolidation flow (fake DB) ──

async def test_create_dedupes_across_resume_versions(fakedb, canned):
    fakedb["resumes"] = FakeColl([_resume(1), _resume(2)])
    fakedb["github_repositories"] = FakeColl([{
        "_id": "g1", "name": "pestflow-app", "full_name": "rajibmahata/pestflow-app",
        "html_url": "https://github.com/rajibmahata/pestflow-app",
        "description": "Enterprise pest control SaaS for large service companies with scheduling and billing.",
        "language": "TypeScript", "topics": ["saas", "react"], "is_private": False}])
    stats = await rp.consolidate_resume_projects(fakedb, triggered_by="test")
    assert stats["resumes_scanned"] == 2
    assert stats["deduped"] == 2  # PestFlow merged across versions, not duplicated
    assert stats["created"] == 2
    pest = await fakedb["projects"].find_one({"slug": "pestflow"})
    assert pest["github_url"] == "https://github.com/rajibmahata/pestflow-app"
    assert "TypeScript" in pest["technologies"]  # enriched from stored repo
    sources = {e["source"] for e in pest["evidence"]}
    assert {"resume", "github"} <= sources
    assert pest["portfolio_worthy"] is True and pest["portfolio_score"] >= 60
    tiny = await fakedb["projects"].find_one({"slug": "tiny-tool"})
    assert tiny["portfolio_worthy"] is False


async def test_rerun_idempotent_without_changes(fakedb, canned):
    fakedb["resumes"] = FakeColl([_resume(1), _resume(2)])
    first = await rp.consolidate_resume_projects(fakedb, triggered_by="test")
    assert first["created"] == 2
    second = await rp.consolidate_resume_projects(fakedb, triggered_by="test")
    assert second["created"] == 0 and second["updated"] == 0


async def test_locked_fields_never_overwritten(fakedb, canned, monkeypatch):
    fakedb["resumes"] = FakeColl([_resume(2)])
    fakedb["projects"] = FakeColl([{
        "_id": "p1", "slug": "pestflow", "name": "PestFlow",
        "short_description": "Admin-written description",
        "technologies": ["AdminTech"], "locked_fields": ["short_description", "technologies"],
        "status": "published", "evidence": []}])

    async def _one(text):
        return [{"name": "PestFlow", "short_description": "Resume description that must not win",
                 "technologies": ["React"], "client": "", "period": ""}]

    monkeypatch.setattr(rp, "extract_projects_from_text", _one)
    await rp.consolidate_resume_projects(fakedb, triggered_by="test")
    pest = await fakedb["projects"].find_one({"slug": "pestflow"})
    assert pest["short_description"] == "Admin-written description"
    assert pest["technologies"] == ["AdminTech"]
    # agent-owned evidence still accumulates
    assert any(e["source"] == "resume" for e in pest["evidence"])


async def test_no_github_url_invention(fakedb, canned):
    fakedb["resumes"] = FakeColl([_resume(2)])
    fakedb["github_repositories"] = FakeColl([])
    await rp.consolidate_resume_projects(fakedb, triggered_by="test")
    tiny = await fakedb["projects"].find_one({"slug": "tiny-tool"})
    assert tiny["github_url"] is None and tiny["live_url"] is None


async def test_portfolio_autodraft_opt_in(fakedb, canned):
    fakedb["resumes"] = FakeColl([_resume(2)])
    fakedb["site_settings"] = FakeColl([{
        "_id": "s1", "key": "portfolio_criteria",
        "value": {"score_threshold": 10, "auto_create_draft": True}}])
    stats = await rp.consolidate_resume_projects(fakedb, triggered_by="test")
    assert stats["portfolio_drafts"] >= 1
    draft = await fakedb["portfolio"].find_one({"slug": "pestflow"})
    assert draft and draft["status"] == "draft"


async def test_portfolio_autodraft_off_by_default(fakedb, canned):
    fakedb["resumes"] = FakeColl([_resume(2)])
    await rp.consolidate_resume_projects(fakedb, triggered_by="test")
    assert await fakedb["portfolio"].find_one({"slug": "pestflow"}) is None


async def test_empty_resume_never_reextracted(fakedb, monkeypatch):
    """Consolidate must not call extract_and_store for already-attempted
    empty resumes (this mutual recursion was an infinite loop)."""
    import app.services.resume_text as rt
    from datetime import datetime, timezone
    fakedb["resumes"] = FakeColl([{
        "_id": "e1", "version": 1, "extracted_text": "",
        "extracted_at": datetime.now(timezone.utc), "status": "archived"}])
    calls = []

    async def _boom(rid):
        calls.append(rid)
        return ""

    monkeypatch.setattr(rt, "extract_and_store", _boom)
    stats = await rp.consolidate_resume_projects(fakedb, triggered_by="test")
    assert calls == []
    assert stats["skipped"] == 1


async def test_role_linked_from_matching_career(fakedb, canned, monkeypatch):
    fakedb["resumes"] = FakeColl([_resume(2)])
    fakedb["profiles"] = FakeColl([{
        "_id": "prof", "career": [
            {"company": "ABC Corp", "role": "Solutions Architect",
             "period": "2022-2024", "client": "ABC Corp"}]}])

    async def _one(text):
        return [{"name": "PestFlow", "short_description": "Enterprise platform",
                 "technologies": [], "client": "ABC Corp", "period": ""}]

    monkeypatch.setattr(rp, "extract_projects_from_text", _one)
    await rp.consolidate_resume_projects(fakedb, triggered_by="test")
    pest = await fakedb["projects"].find_one({"slug": "pestflow"})
    assert pest["role"] == "Solutions Architect (2022-2024)"


async def test_role_empty_without_career_match(fakedb, canned, monkeypatch):
    fakedb["resumes"] = FakeColl([_resume(2)])
    fakedb["profiles"] = FakeColl([{"_id": "prof", "career": []}])

    async def _one(text):
        return [{"name": "PestFlow", "short_description": "Enterprise platform",
                 "technologies": [], "client": "Unknown Client", "period": ""}]

    monkeypatch.setattr(rp, "extract_projects_from_text", _one)
    await rp.consolidate_resume_projects(fakedb, triggered_by="test")
    pest = await fakedb["projects"].find_one({"slug": "pestflow"})
    assert pest["role"] == ""  # never invented


async def test_history_indexed_admin_only_and_orphans_swept(monkeypatch):
    import app.services.rag_ingest as ri
    db = FakeDB()
    db["profiles"] = FakeColl([])
    db["resumes"] = FakeColl([
        {"_id": "active1", "version": 2, "active": True,
         "extracted_text": "Active resume text here"},
        {"_id": "old1", "version": 1, "active": False,
         "extracted_text": "Historical resume text here"},
        {"_id": "empty1", "version": 0, "active": False, "extracted_text": ""},
    ])
    db["knowledge_documents"] = FakeColl([
        {"_id": "k-gone", "source_type": "resume", "source_id": "resume:file:deleted9",
         "status": "active"},
        {"_id": "k-live", "source_type": "resume", "source_id": "resume:file:active1",
         "status": "active"},
    ])
    calls = []
    deactivated = []

    async def _fake_upsert(source_type, source_id, title, content, **kw):
        calls.append({"source_id": source_id,
                      "guardrails": kw.get("guardrails"),
                      "tags": kw.get("tags")})
        return {"status": "created"}

    async def _fake_deactivate(document_id):
        deactivated.append(document_id)
        return True

    monkeypatch.setattr(ri, "upsert_document", _fake_upsert)
    monkeypatch.setattr(ri, "deactivate_document", _fake_deactivate)
    monkeypatch.setattr(ri, "get_db", lambda: db)
    stats = await ri.ingest_resume()
    by_id = {c["source_id"]: c for c in calls}
    # active resume indexed publicly (no guardrails override)
    assert "resume:file:active1" in by_id
    assert by_id["resume:file:active1"]["guardrails"] is None
    # historical resume indexed admin-only
    assert "resume:history:old1" in by_id
    assert by_id["resume:history:old1"]["guardrails"] == {"public_access": False}
    # empty historical resume skipped
    assert not any("empty1" in sid for sid in by_id)
    # orphan for deleted resume swept, live docs untouched
    assert deactivated == ["k-gone"]
    assert stats["created"] >= 2


async def test_extract_triggers_skill_sync(tmp_path, monkeypatch):
    import app.services.resume_text as rt
    db = FakeDB()
    pdf = tmp_path / "r.pdf"
    pdf.write_bytes(b"%PDF-1.4\n1 0 obj\n<<>>\nendobj\ntrailer\n<<>>\n%%EOF\nhello")
    db["resumes"] = FakeColl([{
        "_id": "rx", "legacy_id": "rx", "version": 1, "active": False,
        "status": "archived", "stored_path": str(pdf),
        # pre-existing text differs from the (empty) re-extraction → changed
        "extracted_text": "previous text"}])
    monkeypatch.setattr(rt, "get_db", lambda: db)
    seen = {}

    async def _fake_sync(triggered_by=""):
        seen["by"] = triggered_by
        return {"created": 0}

    async def _fake_consolidate(_db=None, triggered_by=""):
        return {}

    monkeypatch.setattr("app.services.skill_intelligence.sync_skills", _fake_sync)
    # consolidate is imported inside extract_and_store; patch at its home module
    import app.services.resume_projects as _rp
    monkeypatch.setattr(_rp, "consolidate_resume_projects", _fake_consolidate)
    await rt.extract_and_store("rx")
    assert seen.get("by") == "resume:rx"


async def test_noop_reextract_skips_downstream_storm(tmp_path, monkeypatch):
    """Empty re-extraction with unchanged text must not fan out (no loop)."""
    import app.services.resume_text as rt
    db = FakeDB()
    pdf = tmp_path / "r.pdf"
    pdf.write_bytes(b"%PDF-1.4\n1 0 obj\n<<>>\nendobj\ntrailer\n<<>>\n%%EOF\nhello")
    db["resumes"] = FakeColl([{
        "_id": "rx", "legacy_id": "rx", "version": 1, "active": False,
        "status": "archived", "stored_path": str(pdf), "extracted_text": ""}])
    monkeypatch.setattr(rt, "get_db", lambda: db)
    calls = []

    async def _fake_sync(triggered_by=""):
        calls.append(("sync", triggered_by))
        return {}

    async def _fake_consolidate(_db=None, triggered_by=""):
        calls.append(("consolidate", triggered_by))
        return {}

    monkeypatch.setattr("app.services.skill_intelligence.sync_skills", _fake_sync)
    import app.services.resume_projects as _rp
    monkeypatch.setattr(_rp, "consolidate_resume_projects", _fake_consolidate)
    await rt.extract_and_store("rx")
    assert calls == []
