"""Portfolio + products catalog tests: CRUD, search/filter/sort/page, toggles,
uploads, video URLs, RAG lifecycle, auth. Live tests skip without MongoDB."""
import io

import pytest
from httpx import ASGITransport, AsyncClient


async def _live_db():
    try:
        from app.database import get_db
        db = get_db()
        await db.command("ping")
        return db
    except Exception:
        pytest.skip("MongoDB not running locally")


def _authed(app):
    from app.auth.dependencies import require_admin
    app.dependency_overrides[require_admin] = lambda: "admin@test.local"
    return app


# ── pure: video embed validation ──

def test_video_embed_url_providers():
    from app.routers.legacy import video_embed_url
    assert video_embed_url("https://www.youtube.com/watch?v=dQw4w9WgXcQ") == \
        "https://www.youtube.com/embed/dQw4w9WgXcQ"
    assert video_embed_url("https://youtu.be/dQw4w9WgXcQ?t=3") == \
        "https://www.youtube.com/embed/dQw4w9WgXcQ"
    assert video_embed_url("https://www.youtube.com/shorts/dQw4w9WgXcQ") == \
        "https://www.youtube.com/embed/dQw4w9WgXcQ"
    assert video_embed_url("https://vimeo.com/12345678") == \
        "https://player.vimeo.com/video/12345678"
    assert video_embed_url("https://player.vimeo.com/video/12345678?x=1") == \
        "https://player.vimeo.com/video/12345678"


def test_video_embed_url_rejects_unsafe():
    from app.routers.legacy import video_embed_url
    assert video_embed_url(None) is None
    assert video_embed_url("") is None
    assert video_embed_url("https://evil.example.com/x") is None
    assert video_embed_url("javascript:alert(1)") is None
    assert video_embed_url("https://youtube.com/watch?v=short") is None
    assert video_embed_url("https://vimeo.com/abc") is None


# ── pure: list query builder ──

def test_list_query_search_and_filters():
    from app.routers.legacy import _list_query
    q = _list_query("pay (app)", "published", True, ".NET", "saas", {"category": "x"})
    assert q["status"] == "published" and q["featured"] is True
    assert q["category"] == "x"
    assert any("tech_stack" in str(c) for c in q["$and"])
    ors = q["$or"]
    assert {list(o)[0] for o in ors} >= {"title", "description", "tags", "tech_stack"}
    # regex-escaped: no live parens group
    assert "\\(" in ors[0]["title"]["$regex"]
    assert _list_query(None, None, None, None, None) == {}


def test_list_sort_options():
    from app.routers.legacy import _list_sort
    assert _list_sort("title") == [("title", 1)]
    assert _list_sort("-updated") == [("updated_at", -1)]
    assert _list_sort("bogus") == [("display_order", 1), ("updated_at", -1)]


# ── auth gates (no DB) ──

@pytest.mark.asyncio
async def test_catalog_admin_requires_auth():
    from app.main import create_app
    app = create_app()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        for method, path in (
                ("GET", "/api/admin/portfolio"), ("POST", "/api/admin/portfolio"),
                ("PUT", "/api/admin/portfolio/x"), ("DELETE", "/api/admin/portfolio/x"),
                ("PATCH", "/api/admin/portfolio/x/status"),
                ("PATCH", "/api/admin/portfolio/x/featured"),
                ("GET", "/api/admin/products"), ("POST", "/api/admin/products"),
                ("PUT", "/api/admin/products/x"), ("DELETE", "/api/admin/products/x"),
                ("PATCH", "/api/admin/products/x/status"),
                ("PATCH", "/api/admin/products/x/featured"),
                ("POST", "/api/admin/uploads/image"), ("DELETE", "/api/admin/uploads")):
            r = await c.request(method, path, json={})
            assert r.status_code == 401, (method, path)


# ── live CRUD + filters + toggles ──

