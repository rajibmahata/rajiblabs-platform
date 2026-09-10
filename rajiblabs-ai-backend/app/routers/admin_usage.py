"""Admin AI Usage Dashboard — cost/latency/cache monitoring."""
from datetime import datetime, timezone, timedelta
from fastapi import APIRouter, Depends
from app.database import get_db
from app.routers.admin_auth import require_admin

router = APIRouter(prefix="/api/admin/usage", dependencies=[Depends(require_admin)])


@router.get("/today")
async def usage_today(db=Depends(get_db)):
    """LLM calls today, tokens, estimated cost, breakdown by tag."""
    now = datetime.now(timezone.utc)
    start_of_day = now.replace(hour=0, minute=0, second=0, microsecond=0)
    cur = db["ai_usage"].find({"created_at": {"$gte": start_of_day}})
    total_calls = 0
    total_in_tokens = 0
    total_out_tokens = 0
    total_cost = 0.0
    by_tag: dict[str, dict] = {}
    by_provider: dict[str, dict] = {}
    cache_hits = 0
    retrieval_hits = 0
    llm_fallbacks = 0
    async for doc in cur:
        total_calls += 1
        in_tok = doc.get("in_tokens", 0)
        out_tok = doc.get("out_tokens", 0)
        cost = doc.get("est_cost_usd", 0)
        tag = doc.get("tag", "unknown")
        provider = doc.get("provider", "unknown")
        total_in_tokens += in_tok
        total_out_tokens += out_tok
        total_cost += cost
        if doc.get("cache_hit"):
            cache_hits += 1
        if doc.get("retrieval_hit"):
            retrieval_hits += 1
        if doc.get("fallback_reason"):
            llm_fallbacks += 1
        # by tag
        if tag not in by_tag:
            by_tag[tag] = {"calls": 0, "in_tokens": 0, "out_tokens": 0, "cost": 0.0, "latency_ms": 0}
        by_tag[tag]["calls"] += 1
        by_tag[tag]["in_tokens"] += in_tok
        by_tag[tag]["out_tokens"] += out_tok
        by_tag[tag]["cost"] += cost
        by_tag[tag]["latency_ms"] += doc.get("latency_ms", 0)
        # by provider
        if provider not in by_provider:
            by_provider[provider] = {"calls": 0, "tokens": 0, "cost": 0.0}
        by_provider[provider]["calls"] += 1
        by_provider[provider]["tokens"] += in_tok + out_tok
        by_provider[provider]["cost"] += cost
    # compute avg latency per tag
    for tag_data in by_tag.values():
        if tag_data["calls"] > 0:
            tag_data["avg_latency_ms"] = round(tag_data["latency_ms"] / tag_data["calls"])
        else:
            tag_data["avg_latency_ms"] = 0
        del tag_data["latency_ms"]
    return {
        "date": start_of_day.isoformat(),
        "total_calls": total_calls,
        "total_in_tokens": total_in_tokens,
        "total_out_tokens": total_out_tokens,
        "total_tokens": total_in_tokens + total_out_tokens,
        "estimated_cost_usd": round(total_cost, 6),
        "cache_hits": cache_hits,
        "cache_hit_rate": round(cache_hits / max(1, total_calls) * 100, 1),
        "retrieval_hits": retrieval_hits,
        "llm_fallbacks": llm_fallbacks,
        "by_tag": by_tag,
        "by_provider": by_provider,
    }


@router.get("/week")
async def usage_week(db=Depends(get_db)):
    """Daily usage for the past 7 days."""
    now = datetime.now(timezone.utc)
    days = []
    for i in range(7):
        day_start = (now - timedelta(days=i)).replace(hour=0, minute=0, second=0, microsecond=0)
        day_end = day_start + timedelta(days=1)
        cur = db["ai_usage"].find({"created_at": {"$gte": day_start, "$lt": day_end}})
        calls = 0
        tokens = 0
        cost = 0.0
        async for doc in cur:
            calls += 1
            tokens += doc.get("in_tokens", 0) + doc.get("out_tokens", 0)
            cost += doc.get("est_cost_usd", 0)
        days.append({
            "date": day_start.strftime("%Y-%m-%d"),
            "calls": calls,
            "tokens": tokens,
            "cost_usd": round(cost, 6),
        })
    days.reverse()
    return {"days": days}


@router.get("/cache-stats")
async def cache_stats(db=Depends(get_db)):
    """Embedding cache + response cache hit rates."""
    from datetime import datetime, timezone
    now = datetime.now(timezone.utc)
    h24 = now - timedelta(hours=24)
    # Embedding cache
    emb_total = await db["embedding_cache"].count_documents({})
    emb_recent = await db["embedding_cache"].count_documents({"created_at": {"$gte": h24}})
    # Response cache
    resp_total = await db["response_cache"].count_documents({})
    resp_recent = await db["response_cache"].count_documents({"created_ts": {"$gte": h24.timestamp()}})
    # KB version
    from app.services.ai_economy import kb_version
    ver = await kb_version(db)
    return {
        "embedding_cache": {"total_entries": emb_total, "entries_24h": emb_recent},
        "response_cache": {"total_entries": resp_total, "entries_24h": resp_recent},
        "kb_version": ver,
    }


@router.get("/health")
async def usage_health(db=Depends(get_db)):
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
