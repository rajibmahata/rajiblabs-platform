"""Admin customer-marketing console: customers 360, templates, campaigns.

Reuse-first: leads stay in customer_leads (extended in place), delivery via
email_service, events in audit_logs + email_sends. All routes need admin JWT.
"""
from fastapi import APIRouter, Depends, HTTPException, Query

from app.auth.dependencies import require_admin
from app.database import get_db, utcnow
from app.models import oid_str
from app.schemas import (CampaignDecision, EmailCampaignIn, EmailTemplateIn,
                         EmailTemplatePatch)
from app.services import leads as rules
from app.services.notify import audit

router = APIRouter(prefix="/api/admin/marketing")


def _oid(pid: str):
    from bson import ObjectId
    try:
        return ObjectId(pid)
    except Exception:
        raise HTTPException(400, "Invalid id")


# ── customers (unified 360 over customer_leads) ─────────────────────
@router.get("/customers")
async def customers(status: str | None = None, consent: str | None = None,
                    q: str | None = None, page: int = 1, page_size: int = 25,
                    email: str = Depends(require_admin)):
    """Leads + customers with consent/opt-out filters. No sensitive internals."""
    db = get_db()
    query: dict = {}
    if status:
        query["status"] = status
    if consent == "yes":
        query["marketing_consent"] = True
    elif consent == "no":
        query["marketing_consent"] = {"$ne": True}
    if q and q.strip():
        rx = {"$regex": q.strip()[:120], "$options": "i"}
        query["$or"] = [{"name": rx}, {"email": rx}, {"company_name": rx},
                        {"phone": rx}]
    page, page_size = max(1, page), max(1, min(page_size, 200))
    total = await db["customer_leads"].count_documents(query)
    cur = db["customer_leads"].find(query).sort("updated_at", -1).skip(
        (page - 1) * page_size).limit(page_size)
    items = []
    async for d in cur:
        d = oid_str(d)
        convs = await db["customer_conversations"].count_documents(
            {"lead_id": d.get("id")})
        items.append({
            "id": d.get("id"), "name": d.get("name", ""), "email": d.get("email", ""),
            "phone": d.get("phone", ""), "company_name": d.get("company_name", ""),
            "industry": d.get("industry", ""), "source": d.get("source", ""),
            "status": d.get("status", "new"), "lead_score": d.get("lead_score", 0),
            "score_reasons": d.get("score_reasons", []),
            "marketing_consent": bool(d.get("marketing_consent")),
            "consent_timestamp": d.get("consent_timestamp"),
            "unsubscribe": bool(d.get("unsubscribe")),
            "tags": d.get("tags", []), "interests": d.get("interests", []),
            "conversations": convs,
            "emails_sent": d.get("emails_sent", 0),
            "last_email_at": d.get("last_email_at"),
            "last_contacted_at": d.get("last_contacted_at"),
            "created_at": d.get("created_at"), "updated_at": d.get("updated_at"),
        })
    return {"items": items, "total": total, "page": page, "page_size": page_size}


@router.get("/customers/{lid}")
async def customer_detail(lid: str, email: str = Depends(require_admin)):
    """360 view: profile + conversations + ideas + email history + timeline."""
    from bson import ObjectId
    db = get_db()
    try:
        oid = ObjectId(lid)
    except Exception:
        raise HTTPException(404, "Not found")
    lead = await db["customer_leads"].find_one({"_id": oid})
    if not lead:
        raise HTTPException(404, "Not found")
    lid_s = str(lead["_id"])
    convs = [oid_str(c) async for c in db["customer_conversations"].find(
        {"$or": [{"lead_id": lid_s}, {"session_token": {"$in": lead.get("session_ids", [])}}]})
        .sort("last_activity_at", -1).limit(20)]
    for c in convs:
        c["message_count"] = await db["customer_messages"].count_documents(
            {"session_token": c.get("session_token")})
    ideas = [oid_str(i) async for i in db["ideas"].find({"lead_id": oid})
             .sort("updated_at", -1).limit(20)]
    # email history: recorded sends + tracked events, newest first
    sends = [oid_str(s) async for s in db["email_sends"].find({"lead_id": lid_s})
             .sort("created_at", -1).limit(50)]
    for s in sends:
        s.pop("token", None)
    # unified timeline from the audit event store (no new collection)
    timeline = []
    async for a in db["audit_logs"].find(
            {"$or": [{"lead_id": lid_s},
                     {"session_id": {"$in": lead.get("session_ids", [])}}]}) \
            .sort("created_at", -1).limit(100):
        a = oid_str(a)
        timeline.append({"at": a.get("created_at"), "action": a.get("action"),
                         "actor": a.get("actor"), "detail": a.get("metadata", {})})
    out = oid_str(lead)
    out.pop("locked_fields", None)
    return {"lead": out, "conversations": convs, "ideas": ideas,
            "email_history": sends, "timeline": timeline}