@pytest.mark.asyncio
async def test_portfolio_crud_and_filters_live(monkeypatch):
    import app.services.rag_ingest as ri

    async def _no_rag(*a, **k):
        return None

    monkeypatch.setattr(ri, "upsert_document", _no_rag)
    monkeypatch.setattr(ri, "deactivate_document", _no_rag)
    monkeypatch.setattr(ri, "delete_document", _no_rag)
    from app.main import create_app
    db = await _live_db()
    app = _authed(create_app())
    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
            r = await c.post("/api/admin/portfolio", json={
                "title": "E2E Pay App", "status": "draft",
                "shortDescription": "payments demo", "techStack": ["React", ".NET"],
                "tags": ["fintech"], "displayOrder": 3,
                "videoUrl": "https://youtu.be/dQw4w9WgXcQ",
                "liveUrl": "https://pay.example.com",
                "seoTitle": "Pay App SEO"})
            assert r.status_code == 201, r.text
            pid, slug = r.json()["id"], r.json()["slug"]
            assert r.json()["videoEmbedUrl"] == "https://www.youtube.com/embed/dQw4w9WgXcQ"
            # validation: title required
            r = await c.post("/api/admin/portfolio", json={"title": " "})
            assert r.status_code == 400
            # duplicate slug rejected
            r = await c.post("/api/admin/portfolio", json={"title": "E2E Pay App"})
            assert r.status_code == 400
            # draft hidden from public
            r = await c.get("/api/portfolio")
            assert all(p["slug"] != slug for p in r.json())
            # search + filters on admin list
            r = await c.get("/api/admin/portfolio", params={"q": "pay app"})
            assert r.json()["total"] >= 1
            r = await c.get("/api/admin/portfolio", params={"status": "draft", "tech": ".net"})
            assert r.json()["total"] >= 1
            r = await c.get("/api/admin/portfolio", params={"tag": "FINTECH"})
            assert r.json()["total"] >= 1
            # activate → visible publicly + published flag
            r = await c.patch(f"/api/admin/portfolio/{pid}/status", json={"status": "published"})
            assert r.status_code == 200 and r.json()["status"] == "published"
            r = await c.get("/api/portfolio")
            assert any(p["slug"] == slug for p in r.json())
            # featured toggle
            r = await c.patch(f"/api/admin/portfolio/{pid}/featured", json={"featured": True})
            assert r.json()["featured"] is True
            # detail carries new fields
            r = await c.get(f"/api/portfolio/{slug}")
            assert r.json()["seoTitle"] == "Pay App SEO"
            assert r.json()["liveUrl"] == "https://pay.example.com"
            # delete
            r = await c.delete(f"/api/admin/portfolio/{pid}")
            assert r.status_code == 200
            r = await c.get(f"/api/portfolio/{slug}")
            assert r.status_code == 404
    finally:
        app.dependency_overrides.clear()
        await db["portfolio"].delete_many({"slug": "e2e-pay-app"})


@pytest.mark.asyncio
async def test_products_crud_and_category_live(monkeypatch):
    import app.services.rag_ingest as ri

    async def _no_rag(*a, **k):
        return None

    monkeypatch.setattr(ri, "upsert_document", _no_rag)
    monkeypatch.setattr(ri, "deactivate_document", _no_rag)
    monkeypatch.setattr(ri, "delete_document", _no_rag)
    from app.main import create_app
    db = await _live_db()
    app = _authed(create_app())
    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
            r = await c.post("/api/admin/products", json={
                "name": "E2E Widget", "category": "SaaS", "status": "published",
                "features": ["a", "b"], "tags": ["widget"]})
            assert r.status_code == 201, r.text
            pid, slug = r.json()["id"], r.json()["slug"]
            r = await c.get("/api/admin/products", params={"category": "SaaS", "status": "published"})
            assert r.json()["total"] >= 1
            r = await c.put(f"/api/admin/products/{pid}", json={"featured": True, "displayOrder": 1})
            assert r.json()["featured"] is True
            r = await c.patch(f"/api/admin/products/{pid}/status", json={"status": "draft"})
            assert r.json()["status"] == "draft"
            assert all(p["slug"] != slug for p in (await c.get("/api/products")).json())
            await c.delete(f"/api/admin/products/{pid}")
    finally:
        app.dependency_overrides.clear()
        await db["products"].delete_many({"slug": "e2e-widget"})


# ── live: uploads ──

