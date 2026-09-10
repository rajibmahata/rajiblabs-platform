"""Resume → Projects consolidation tests (Profile Agent owned).

No network, no LLM, no live Mongo: a minimal fake DB stands in for Motor,
extraction is stubbed, RAG sync and audit are no-ops.
"""
import pytest

from app.services import resume_projects as rp


# ── fake Mongo boundary ──

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
            for d in self.docs:
                yield d
        return gen()


class FakeColl:
    def __init__(self, docs=None):
        self.docs = docs or []

    def find(self, q=None, *a, **k):
        return FakeCursor([d for d in self.docs if _match(d, q or {})])

    async def find_one(self, q=None, *a, **k):
        for d in self.docs:
            if _match(d, q or {}):
                return d
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