@router.post("/customers/{lid}/unsubscribe")
async def customer_unsubscribe(lid: str, email: str = Depends(require_admin)):
    """Admin opt-out (idempotent): blocks all future promotional sends."""
    from app.services.marketing import unsubscribe_lead
    res = await unsubscribe_lead(get_db(), lid, source="admin")
    await audit(email, "LEAD_UNSUBSCRIBED", lid, {"source": "admin"},
                event_type="LEAD_UNSUBSCRIBED", lead_id=lid)
    return res


@router.get("/segments")
async def segments(email: str = Depends(require_admin)):
    """Eligible audience size per segment (consent + opt-out enforced)."""
    from app.services.marketing import eligible_filter, segment_query
    db = get_db()
    out = []
    for key in rules.SEGMENTS:
        q = {**segment_query(key), **eligible_filter()}
        out.append({"segment": key, "eligible": await db["customer_leads"].count_documents(q)})
    return {"segments": out}


# ── templates ───────────────────────────────────────────────────────
@router.get("/templates")
async def templates(status: str | None = None, email: str = Depends(require_admin)):
    db = get_db()
    q = {"status": status} if status in rules.TEMPLATE_STATUSES else {}
    items = [oid_str(d) async for d in db["email_templates"].find(q)
             .sort("updated_at", -1).limit(200)]
    return {"items": items}


@router.post("/templates", status_code=201)
async def template_create(body: EmailTemplateIn, email: str = Depends(require_admin)):
    from app.services.marketing import sanitize_html
    if body.status not in rules.TEMPLATE_STATUSES:
        raise HTTPException(400, "Invalid status")
    db = get_db()
    doc = {"name": body.name.strip(), "subject": body.subject.strip(),
           "preheader": body.preheader.strip(),
           "html": sanitize_html(body.html), "text": (body.text or "").strip()[:20000],
           "category": body.category.strip() or "general", "status": body.status,
           "created_at": utcnow(), "updated_at": utcnow(), "created_by": email}
    res = await db["email_templates"].insert_one(doc)
    doc["_id"] = res.inserted_id
    await audit(email, "TEMPLATE_CREATE", str(res.inserted_id), {"name": doc["name"]})
    return oid_str(doc)


@router.put("/templates/{tid}")
async def template_update(tid: str, body: EmailTemplatePatch,
                          email: str = Depends(require_admin)):
    from app.services.marketing import sanitize_html
    db = get_db()
    patch = {k: v for k, v in
             {"name": (body.name or "").strip() or None,
              "subject": (body.subject or "").strip() or None,
              "preheader": body.preheader,
              "html": sanitize_html(body.html) if body.html is not None else None,
              "text": body.text,
              "category": (body.category or "").strip() or None,
              "status": body.status}.items() if v is not None}
    if "status" in patch and patch["status"] not in rules.TEMPLATE_STATUSES:
        raise HTTPException(400, "Invalid status")
    if not patch:
        raise HTTPException(400, "Nothing to update")
    patch["updated_at"] = utcnow()
    r = await db["email_templates"].update_one({"_id": _oid(tid)}, {"$set": patch})
    if not r.matched_count:
        raise HTTPException(404, "Not found")
    await audit(email, "TEMPLATE_UPDATE", tid, {"fields": sorted(patch.keys())})
    return oid_str(await db["email_templates"].find_one({"_id": _oid(tid)}))


@router.post("/templates/{tid}/preview")
async def template_preview(tid: str, lead_id: str | None = None,
                           email: str = Depends(require_admin)):
    """Render with a real lead (or blank) — what the recipient would get."""
    from app.services.marketing import (lead_template_context, render_template,
                                        tracking_urls)
    from app.config import get_settings
    db = get_db()
    t = await db["email_templates"].find_one({"_id": _oid(tid)})
    if not t:
        raise HTTPException(404, "Not found")
    lead: dict = {}
    if lead_id:
        try:
            from bson import ObjectId
            lead = await db["customer_leads"].find_one({"_id": ObjectId(lead_id)}) or {}
        except Exception:
            lead = {}
    ctx = lead_template_context(lead, {
        "unsubscribe_url": tracking_urls(get_settings().app_url, "preview")["unsubscribe_url"]})
    return {"subject": render_template(t.get("subject", ""), ctx),
            "html": render_template(t.get("html", ""), ctx),
            "text": render_template(t.get("text", ""), ctx)}


