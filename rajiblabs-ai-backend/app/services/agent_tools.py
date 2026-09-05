"""Public concierge tools — sanitized, server-side authorized.

Every function returns allowlisted public fields only (no tokens, keys,
passwords, credentials, infra internals). URLs come exclusively from the
database/RAG metadata — never constructed or invented. Admin-only
operations are named in ADMIN_ONLY_TOOLS and always rejected here; the
LLM is never trusted with that decision.
"""
import re

from app.database import get_db
from app.services.notify import scrub_text

# Secret-looking keys are dropped even if a future caller passes them through.
_BLOCKED_KEY_RE = re.compile(
    r"(?i)(password|passwd|secret|token|api[_-]?key|jwt|credential|"
    r"connection[_-]?string|private[_-]?key|auth)")


def _clean(obj):
    """Recursively drop blocked keys from tool output."""
    if isinstance(obj, dict):
        return {k: _clean(v) for k, v in obj.items()
                if not _BLOCKED_KEY_RE.search(str(k))}
    if isinstance(obj, list):
        return [_clean(v) for v in obj]
    return obj


class ToolAuthError(Exception):
    """Raised when a non-public (e.g. admin-only) tool is requested."""


ADMIN_ONLY_TOOLS = frozenset({
    "run_daily_agent", "reindex_all", "set_github_token", "test_github_token",
    "delete_knowledge", "unpublish_document", "update_settings",
    "purge_logs", "sync_github_now", "approve_proposal",
})

PUBLIC_TOOL_NAMES = frozenset({
    "search_knowledge", "get_rajib_profile", "get_projects",
    "get_project_details", "get_project_live_url", "get_products",
    "get_services", "get_github_projects", "get_contact_information",
    "get_relevant_sources",
})


def _oid_str(doc: dict) -> dict:
    d = dict(doc or {})
    if "_id" in d:
        d["id"] = str(d.pop("_id"))
    return d


async def search_knowledge(db, query: str, top_k: int = 6) -> list[dict]:
    """Shared RAG index (public docs only — enforced inside retrieve)."""
    from app.services import rag_query as _rq
    hits = await _rq.retrieve((query or "")[:500], top_k=max(1, min(top_k, 10)))
    return _clean([{
        "title": h.get("title", ""), "url": h.get("url"),
        "source_type": h.get("source_type", ""),
        "repository": h.get("repository"), "language": h.get("language"),
        "score": h.get("score", 0),
        "snippet": (h.get("content") or "")[:600],
    } for h in hits])


async def get_rajib_profile(db) -> dict:
    d = await db["profiles"].find_one() or {}
    links = d.get("social_links") or {}
    return _clean({
        "full_name": d.get("full_name", ""), "title": d.get("title", ""),
        "bio": d.get("bio", ""), "headline": d.get("headline"),
        "location": d.get("location"), "skills": d.get("skills", []),
        "social_links": {k: links.get(k) for k in ("github", "linkedin") if links.get(k)},
        "career": [{
            "company": c.get("company", ""), "role": c.get("role", ""),
            "period": c.get("period", ""), "client": c.get("client", ""),
            "achievements": (c.get("achievements") or [])[:8],
            "tech_stack": c.get("tech_stack", []) or c.get("technologies", []),
        } for c in (d.get("career") or [])],
    })


def _project_out(d: dict) -> dict:
    return _clean({
        "name": d.get("title") or d.get("name", ""),
        "slug": d.get("slug", ""),
        "description": d.get("description", "") or d.get("short_description", ""),
        "tech_stack": d.get("tech_stack") or d.get("technologies", []),
        "github_url": d.get("github_url"), "live_url": d.get("live_url"),
        "demo_url": d.get("demo_url"), "status": d.get("status", ""),
    })


async def get_projects(db, tech: str | None = None, limit: int = 20) -> list[dict]:
    """Published projects across both project stores, slug-deduped."""
    seen: dict[str, dict] = {}

    async def harvest(coll: str, filt: dict):
        cur = db[coll].find(filt).sort("updated_at", -1).limit(100)
        async for d in cur:
            out = _project_out(_oid_str(d))
            key = (out["slug"] or out["name"]).lower()
            if key and key not in seen:
                seen[key] = out

    await harvest("projects", {"published": True})
    await harvest("legacy_projects", {})
    items = list(seen.values())
    if tech:
        t = tech.lower()
        items = [p for p in items
                 if any(t in str(x).lower() for x in (p["tech_stack"] or []))]
    return items[:max(1, min(limit, 50))]


async def get_project_details(db, ref: str) -> dict | None:
    """Match one project by slug, then by name-contains (case-insensitive)."""
    ref = (ref or "").strip().lower()
    if not ref:
        return None
    for coll in ("projects", "legacy_projects"):
        d = await db[coll].find_one({"slug": ref})
        if d:
            return _project_out(_oid_str(d))
    for coll in ("projects", "legacy_projects"):
        cur = db[coll].find({"$or": [
            {"slug": {"$regex": re.escape(ref), "$options": "i"}},
            {"title": {"$regex": re.escape(ref), "$options": "i"}},
            {"name": {"$regex": re.escape(ref), "$options": "i"}},
        ]}).limit(5)
        async for d in cur:
            return _project_out(_oid_str(d))
    return None


