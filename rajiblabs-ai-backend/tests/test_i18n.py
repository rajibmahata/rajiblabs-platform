"""Multilingual framework tests (20 cases).

No network, no secrets, no live Mongo: a minimal fake DB stands in for Motor,
the orchestrator is faked at the service boundary, LLM calls are counted to
prove the cache-first cost rule.
"""
import pytest
from httpx import ASGITransport, AsyncClient

from app.services import lang_service as ls
from app.services import translation_service as ts
from app.services.translation_agents import (
    TranslationAgent, TranslationQualityAgent,
)


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
                for k, v in update.get("$setOnInsert", {}).items():
                    d.setdefault(k, v)
                return
        if upsert:
            doc = dict(filt)
            doc.update(update.get("$setOnInsert", {}))
            doc.update(update.get("$set", {}))
            self.docs.append(doc)

    async def count_documents(self, q=None):
        return sum(1 for d in self.docs if _match(d, q or {}))

    async def insert_one(self, doc):
        self.docs.append(dict(doc))

        class R:
            inserted_id = "x"
        return R()

    async def delete_one(self, filt):
        before = len(self.docs)
        self.docs = [d for d in self.docs if not _match(d, filt)]
        class R:
            deleted_count = before - len(self.docs)
        return R()


class FakeDB(dict):
    def __getitem__(self, name):
        if name not in self:
            self[name] = FakeColl()
        return dict.__getitem__(self, name)


def _langs(*codes):
    base = {"en": ("English", "English", "ltr"), "bn": ("Bengali", "বাংলা", "ltr"),
            "ar": ("Arabic", "العربية", "rtl")}
    out = []
    for i, c in enumerate(codes):
        name, native, direction = base[c]
        out.append({"_id": f"id-{c}", "code": c, "name": name, "native_name": native,
                    "enabled": True, "is_default": c == "en", "direction": direction,
                    "sort_order": i + 1})
    return out


@pytest.fixture
def fakedb(monkeypatch):
    db = FakeDB()
    db["languages"] = FakeColl(_langs("en", "bn", "ar"))
    monkeypatch.setattr(ls, "get_db", lambda: db)
    monkeypatch.setattr(ts, "get_db", lambda: db)

    async def _noop(*a, **k):
        return None
    monkeypatch.setattr("app.services.notify.audit", _noop)
    ls.invalidate_cache()
    TranslationAgent.calls = 0
    return db


class FakeOrchestrator:
    configured = True

    def __init__(self, *a, **k):
        pass

    async def _complete(self, messages, max_tokens, temperature, tag):
        user = next(m["content"] for m in messages if m["role"] == "user")
        return {"provider": "openai", "model": "test-model",
                "data": {"text": f"[{tag}] {user[:60]}"}}


@pytest.fixture
def fake_ai(monkeypatch):
    monkeypatch.setattr("app.services.lead_ai.AIService", FakeOrchestrator)


# ── 1–7. language master ──

def test_seed_languages_shape():
    from app.database import SEED_LANGUAGES
    assert len(SEED_LANGUAGES) == 12
    by_code = {c[0]: c for c in SEED_LANGUAGES}
    assert by_code["en"][4] == 1 and by_code["ar"][3] == "rtl"
    assert len({c[0] for c in SEED_LANGUAGES}) == 12  # unique codes


async def test_resolve_exact(fakedb):
    assert await ls.resolve("bn", fakedb) == "bn"


async def test_resolve_base_fallback(fakedb):
    assert await ls.resolve("bn-BD", fakedb) == "bn"
    assert await ls.resolve("ar_EG", fakedb) == "ar"


async def test_resolve_unknown_and_none(fakedb):
    assert await ls.resolve("xx", fakedb) == "en"
    assert await ls.resolve(None, fakedb) == "en"
    assert await ls.resolve("", fakedb) == "en"


async def test_resolve_disabled_falls_back(fakedb):
    fakedb["languages"].docs[1]["enabled"] = False
    ls.invalidate_cache()
    assert await ls.resolve("bn", fakedb) == "en"