@router.delete("/templates/{tid}")
async def template_delete(tid: str, email: str = Depends(require_admin)):
    db = get_db()
    if await db["email_campaigns"].count_documents({"template_id": tid}):
        raise HTTPException(400, "Template is used by a campaign (archive instead)")
    r = await db["email_templates"].delete_one({"_id": _oid(tid)})
    if not r.deleted_count:
        raise HTTPException(404, "Not found")
    await audit(email, "TEMPLATE_DELETE", tid, {})
    return {"message": "Deleted"}


# ── campaigns ───────────────────────────────────────────────────────
def _campaign_out(d: dict) -> dict:
    d = oid_str(d)
    return d


@router.get("/campaigns")
async def campaigns(status: str | None = None, email: str = Depends(require_admin)):
    db = get_db()
    q = {"status": status} if status in rules.CAMPAIGN_STATUSES else {}
    items = [_campaign_out(d) async for d in db["email_campaigns"].find(q)
             .sort("created_at", -1).limit(200)]
    for it in items:
        it["sent"] = await db["email_sends"].count_documents(
            {"campaign_id": it["id"], "status": {"$in": ["sent", "delivered"]}})
        it["failed"] = await db["email_sends"].count_documents(
            {"campaign_id": it["id"], "status": "failed"})
    return {"items": items}


@router.post("/campaigns", status_code=201)
async def campaign_create(body: EmailCampaignIn, email: str = Depends(require_admin)):
    """Always starts as DRAFT (safe default). Approval/send is explicit."""
    from app.services.marketing import sanitize_html
    db = get_db()
    html, text = body.html or "", body.text or ""
    if body.template_id:
        t = await db["email_templates"].find_one({"_id": _oid(body.template_id)})
        if not t:
            raise HTTPException(400, "Template not found")
        html = html or t.get("html", "")
        text = text or t.get("text", "") or t.get("subject", "")
    if not html.strip() and not text.strip():
        raise HTTPException(400, "Campaign needs a template or inline content")
    now = utcnow()
    doc = {"name": body.name.strip(), "template_id": body.template_id,
           "subject": body.subject.strip(), "html": sanitize_html(html),
           "text": text.strip()[:20000],
           "audience": {"segment": body.audience.segment,
                        "tags": body.audience.tags, "statuses": body.audience.statuses},
           "max_per_7_days": body.max_per_7_days,
           "min_interval_hours": body.min_interval_hours,
           "schedule_at": body.schedule_at, "auto_send": bool(body.auto_send),
           "status": "draft",
           "stats": {"queued": 0, "sent": 0, "failed": 0, "opened": 0,
                     "clicked": 0, "unsubscribed": 0},
           "created_at": now, "updated_at": now, "created_by": email,
           "decided_by": None, "decided_at": None, "sent_at": None}
    res = await db["email_campaigns"].insert_one(doc)
    doc["_id"] = res.inserted_id
    await audit(email, "CAMPAIGN_CREATE", str(res.inserted_id), {"name": doc["name"]})
    return _campaign_out(doc)


@router.get("/campaigns/{cid}")
async def campaign_detail(cid: str, email: str = Depends(require_admin)):
    db = get_db()
    c = await db["email_campaigns"].find_one({"_id": _oid(cid)})
    if not c:
        raise HTTPException(404, "Not found")
    out = _campaign_out(c)
    sends = [oid_str(s) async for s in db["email_sends"].find({"campaign_id": cid})
             .sort("created_at", -1).limit(200)]
    for s in sends:
        s.pop("token", None)
    out["sends"] = sends
    return out


@router.post("/campaigns/{cid}/audience-preview")
async def audience_preview(cid: str, email: str = Depends(require_admin)):
    """How many eligible recipients right now (no send)."""
    from app.services.marketing import eligible_filter, segment_query
    db = get_db()
    c = await db["email_campaigns"].find_one({"_id": _oid(cid)})
    if not c:
        raise HTTPException(404, "Not found")
    a = c.get("audience", {})
    q = {**segment_query(a.get("segment", "all_opted_in"), a), **eligible_filter()}
    return {"eligible": await db["customer_leads"].count_documents(q)}