async def get_project_live_url(db, ref: str) -> dict:
    d = await get_project_details(db, ref)
    if not d:
        return {"project": None, "live_url": None}
    return {"project": d["name"], "live_url": d.get("live_url") or None,
            "github_url": d.get("github_url") or None}


async def get_products(db) -> list[dict]:
    cur = db["products"].find(
        {"status": {"$in": ["published", "featured"]}}).sort("display_order", 1)
    out = []
    async for d in cur:
        d = _oid_str(d)
        out.append(_clean({
            "name": d.get("name", ""), "slug": d.get("slug", ""),
            "category": d.get("category", ""), "description": d.get("description", ""),
            "features": d.get("features", []), "tech_stack": d.get("tech_stack", []),
            "product_url": d.get("product_url"), "live_url": d.get("live_url"),
        }))
    return out


async def get_services(db) -> list[dict]:
    """Curated service catalog (single source of truth with the site)."""
    return [
        {"slug": "architecture", "title": "Software Architecture",
         "description": "Enterprise software architecture: .NET microservices, event-driven systems, CQRS, domain-driven design, Azure cloud-native platforms."},
        {"slug": "ai-products", "title": "AI Products & GenAI",
         "description": "AI product engineering: RAG pipelines, LLM integration, vector search, AI chat assistants, document intelligence."},
        {"slug": "saas", "title": "SaaS Development",
         "description": "Multi-tenant SaaS platforms: subscriptions, payments, white-label APIs, PWA frontends with React and TypeScript."},
    ]


async def get_github_projects(db, tech: str | None = None, limit: int = 20) -> list[dict]:
    """Public, RAG-enabled repos only — metadata + verified URLs."""
    q: dict = {"is_private": {"$ne": True}, "rag_enabled": {"$ne": False}}
    cur = db["github_repositories"].find(q).sort("stars", -1).limit(100)
    out = []
    async for d in cur:
        d = _oid_str(d)
        out.append(_clean({
            "name": d.get("name", ""), "full_name": d.get("full_name", ""),
            "description": d.get("description", ""),
            "url": d.get("html_url"), "language": d.get("language", ""),
            "topics": d.get("topics", []), "stars": d.get("stars", 0),
            "default_branch": d.get("default_branch", "main"),
        }))
    if tech:
        t = tech.lower()
        out = [r for r in out
               if t in (r["language"] or "").lower()
               or any(t in str(x).lower() for x in (r["topics"] or []))
               or t in (r["description"] or "").lower()
               or t in (r["name"] or "").lower()]
    return out[:max(1, min(limit, 50))]


async def get_contact_information(db) -> dict:
    s = await db["site_settings"].find_one({"key": "contact"}) or {}
    v = s.get("value", {}) if isinstance(s.get("value"), dict) else {}
    prof = await db["profiles"].find_one() or {}
    links = prof.get("social_links") or {}
    return _clean({
        "emails": v.get("emails", ["rajibmahata143@gmail.com"]),
        "primary_phone": v.get("primary_phone") or prof.get("phone"),
        "whatsapp": v.get("whatsapp"),
        "linkedin": links.get("linkedin") or prof.get("linkedin"),
        "github": links.get("github") or prof.get("github"),
        "website": "https://rajiblabs.com",
    })


async def get_relevant_sources(db, query: str, top_k: int = 6) -> list[dict]:
    """Source chips for answers: titles + verified URLs only."""
    hits = await search_knowledge(db, query, top_k)
    return [{"title": h["title"], "url": h["url"],
             "source_type": h["source_type"]} for h in hits]


async def run_public_tool(name: str, db=None, **args):
    """Execute a public tool by name. Unknown/admin-only names are rejected —
    the LLM never decides authorization; this layer does."""
    if name in ADMIN_ONLY_TOOLS:
        raise ToolAuthError(f"tool '{name}' is admin-only")
    if name not in PUBLIC_TOOL_NAMES:
        raise ToolAuthError(f"unknown tool '{name}'")
    db = get_db() if db is None else db
    fn = _IMPL[name]
    return await fn(db, **{k: v for k, v in args.items() if v is not None})


_IMPL = {
    "search_knowledge": search_knowledge,
    "get_rajib_profile": get_rajib_profile,
    "get_projects": get_projects,
    "get_project_details": get_project_details,
    "get_project_live_url": get_project_live_url,
    "get_products": get_products,
    "get_services": get_services,
    "get_github_projects": get_github_projects,
    "get_contact_information": get_contact_information,
    "get_relevant_sources": get_relevant_sources,
}
