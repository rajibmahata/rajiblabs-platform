"""RajibLabs Marketing Intelligence Agent — autonomous promotional flow.

Token-efficient by design: deterministic checks (SMTP, due campaigns,
audience, fresh content, duplicates) run first and NO-ACTION early-outs
before any LLM call. The LLM only drafts from retrieved verified knowledge
and every claim/link is validated before a campaign is created.

Reuses: AIService (AI Orchestrator), rag_query (shared RAG), customer_leads,
email_service (SMTP), audit/notify. Default mode is DRAFT for admin approval.
"""
import hashlib
import logging
import re

from app.database import get_db, utcnow
from app.services.notify import audit, log_error, notify

log = logging.getLogger("rajiblabs")

# Weekday content rotation (Mon=0). Weekends only announce or skip.
WEEKDAY_TOPICS = {
    0: ("project", "Project / case study"),
    1: ("technical", "Technical insight"),
    2: ("ai", "AI / automation insight"),
    3: ("architecture", "Architecture insight"),
    4: ("product", "RajibLabs product / capability"),
    5: ("announcement", "Announcement or skip"),
    6: ("announcement", "Announcement or skip"),
}

DEFAULT_SETTINGS = {
    "enabled": True,
    "hour": 9, "minute": 0,
    "lookback_days": 14,
    "max_per_7_days": 2,
    "min_interval_hours": 48,
    "auto_send": False,  # safe default: drafts need approval
    "weekend_send": False,
}


async def get_settings_doc(db) -> dict:
    doc = await db["marketing_settings"].find_one({"_id": "singleton"})
    merged = dict(DEFAULT_SETTINGS)
    if doc:
        merged.update({k: v for k, v in doc.items() if k in DEFAULT_SETTINGS})
    return merged


def _content_hash(*parts: str) -> str:
    return hashlib.sha256("|".join(p or "" for p in parts).encode()).hexdigest()[:16]


async def _record_run(db, status: str, detail: dict) -> str:
    res = await db["marketing_agent_runs"].insert_one({
        "status": status, "detail": detail,
        "started_at": utcnow(), "finished_at": utcnow()})
    return str(res.inserted_id)


async def discover_content(db, topic_key: str, lookback_days: int) -> dict | None:
    """Find one meaningful, recent, verified content item. None → skip day."""
    from datetime import timedelta
    from app.database import utcnow as _now
    since = _now() - timedelta(days=lookback_days)
    # 1. recent published projects/products (verified site content first)
    for coll, kind in (("projects", "project"), ("portfolio", "project")):
        try:
            cur = db[coll].find({"$or": [{"published": True}, {"status": "published"}]})
            best = None
            async for d in cur.sort("updated_at", -1).limit(10):
                if (d.get("updated_at") or d.get("created_at") or since) >= since:
                    best = (d, kind)
                    break
            if best:
                d, kind = best
                name = d.get("name") or d.get("title") or "Untitled"
                return {"kind": kind, "id": str(d.get("_id")),
                        "title": name, "slug": d.get("slug", ""),
                        "body": (d.get("short_description") or d.get("description") or "")[:1500],
                        "url": f"https://rajiblabs.com/{'products' if coll == 'products' else 'portfolio'}/{d.get('slug', '')}",
                        "tech": ", ".join((d.get("technologies") or d.get("tech_stack") or [])[:6])}
        except Exception as e:
            log.warning("marketing discovery %s failed: %s", coll, e)
    # 2. recent knowledge documents (services, announcements)
    try:
        async for d in db["knowledge_documents"].find(
                {"status": "active"}).sort("updated_at", -1).limit(10):
            if (d.get("updated_at") or since) >= since and (d.get("content") or "").strip():
                return {"kind": "knowledge", "id": str(d.get("_id")),
                        "title": d.get("title", ""), "slug": "",
                        "body": (d.get("content") or "")[:1500],
                        "url": d.get("url") or "https://rajiblabs.com", "tech": ""}
    except Exception as e:
        log.warning("marketing discovery knowledge failed: %s", e)
    return None