@router.post("/campaigns/{cid}/decision")
async def campaign_decision(cid: str, body: CampaignDecision,
                            email: str = Depends(require_admin)):
    """approve → ready | send → immediate dispatch | pause | cancel."""
    from app.services.marketing import run_campaign
    db = get_db()
    c = await db["email_campaigns"].find_one({"_id": _oid(cid)})
    if not c:
        raise HTTPException(404, "Not found")
    action = (body.action or "").lower()
    now = utcnow()
    if action == "approve":
        if c["status"] != "draft":
            raise HTTPException(400, "Only drafts can be approved")
        await db["email_campaigns"].update_one(
            {"_id": c["_id"]}, {"$set": {"status": "ready", "decided_by": email,
                                         "decided_at": now, "updated_at": now}})
        await audit(email, "CAMPAIGN_APPROVE", cid, {})
        return {"status": "ready"}
    if action == "send":
        if c["status"] not in ("draft", "ready", "scheduled"):
            raise HTTPException(400, f"Cannot send from {c['status']}")
        result = await run_campaign(db, cid, decided_by=email)
        return result
    if action == "pause":
        await db["email_campaigns"].update_one(
            {"_id": c["_id"]}, {"$set": {"status": "paused", "updated_at": now}})
        await audit(email, "CAMPAIGN_PAUSE", cid, {})
        return {"status": "paused"}
    if action == "cancel":
        await db["email_campaigns"].update_one(
            {"_id": c["_id"]}, {"$set": {"status": "cancelled", "updated_at": now}})
        await audit(email, "CAMPAIGN_CANCEL", cid, {})
        return {"status": "cancelled"}
    raise HTTPException(400, "Unknown action (approve|send|pause|cancel)")


@router.get("/settings")
async def marketing_settings_get(email: str = Depends(require_admin)):
    """Agent policy: cadence, caps, approval mode."""
    from app.services.marketing_agent import DEFAULT_SETTINGS, get_settings_doc
    return await get_settings_doc(get_db())


@router.put("/settings")
async def marketing_settings_put(body: dict, email: str = Depends(require_admin)):
    from app.services.marketing_agent import DEFAULT_SETTINGS
    db = get_db()
    patch = {k: body[k] for k in DEFAULT_SETTINGS if k in body}
    if "hour" in patch:
        patch["hour"] = max(0, min(23, int(patch["hour"])))
    for k in ("lookback_days", "max_per_7_days", "min_interval_hours"):
        if k in patch:
            patch[k] = max(1, int(patch[k]))
    for k in ("enabled", "auto_send", "weekend_send"):
        if k in patch:
            patch[k] = bool(patch[k])
    await db["marketing_settings"].update_one({"_id": "singleton"},
                                              {"$set": patch}, upsert=True)
    await audit(email, "MARKETING_SETTINGS", "singleton", {"fields": sorted(patch.keys())})
    return {"ok": True, "settings": patch}


@router.post("/agent/run")
async def marketing_agent_run(email: str = Depends(require_admin)):
    """Manual trigger (same flow as the scheduler; respects all gates)."""
    from app.services.marketing_agent import run_daily
    return await run_daily(triggered_by=f"admin:{email}")


@router.get("/dashboard")
async def marketing_dashboard(email: str = Depends(require_admin)):
    """Growth overview: audience, consent, recent campaigns, agent runs."""
    db = get_db()
    total = await db["customer_leads"].count_documents({})
    opted = await db["customer_leads"].count_documents(
        {"marketing_consent": True, "unsubscribe": {"$ne": True}})
    unsub = await db["customer_leads"].count_documents({"unsubscribe": True})
    camps = await db["email_campaigns"].count_documents({})
    recent = [_campaign_out(d) async for d in db["email_campaigns"].find({})
              .sort("created_at", -1).limit(5)]
    agent_runs = [oid_str(r) async for r in db["marketing_agent_runs"].find({})
                  .sort("started_at", -1).limit(5)]
    return {"leads_total": total, "opted_in": opted, "unsubscribed": unsub,
            "campaigns": camps, "recent_campaigns": recent,
            "agent_runs": agent_runs,
            "smtp_configured": __import__("app.services.email_service",
                                          fromlist=["is_configured"]).is_configured()}
