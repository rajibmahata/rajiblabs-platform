"""Admin Agent & AI Operations Dashboard — execution visibility, usage, costs."""
from datetime import datetime, timezone, timedelta
from fastapi import APIRouter, Depends, Query
from app.database import get_db
from app.routers.admin_auth import require_admin

router = APIRouter(prefix="/api/admin/ops", dependencies=[Depends(require_admin)])


@router.get("/summary")
async def ops_summary(db=Depends(get_db)):
    """Aggregated stats: total LLM calls, cost, cache hit rate, agent turns, leads."""
    now = datetime.now(timezone.utc)
    today = now.replace(hour=0, minute=0, second=0, microsecond=0)
    week_ago = now - timedelta(days=7)

    # ai_usage aggregates
    cur = db["ai_usage"].find({"created_at": {"$gte": today}})
    total_calls = 0
    total_in = 0
    total_out = 0
    total_cost = 0.0
    cache_hits = 0
    retrieval_hits = 0
    llm_fallbacks = 0
    providers: dict[str, dict] = {}
    tags: dict[str, dict] = {}
    async for doc in cur:
        total_calls += 1
        it = doc.get("in_tokens", 0)
        ot = doc.get("out_tokens", 0)
        c = doc.get("est_cost_usd", 0)
        total_in += it
        total_out += ot
        total_cost += c
        if doc.get("cache_hit"):
            cache_hits += 1
        if doc.get("retrieval_hit"):
            retrieval_hits += 1
        if doc.get("fallback_reason"):
            llm_fallbacks += 1
        p = doc.get("provider", "unknown")
        if p not in providers:
            providers[p] = {"calls": 0, "tokens": 0, "cost": 0.0}
        providers[p]["calls"] += 1
        providers[p]["tokens"] += it + ot
        providers[p]["cost"] += c
        t = doc.get("tag", "unknown")
        if t not in tags:
            tags[t] = {"calls": 0, "tokens": 0, "cost": 0.0}
        tags[t]["calls"] += 1
        tags[t]["tokens"] += it + ot
        tags[t]["cost"] += c

    # weekly cost timeline
    week_cost = 0.0
    week_calls = 0
    cur2 = db["ai_usage"].find({"created_at": {"$gte": week_ago}})
    async for doc in cur2:
        week_calls += 1
        week_cost += doc.get("est_cost_usd", 0)

    # agent stats
    agents = []
    async for a in db["ai_agents"].find().sort("created_at", 1):
        stats = a.get("stats") or {}
        agents.append({
            "slug": a.get("slug"),
            "name": a.get("name"),
            "agent_type": a.get("agent_type"),
            "enabled": a.get("enabled"),
            "public_enabled": a.get("public_enabled"),
            "turns": stats.get("turns", 0),
            "tool_calls": stats.get("tool_calls", 0),
            "leads": stats.get("leads", 0),
            "errors": stats.get("errors", 0),
            "runs": stats.get("runs", 0),
        })

    # customer message count (conversations)
    total_messages = await db["customer_messages"].count_documents({})
    total_sessions = await db["customer_conversations"].count_documents({})
    active_sessions_24h = await db["customer_conversations"].count_documents(
        {"last_message_at": {"$gte": today}})

    # leads
    total_leads = await db["leads"].count_documents({})

    return {
        "today": {
            "total_calls": total_calls,
            "total_in_tokens": total_in,
            "total_out_tokens": total_out,
            "total_tokens": total_in + total_out,
            "estimated_cost_usd": round(total_cost, 6),
            "cache_hits": cache_hits,
            "cache_hit_rate": round(cache_hits / max(1, total_calls) * 100, 1),
            "retrieval_hits": retrieval_hits,
            "llm_fallbacks": llm_fallbacks,
        },
        "week": {"cost_usd": round(week_cost, 6), "calls": week_calls},
        "agents": agents,
        "conversations": {
            "total_messages": total_messages,
            "total_sessions": total_sessions,
            "active_24h": active_sessions_24h,
        },
        "leads_total": total_leads,
        "providers": providers,
        "tags": tags,
    }


@router.get("/usage-timeline")
async def usage_timeline(db=Depends(get_db), days: int = Query(14, ge=1, le=90)):
    """Daily usage for the past N days."""
    now = datetime.now(timezone.utc)
    result = []
    for i in range(days):
        day_start = (now - timedelta(days=i)).replace(hour=0, minute=0, second=0, microsecond=0)
        day_end = day_start + timedelta(days=1)
        cur = db["ai_usage"].find({"created_at": {"$gte": day_start, "$lt": day_end}})
        calls = 0
        tokens = 0
        cost = 0.0
        cache_hits = 0
        async for doc in cur:
            calls += 1
            tokens += doc.get("in_tokens", 0) + doc.get("out_tokens", 0)
            cost += doc.get("est_cost_usd", 0)
            if doc.get("cache_hit"):
                cache_hits += 1
        result.append({
            "date": day_start.strftime("%Y-%m-%d"),
            "calls": calls,
            "tokens": tokens,
            "cost_usd": round(cost, 6),
            "cache_hits": cache_hits,
        })
    result.reverse()
    return {"days": result}