async def draft_content(item: dict) -> dict | None:
    """One LLM call: evidence-only promotional draft. None on any failure."""
    try:
        from app.services.lead_ai import AIService
        svc = AIService()
        if not svc.configured:
            return None
        evidence = (f"Title: {item['title']}\nURL: {item['url']}\n"
                    f"Tech: {item.get('tech', '')}\nVerified description:\n{item['body'][:2000]}")
        out = await svc._complete(
            [{"role": "system", "content": (
                "Write a short professional promotional email as JSON with keys: "
                "subject (<=70 chars), preheader (<=120 chars), "
                "html (<=300 words, simple <p><a><strong><ul><li> only), "
                "text (plain version). Rules: use ONLY the verified evidence; "
                "never invent customers, metrics, testimonials, revenue, partnerships "
                "or capabilities; include the given URL exactly once; professional tone; "
                "no hype, no emojis. Return JSON only.")},
             {"role": "user", "content": evidence}],
            max_tokens=900, temperature=0.4, tag="marketing-draft")
        data = out.get("data", {})
        if not data.get("subject") or not (data.get("html") or data.get("text")):
            return None
        return {"subject": str(data["subject"])[:200],
                "preheader": str(data.get("preheader", ""))[:300],
                "html": str(data.get("html", ""))[:8000],
                "text": str(data.get("text", ""))[:8000]}
    except Exception as e:
        log.warning("marketing draft failed: %s", e)
        return None


def validate_draft(draft: dict, item: dict) -> tuple[bool, str]:
    """Factual guardrails: known URL present, no invented links/domains."""
    html = (draft.get("html") or "") + (draft.get("text") or "")
    urls = re.findall(r"https?://[^\s\"'<>]+", html)
    allowed_hosts = ("rajiblabs.com",)
    for u in urls:
        try:
            from urllib.parse import urlparse
            host = (urlparse(u).hostname or "").lower()
        except Exception:
            return False, f"unparseable URL: {u[:80]}"
        if host and not host.endswith(allowed_hosts) and host not in (
                "wa.me", "github.com", "linkedin.com"):
            return False, f"external URL not allowlisted: {u[:80]}"
    if item.get("url", "") not in html:
        return False, "verified source URL missing from draft"
    banned = ("guarantee", "best in", "#1", "100%", "risk-free", "act now",
              "limited time", "!!!", "testimonial")
    low = html.lower()
    if any(b in low for b in banned):
        return False, "hype language detected"
    return True, "ok"