def test_guard_default_cannot_disable():
    with pytest.raises(ValueError):
        ls.guard_status_change({"code": "en", "is_default": True}, False)
    ls.guard_status_change({"code": "en", "is_default": True}, True)  # no-op ok


async def test_guard_delete(fakedb):
    with pytest.raises(ValueError):
        await ls.guard_delete(fakedb, {"code": "en", "is_default": True})
    fakedb["translations"].docs.append({"key": "k", "target_language": "bn"})
    with pytest.raises(ValueError):
        await ls.guard_delete(fakedb, {"code": "bn"})
    fakedb["translations"].docs.clear()
    await ls.guard_delete(fakedb, {"code": "bn"})  # unused → allowed


# ── 8–12. agents ──

def test_protect_restore_segments():
    from app.services.translation_agents import protect_segments, restore_segments
    src = "See https://rajiblabs.com/x and `code()` plus {name} and a@b.com end"
    masked, originals = protect_segments(src)
    assert "https://" not in masked and "{name}" not in masked
    assert restore_segments(masked, originals) == src


async def test_agent_refuses_secrets(fake_ai):
    with pytest.raises(ValueError):
        await TranslationAgent.translate("api_key: sk-abcdef1234567890", "bn", "Bengali")
    assert TranslationAgent.calls == 0


async def test_agent_bills_orchestrator_once(fake_ai):
    text, meta = await TranslationAgent.translate("Hello world", "bn", "Bengali")
    assert text and meta["provider"] == "openai" and meta["model"] == "test-model"
    assert TranslationAgent.calls == 1


def test_quality_flags():
    q = TranslationQualityAgent.check(
        "Visit https://a.com/x and use {name} today",
        "Rendez-vous sur place et utilisez outlook demain", "fr")
    assert "broken_urls" in q["issues"] and "incorrect_placeholders" in q["issues"]
    assert not q["passed"]


def test_quality_language_mismatch():
    bad = TranslationQualityAgent.check("আমি বাংলায় লিখছি একটি বড় বাক্য", "This is plain english text here", "bn")
    assert "language_mismatch" in bad["issues"]
    good = TranslationQualityAgent.check("Hello world, this is a longer English sentence here",
                                         "হ্যালো বিশ্ব, এটি একটি দীর্ঘ বাংলা বাক্য", "bn")
    assert good["passed"], good["issues"]


# ── 13–17. chain / cache cost rule ──

async def test_chain_approved_first_no_llm(fakedb, fake_ai):
    fakedb["translations"].docs.append({
        "key": "k1", "target_language": "bn", "translated_text": "অনুমোদিত",
        "source_hash": ts.source_hash("Hello"), "status": "approved"})
    text, status = await ts.TranslationService.get_text("k1", "Hello", "bn", db=fakedb)
    assert (text, status) == ("অনুমোদিত", "approved")
    assert TranslationAgent.calls == 0


async def test_chain_cache_promotes_to_record(fakedb, fake_ai):
    h = ts.source_hash("Hello")
    fakedb["translation_cache"].docs.append({
        "source_hash": h, "target_language": "bn", "translated_text": "ক্যাশ",
        "provider": "openai", "model": "m"})
    text, status = await ts.TranslationService.get_text("k9", "Hello", "bn", db=fakedb)
    assert (text, status) == ("ক্যাশ", "cached")
    assert TranslationAgent.calls == 0
    rec = await fakedb["translations"].find_one({"key": "k9", "target_language": "bn"})
    assert rec and rec["status"] == "generated"


async def test_chain_missing_without_generate(fakedb, fake_ai):
    text, status = await ts.TranslationService.get_text("kx", "Some new string", "bn", db=fakedb)
    assert (text, status) == ("Some new string", "missing")
    assert TranslationAgent.calls == 0


async def test_chain_generate_bills_once_then_cached(fakedb, fake_ai):
    t1, s1 = await ts.TranslationService.get_text("k2", "Ship it fast", "bn", db=fakedb, generate=True)
    assert s1 in ("generated", "needs_review") and TranslationAgent.calls == 1
    t2, s2 = await ts.TranslationService.get_text("k2", "Ship it fast", "bn", db=fakedb)
    assert t2 == t1 and s2 in ("generated", "cached") and TranslationAgent.calls == 1