@router.get("/conversations")
async def ops_conversations(
    db=Depends(get_db),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    agent: str = Query(""),
    has_llm: bool | None = Query(None),
):
    """Customer conversations with LLM usage info."""
    query: dict = {}
    if agent:
        query["agent_slug"] = agent
    if has_llm is True:
        query["ai_provider"] = {"$ne": None}
    elif has_llm is False:
        query["ai_provider"] = None

    cur = db["customer_messages"].find(query).sort("created_at", -1).skip(offset).limit(limit)
    messages = []
    async for m in cur:
        messages.append({
            "id": str(m.get("_id")),
            "conversation_id": m.get("conversation_id"),
            "session_token": m.get("session_token"),
            "sender": m.get("sender"),
            "message": (m.get("message") or "")[:200],
            "intent": m.get("intent"),
            "tools_called": m.get("tools_called", []),
            "agent_slug": m.get("agent_slug"),
            "ai_provider": m.get("ai_provider"),
            "ai_model": m.get("ai_model"),
            "usage": m.get("usage"),
            "duration_ms": m.get("duration_ms"),
            "created_at": m.get("created_at"),
        })
    total = await db["customer_messages"].count_documents(query)
    return {"messages": messages, "total": total, "limit": limit, "offset": offset}


@router.get("/conversations/{conversation_id}")
async def ops_conversation_detail(conversation_id: str, db=Depends(get_db)):
    """Full conversation history for a given session."""
    cur = db["customer_messages"].find(
        {"conversation_id": conversation_id}).sort("created_at", 1)
    messages = []
    async for m in cur:
        messages.append({
            "id": str(m.get("_id")),
            "sender": m.get("sender"),
            "message": m.get("message") or m.get("content") or "",
            "intent": m.get("intent"),
            "tools_called": m.get("tools_called", []),
            "sources_used": m.get("sources_used", []),
            "agent_slug": m.get("agent_slug"),
            "ai_provider": m.get("ai_provider"),
            "ai_model": m.get("ai_model"),
            "usage": m.get("usage"),
            "duration_ms": m.get("duration_ms"),
            "lead_id": m.get("lead_id"),
            "created_at": m.get("created_at"),
        })
    # session metadata
    session = await db["customer_conversations"].find_one(
        {"_id": messages[0]["conversation_id"]} if messages else {"_id": "__none__"})
    return {"conversation_id": conversation_id, "session": session, "messages": messages}


@router.get("/agents/{slug}")
async def ops_agent_detail(slug: str, db=Depends(get_db)):
    """Per-agent detail: config, stats, recent usage from ai_usage by tag."""
    agent = await db["ai_agents"].find_one({"slug": slug})
    if not agent:
        return {"error": "agent not found"}

    stats = agent.get("stats") or {}
    # recent usage for this agent's tag
    now = datetime.now(timezone.utc)
    h24 = now - timedelta(hours=24)
    cur = db["ai_usage"].find({"tag": {"$regex": slug, "$options": "i"},
                               "created_at": {"$gte": h24}})
    calls_24h = 0
    tokens_24h = 0
    cost_24h = 0.0
    cache_24h = 0
    async for doc in cur:
        calls_24h += 1
        tokens_24h += doc.get("in_tokens", 0) + doc.get("out_tokens", 0)
        cost_24h += doc.get("est_cost_usd", 0)
        if doc.get("cache_hit"):
            cache_24h += 1

    # recent runs (agent-specific collection)
    runs = []
    run_col = f"{slug.replace('-', '_')}_runs"
    try:
        cur2 = db[run_col].find().sort("started_at", -1).limit(10)
        async for r in cur2:
            runs.append({
                "id": str(r.get("_id")),
                "status": r.get("status"),
                "triggered_by": r.get("triggered_by"),
                "started_at": r.get("started_at"),
                "finished_at": r.get("finished_at"),
                "results": {k: v for k, v in (r.get("results") or {}).items()
                            if not isinstance(v, list)} if isinstance(r.get("results"), dict) else {},
            })
    except Exception:
        pass

    return {
        "slug": slug,
        "name": agent.get("name"),
        "agent_type": agent.get("agent_type"),
        "enabled": agent.get("enabled"),
        "public_enabled": agent.get("public_enabled"),
        "description": agent.get("description"),
        "stats": stats,
        "usage_24h": {
            "calls": calls_24h,
            "tokens": tokens_24h,
            "cost_usd": round(cost_24h, 6),
            "cache_hits": cache_24h,
        },
        "recent_runs": runs,
    }


@router.get("/cache")
async def ops_cache(db=Depends(get_db)):
    """Cache health: embedding cache, response cache, KB version."""
    now = datetime.now(timezone.utc)
    h24 = now - timedelta(hours=24)
    emb_total = await db["embedding_cache"].count_documents({})
    emb_recent = await db["embedding_cache"].count_documents({"created_at": {"$gte": h24}})
    resp_total = await db["response_cache"].count_documents({})
    resp_recent = await db["response_cache"].count_documents({"created_ts": {"$gte": h24.timestamp()}})
    try:
        from app.services.ai_economy import kb_version
        ver = await kb_version(db)
    except Exception:
        ver = "0"
    return {
        "embedding_cache": {"total": emb_total, "last_24h": emb_recent},
        "response_cache": {"total": resp_total, "last_24h": resp_recent},
        "kb_version": ver,
    }


@router.get("/health")
async def ops_health(db=Depends(get_db)):
    """Quick health: LLM error rate, avg latency, provider availability."""
    now = datetime.now(timezone.utc)
    h1 = now - timedelta(hours=1)
    cur = db["ai_usage"].find({"created_at": {"$gte": h1}})
    errors = 0
    total = 0
    total_latency = 0
    async for doc in cur:
        total += 1
        total_latency += doc.get("latency_ms", 0)
        if doc.get("fallback_reason"):
            errors += 1
    return {
        "period": "1h",
        "total_calls": total,
        "error_rate": round(errors / max(1, total) * 100, 1),
        "avg_latency_ms": round(total_latency / max(1, total)),
    }
