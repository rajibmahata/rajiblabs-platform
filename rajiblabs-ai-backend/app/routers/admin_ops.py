"""Admin Agent & AI Operations Dashboard — execution visibility, usage, costs."""
from datetime import datetime, timezone, timedelta
from typing import Optional
from fastapi import APIRouter, Depends, Query, Body
from fastapi.responses import JSONResponse
from bson import ObjectId
from app.database import get_db, utcnow
from app.routers.admin_auth import require_admin

router = APIRouter(prefix="/api/admin/ops", dependencies=[Depends(require_admin)])

# ── Run collections (canonical list — never invent new ones) ──
RUN_COLLECTIONS = {
    "rajiblabs-profile": "profile_agent_runs",
    "rajiblabs-learning": "learning_agent_runs",
    "rajiblabs-marketing": "marketing_agent_runs",
}

# Prevent asyncio task GC: background tasks are held here until completion
_background_tasks: set = set()


def _oid(oid_str: str) -> ObjectId | None:
    try:
        return ObjectId(oid_str)
    except Exception:
        return None


# ══════════════════════════════════════════════════════════════════
# 1. SUMMARY (enhanced)
# ══════════════════════════════════════════════════════════════════

@router.get("/summary")
async def ops_summary(db=Depends(get_db)):
    """Full dashboard summary: today stats, week, agents, errors, system health."""
    now = datetime.now(timezone.utc)
    today = now.replace(hour=0, minute=0, second=0, microsecond=0)
    week_ago = now - timedelta(days=7)
    month_ago = now - timedelta(days=30)

    # ── ai_usage aggregates (today) ──
    cur = db["ai_usage"].find({"created_at": {"$gte": today}})
    today_calls = 0
    today_in = 0
    today_out = 0
    today_cost = 0.0
    today_cache = 0
    today_retrieval = 0
    today_fallback = 0
    today_llm = 0
    async for doc in cur:
        today_calls += 1
        it = doc.get("in_tokens", 0)
        ot = doc.get("out_tokens", 0)
        today_in += it
        today_out += ot
        today_cost += doc.get("est_cost_usd", 0)
        if doc.get("cache_hit"):
            today_cache += 1
        if doc.get("retrieval_hit"):
            today_retrieval += 1
        if doc.get("fallback_reason"):
            today_fallback += 1
        if doc.get("response_type") in ("LLM_SYNTHESIS", "LLM_FALLBACK"):
            today_llm += 1

    # ── ai_usage aggregates (month) ──
    month_calls = 0
    month_cost = 0.0
    month_in = 0
    month_out = 0
    cur_m = db["ai_usage"].find({"created_at": {"$gte": month_ago}})
    async for doc in cur_m:
        month_calls += 1
        month_cost += doc.get("est_cost_usd", 0)
        month_in += doc.get("in_tokens", 0)
        month_out += doc.get("out_tokens", 0)

    # ── week cost ──
    week_cost = 0.0
    week_calls = 0
    cur2 = db["ai_usage"].find({"created_at": {"$gte": week_ago}})
    async for doc in cur2:
        week_calls += 1
        week_cost += doc.get("est_cost_usd", 0)

    # ── response type breakdown (today) ──
    response_types: dict[str, int] = {}
    cur_rt = db["ai_usage"].find({"created_at": {"$gte": today}}, {"response_type": 1})
    async for doc in cur_rt:
        rt = doc.get("response_type") or "UNKNOWN"
        response_types[rt] = response_types.get(rt, 0) + 1

    # ── agents with health ──
    agents = []
    running_agents = 0
    failed_agents = 0
    async for a in db["ai_agents"].find().sort("created_at", 1):
        stats = a.get("stats") or {}
        errors = stats.get("errors", 0)
        if errors > 0:
            failed_agents += 1
        slug = a.get("slug", "")
        # check for running jobs
        run_col = RUN_COLLECTIONS.get(slug)
        has_running = False
        if run_col:
            try:
                has_running = await db[run_col].count_documents(
                    {"status": "running"}, limit=1) > 0
            except Exception:
                pass
        if has_running:
            running_agents += 1
        agents.append({
            "slug": slug,
            "name": a.get("name"),
            "agent_type": a.get("agent_type"),
            "enabled": a.get("enabled"),
            "public_enabled": a.get("public_enabled"),
            "turns": stats.get("turns", 0),
            "tool_calls": stats.get("tool_calls", 0),
            "leads": stats.get("leads", 0),
            "errors": errors,
            "runs": stats.get("runs", 0),
            "has_running_job": has_running,
        })

    # ── recent errors (last 24h) ──
    h24 = now - timedelta(hours=24)
    recent_errors = []
    cur_err = db["error_logs"].find(
        {"level": "error", "created_at": {"$gte": h24}}
    ).sort("created_at", -1).limit(10)
    async for e in cur_err:
        recent_errors.append({
            "id": str(e.get("_id")),
            "source": e.get("source"),
            "message": (e.get("message") or "")[:200],
            "created_at": e.get("created_at"),
        })

    # ── conversations ──
    total_sessions = await db["customer_conversations"].count_documents({})
    active_sessions_24h = await db["customer_conversations"].count_documents(
        {"last_message_at": {"$gte": today}})
    total_messages = await db["customer_messages"].count_documents({})

    # ── leads ──
    total_leads = await db["leads"].count_documents({})

    # ── system health ──
    h1 = now - timedelta(hours=1)
    health_cur = db["ai_usage"].find({"created_at": {"$gte": h1}})
    h_calls = 0
    h_latency = 0
    h_errors = 0
    async for doc in health_cur:
        h_calls += 1
        h_latency += doc.get("latency_ms", 0)
        if doc.get("fallback_reason"):
            h_errors += 1

    # ── cache ──
    emb_total = await db["embedding_cache"].count_documents({})
    resp_total = await db["response_cache"].count_documents({})

    return {
        "today": {
            "calls": today_calls,
            "in_tokens": today_in,
            "out_tokens": today_out,
            "total_tokens": today_in + today_out,
            "cost_usd": round(today_cost, 6),
            "cache_hits": today_cache,
            "cache_hit_rate": round(today_cache / max(1, today_calls) * 100, 1),
            "retrieval_hits": today_retrieval,
            "llm_fallbacks": today_fallback,
            "llm_calls": today_llm,
            "rag_only": today_calls - today_llm,
        },
        "week": {"cost_usd": round(week_cost, 6), "calls": week_calls},
        "month": {
            "cost_usd": round(month_cost, 6),
            "calls": month_calls,
            "in_tokens": month_in,
            "out_tokens": month_out,
            "total_tokens": month_in + month_out,
        },
        "response_types": response_types,
        "agents": agents,
        "agent_health": {
            "total": len(agents),
            "enabled": sum(1 for a in agents if a["enabled"]),
            "running": running_agents,
            "with_errors": failed_agents,
        },
        "conversations": {
            "total_messages": total_messages,
            "total_sessions": total_sessions,
            "active_24h": active_sessions_24h,
        },
        "leads_total": total_leads,
        "recent_errors": recent_errors,
        "system_health": {
            "calls_1h": h_calls,
            "avg_latency_ms": round(h_latency / max(1, h_calls)),
            "error_rate_1h": round(h_errors / max(1, h_calls) * 100, 1),
            "embedding_cache": emb_total,
            "response_cache": resp_total,
        },
    }