@pytest.mark.asyncio
async def test_image_upload_validation_live(tmp_path):
    from app.main import create_app
    from app.routers import legacy as legacy_mod
    await _live_db()
    orig_settings = legacy_mod.get_settings
    legacy_mod.get_settings = lambda: orig_settings().model_copy(
        update={"upload_dir": str(tmp_path), "max_image_mb": 5})
    app = _authed(create_app())
    png = b"\x89PNG\r\n\x1a\n" + b"\x00" * 100
    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
            r = await c.post("/api/admin/uploads/image?kind=portfolio",
                             files={"file": ("x.png", png, "image/png")})
            assert r.status_code == 200, r.text
            url = r.json()["url"]
            assert url.startswith("/uploads/portfolio/") and ".." not in url
            # wrong kind / bad ext / fake content rejected
            r = await c.post("/api/admin/uploads/image?kind=nope",
                             files={"file": ("x.png", png, "image/png")})
            assert r.status_code == 400
            r = await c.post("/api/admin/uploads/image?kind=portfolio",
                             files={"file": ("x.exe", b"MZ" + b"\x00" * 100, "application/octet-stream")})
            assert r.status_code == 400
            r = await c.post("/api/admin/uploads/image?kind=portfolio",
                             files={"file": ("x.png", b"not an image" * 20, "image/png")})
            assert r.status_code == 400
            # traversal delete rejected; real delete works
            r = await c.request("DELETE", "/api/admin/uploads", params={"path": "../../etc/passwd"})
            assert r.status_code == 400
            r = await c.request("DELETE", "/api/admin/uploads", params={"path": url})
            assert r.json() == {"ok": True}
    finally:
        legacy_mod.get_settings = orig_settings
        app.dependency_overrides.clear()


# ── live: RAG lifecycle ──

@pytest.mark.asyncio
async def test_rag_sync_lifecycle_live(monkeypatch):
    import app.services.rag_ingest as ri
    calls = []

    async def _fake_upsert(source_type, source_id, title, content, **kw):
        calls.append((source_type, source_id, title, content, kw.get("url")))
        return {"document_id": "fake", "status": "created"}

    async def _fake_deactivate(document_id):
        calls.append(("deactivate", document_id))
        return True

    async def _fake_delete(document_id):
        calls.append(("delete", document_id))
        return True

    monkeypatch.setattr(ri, "upsert_document", _fake_upsert)
    monkeypatch.setattr(ri, "deactivate_document", _fake_deactivate)
    monkeypatch.setattr(ri, "delete_document", _fake_delete)
    from app.main import create_app
    from app.database import get_db
    db = await _live_db()
    app = _authed(create_app())
    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
            # publish → upserted with portfolio source + verified URL
            r = await c.post("/api/admin/portfolio", json={
                "title": "E2E RAG App", "status": "published",
                "shortDescription": "rag test", "liveUrl": "https://rag.example.com"})
            pid = r.json()["id"]
            ups = [x for x in calls if x[0] == "project"]
            assert ups and ups[0][1] == "portfolio:e2e-rag-app"
            assert ups[0][4] == "https://rajiblabs.com/portfolio/e2e-rag-app"
            assert "https://rag.example.com" in ups[0][3]
            # unpublish → deactivated (need a knowledge doc to exist first)
            await db["knowledge_documents"].insert_one({
                "source_type": "project", "source_id": "portfolio:e2e-rag-app",
                "status": "active"})
            r = await c.patch(f"/api/admin/portfolio/{pid}/status", json={"status": "draft"})
            assert any(x[0] == "deactivate" for x in calls)
            # rag_indexed False → skip upsert on next publish
            calls.clear()
            await c.put(f"/api/admin/portfolio/{pid}",
                        json={"status": "published", "ragIndexed": False})
            assert not [x for x in calls if x[0] == "project"]
            await c.delete(f"/api/admin/portfolio/{pid}")
    finally:
        app.dependency_overrides.clear()
        await db["portfolio"].delete_many({"slug": "e2e-rag-app"})
        await db["knowledge_documents"].delete_many({"source_id": "portfolio:e2e-rag-app"})
