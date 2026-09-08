"""Customer marketing core — templates, audience, frequency, sending.

Reuse-first: delivery goes through email_service (same SMTP path), lead
identity stays in customer_leads, events land in audit_logs + email_sends.
No parallel chat/lead/AI/RAG/email systems are created here.
"""
import hashlib
import hmac
import html as _html
import logging
import re
from datetime import datetime, timedelta, timezone
from html.parser import HTMLParser

from app.config import get_settings
from app.database import utcnow
from app.services import leads as rules
from app.services.notify import audit

log = logging.getLogger("rajiblabs")

# ── template variables ──────────────────────────────────────────────
# Only these {{vars}} render. Unknown names become "" (never leak internals).
# first_name derives from the lead name; professional fields only — never
# private chat content (spec §17: no creepy personalization).
ALLOWED_VARIABLES = frozenset({
    "first_name", "full_name", "company_name", "project_name",
    "project_url", "unsubscribe_url",
})

_VAR_RE = re.compile(r"\{\{\s*([a-z_]+)\s*\}\}")


def render_template(text: str, context: dict) -> str:
    """Substitute allowlisted {{variables}}. Unknown → empty string."""
    ctx = dict(context or {})

    def _sub(m: re.Match) -> str:
        name = m.group(1)
        if name not in ALLOWED_VARIABLES:
            return ""
        return str(ctx.get(name, "") or "")
    return _VAR_RE.sub(_sub, text or "")


def lead_template_context(lead: dict, extra: dict | None = None) -> dict:
    """Professional personalization context for one lead (no chat content)."""
    name = (lead.get("name") or "").strip()
    ctx = {
        "full_name": name,
        "first_name": name.split()[0] if name else "there",
        "company_name": (lead.get("company_name") or "").strip(),
    }
    if extra:
        for k in ("project_name", "project_url", "unsubscribe_url"):
            if extra.get(k):
                ctx[k] = extra[k]
    return ctx


# ── HTML sanitization (stdlib only, allowlist) ──────────────────────
_ALLOWED_TAGS = frozenset({
    "p", "br", "div", "span", "a", "strong", "b", "em", "i", "u",
    "h1", "h2", "h3", "h4", "ul", "ol", "li", "table", "thead",
    "tbody", "tr", "td", "th", "img", "hr", "blockquote", "code", "pre",
})
_ALLOWED_ATTRS = {
    "a": {"href", "title"},
    "img": {"src", "alt", "width", "height"},
    "table": {"width", "cellpadding", "cellspacing", "border"},
    "td": {"align", "valign", "width"},
    "th": {"align", "valign", "width"},
}
_SAFE_URL = re.compile(r"^https?://", re.I)


