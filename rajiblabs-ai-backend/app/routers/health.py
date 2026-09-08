"""GET /health — no secrets exposed."""
from fastapi import APIRouter
from fastapi.responses import Response
from app.config import get_settings
from app.database import get_db

router = APIRouter()


@router.get("/sitemap.xml", response_class=Response)
async def sitemap():
    """Dynamic sitemap: static routes + every published project/product slug.

    Public, DB-driven, no secrets. Falls back to the 3 static URLs when
    MongoDB is unreachable so crawlers never get a 500.
    """
    urls = [
        ("https://rajiblabs.com/", "weekly", "1.0", None),
        ("https://rajiblabs.com/#projects", "weekly", "0.8", None),
        ("https://rajiblabs.com/#contact", "monthly", "0.7", None),
    ]
    try:
        db = get_db()
        cur = db["projects"].find(
            {"published": True, "slug": {"$ne": ""}},
            {"slug": 1, "category": 1, "updated_at": 1})
        async for d in cur:
            slug = (d.get("slug") or "").strip()
            if not slug:
                continue
            kind = "products" if (d.get("category") or "") == "product" else "portfolio"
            lastmod = d.get("updated_at")
            try:
                lastmod = lastmod.date().isoformat() if hasattr(lastmod, "date") else None
            except Exception:
                lastmod = None
            urls.append((f"https://rajiblabs.com/{kind}/{slug}", "monthly", "0.7", lastmod))
    except Exception:
        pass  # static fallback above
    parts = ['<?xml version="1.0" encoding="UTF-8"?>',
             '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for loc, freq, prio, lastmod in urls:
        parts.append(f"<url><loc>{loc}</loc>"
                     + (f"<lastmod>{lastmod}</lastmod>" if lastmod else "")
                     + f"<changefreq>{freq}</changefreq><priority>{prio}</priority></url>")
    parts.append("</urlset>")
    return Response(content="".join(parts), media_type="application/xml")


@router.get("/health")
async def health():
    s = get_settings()
    db_ok = github_ok = openai_ok = "ok"
    try:
        await get_db().command("ping")
    except Exception:
        db_ok = "down"
    if not s.github_token:
        github_ok = "not-configured"
    if not s.openai_api_key:
        openai_ok = "not-configured"
    status = "ok" if db_ok == "ok" else "degraded"
    return {"status": status, "database": db_ok, "github": github_ok, "openai": openai_ok}