async def run_daily(triggered_by: str = "scheduler") -> dict:
    """Autonomous daily flow. Returns a small result dict; never raises."""
    db = get_db()
    from datetime import datetime, timezone
    from app.services import email_service as _es
    from app.services.marketing import (eligible_filter, sanitize_html,
                                        segment_query)

    async def _noop(reason: str, extra: dict | None = None) -> dict:
        detail = {"triggered_by": triggered_by, "action": "no_action",
                  "reason": reason, **(extra or {})}
        rid = await _record_run(db, "no_action", detail)
        return {"run_id": rid, **detail}

    try:
        cfg = await get_settings_doc(db)
        if not cfg.get("enabled"):
            return await _noop("agent disabled")
        if not _es.is_configured():
            return await _noop("SMTP not configured")

        # 1. due scheduled campaigns first (explicit admin intent wins)
        now = utcnow()
        due = [d async for d in db["email_campaigns"].find(
            {"status": {"$in": ["ready", "scheduled"]}}).limit(20)]
        sent_any = []
        for c in due:
            sched = c.get("schedule_at")
            if c.get("status") == "scheduled" and sched:
                try:
                    if isinstance(sched, str):
                        sched = datetime.fromisoformat(sched)
                    if sched.tzinfo is None:
                        sched = sched.replace(tzinfo=timezone.utc)
                    if sched > now:
                        continue
                except Exception:
                    pass
            from app.services.marketing import run_campaign
            res = await run_campaign(db, str(c["_id"]), decided_by="marketing-agent")
            sent_any.append({"campaign": str(c["_id"]), **res})
        if sent_any:
            rid = await _record_run(db, "sent_scheduled",
                                    {"triggered_by": triggered_by, "campaigns": sent_any})
            return {"run_id": rid, "action": "sent_scheduled", "campaigns": sent_any}

        # 2. eligible audience?
        eligible = await db["customer_leads"].count_documents(eligible_filter())
        if not eligible:
            return await _noop("no eligible audience", {"eligible": 0})

        # 3. weekend/cadence gate
        weekday = now.weekday()
        if weekday >= 5 and not cfg.get("weekend_send"):
            return await _noop("weekend skip", {"eligible": eligible})
        topic_key, topic_label = WEEKDAY_TOPICS.get(weekday, ("announcement", "Announcement"))

        # 4. content discovery (no content → NO ACTION, no LLM spent)
        item = await discover_content(db, topic_key, int(cfg.get("lookback_days", 14)))
        if not item:
            return await _noop("no fresh promotional content",
                               {"eligible": eligible, "topic": topic_label})

        # 5. duplicate check (same source recently campaigned?)
        chash = _content_hash(item["kind"], item["id"], item["title"])
        dup = await db["email_campaigns"].find_one(
            {"content_hash": chash, "status": {"$nin": ["cancelled", "failed"]}})
        if dup:
            return await _noop("duplicate content", {"eligible": eligible,
                                                     "title": item["title"]})

        # 6. RAG grounding (small, relevant-only) — enriches, never replaces evidence
        try:
            from app.services import rag_query as _rag
            chunks = await _rag.retrieve(item["title"], top_k=3)
            if chunks:
                extra = "\n".join(c.get("content", "")[:500] for c in chunks[:2])
                item["body"] = (item["body"] + "\n" + extra)[:3000]
        except Exception as e:
            log.warning("marketing RAG skipped: %s", e)

        # 7. AI draft (single call) + validation
        draft = await draft_content(item)
        if not draft:
            return await _noop("draft generation failed", {"title": item["title"]})
        ok, reason = validate_draft(draft, item)
        if not ok:
            await _record_run(db, "validation_failed",
                              {"triggered_by": triggered_by, "title": item["title"],
                               "reason": reason})
            try:
                await notify("MarketingDraftBlocked",
                             f"Draft blocked: {item['title']}", reason[:200],
                             "campaign", "")
            except Exception:
                pass
            return {"action": "validation_failed", "reason": reason}

        # 8. create campaign (DRAFT default; auto only when explicitly enabled)
        camp = {"name": f"{topic_label}: {item['title']}"[:200],
                "template_id": None, "subject": draft["subject"],
                "html": sanitize_html(draft["html"]),
                "text": (draft.get("text") or "")[:20000],
                "audience": {"segment": "all_opted_in", "tags": [], "statuses": []},
                "max_per_7_days": int(cfg.get("max_per_7_days", 2)),
                "min_interval_hours": int(cfg.get("min_interval_hours", 48)),
                "schedule_at": None, "auto_send": bool(cfg.get("auto_send")),
                "status": "draft", "content_hash": chash,
                "project_name": item["title"], "project_url": item.get("url", ""),
                "stats": {"queued": 0, "sent": 0, "failed": 0, "opened": 0,
                          "clicked": 0, "unsubscribed": 0},
                "created_at": now, "updated_at": now, "created_by": "marketing-agent",
                "decided_by": None, "decided_at": None, "sent_at": None}
        res = await db["email_campaigns"].insert_one(camp)
        cid = str(res.inserted_id)
        try:
            await audit("marketing-agent", "CAMPAIGN_CREATE", cid,
                        {"name": camp["name"], "topic": topic_label},
                        event_type="CAMPAIGN_CREATE")
        except Exception:
            pass
        if cfg.get("auto_send"):
            from app.services.marketing import run_campaign
            result = await run_campaign(db, cid, decided_by="marketing-agent(auto)")
            rid = await _record_run(db, "auto_sent",
                                    {"triggered_by": triggered_by, "campaign_id": cid,
                                     **result})
            return {"run_id": rid, "action": "auto_sent", "campaign_id": cid, **result}
        rid = await _record_run(db, "draft_created",
                                {"triggered_by": triggered_by, "campaign_id": cid,
                                 "title": item["title"], "eligible": eligible})
        try:
            await notify("MarketingDraftReady", f"Review: {camp['name']}",
                         f"{eligible} eligible recipients. Approve in Campaigns.",
                         "campaign", cid)
        except Exception:
            pass
        return {"run_id": rid, "action": "draft_created", "campaign_id": cid,
                "eligible": eligible}
    except Exception as e:
        log.exception("marketing agent failed")
        try:
            await log_error("marketing_agent", "Daily run failed", str(e)[:2000])
        except Exception:
            pass
        rid = await _record_run(db, "failed",
                                {"triggered_by": triggered_by, "error": f"{type(e).__name__}"})
        return {"run_id": rid, "action": "failed"}