class _Sanitizer(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self._out: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        tag = tag.lower()
        if tag not in _ALLOWED_TAGS:
            return
        safe: list[str] = []
        for k, v in attrs:
            k = (k or "").lower()
            if k not in _ALLOWED_ATTRS.get(tag, set()):
                continue
            v = v or ""
            if k in ("href", "src") and not _SAFE_URL.match(v.strip()):
                continue
            if k == "style":
                continue
            safe.append(f'{k}="{_html.escape(v, quote=True)}"')
        self._out.append(f"<{tag}{' ' + ' '.join(safe) if safe else ''}>")

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() in _ALLOWED_TAGS and tag.lower() not in ("br", "hr", "img"):
            self._out.append(f"</{tag.lower()}>")

    def handle_data(self, data: str) -> None:
        self._out.append(_html.escape(data))

    def result(self) -> str:
        return "".join(self._out)


def sanitize_html(body_html: str) -> str:
    """Strip everything outside the email-safe allowlist. Never raises."""
    try:
        p = _Sanitizer()
        p.feed(body_html or "")
        return p.result()[:80000]
    except Exception:
        log.warning("HTML sanitize failed; falling back to text")
        return _html.escape(re.sub(r"<[^>]+>", "", body_html or ""))[:80000]


def html_to_text(body_html: str) -> str:
    """Plain-text fallback derived from sanitized HTML."""
    try:
        p = _Sanitizer()
        p.feed(body_html or "")
        text = re.sub(r"</(p|div|h1|h2|h3|h4|li|tr)>)", "\n", p.result())
        text = re.sub(r"<[^>]+>", "", text)
        text = _html.unescape(text)
        return re.sub(r"\n{3,}", "\n\n", text).strip()[:20000]
    except Exception:
        return re.sub(r"<[^>]+>", "", body_html or "")[:20000]


# ── signed tokens (tracking pixel, click, unsubscribe) ──────────────
def _sign(payload: str) -> str:
    s = get_settings()
    return hmac.new((s.secret_key or "dev-secret").encode(),
                    payload.encode(), hashlib.sha256).hexdigest()[:32]


def make_send_token(campaign_id: str, lead_id: str, email: str) -> str:
    """Opaque per-recipient token: base ids + HMAC (no DB lookup to verify)."""
    raw = f"{campaign_id}.{lead_id}"
    return f"{raw}.{_sign(raw + (email or '').lower())}"


def verify_send_token(token: str, email: str) -> tuple[str, str] | None:
    """Returns (campaign_id, lead_id) or None. Never raises."""
    try:
        campaign_id, lead_id, sig = (token or "").split(".")
        if not campaign_id or not lead_id or not sig:
            return None
        if not hmac.compare_digest(sig, _sign(f"{campaign_id}.{lead_id}{(email or '').lower()}")):
            return None
        return campaign_id, lead_id
    except Exception:
        return None


def tracking_urls(base_url: str, token: str) -> dict:
    base = (base_url or "https://rajiblabs.com").rstrip("/")
    return {
        "open_url": f"{base}/api/public/email/open/{token}",
        "click_base": f"{base}/api/public/email/click/{token}",
        "unsubscribe_url": f"{base}/api/public/email/unsubscribe/{token}",
    }


# ── audience segments → Mongo queries (customer_leads only) ─────────
def segment_query(segment: str, extra: dict | None = None) -> dict:
    """Deterministic audience filter. Consent/opt-out enforced by callers
    on top (never rely on the segment alone for compliance)."""
    extra = extra or {}
    tags = extra.get("tags") or []
    base_tag: dict = {"tags": {"$in": tags}} if tags else {}
    q: dict = dict(base_tag)
    if segment == "all_opted_in":
        pass
    elif segment == "new_leads":
        q["status"] = "new"
    elif segment == "hot_leads":
        q["$or"] = [{"status": "hot"}, {"lead_score": {"$gte": rules.HOT_LEAD_THRESHOLD}}]
    elif segment == "warm_leads":
        q["status"] = {"$in": ["warm", "qualified", "contacted", "follow_up"]}
    elif segment == "previous_customer":
        q["status"] = {"$in": ["customer", "converted", "won"]}
    elif segment in ("project_interest", "ai_interest", "architecture_interest",
                     "saas_interest", "automation_interest"):
        q["interests"] = segment.replace("_interest", "")
    else:
        q["status"] = {"$nin": ["spam", "archived", "lost"]}
    if extra.get("statuses"):
        q["status"] = {"$in": list(extra["statuses"])}
    return q


def eligible_filter(now: datetime | None = None) -> dict:
    """Compliance gate: explicit opt-in, valid email, not unsubscribed."""
    return {"marketing_consent": True, "unsubscribe": {"$ne": True},
            "email": {"$ne": ""}, "status": {"$nin": ["spam", "unsubscribed"]}}


async def count_recent_sends(db, lead_id: str, days: int = 7) -> int:
    """Promotional sends to one lead in the trailing window (fatigue input)."""
    since = utcnow() - timedelta(days=days)
    return await db["email_sends"].count_documents(
        {"lead_id": lead_id, "status": {"$in": ["queued", "sent", "delivered"]},
         "sent_at": {"$gte": since}})


async def last_send_at(db, lead_id: str):
    doc = await db["email_sends"].find(
        {"lead_id": lead_id, "status": {"$in": ["queued", "sent", "delivered"]}}
    ).sort("sent_at", -1).limit(1).to_list(1)
    return (doc[0].get("sent_at") if doc else None)


async def is_eligible(db, lead: dict, *, max_per_7_days: int = 2,
                      min_interval_hours: int = 48,
                      now: datetime | None = None) -> tuple[bool, str]:
    """Fatigue + compliance check for one lead. (eligible, reason)."""
    now = now or utcnow()
    if not lead.get("marketing_consent"):
        return False, "no marketing consent"
    if lead.get("unsubscribe"):
        return False, "unsubscribed"
    if not rules.valid_email(lead.get("email")):
        return False, "no valid email"
    if (lead.get("status") or "") in ("spam", "unsubscribed"):
        return False, f"status {lead.get('status')} excluded"
    lead_id = str(lead.get("_id"))
    if await count_recent_sends(db, lead_id, 7) >= max_per_7_days:
        return False, f"already received {max_per_7_days} in 7 days"
    last = await last_send_at(db, lead_id)
    if last:
        try:
            last_dt = last if last.tzinfo else last.replace(tzinfo=timezone.utc)
            if (now - last_dt) < timedelta(hours=min_interval_hours):
                return False, "minimum interval not elapsed"
        except Exception:
            pass
    return True, "eligible"


async def unsubscribe_lead(db, lead_id: str, source: str = "link") -> dict:
    """Idempotent opt-out: blocks all future promotional sends, revokes
    consent, timestamps. Resubscribe happens ONLY via explicit opt-in
    (lead capture consent flow or admin), never automatically."""
    from bson import ObjectId
    try:
        oid = ObjectId(lead_id)
    except Exception:
        return {"ok": False, "reason": "unknown lead"}
    now = utcnow()
    r = await db["customer_leads"].update_one(
        {"_id": oid},
        {"$set": {"unsubscribe": True, "marketing_consent": False,
                  "unsubscribe_timestamp": now, "status": "unsubscribed",
                  "updated_at": now}})
    if r.matched_count:
        try:
            await audit("marketing", "LEAD_UNSUBSCRIBED", lead_id,
                        {"source": source}, event_type="LEAD_UNSUBSCRIBED",
                        lead_id=lead_id)
        except Exception:
            pass
        return {"ok": True, "already": r.modified_count == 0}
    return {"ok": False, "reason": "unknown lead"}


async def run_campaign(db, campaign_id: str, decided_by: str = "admin") -> dict:
    """Dispatch one approved campaign with per-recipient eligibility +
    frequency caps. Sequential sends (SMTP-safe), stats rolled up at the end.
    Safe to re-run: terminal campaigns refuse; per-lead dedup skips repeats."""
    from bson import ObjectId
    try:
        oid = ObjectId(campaign_id)
    except Exception:
        return {"status": "failed", "error": "unknown campaign"}
    camp = await db["email_campaigns"].find_one({"_id": oid})
    if not camp:
        return {"status": "failed", "error": "unknown campaign"}
    if camp.get("status") in ("sending", "sent", "cancelled"):
        return {"status": camp["status"], "note": "terminal state, not re-run"}
    now = utcnow()
    await db["email_campaigns"].update_one(
        {"_id": oid}, {"$set": {"status": "sending", "decided_by": decided_by,
                                "decided_at": now, "updated_at": now}})
    try:
        await audit(decided_by, "CAMPAIGN_SEND_START", campaign_id, {})
    except Exception:
        pass
    a = camp.get("audience", {})
    query = {**segment_query(a.get("segment", "all_opted_in"), a),
             **eligible_filter()}
    # Dedup: skip leads already sent this campaign (re-run safe).
    already = {s["lead_id"] async for s in db["email_sends"].find(
        {"campaign_id": campaign_id,
         "status": {"$in": ["sent", "delivered", "queued"]}}, {"lead_id": 1})}
    sent = skipped = failed = 0
    cap7, cap_hrs = int(camp.get("max_per_7_days", 2)), int(camp.get("min_interval_hours", 48))
    async for lead in db["customer_leads"].find(query).sort("lead_score", -1).limit(2000):
        if str(lead.get("_id")) in already:
            skipped += 1
            continue
        try:
            res = await send_to_lead(db, {**camp, "_id": oid}, lead,
                                     max_per_7_days=cap7, min_interval_hours=cap_hrs)
            if res.get("status") == "sent":
                sent += 1
            elif res.get("status") == "skipped":
                skipped += 1
            else:
                failed += 1
        except Exception as e:
            log.warning("campaign send failed: %s", e)
            failed += 1
    final = "sent" if failed == 0 or sent > 0 else "failed"
    if failed and not sent:
        final = "failed"
    await db["email_campaigns"].update_one(
        {"_id": oid}, {"$set": {"status": final, "sent_at": now, "updated_at": now,
                                "stats.sent": sent, "stats.failed": failed}})
    try:
        await audit(decided_by, "CAMPAIGN_SENT", campaign_id,
                    {"sent": sent, "skipped": skipped, "failed": failed},
                    event_type="CAMPAIGN_SENT")
    except Exception:
        pass
    return {"status": final, "sent": sent, "skipped": skipped, "failed": failed}


# ── sender (campaign layer enforces consent; this is the last gate) ──
async def send_to_lead(db, campaign: dict, lead: dict, *,
                       max_per_7_days: int = 2,
                       min_interval_hours: int = 48) -> dict:
    """Render + send one promotional email. Skips (never sends) when the
    lead is ineligible. Records email_sends + lead counters + audit."""
    from app.services import email_service as _es
    ok, reason = await is_eligible(db, lead, max_per_7_days=max_per_7_days,
                                   min_interval_hours=min_interval_hours)
    lead_id = str(lead.get("_id"))
    camp_id = str(campaign.get("_id"))
    email = rules.normalize_email(lead.get("email"))
    if not ok:
        await db["email_sends"].insert_one({
            "campaign_id": camp_id, "lead_id": lead_id, "email": email,
            "status": "skipped", "reason": reason,
            "created_at": utcnow(), "sent_at": None})
        return {"status": "skipped", "reason": reason}

    token = make_send_token(camp_id, lead_id, email)
    s = get_settings()
    urls = tracking_urls(s.app_url, token)
    ctx = lead_template_context(lead, {"unsubscribe_url": urls["unsubscribe_url"],
                                       "project_name": campaign.get("project_name", ""),
                                       "project_url": campaign.get("project_url", "")})
    subject = render_template(campaign.get("subject", ""), ctx)
    # Open tracking is best-effort: pixel appended only when HTML exists.
    html_body = render_template(campaign.get("html", ""), ctx)
    if html_body.strip():
        html_body += (f'<img src="{urls["open_url"]}" width="1" height="1" '
                      f'alt="" style="display:none">')
    text_body = render_template(campaign.get("text", ""), ctx) or html_to_text(html_body)
    # Click tracking wraps http(s) links in <a href> at send time.
    if html_body.strip():
        def _wrap(m: re.Match) -> str:
            url = m.group(1)
            if "api/public/email" in url:
                return m.group(0)
            from urllib.parse import quote
            return f'<a href="{urls["click_base"]}?u={quote(url, safe="")}"'
        html_body = re.sub(r'<a\s+href="(https?://[^"]+)"', _wrap, html_body)
    try:
        _es.send_html_email(email, subject, text_body,
                            body_html=html_body or None,
                            unsubscribe_url=urls["unsubscribe_url"])
        status: dict = {"status": "sent", "token": token}
    except Exception as e:
        await db["email_sends"].insert_one({
            "campaign_id": camp_id, "lead_id": lead_id, "email": email,
            "status": "failed", "error": f"{type(e).__name__}",
            "created_at": utcnow(), "sent_at": utcnow()})
        try:
            await audit("marketing", "EMAIL_SEND_FAILED", camp_id,
                        {"lead_id": lead_id, "error": type(e).__name__},
                        event_type="EMAIL_SEND_FAILED", lead_id=lead_id)
        except Exception:
            pass
        return {"status": "failed", "error": type(e).__name__}

    now = utcnow()
    await db["email_sends"].insert_one({
        "campaign_id": camp_id, "lead_id": lead_id, "email": email,
        "status": "sent", "token": token, "subject": subject[:200],
        "created_at": now, "sent_at": now})
    try:
        await db["customer_leads"].update_one(
            {"_id": lead["_id"]},
            {"$set": {"last_contacted_at": now, "last_email_at": now,
                      "updated_at": now},
             "$inc": {"emails_sent": 1},
             "$push": {"email_history": {"campaign_id": camp_id,
                                         "subject": subject[:200], "at": now}},
             "$addToSet": {"campaigns": camp_id}})
        await audit("marketing", "EMAIL_SENT", camp_id,
                    {"lead_id": lead_id, "subject": subject[:120]},
                    event_type="EMAIL_SENT", lead_id=lead_id)
    except Exception as e:
        log.warning("send bookkeeping failed: %s", e)
    return status