# ══════════════════════════════════════════════════════════════════
# 2. USAGE TIMELINE
# ══════════════════════════════════════════════════════════════════

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
        llm_calls = 0
        async for doc in cur:
            calls += 1
            tokens += doc.get("in_tokens", 0) + doc.get("out_tokens", 0)
            cost += doc.get("est_cost_usd", 0)
            if doc.get("cache_hit"):
                cache_hits += 1
            if doc.get("response_type") in ("LLM_SYNTHESIS", "LLM_FALLBACK"):
                llm_calls += 1
        result.append({
            "date": day_start.strftime("%Y-%m-%d"),
            "calls": calls,
            "tokens": tokens,
            "cost_usd": round(cost, 6),
            "cache_hits": cache_hits,
            "llm_calls": llm_calls,
            "rag_calls": calls - llm_calls,
        })
    result.reverse()
    return {"days": result}


# ══════════════════════════════════════════════════════════════════
# 3. ANALYTICS (month with date range)
# ══════════════════════════════════════════════════════════════════

@router.get("/analytics")
async def ops_analytics(
    db=Depends(get_db),
    start: Optional[str] = Query(None),
    end: Optional[str] = Query(None),
):
    """Detailed analytics: cost, tokens, latency, breakdown by agent/model/response_type."""
    now = datetime.now(timezone.utc)
    try:
        dt_start = datetime.fromisoformat(start) if start else (now - timedelta(days=30))
        dt_end = datetime.fromisoformat(end) if end else now
    except Exception:
        dt_start = now - timedelta(days=30)
        dt_end = now

    if dt_start.tzinfo is None:
        dt_start = dt_start.replace(tzinfo=timezone.utc)
    if dt_end.tzinfo is None:
        dt_end = dt_end.replace(tzinfo=timezone.utc)

    query = {"created_at": {"$gte": dt_start, "$lt": dt_end}}
    cur = db["ai_usage"].find(query)

    total_calls = 0
    total_in = 0
    total_out = 0
    total_cost = 0.0
    total_latency = 0
    by_agent: dict[str, dict] = {}
    by_model: dict[str, dict] = {}
    by_response_type: dict[str, int] = {}
    cache_hits = 0
    llm_fallbacks = 0

    async for doc in cur:
        total_calls += 1
        it = doc.get("in_tokens", 0)
        ot = doc.get("out_tokens", 0)
        c = doc.get("est_cost_usd", 0)
        lat = doc.get("latency_ms", 0)
        total_in += it
        total_out += ot
        total_cost += c
        total_latency += lat
        if doc.get("cache_hit"):
            cache_hits += 1
        if doc.get("fallback_reason"):
            llm_fallbacks += 1

        tag = doc.get("tag", "unknown")
        if tag not in by_agent:
            by_agent[tag] = {"calls": 0, "tokens": 0, "cost": 0.0, "latency": 0}
        by_agent[tag]["calls"] += 1
        by_agent[tag]["tokens"] += it + ot
        by_agent[tag]["cost"] += c
        by_agent[tag]["latency"] += lat

        model = doc.get("model", "unknown")
        if model not in by_model:
            by_model[model] = {"calls": 0, "tokens": 0, "cost": 0.0}
        by_model[model]["calls"] += 1
        by_model[model]["tokens"] += it + ot
        by_model[model]["cost"] += c

        rt = doc.get("response_type") or "UNKNOWN"
        by_response_type[rt] = by_response_type.get(rt, 0) + 1

    # compute averages
    for v in by_agent.values():
        v["avg_latency_ms"] = round(v["latency"] / max(1, v["calls"]))
        v["cost"] = round(v["cost"], 6)
        del v["latency"]
    for v in by_model.values():
        v["cost"] = round(v["cost"], 6)

    # top agent by cost
    top_agent = max(by_agent.items(), key=lambda x: x[1]["cost"])[0] if by_agent else None

    return {
        "period": {"start": dt_start.isoformat(), "end": dt_end.isoformat()},
        "totals": {
            "calls": total_calls,
            "in_tokens": total_in,
            "out_tokens": total_out,
            "total_tokens": total_in + total_out,
            "cost_usd": round(total_cost, 6),
            "avg_tokens_per_request": round((total_in + total_out) / max(1, total_calls)),
            "avg_latency_ms": round(total_latency / max(1, total_calls)),
            "cache_hit_rate": round(cache_hits / max(1, total_calls) * 100, 1),
            "llm_fallback_rate": round(llm_fallbacks / max(1, total_calls) * 100, 1),
        },
        "by_agent": dict(sorted(by_agent.items(), key=lambda x: x[1]["cost"], reverse=True)),
        "by_model": dict(sorted(by_model.items(), key=lambda x: x[1]["cost"], reverse=True)),
        "by_response_type": by_response_type,
        "top_cost_agent": top_agent,
    }


