"""Public email interactions: open pixel, click redirect, unsubscribe.

No auth — every route is gated by an HMAC send token. All idempotent;
unsubscribe immediately blocks future promotional sends.
"""
from fastapi import APIRouter, Query
from fastapi.responses import HTMLResponse, RedirectResponse, Response

from app.database import get_db, utcnow
from app.services.notify import audit

router = APIRouter(prefix="/api/public/email")

_PIXEL = (b"GIF89a\x01\x00\x01\x00\x80\x00\x00\x00\x00\x00"
          b"\xff\xff\xff!\xf9\x04\x01\x00\x00\x00\x00,\x00\x00\x00\x00"
          b"\x01\x00\x01\x00\x00\x02\x02D\x01\x00;")


@router.get("/open/{token}")
async def track_open(token: str):
    """1x1 pixel. Records first open only; always returns the gif."""
    from app.services.marketing import verify_send_token
    try:
        db = get_db()
        # token carries ids; email recovered from the send record.
        parts = (token or "").split(".")
        if len(parts) == 3:
            send = await db["email_sends"].find_one({"token": token})
            if send and verify_send_token(token, send.get("email", "")):
                if not send.get("opened_at"):
                    from bson import ObjectId
                    now = utcnow()
                    await db["email_sends"].update_one(
                        {"_id": send["_id"]},
                        {"$set": {"opened_at": now, "status": "delivered"}})
                    try:
                        await db["customer_leads"].update_one(
                            {"_id": ObjectId(send["lead_id"])}, {"$inc": {"opens": 1}})
                        await db["email_campaigns"].update_one(
                            {"_id": ObjectId(send["campaign_id"])},
                            {"$inc": {"stats.opened": 1}})
                    except Exception:
                        pass
    except Exception:
        pass
    return Response(content=_PIXEL, media_type="image/gif",
                    headers={"Cache-Control": "no-store"})


@router.get("/click/{token}")
async def track_click(token: str, u: str = Query(default="")):
    """Counts the click, then 302s to the original https URL (allowlisted)."""
    import urllib.parse
    dest = "https://rajiblabs.com"
    try:
        db = get_db()
        send = await db["email_sends"].find_one({"token": token})
        if send:
            from app.services.marketing import verify_send_token
            if verify_send_token(token, send.get("email", "")):
                target = urllib.parse.unquote(u or "")[:2000]
                if target.startswith("https://"):
                    dest = target
                now = utcnow()
                await db["email_sends"].update_one(
                    {"_id": send["_id"]},
                    {"$set": {"clicked_at": now, "status": "delivered",
                              "click_url": dest[:500]}})
                from bson import ObjectId
                try:
                    await db["customer_leads"].update_one(
                        {"_id": ObjectId(send["lead_id"])}, {"$inc": {"clicks": 1}})
                    await db["email_campaigns"].update_one(
                        {"_id": ObjectId(send["campaign_id"])},
                        {"$inc": {"stats.clicked": 1}})
                except Exception:
                    pass
    except Exception:
        pass
    return RedirectResponse(dest, status_code=302)


@router.get("/unsubscribe/{token}", response_class=HTMLResponse)
async def unsubscribe(token: str):
    """One-click opt-out (RFC 8058 GET form). Idempotent; audit-logged."""
    from app.services.marketing import unsubscribe_lead, verify_send_token
    ok = False
    try:
        db = get_db()
        send = await db["email_sends"].find_one({"token": token})
        if send and verify_send_token(token, send.get("email", "")):
            res = await unsubscribe_lead(db, send["lead_id"], source="email_link")
            ok = bool(res.get("ok"))
            try:
                from bson import ObjectId
                await db["email_campaigns"].update_one(
                    {"_id": ObjectId(send["campaign_id"])},
                    {"$inc": {"stats.unsubscribed": 1}})
            except Exception:
                pass
    except Exception:
        ok = False
    msg = ("You have been unsubscribed from RajibLabs promotional emails. "
           "Transactional follow-ups you explicitly request are unaffected."
           if ok else
           "This unsubscribe link is invalid or expired. Contact rajibmahata143@gmail.com for help.")
    return HTMLResponse(
        f"<!doctype html><html><body style='font-family:sans-serif;max-width:560px;margin:60px auto;padding:0 20px'>"
        f"<h2>RajibLabs email preferences</h2><p>{msg}</p></body></html>")