async def test_chain_stale_source_serves_approved_and_flags(fakedb, fake_ai):
    fakedb["translations"].docs.append({
        "_id": "rec-k3", "key": "k3", "target_language": "bn", "translated_text": "পুরনো",
        "source_text": "Old", "source_hash": ts.source_hash("Old"), "status": "approved"})
    text, status = await ts.TranslationService.get_text("k3", "Brand new text", "bn", db=fakedb)
    assert (text, status) == ("পুরনো", "stale")
    rec = await fakedb["translations"].find_one({"key": "k3"})
    assert rec["status"] == "needs_update"
    assert TranslationAgent.calls == 0  # public path never bills


# ── 18–20. overlay, leaves, endpoints ──

async def test_localize_doc_replaces_and_skips_technical(fakedb, fake_ai):
    fakedb["projects"].docs.append({
        "slug": "p1", "name": "PestFlow", "short_description": "Pest control platform",
        "github_url": "https://github.com/rajibmahata/pestflow", "published": True})
    fakedb["translations"].docs.append({
        "key": "projects.p1.short_description", "target_language": "bn",
        "translated_text": "পোকা নিয়ন্ত্রণ প্ল্যাটফর্ম",
        "source_hash": ts.source_hash("Pest control platform"), "status": "approved"})
    doc = dict(fakedb["projects"].docs[0])
    out, stats = await ts.TranslationService.localize_doc("projects", doc, "bn", fakedb)
    assert out["short_description"] == "পোকা নিয়ন্ত্রণ প্ল্যাটফর্ম"
    assert out["github_url"] == "https://github.com/rajibmahata/pestflow"  # never translated
    assert out["slug"] == "p1" and out["_lang"] == "bn"
    assert stats["replaced"] >= 1


async def test_endpoints_require_admin():
    from app.main import create_app
    app = create_app()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        for method, path, body in (
                ("GET", "/api/admin/languages", None),
                ("POST", "/api/admin/languages", {"code": "xx", "name": "X", "native_name": "X"}),
                ("PUT", "/api/admin/languages/bn", {"name": "X"}),
                ("PATCH", "/api/admin/languages/bn/status", {"enabled": False}),
                ("DELETE", "/api/admin/languages/bn", None),
                ("GET", "/api/admin/translations", None),
                ("POST", "/api/admin/translations/generate", {"target_language": "bn"}),
                ("GET", "/api/admin/translations/coverage", None)):
            r = await c.request(method, path, json=body) if body else await c.request(method, path)
            assert r.status_code in (401, 403), (method, path, r.status_code)


async def test_chat_reply_localized_same_knowledge(fakedb, monkeypatch):
    """chat_with_lead injects the Bengali instruction; knowledge/schema unchanged."""
    from app.services import lang_service as langmod
    from app.services.lead_ai import AIService
    seen: dict = {}

    async def _fake_instruction(requested, db=None):
        return ("bn", "INS-BN: respond entirely in Bengali")

    monkeypatch.setattr(langmod, "response_instruction", _fake_instruction)

    async def _capture(self, messages, max_tokens=0, temperature=0, tag=""):
        seen["messages"] = messages
        return {"provider": "openai", "model": "m",
                "data": {"reply": "x", "lead": {}, "idea": {},
                         "missing_fields": [], "is_lead_captured": False,
                         "next_action": "continue"}}

    monkeypatch.setattr(AIService, "_complete", _capture)
    result, meta = await AIService().chat_with_lead([], "Hi", "KNOWLEDGE-BLOCK", {},
                                                    language="bn")
    systems = [m["content"] for m in seen["messages"] if m["role"] == "system"]
    assert any("INS-BN" in s for s in systems)
    assert any("KNOWLEDGE-BLOCK" in s for s in systems)  # same grounded knowledge
    assert result.reply == "x"


async def test_public_languages_no_auth_english_fallback():
    from app.main import create_app
    app = create_app()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        r = await c.get("/api/public/languages")
        assert r.status_code == 200
        codes = [l["code"] for l in r.json()]
        assert "en" in codes  # always present, DB or fallback