# ══════════════════════════════════════════════════════════════════
# 4. AGENTS (health + control)
# ══════════════════════════════════════════════════════════════════

@router.get("/agents")
async def ops_agents(db=Depends(get_db)):
    """All agents with health status, last run, running status."""
    now = datetime.now(timezone.utc)
    agents = []
    async for a in db["ai_agents"].find().sort("created_at", 1):
        slug = a.get("slug", "")
        stats = a.get("stats") or {}
        run_col = RUN_COLLECTIONS.get(slug)
        last_run = None
        has_running = False
        running_since = None
        if run_col:
            try:
                lr = await db[run_col].find_one(sort=[("started_at", -1)])
                if lr:
                    last_run = {
                        "id": str(lr.get("_id")),
                        "status": lr.get("status"),
                        "started_at": lr.get("started_at"),
                        "finished_at": lr.get("finished_at"),
                        "triggered_by": lr.get("triggered_by"),
                    }
                running = await db[run_col].find_one({"status": "running"})
                if running:
                    has_running = True
                    running_since = running.get("started_at")
            except Exception:
                pass
        # 24h usage
        h24 = now - timedelta(hours=24)
        cur_u = db["ai_usage"].find(
            {"tag": {"$regex": slug, "$options": "i"}, "created_at": {"$gte": h24}})
        calls_24h = 0
        tokens_24h = 0
        cost_24h = 0.0
        async for doc in cur_u:
            calls_24h += 1
            tokens_24h += doc.get("in_tokens", 0) + doc.get("out_tokens", 0)
            cost_24h += doc.get("est_cost_usd", 0)

        agents.append({
            "slug": slug,
            "name": a.get("name"),
            "agent_type": a.get("agent_type"),
            "enabled": a.get("enabled"),
            "public_enabled": a.get("public_enabled"),
            "description": (a.get("description") or "")[:120],
            "stats": stats,
            "last_run": last_run,
            "has_running_job": has_running,
            "running_since": running_since,
            "usage_24h": {"calls": calls_24h, "tokens": tokens_24h, "cost_usd": round(cost_24h, 6)},
        })
    return {"agents": agents}


