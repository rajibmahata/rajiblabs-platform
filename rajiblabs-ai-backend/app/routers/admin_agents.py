"""Admin AI Agents: config CRUD, test console, stats, conversations.

All routes require admin JWT. Agent configs live in MongoDB `ai_agents`;
all agents share the single RAG knowledge base with per-agent permissions.
"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from app.auth.dependencies import require_admin
from app.database import get_db
from app.models import oid_str
from app.services import agent_config as agents
from app.services.notify import audit

router = APIRouter(prefix="/api/admin/agents")


class AgentUpdateIn(BaseModel):
    model_config = {"extra": "allow"}

    def patch(self) -> dict:
        return self.model_dump(exclude_unset=True)


class AgentCreateIn(BaseModel):
    model_config = {"extra": "allow"}
    slug: str = ""
    name: str = ""
    agent_type: str = "support"


def _out(d: dict | None) -> dict | None:
    if not d:
        return None
    d = oid_str(d)
    d.pop("stats", None)
    return d


@router.get("")
async def list_all(email: str = Depends(require_admin)):
    db = get_db()
    docs = await agents.list_agents(db)
    out = []
    for d in docs:
        d = oid_str(d)
        d["turns_recorded"] = await db["customer_messages"].count_documents(
            {"agent_slug": d.get("slug")})
        out.append(d)
    return out


@router.post("")
async def create_one(body: AgentCreateIn, email: str = Depends(require_admin)):
    db = get_db()
    try:
        doc = await agents.create_agent(
            db, {"slug": body.slug, **body.model_dump(exclude_unset=True)}, actor=email)
    except ValueError as e:
        raise HTTPException(400, str(e))
    return _out(doc)


@router.get("/{slug}")
async def get_one(slug: str, email: str = Depends(require_admin)):
    from app.services.agent_tools import PUBLIC_TOOL_NAMES
    from app.services.agent_config import DEFAULT_SOURCE_POLICY
    db = get_db()
    doc = await agents.get_agent(db, slug)
    if not doc:
        raise HTTPException(404, "Agent not found")
    out = _out(doc) or {}
    out["public_tools"] = sorted(PUBLIC_TOOL_NAMES)
    out["known_sources"] = sorted(DEFAULT_SOURCE_POLICY)
    return out


@router.put("/{slug}")
async def update_one(slug: str, body: AgentUpdateIn, email: str = Depends(require_admin)):
    from app.services.agent_tools import PUBLIC_TOOL_NAMES
    db = get_db()
    if await agents.get_agent(db, slug) is None:
        raise HTTPException(404, "Agent not found")
    doc = await agents.update_agent(db, slug, body.patch(), actor=email)
    out = _out(doc) or {}
    out["public_tools"] = sorted(PUBLIC_TOOL_NAMES)
    return out


@router.post("/{slug}/test")
async def test_agent(slug: str, body: dict, email: str = Depends(require_admin)):
    """Dry-run a message through the agent loop without storing anything."""
    from app.services import concierge as _cg
    db = get_db()
    if slug != _cg.AGENT_SLUG or await agents.get_agent(db, slug) is None:
        raise HTTPException(404, "Agent not found")
    message = ((body or {}).get("message") or "").strip()[:2000]
    if not message:
        raise HTTPException(400, "Message is required")
    try:
        res = await _cg.run_concierge_turn(db, message, None, "admin-test", preview=True)
    except Exception as e:
        raise HTTPException(502, f"Test failed: {e}"[:300])
    await audit(email, "AGENT_TEST", slug, {"intent": res.get("intent")})
    return res


@router.get("/{slug}/stats")
async def agent_stats(slug: str, email: str = Depends(require_admin)):
    """Observability: turns, tool usage, conversions, errors, latency, models."""
    db = get_db()
    doc = await agents.get_agent(db, slug)
    if not doc:
        raise HTTPException(404, "Agent not found")
    match = {"agent_slug": slug}
    turns = await db["customer_messages"].count_documents({**match, "sender": "assistant"})
    errors_pipeline = [
        d async for d in db["error_logs"].find(
            {"source": {"$in": ["concierge", "concierge_tool", "concierge_store"]}})
        .sort("created_at", -1).limit(10)]
    tool_usage: dict[str, int] = {}
    latencies: list[int] = []
    models: dict[str, int] = {}
    leads_set: set[str] = set()
    async for m in db["customer_messages"].find(match).sort("created_at", -1).limit(2000):
        for t in (m.get("tools_called") or []):
            tool_usage[t] = tool_usage.get(t, 0) + 1
        if isinstance(m.get("duration_ms"), int):
            latencies.append(m["duration_ms"])
        prov = m.get("ai_provider")
        if prov:
            models[f"{prov}:{m.get('ai_model') or '?'}"] = models.get(f"{prov}:{m.get('ai_model') or '?'}", 0) + 1
        if m.get("lead_id"):
            leads_set.add(m["lead_id"])
    latencies.sort()
    p50 = latencies[len(latencies) // 2] if latencies else None
    # conversations carrying this agent's turns
    sessions = await db["customer_messages"].distinct("session_token", match)
    return {
        "slug": slug, "enabled": doc.get("enabled"), "stats": doc.get("stats", {}),
        "assistant_turns": turns, "conversations": len(sessions),
        "tool_usage": tool_usage, "leads_converted": len(leads_set),
        "errors_recent": [{"message": e.get("message", ""), "created_at": e.get("created_at")}
                          for e in errors_pipeline],
        "latency_ms_p50": p50,
        "latency_samples": len(latencies),
        "models": models,
    }


@router.get("/{slug}/conversations")
async def agent_conversations(slug: str, limit: int = 20,
                              email: str = Depends(require_admin)):
    """Recent sessions with this agent's turns (no message bodies beyond preview)."""
    db = get_db()
    if await agents.get_agent(db, slug) is None:
        raise HTTPException(404, "Agent not found")
    pipe = [
        {"$match": {"agent_slug": slug}},
        {"$sort": {"created_at": -1}},
        {"$group": {"_id": "$session_token",
                    "turns": {"$sum": 1},
                    "last_at": {"$max": "$created_at"},
                    "intents": {"$addToSet": "$intent"},
                    "lead_id": {"$max": "$lead_id"},
                    "last_preview": {"$first": "$content"}}},
        {"$sort": {"last_at": -1}},
        {"$limit": max(1, min(limit, 100))},
    ]
    out = []
    async for r in db["customer_messages"].aggregate(pipe):
        out.append({"session_token": r["_id"], "turns": r["turns"],
                    "last_at": r["last_at"],
                    "intents": [i for i in (r["intents"] or []) if i],
                    "lead_id": r["lead_id"],
                    "preview": str(r.get("last_preview") or "")[:200]})
    return out
