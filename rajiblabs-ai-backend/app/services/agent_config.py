"""Agent configuration store (MongoDB `ai_agents`).

One shared knowledge base for all agents; per-agent permissions live here:
allowed tools, knowledge-source policy, guardrails, style, lead behavior.
The system prompt stays small — facts always come through tools/RAG.
"""
from app.database import get_db, utcnow

CONCIERGE_SLUG = "rajiblabs-concierge"

# Default per-source policy. Retrieval enforces public_allowed server-side;
# priority orders mixed results (lower = more authoritative).
DEFAULT_SOURCE_POLICY = {
    "profile": {"public_allowed": True, "priority": 1},
    "resume": {"public_allowed": True, "priority": 2},
    "project": {"public_allowed": True, "priority": 1},
    "product": {"public_allowed": True, "priority": 2},
    "service": {"public_allowed": True, "priority": 2},
    "case_study": {"public_allowed": True, "priority": 2},
    "wip": {"public_allowed": True, "priority": 3},
    "github_repository": {"public_allowed": True, "priority": 2},
    "github_readme": {"public_allowed": True, "priority": 2},
    "github_documentation": {"public_allowed": True, "priority": 3},
    "github_commit": {"public_allowed": True, "priority": 4},
    "github_issue": {"public_allowed": True, "priority": 4},
    "website_content": {"public_allowed": True, "priority": 3},
    "admin_knowledge": {"public_allowed": True, "priority": 2},
}

DEFAULT_CONCIERGE = {
    "name": "RajibLabs Concierge Agent",
    "slug": CONCIERGE_SLUG,
    "description": "Default public agent: answers questions about Rajib, RajibLabs, "
                   "projects, services and GitHub work from verified knowledge, "
                   "and captures leads for genuine enquiries.",
    "enabled": True,
    "public_enabled": True,
    "agent_type": "concierge",
    "system_prompt": (
        "You are the RajibLabs Concierge Agent, a knowledgeable representative "
        "of RajibLabs (Rajib Mahata's software studio). Answer ONLY from the "
        "verified tool results provided. Never invent projects, clients, "
        "technologies, URLs, metrics, or history. If the results lack the "
        "answer, say you don't have verified information and offer to connect "
        "the visitor with RajibLabs. Be concise, warm, and business-friendly. "
        "Use only the URLs present in the tool results."
    ),
    "allowed_tools": [
        "search_knowledge", "get_rajib_profile", "get_projects",
        "get_project_details", "get_project_live_url", "get_products",
        "get_services", "get_github_projects", "get_contact_information",
        "get_relevant_sources",
    ],
    "knowledge_sources": list(DEFAULT_SOURCE_POLICY),
    "knowledge_policy": dict(DEFAULT_SOURCE_POLICY),
    "guardrail_policy": "public",
    "hallucination_policy": "verified-only",
    "response_policy": "concise-grounded",
    "response_style": "concise, warm, business-friendly; short paragraphs; "
                      "no jargon; never repeat the user's question",
    "lead_capture_enabled": True,
    "lead_fields": ["first_name", "email", "phone", "company", "idea"],
    "fallback_message": (
        "I don't currently have verified information about that in the "
        "RajibLabs knowledge base. If you'd like, I can help you contact "
        "RajibLabs."
    ),
}

# Admin-editable top-level keys (everything else is system-managed).
EDITABLE_FIELDS = {
    "name", "description", "enabled", "public_enabled", "system_prompt",
    "allowed_tools", "knowledge_sources", "knowledge_policy",
    "guardrail_policy", "hallucination_policy", "response_policy",
    "response_style", "lead_capture_enabled", "lead_fields",
    "fallback_message",
}

AGENT_TYPES = ("concierge", "proposal", "recruiter", "marketing",
               "research", "support")


async def ensure_seed(db=None) -> dict:
    db = get_db() if db is None else db
    existing = await db["ai_agents"].find_one({"slug": CONCIERGE_SLUG})
    if existing:
        return existing
    doc = {**DEFAULT_CONCIERGE, "created_at": utcnow(), "updated_at": utcnow(),
           "stats": {"turns": 0, "tool_calls": 0, "leads": 0, "errors": 0}}
    await db["ai_agents"].insert_one(doc)
    return doc


async def get_agent(db, slug: str = CONCIERGE_SLUG) -> dict | None:
    if slug == CONCIERGE_SLUG:
        return await ensure_seed(db)
    return await db["ai_agents"].find_one({"slug": slug})


async def list_agents(db) -> list[dict]:
    await ensure_seed(db)
    return [d async for d in db["ai_agents"].find().sort("created_at", 1)]


async def update_agent(db, slug: str, patch: dict, actor: str = "") -> dict | None:
    allowed = {k: v for k, v in (patch or {}).items() if k in EDITABLE_FIELDS}
    if "allowed_tools" in allowed:
        from app.services.agent_tools import PUBLIC_TOOL_NAMES
        allowed["allowed_tools"] = [t for t in (allowed.get("allowed_tools") or [])
                                    if t in PUBLIC_TOOL_NAMES]
    if "knowledge_sources" in allowed:
        allowed["knowledge_sources"] = [s for s in (allowed.get("knowledge_sources") or [])
                                        if isinstance(s, str)][:60]
    if not allowed:
        return await db["ai_agents"].find_one({"slug": slug})
    allowed["updated_at"] = utcnow()
    await db["ai_agents"].update_one({"slug": slug}, {"$set": allowed})
    if actor:
        from app.services.notify import audit
        try:
            await audit(actor, "AGENT_UPDATE", slug, {"fields": sorted(allowed)})
        except Exception:
            pass
    return await db["ai_agents"].find_one({"slug": slug})


async def create_agent(db, spec: dict, actor: str = "") -> dict:
    from app.services.agent_tools import PUBLIC_TOOL_NAMES
    slug = str(spec.get("slug") or "").strip().lower()[:60]
    if not slug or await db["ai_agents"].find_one({"slug": slug}):
        raise ValueError("slug required and must be unique")
    doc = {**DEFAULT_CONCIERGE}
    doc.update({k: v for k, v in spec.items() if k in EDITABLE_FIELDS and v is not None})
    doc.update({"slug": slug,
                "agent_type": spec.get("agent_type") if spec.get("agent_type") in AGENT_TYPES else "support",
                "enabled": bool(spec.get("enabled", True)),
                "public_enabled": bool(spec.get("public_enabled", False)),
                "allowed_tools": [t for t in (doc.get("allowed_tools") or [])
                                  if t in PUBLIC_TOOL_NAMES],
                "created_at": utcnow(), "updated_at": utcnow(),
                "stats": {"turns": 0, "tool_calls": 0, "leads": 0, "errors": 0}})
    await db["ai_agents"].insert_one(doc)
    if actor:
        from app.services.notify import audit
        try:
            await audit(actor, "AGENT_CREATE", slug, {})
        except Exception:
            pass
    return doc


async def bump_stat(db, slug: str, field: str, by: int = 1) -> None:
    try:
        await db["ai_agents"].update_one({"slug": slug}, {"$inc": {f"stats.{field}": by}})
    except Exception:
        pass