@router.put("/agents/{slug}/toggle")
async def ops_agent_toggle(slug: str, db=Depends(get_db)):
    """Enable or disable an agent."""
    agent = await db["ai_agents"].find_one({"slug": slug})
    if not agent:
        return JSONResponse({"error": "agent not found"}, status_code=404)
    new_state = not agent.get("enabled", True)
    await db["ai_agents"].update_one(
        {"slug": slug}, {"$set": {"enabled": new_state, "updated_at": utcnow()}})
    from app.services.notify import audit
    try:
        await audit("admin", "AGENT_TOGGLE", slug, {"enabled": new_state})
    except Exception:
        pass
    return {"slug": slug, "enabled": new_state}


@router.post("/agents/{slug}/run")
async def ops_agent_run(slug: str, db=Depends(get_db)):
    """Trigger an immediate agent run (non-blocking)."""
    agent = await db["ai_agents"].find_one({"slug": slug})
    if not agent:
        return JSONResponse({"error": "agent not found"}, status_code=404)
    if not agent.get("enabled"):
        return JSONResponse({"error": "agent is disabled"}, status_code=400)
    # Check if already running
    run_col = RUN_COLLECTIONS.get(slug)
    if run_col:
        try:
            running = await db[run_col].find_one({"status": "running"})
            if running:
                return JSONResponse({"error": "agent already running", "run_id": str(running["_id"])}, status_code=409)
        except Exception:
            pass
    # Dispatch to the appropriate agent runner
    # All agent functions accept only (triggered_by: str) — no db parameter.
    import asyncio
    task = None
    try:
        if slug == "rajiblabs-profile":
            from app.services.profile_agent import run_profile_agent
            task = asyncio.create_task(run_profile_agent(triggered_by="admin"))
        elif slug == "rajiblabs-learning":
            from app.services.learning_agent import run_daily as run_learning
            task = asyncio.create_task(run_learning(triggered_by="admin"))
        elif slug == "rajiblabs-marketing":
            from app.services.marketing_agent import run_daily as run_marketing
            task = asyncio.create_task(run_marketing(triggered_by="admin"))
        else:
            return JSONResponse({"error": f"run not implemented for {slug}"}, status_code=400)
    except Exception as e:
        return JSONResponse({"error": f"dispatch failed: {str(e)[:200]}"}, status_code=500)
    # Prevent GC of the background task
    if task is not None:
        _background_tasks.add(task)
        task.add_done_callback(_background_tasks.discard)

    from app.services.notify import audit
    try:
        await audit("admin", "AGENT_RUN_TRIGGERED", slug, {})
    except Exception:
        pass
    return {"slug": slug, "status": "dispatched"}


# ══════════════════════════════════════════════════════════════════
# 5. UNIFIED RUNS (cross-agent history)
# ══════════════════════════════════════════════════════════════════

@router.get("/runs")
async def ops_runs(
    db=Depends(get_db),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    agent: str = Query(""),
    status: str = Query(""),
    date_from: Optional[str] = Query(None),
    date_to: Optional[str] = Query(None),
):
    """Unified cross-agent run history. Merges profile/learning/marketing runs."""
    query: dict = {}
    if agent:
        # filter to specific collection
        collections = [RUN_COLLECTIONS[agent]] if agent in RUN_COLLECTIONS else list(RUN_COLLECTIONS.values())
    else:
        collections = list(RUN_COLLECTIONS.values())
    if status:
        query["status"] = status
    if date_from:
        try:
            dt = datetime.fromisoformat(date_from).replace(tzinfo=timezone.utc)
            query.setdefault("started_at", {})["$gte"] = dt
        except Exception:
            pass
    if date_to:
        try:
            dt = datetime.fromisoformat(date_to).replace(tzinfo=timezone.utc)
            query.setdefault("started_at", {})["$lte"] = dt
        except Exception:
            pass

    # Aggregate across all run collections
    all_runs = []
    slug_map = {v: k for k, v in RUN_COLLECTIONS.items()}
    for col_name in collections:
        try:
            cur = db[col_name].find(query).sort("started_at", -1).limit(limit + offset)
            async for r in cur:
                all_runs.append({
                    "id": str(r.get("_id")),
                    "agent_slug": slug_map.get(col_name, col_name),
                    "status": r.get("status"),
                    "triggered_by": r.get("triggered_by"),
                    "started_at": r.get("started_at"),
                    "finished_at": r.get("finished_at"),
                    "sources_inspected": r.get("sources_inspected", []),
                    "proposed": r.get("proposed", 0),
                    "applied": r.get("applied", 0),
                    "errors": r.get("errors", []),
                    "detail": (r.get("detail") or "")[:200],
                })
        except Exception:
            pass

    # Sort by started_at and paginate
    all_runs.sort(key=lambda r: r.get("started_at") or datetime.min.replace(tzinfo=timezone.utc), reverse=True)
    total = len(all_runs)
    paginated = all_runs[offset:offset + limit]
    return {"runs": paginated, "total": total, "limit": limit, "offset": offset}


@router.get("/runs/{run_id}")
async def ops_run_detail(run_id: str, db=Depends(get_db)):
    """Detail for a single run across any agent collection."""
    oid = _oid(run_id)
    if not oid:
        return JSONResponse({"error": "invalid run id"}, status_code=400)
    for col_name in RUN_COLLECTIONS.values():
        try:
            doc = await db[col_name].find_one({"_id": oid})
            if doc:
                slug_map = {v: k for k, v in RUN_COLLECTIONS.items()}
                return {
                    "id": str(doc.get("_id")),
                    "agent_slug": slug_map.get(col_name, col_name),
                    "status": doc.get("status"),
                    "triggered_by": doc.get("triggered_by"),
                    "started_at": doc.get("started_at"),
                    "finished_at": doc.get("finished_at"),
                    "sources_inspected": doc.get("sources_inspected", []),
                    "proposed": doc.get("proposed", 0),
                    "applied": doc.get("applied", 0),
                    "errors": doc.get("errors", []),
                    "health": doc.get("health"),
                    "gh_result": doc.get("gh_result"),
                    "resume_hash": doc.get("resume_hash"),
                    "detail": doc.get("detail"),
                    "results": doc.get("results"),
                    "full_document": {k: str(v) if isinstance(v, ObjectId) else v
                                       for k, v in doc.items() if k != "_id"},
                }
        except Exception:
            pass
    return JSONResponse({"error": "run not found"}, status_code=404)


# ══════════════════════════════════════════════════════════════════
# 6. CONVERSATIONS
# ══════════════════════════════════════════════════════════════════

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
    session = None
    if messages:
        session = await db["customer_conversations"].find_one(
            {"_id": messages[0].get("conversation_id")})
    return {"conversation_id": conversation_id, "session": session, "messages": messages}


# ══════════════════════════════════════════════════════════════════
# 7. AGENT DETAIL (per-agent)
# ══════════════════════════════════════════════════════════════════

@router.get("/agents/{slug}")
async def ops_agent_detail(slug: str, db=Depends(get_db)):
    """Per-agent detail: config, stats, usage, runs, token breakdown."""
    agent = await db["ai_agents"].find_one({"slug": slug})
    if not agent:
        return JSONResponse({"error": "agent not found"}, status_code=404)

    stats = agent.get("stats") or {}
    now = datetime.now(timezone.utc)
    h24 = now - timedelta(hours=24)

    # 24h usage breakdown
    cur = db["ai_usage"].find({"tag": {"$regex": slug, "$options": "i"},
                               "created_at": {"$gte": h24}})
    usage_24h = {"calls": 0, "in_tokens": 0, "out_tokens": 0, "cost": 0.0,
                 "cache_hits": 0, "llm_calls": 0, "by_model": {}}
    async for doc in cur:
        usage_24h["calls"] += 1
        it = doc.get("in_tokens", 0)
        ot = doc.get("out_tokens", 0)
        usage_24h["in_tokens"] += it
        usage_24h["out_tokens"] += ot
        usage_24h["cost"] += doc.get("est_cost_usd", 0)
        if doc.get("cache_hit"):
            usage_24h["cache_hits"] += 1
        if doc.get("response_type") in ("LLM_SYNTHESIS", "LLM_FALLBACK"):
            usage_24h["llm_calls"] += 1
        m = doc.get("model", "unknown")
        if m not in usage_24h["by_model"]:
            usage_24h["by_model"][m] = {"calls": 0, "tokens": 0, "cost": 0.0}
        usage_24h["by_model"][m]["calls"] += 1
        usage_24h["by_model"][m]["tokens"] += it + ot
        usage_24h["by_model"][m]["cost"] += doc.get("est_cost_usd", 0)
    usage_24h["cost"] = round(usage_24h["cost"], 6)
    for v in usage_24h["by_model"].values():
        v["cost"] = round(v["cost"], 6)

    # recent runs
    run_col = RUN_COLLECTIONS.get(slug)
    runs = []
    if run_col:
        try:
            cur2 = db[run_col].find().sort("started_at", -1).limit(15)
            async for r in cur2:
                runs.append({
                    "id": str(r.get("_id")),
                    "status": r.get("status"),
                    "triggered_by": r.get("triggered_by"),
                    "started_at": r.get("started_at"),
                    "finished_at": r.get("finished_at"),
                    "sources_inspected": r.get("sources_inspected", []),
                    "proposed": r.get("proposed", 0),
                    "applied": r.get("applied", 0),
                    "errors": r.get("errors", []),
                    "detail": (r.get("detail") or "")[:150],
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
        "usage_24h": usage_24h,
        "recent_runs": runs,
    }


# ══════════════════════════════════════════════════════════════════
# 8. CACHE
# ══════════════════════════════════════════════════════════════════

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


# ══════════════════════════════════════════════════════════════════
# 9. HEALTH
# ══════════════════════════════════════════════════════════════════

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


# ══════════════════════════════════════════════════════════════════
# 10. TOKEN BUDGET
# ══════════════════════════════════════════════════════════════════

@router.get("/token-budget")
async def ops_token_budget_get(db=Depends(get_db)):
    """Get current token budget configuration."""
    doc = await db["site_settings"].find_one({"key": "token_budget"})
    budget = (doc or {}).get("value") or {}
    return {
        "daily_token_budget": budget.get("daily_token_budget", 0),
        "monthly_token_budget": budget.get("monthly_token_budget", 0),
        "per_agent_budget": budget.get("per_agent_budget", {}),
        "per_operation_budget": budget.get("per_operation_budget", {}),
        "max_tokens_per_request": budget.get("max_tokens_per_request", 4000),
        "allowed_models": budget.get("allowed_models", ["gpt-5-nano", "gpt-4o-mini", "deepseek-chat"]),
        "fallback_model": budget.get("fallback_model", "gpt-4o-mini"),
        "llm_enabled": budget.get("llm_enabled", True),
        "rag_first_enforced": budget.get("rag_first_enforced", True),
    }


@router.put("/token-budget")
async def ops_token_budget_set(db=Depends(get_db), body: dict = Body(...)):
    """Update token budget configuration."""
    allowed = {
        "daily_token_budget", "monthly_token_budget", "per_agent_budget",
        "per_operation_budget", "max_tokens_per_request", "allowed_models",
        "fallback_model", "llm_enabled", "rag_first_enforced",
    }
    patch = {k: v for k, v in (body or {}).items() if k in allowed}
    if not patch:
        return JSONResponse({"error": "no valid fields"}, status_code=400)
    await db["site_settings"].update_one(
        {"key": "token_budget"},
        {"$set": {"value": patch, "updated_at": utcnow()}},
        upsert=True)
    from app.services.notify import audit
    try:
        await audit("admin", "TOKEN_BUDGET_UPDATE", "token_budget", {"fields": sorted(patch)})
    except Exception:
        pass
    return {"status": "updated", "fields": sorted(patch)}


@router.get("/token-budget/check")
async def ops_token_budget_check(
    db=Depends(get_db),
    agent: str = Query(""),
    tokens_requested: int = Query(0),
):
    """Check if a token request is within budget. Returns allowed + remaining."""
    doc = await db["site_settings"].find_one({"key": "token_budget"})
    budget = (doc or {}).get("value") or {}
    now = datetime.now(timezone.utc)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    month_start = today_start.replace(day=1)

    # Current usage
    today_usage = db["ai_usage"].aggregate([
        {"$match": {"created_at": {"$gte": today_start}}},
        {"$group": {"_id": None, "total_tokens": {"$sum": {"$add": ["$in_tokens", "$out_tokens"]}}}}
    ])
    today_tokens = 0
    async for doc_t in today_usage:
        today_tokens = doc_t.get("total_tokens", 0)

    month_usage = db["ai_usage"].aggregate([
        {"$match": {"created_at": {"$gte": month_start}}},
        {"$group": {"_id": None, "total_tokens": {"$sum": {"$add": ["$in_tokens", "$out_tokens"]}}}}
    ])
    month_tokens = 0
    async for doc_m in month_usage:
        month_tokens = doc_m.get("total_tokens", 0)

    daily_limit = budget.get("daily_token_budget", 0)
    monthly_limit = budget.get("monthly_token_budget", 0)
    llm_enabled = budget.get("llm_enabled", True)
    rag_enforced = budget.get("rag_first_enforced", True)

    allowed = True
    reason = ""
    if not llm_enabled:
        allowed = False
        reason = "LLM is disabled by admin"
    elif daily_limit > 0 and (today_tokens + tokens_requested) > daily_limit:
        allowed = False
        reason = f"Daily budget exceeded ({today_tokens}/{daily_limit})"
    elif monthly_limit > 0 and (month_tokens + tokens_requested) > monthly_limit:
        allowed = False
        reason = f"Monthly budget exceeded ({month_tokens}/{monthly_limit})"

    return {
        "allowed": allowed,
        "reason": reason,
        "today_tokens": today_tokens,
        "month_tokens": month_tokens,
        "daily_limit": daily_limit,
        "monthly_limit": monthly_limit,
        "daily_remaining": max(0, daily_limit - today_tokens) if daily_limit > 0 else -1,
        "monthly_remaining": max(0, monthly_limit - month_tokens) if monthly_limit > 0 else -1,
        "rag_first_enforced": rag_enforced,
    }


# ══════════════════════════════════════════════════════════════════
# 11. RESPONSE TYPES (RAG-first analytics)
# ══════════════════════════════════════════════════════════════════

@router.get("/response-types")
async def ops_response_types(
    db=Depends(get_db),
    days: int = Query(7, ge=1, le=90),
):
    """RAG-first analytics: how many requests were RAG_ONLY vs LLM."""
    now = datetime.now(timezone.utc)
    start = now - timedelta(days=days)
    cur = db["ai_usage"].find({"created_at": {"$gte": start}}, {"response_type": 1, "created_at": 1})
    by_type: dict[str, int] = {}
    daily: dict[str, dict[str, int]] = {}
    async for doc in cur:
        rt = doc.get("response_type") or "UNKNOWN"
        by_type[rt] = by_type.get(rt, 0) + 1
        day = doc.get("created_at", now).strftime("%Y-%m-%d")
        if day not in daily:
            daily[day] = {}
        daily[day][rt] = daily[day].get(rt, 0) + 1
    total = sum(by_type.values())
    llm_total = by_type.get("LLM_SYNTHESIS", 0) + by_type.get("LLM_FALLBACK", 0)
    return {
        "period_days": days,
        "total": total,
        "by_type": by_type,
        "llm_percentage": round(llm_total / max(1, total) * 100, 1),
        "rag_percentage": round((total - llm_total) / max(1, total) * 100, 1),
        "daily": dict(sorted(daily.items())),
    }


# ══════════════════════════════════════════════════════════════════
# 12. ERRORS (recent, linked to system logs)
# ══════════════════════════════════════════════════════════════════

@router.get("/errors")
async def ops_errors(
    db=Depends(get_db),
    limit: int = Query(30, ge=1, le=100),
    agent: str = Query(""),
):
    """Recent errors from error_logs, filterable by agent/source."""
    query: dict = {"level": "error"}
    if agent:
        query["source"] = {"$regex": agent, "$options": "i"}
    cur = db["error_logs"].find(query).sort("created_at", -1).limit(limit)
    errors = []
    async for e in cur:
        errors.append({
            "id": str(e.get("_id")),
            "source": e.get("source"),
            "message": (e.get("message") or "")[:300],
            "details": (e.get("details") or "")[:300],
            "created_at": e.get("created_at"),
        })
    return {"errors": errors, "total": len(errors)}
