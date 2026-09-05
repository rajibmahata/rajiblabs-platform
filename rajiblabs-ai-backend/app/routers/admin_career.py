"""Admin Career Application module (JWT only, never public).

Job → Analyze → Retrieve Evidence → Generate → Validate → Admin Review →
Approve → Send → Track. Email sends ONLY after explicit approval, through
the stdlib SMTP service. Every key action is audited; failures are logged
without secrets (ids and counts only, never bodies or credentials).
"""
import re
import time

from fastapi import APIRouter, Depends, HTTPException
from app.auth.dependencies import require_admin
from app.database import get_db, utcnow
from app.models import oid_str
from app.schemas import (
    ApplicationPatch, CareerAnalyzeIn, CareerGenerateIn, CareerRefineIn,
    CompanyIn, CompanyPatch, ContactIn, ContactPatch, JobIn, JobPatch,
)
from app.services import workbench as wb
from app.services.notify import audit, log_error

router = APIRouter(prefix="/api/admin/career")

_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def _oid(pid: str):
    from bson import ObjectId
    try:
        return ObjectId(pid)
    except Exception:
        raise HTTPException(400, "Invalid id")


async def _get_or_404(coll: str, rid: str, label: str) -> dict:
    db = get_db()
    doc = await db[coll].find_one({"_id": _oid(rid)})
    if not doc:
        raise HTTPException(404, f"{label} not found")
    return doc


def _page(page: int, limit: int) -> tuple[int, int]:
    page = max(1, page)
    return page, min(max(limit, 1), 100)


# ── Companies ──

@router.get("/companies")
async def list_companies(q: str | None = None, active: bool | None = None,
                         page: int = 1, limit: int = 50,
                         email: str = Depends(require_admin)):
    db = get_db()
    query: dict = {}
    if q and q.strip():
        rx = {"$regex": re.escape(q.strip()[:100]), "$options": "i"}
        query["$or"] = [{"name": rx}, {"industry": rx}, {"location": rx}]
    if active is not None:
        query["active"] = active
    page, limit = _page(page, limit)
    total = await db["career_companies"].count_documents(query)
    cur = db["career_companies"].find(query).sort("name", 1).skip(
        (page - 1) * limit).limit(limit)
    items = []
    async for d in cur:
        d = oid_str(d)
        d["contact_count"] = await db["career_contacts"].count_documents(
            {"company_id": d["id"]})
        d["job_count"] = await db["career_jobs"].count_documents(
            {"company_id": d["id"]})
        items.append(d)
    return {"items": items, "total": total, "page": page, "limit": limit}


@router.post("/companies", status_code=201)
async def create_company(body: CompanyIn, email: str = Depends(require_admin)):
    db = get_db()
    now = utcnow()
    doc = body.model_dump()
    doc.update({"created_at": now, "updated_at": now, "created_by": email})
    res = await db["career_companies"].insert_one(doc)
    await audit(email, "CAREER_COMPANY_CREATE", str(res.inserted_id),
                {"name": body.name}, event_type="CAREER_COMPANY_CREATE")
    return oid_str({**doc, "_id": res.inserted_id})


@router.get("/companies/{cid}")
async def get_company(cid: str, email: str = Depends(require_admin)):
    return oid_str(await _get_or_404("career_companies", cid, "Company"))


@router.put("/companies/{cid}")
async def update_company(cid: str, body: CompanyPatch,
                         email: str = Depends(require_admin)):
    db = get_db()
    await _get_or_404("career_companies", cid, "Company")
    patch = {k: v for k, v in body.model_dump(exclude_unset=True).items()
             if v is not None}
    patch["updated_at"] = utcnow()
    await db["career_companies"].update_one({"_id": _oid(cid)}, {"$set": patch})
    await audit(email, "CAREER_COMPANY_UPDATE", cid, {"fields": sorted(patch)},
                event_type="CAREER_COMPANY_UPDATE")
    return oid_str(await db["career_companies"].find_one({"_id": _oid(cid)}))


@router.delete("/companies/{cid}")
async def delete_company(cid: str, email: str = Depends(require_admin)):
    db = get_db()
    await _get_or_404("career_companies", cid, "Company")
    jobs = await db["career_jobs"].count_documents({"company_id": cid})
    contacts = await db["career_contacts"].count_documents({"company_id": cid})
    if jobs or contacts:
        raise HTTPException(409, f"Company has {jobs} job(s) and {contacts} contact(s) — delete those first")
    await db["career_companies"].delete_one({"_id": _oid(cid)})
    await audit(email, "CAREER_COMPANY_DELETE", cid, event_type="CAREER_COMPANY_DELETE")
    return {"ok": True}


# ── Contacts ──

@router.get("/contacts")
async def list_contacts(company_id: str | None = None,
                        active: bool | None = None,
                        page: int = 1, limit: int = 100,
                        email: str = Depends(require_admin)):
    db = get_db()
    query: dict = {}
    if company_id:
        query["company_id"] = company_id
    if active is not None:
        query["active"] = active
    page, limit = _page(page, limit)
    total = await db["career_contacts"].count_documents(query)
    cur = db["career_contacts"].find(query).sort("name", 1).skip(
        (page - 1) * limit).limit(limit)
    return {"items": [oid_str(d) async for d in cur],
            "total": total, "page": page, "limit": limit}


@router.post("/contacts", status_code=201)
async def create_contact(body: ContactIn, email: str = Depends(require_admin)):
    db = get_db()
    await _get_or_404("career_companies", body.company_id, "Company")
    if not _EMAIL_RE.match(body.email.strip()):
        raise HTTPException(400, "Contact email is invalid")
    now = utcnow()
    doc = body.model_dump()
    doc.update({"email": body.email.strip().lower(),
                "created_at": now, "updated_at": now, "created_by": email})
    res = await db["career_contacts"].insert_one(doc)
    await audit(email, "CAREER_CONTACT_CREATE", str(res.inserted_id),
                {"company_id": body.company_id}, event_type="CAREER_CONTACT_CREATE")
    return oid_str({**doc, "_id": res.inserted_id})


@router.get("/contacts/{nid}")
async def get_contact(nid: str, email: str = Depends(require_admin)):
    return oid_str(await _get_or_404("career_contacts", nid, "Contact"))


@router.put("/contacts/{nid}")
async def update_contact(nid: str, body: ContactPatch,
                         email: str = Depends(require_admin)):
    db = get_db()
    await _get_or_404("career_contacts", nid, "Contact")
    patch = {k: v for k, v in body.model_dump(exclude_unset=True).items()
             if v is not None}
    if "company_id" in patch:
        await _get_or_404("career_companies", patch["company_id"], "Company")
    if "email" in patch:
        if not _EMAIL_RE.match(str(patch["email"]).strip()):
            raise HTTPException(400, "Contact email is invalid")
        patch["email"] = str(patch["email"]).strip().lower()
    patch["updated_at"] = utcnow()
    await db["career_contacts"].update_one({"_id": _oid(nid)}, {"$set": patch})
    await audit(email, "CAREER_CONTACT_UPDATE", nid, {"fields": sorted(patch)},
                event_type="CAREER_CONTACT_UPDATE")
    return oid_str(await db["career_contacts"].find_one({"_id": _oid(nid)}))


@router.delete("/contacts/{nid}")
async def delete_contact(nid: str, email: str = Depends(require_admin)):
    db = get_db()
    await _get_or_404("career_contacts", nid, "Contact")
    used = await db["career_applications"].count_documents({"contact_id": nid})
    if used:
        raise HTTPException(409, f"Contact is used by {used} application(s)")
    await db["career_contacts"].delete_one({"_id": _oid(nid)})
    await audit(email, "CAREER_CONTACT_DELETE", nid, event_type="CAREER_CONTACT_DELETE")
    return {"ok": True}


# ── Job openings ──

@router.get("/jobs")
async def list_jobs(q: str | None = None, status: str | None = None,
                    company_id: str | None = None,
                    page: int = 1, limit: int = 50,
                    email: str = Depends(require_admin)):
    from app.schemas import CAREER_JOB_STATUSES
    db = get_db()
    query: dict = {}
    if q and q.strip():
        rx = {"$regex": re.escape(q.strip()[:100]), "$options": "i"}
        query["$or"] = [{"title": rx}, {"description": rx}, {"technologies": rx}]
    if status:
        if status not in CAREER_JOB_STATUSES:
            raise HTTPException(400, "Invalid status")
        query["status"] = status
    if company_id:
        query["company_id"] = company_id
    page, limit = _page(page, limit)
    total = await db["career_jobs"].count_documents(query)
    cur = db["career_jobs"].find(
        query, {"description": 0}).sort("updated_at", -1).skip(
        (page - 1) * limit).limit(limit)
    items = []
    async for d in cur:
        d = oid_str(d)
        comp = None
        if d.get("company_id"):
            try:
                comp = await db["career_companies"].find_one(
                    {"_id": _oid(d["company_id"])}, {"name": 1})
            except HTTPException:
                comp = None
        d["company_name"] = (comp or {}).get("name", "")
        d["application_count"] = await db["career_applications"].count_documents(
            {"job_id": d["id"]})
        items.append(d)
    return {"items": items, "total": total, "page": page, "limit": limit}


@router.post("/jobs", status_code=201)
async def create_job(body: JobIn, email: str = Depends(require_admin)):
    from app.schemas import CAREER_JOB_STATUSES
    db = get_db()
    if body.company_id:
        await _get_or_404("career_companies", body.company_id, "Company")
    if body.status not in CAREER_JOB_STATUSES:
        raise HTTPException(400, "Invalid status")
    now = utcnow()
    doc = body.model_dump()
    doc.update({"created_at": now, "updated_at": now, "created_by": email,
                "analysis": {}, "agent_slug": body.agent_slug or "rajiblabs-career"})
    res = await db["career_jobs"].insert_one(doc)
    await audit(email, "CAREER_JOB_CREATE", str(res.inserted_id),
                {"title": body.title}, event_type="CAREER_JOB_CREATE")
    return oid_str({**doc, "_id": res.inserted_id, "id": str(res.inserted_id)})


@router.get("/jobs/{jid}")
async def get_job(jid: str, email: str = Depends(require_admin)):
    db = get_db()
    d = oid_str(await _get_or_404("career_jobs", jid, "Job opening"))
    if d.get("company_id"):
        try:
            comp = await db["career_companies"].find_one(
                {"_id": _oid(d["company_id"])})
            d["company"] = oid_str(comp) if comp else None
        except HTTPException:
            d["company"] = None
    else:
        d["company"] = None
    cur = db["career_contacts"].find(
        {"company_id": d.get("company_id"), "active": True}).sort("name", 1) \
        if d.get("company_id") else None
    d["contacts"] = [oid_str(c) async for c in cur] if cur is not None else []
    return d


@router.put("/jobs/{jid}")
async def update_job(jid: str, body: JobPatch,
                     email: str = Depends(require_admin)):
    from app.schemas import CAREER_JOB_STATUSES
    db = get_db()
    await _get_or_404("career_jobs", jid, "Job opening")
    patch = {k: v for k, v in body.model_dump(exclude_unset=True).items()
             if v is not None}
    if "company_id" in patch and patch["company_id"]:
        await _get_or_404("career_companies", patch["company_id"], "Company")
    if "status" in patch and patch["status"] not in CAREER_JOB_STATUSES:
        raise HTTPException(400, "Invalid status")
    patch["updated_at"] = utcnow()
    await db["career_jobs"].update_one({"_id": _oid(jid)}, {"$set": patch})
    await audit(email, "CAREER_JOB_UPDATE", jid, {"fields": sorted(patch)},
                event_type="CAREER_JOB_UPDATE")
    return oid_str(await db["career_jobs"].find_one({"_id": _oid(jid)}))


@router.delete("/jobs/{jid}")
async def delete_job(jid: str, email: str = Depends(require_admin)):
    db = get_db()
    await _get_or_404("career_jobs", jid, "Job opening")
    used = await db["career_applications"].count_documents({"job_id": jid})
    if used:
        raise HTTPException(409, f"Job has {used} application(s) — delete those first")
    await db["career_jobs"].delete_one({"_id": _oid(jid)})
    await audit(email, "CAREER_JOB_DELETE", jid, event_type="CAREER_JOB_DELETE")
    return {"ok": True}


# ── Analyze + generate (reuse the workbench pipeline) ──

@router.post("/jobs/{jid}/analyze")
async def analyze_job(jid: str, body: CareerAnalyzeIn,
                      email: str = Depends(require_admin)):
    """Understand the JD, extract requirements, rank verified evidence."""
    import time
    from app.services import agent_config
    db = get_db()
    job = await _get_or_404("career_jobs", jid, "Job opening")
    await agent_config.ensure_career_seed(db)
    await db["career_jobs"].update_one(
        {"_id": job["_id"]}, {"$set": {"status": "Analyzing", "updated_at": utcnow()}})
    t = time.monotonic()
    try:
        analysis, ai_used = await wb.analyze_requirements(job.get("description", ""), db)
        evidence = await wb.retrieve_evidence(analysis, db=db)
        selected = await wb.select_examples(analysis, evidence)
        matches = await wb.match_requirements(analysis, selected, evidence)
        report = wb.match_score(analysis, matches, selected, evidence)
    except Exception as e:
        await db["career_jobs"].update_one(
            {"_id": job["_id"]}, {"$set": {"status": "Open", "updated_at": utcnow()}})
        await log_error("career_analyze", f"analyze failed for job {jid}",
                        str(e)[:1000], logger="app.routers.admin_career")
        raise HTTPException(502, f"Analysis failed: {type(e).__name__}")
    payload = {
        "analysis": analysis.model_dump(),
        "matches": [m.model_dump() for m in matches],
        "report": report.model_dump(),
        "selected": [
            {"title": c.get("doc_title") or c.get("title", ""),
             "source_type": c.get("source_type", ""),
             "url": c.get("doc_url", ""),
             "repository": c.get("doc_repo", ""),
             "reason": c.get("selection_reason", "")} for c in selected],
        "ai_used": ai_used,
        "elapsed_ms": int((time.monotonic() - t) * 1000),
    }
    await db["career_jobs"].update_one(
        {"_id": job["_id"]},
        {"$set": {"analysis": payload["analysis"], "matches": payload["matches"],
                  "report": payload["report"],
                  "status": "Open" if job.get("status") == "Draft" else job.get("status", "Open"),
                  "updated_at": utcnow()}})
    await audit(email, "CAREER_ANALYZE", jid,
                {"match_score": report.match_score, "ai_used": ai_used},
                event_type="CAREER_ANALYZE")
    return payload


@router.post("/jobs/{jid}/generate")
async def generate_application(jid: str, body: CareerGenerateIn,
                               email: str = Depends(require_admin)):
    """Generate email + cover letter + summary, then create a Needs Review application."""
    import time
    from app.services import agent_config
    db = get_db()
    job = await _get_or_404("career_jobs", jid, "Job opening")
    await agent_config.ensure_career_seed(db)
    contact = None
    if body.contact_id:
        contact = await db["career_contacts"].find_one({"_id": _oid(body.contact_id)})
        if not contact:
            raise HTTPException(404, "Contact not found")
    company_name = ""
    if job.get("company_id"):
        try:
            comp = await db["career_companies"].find_one({"_id": _oid(job["company_id"])})
            company_name = (comp or {}).get("name", "")
        except HTTPException:
            pass
    t = time.monotonic()
    try:
        stored = job.get("analysis") or {}
        from app.schemas import RequirementAnalysis
        analysis = RequirementAnalysis.model_validate(stored) \
            if stored.get("title") or stored.get("technologies") else \
            (await wb.analyze_requirements(job.get("description", ""), db))[0]
        evidence = await wb.retrieve_evidence(analysis, db=db)
        selected = await wb.select_examples(analysis, evidence)
        matches = await wb.match_requirements(analysis, selected, evidence)
        report = wb.match_score(analysis, matches, selected, evidence)
        known = await wb.collect_known_urls(db)
        artifacts, ai_used = await wb.generate_career_application(
            analysis, matches, selected, known,
            company_name=company_name,
            contact_name=(contact or {}).get("name", ""), db=db)
        quality = wb.quality_check(artifacts["email_body"], artifacts["cover_letter"],
                                   artifacts["short_summary"], selected, known,
                                   mode="job_application")
    except HTTPException:
        raise
    except Exception as e:
        await log_error("career_generate", f"generate failed for job {jid}",
                        str(e)[:1000], logger="app.routers.admin_career")
        raise HTTPException(502, f"Generation failed: {type(e).__name__}")
    now = utcnow()
    app_doc = {
        "job_id": jid, "company_id": job.get("company_id"),
        "contact_id": body.contact_id,
        "company_name": company_name, "job_title": job.get("title", ""),
        "contact_snapshot": ({k: contact.get(k) for k in
                              ("name", "email", "designation", "department", "contact_type")}
                             if contact else None),
        "agent_slug": job.get("agent_slug") or "rajiblabs-career",
        "match_score": report.match_score,
        "requirements": analysis.model_dump(),
        "matches": [m.model_dump() for m in matches],
        "sources": artifacts["sources"],
        "email_subject": artifacts["email_subject"],
        "email_body": artifacts["email_body"],
        "cover_letter": artifacts["cover_letter"],
        "summary": artifacts["short_summary"],
        "quality": quality, "ai_used": ai_used,
        "status": "Needs Review", "notes": "",
        "resume_version": None, "approved_by": None, "approved_at": None,
        "sent_at": None, "response_at": None, "followup_date": None,
        "created_at": now, "updated_at": now, "created_by": email,
    }
    res = await db["career_applications"].insert_one(app_doc)
    await db["career_jobs"].update_one(
        {"_id": job["_id"]},
        {"$set": {"status": "Ready for Application", "updated_at": utcnow()}})
    await audit(email, "CAREER_GENERATE", str(res.inserted_id),
                {"job_id": jid, "match_score": report.match_score,
                 "quality": quality, "ai_used": ai_used},
                event_type="CAREER_GENERATE")
    return {"application_id": str(res.inserted_id),
            "analysis": analysis.model_dump(),
            "match": report.model_dump(),
            "relevant_experience": [m.model_dump() for m in matches],
            "sources": artifacts["sources"], "quality": quality,
            "ai_generated": ai_used,
            "elapsed_ms": int((time.monotonic() - t) * 1000),
            "email_subject": artifacts["email_subject"],
            "email_body": artifacts["email_body"],
            "cover_letter": artifacts["cover_letter"],
            "summary": artifacts["short_summary"]}


# ── Applications: track / review / approve / send ──

APPROVABLE = ("Draft", "AI Generated", "Needs Review")


@router.get("/applications")
async def list_applications(q: str | None = None, status: str | None = None,
                            company_id: str | None = None,
                            date_from: str | None = None,
                            date_to: str | None = None,
                            sort: str = "-created", page: int = 1, limit: int = 50,
                            email: str = Depends(require_admin)):
    from app.schemas import CAREER_APP_STATUSES
    from datetime import datetime
    db = get_db()
    query: dict = {}
    if q and q.strip():
        rx = {"$regex": re.escape(q.strip()[:100]), "$options": "i"}
        query["$or"] = [{"job_title": rx}, {"company_name": rx},
                        {"email_subject": rx}, {"notes": rx}]
    if status:
        if status not in CAREER_APP_STATUSES:
            raise HTTPException(400, "Invalid status")
        query["status"] = status
    if company_id:
        query["company_id"] = company_id
    for key, op in (("date_from", "$gte"), ("date_to", "$lte")):
        val = {"date_from": date_from, "date_to": date_to}[key]
        if val:
            try:
                dt = datetime.fromisoformat(val.replace("Z", "+00:00"))
            except ValueError:
                raise HTTPException(400, f"Invalid {key} (use ISO date)")
            query.setdefault("created_at", {})[op] = dt
    page, limit = (max(1, page), min(max(limit, 1), 100))
    order = [("created_at", -1)] if sort != "created" else [("created_at", 1)]
    total = await db["career_applications"].count_documents(query)
    cur = db["career_applications"].find(
        query, {"email_body": 0, "cover_letter": 0}).sort(order).skip(
        (page - 1) * limit).limit(limit)
    return {"items": [oid_str(d) async for d in cur],
            "total": total, "page": page, "limit": limit}


@router.get("/applications/{aid}")
async def get_application(aid: str, email: str = Depends(require_admin)):
    return oid_str(await _get_or_404("career_applications", aid, "Application"))


@router.put("/applications/{aid}")
async def update_application(aid: str, body: ApplicationPatch,
                             email: str = Depends(require_admin)):
    from app.schemas import CAREER_APP_STATUSES
    db = get_db()
    await _get_or_404("career_applications", aid, "Application")
    patch = {k: v for k, v in body.model_dump(exclude_unset=True).items()
             if v is not None}
    if "status" in patch and patch["status"] not in CAREER_APP_STATUSES:
        raise HTTPException(400, "Invalid status")
    patch["updated_at"] = utcnow()
    await db["career_applications"].update_one({"_id": _oid(aid)}, {"$set": patch})
    await audit(email, "CAREER_APP_UPDATE", aid, {"fields": sorted(patch)},
                event_type="CAREER_APP_UPDATE")
    return oid_str(await db["career_applications"].find_one({"_id": _oid(aid)}))


@router.post("/applications/{aid}/refine")
async def refine_application(aid: str, body: dict,
                             email: str = Depends(require_admin)):
    return await _refine_application(aid, body, email)


async def _refine_application(aid: str, body: dict, email: str):
    db = get_db()
    doc = await _get_or_404("career_applications", aid, "Application")
    instruction = ((body or {}).get("instruction") or "").strip()
    target = ((body or {}).get("target") or "email_body").strip()
    if len(instruction) < 2:
        raise HTTPException(400, "Instruction is required")
    if target not in ("email_body", "cover_letter", "summary"):
        raise HTTPException(400, "target must be email_body|cover_letter|summary")
    current = (doc.get(target) or "").strip()
    if not current:
        raise HTTPException(400, "Nothing to refine yet — generate first")
    new_text, command = await wb.refine_text(current, instruction)
    known = await wb.collect_known_urls(db)
    new_text = wb._scrub_urls(new_text, known)
    quality = wb.quality_check(
        new_text if target == "email_body" else doc.get("email_body", ""),
        new_text if target == "cover_letter" else doc.get("cover_letter", ""),
        new_text if target == "summary" else doc.get("summary", ""),
        [], known, mode="job_application")
    await db["career_applications"].update_one(
        {"_id": doc["_id"]},
        {"$set": {target: new_text, "quality": quality, "updated_at": utcnow()}})
    await audit(email, "CAREER_APP_REFINE", aid,
                {"target": target, "command": command.get("kind")},
                event_type="CAREER_APP_REFINE")
    return {"text": new_text, "command": command, "quality": quality}


@router.post("/applications/{aid}/approve")
async def approve_application(aid: str, email: str = Depends(require_admin)):
    db = get_db()
    doc = await _get_or_404("career_applications", aid, "Application")
    if doc.get("status") not in APPROVABLE:
        raise HTTPException(409, f"Only {', '.join(APPROVABLE)} applications can be approved")
    now = utcnow()
    await db["career_applications"].update_one(
        {"_id": doc["_id"]},
        {"$set": {"status": "Approved", "approved_by": email,
                  "approved_at": now, "updated_at": now}})
    await audit(email, "CAREER_APP_APPROVE", aid, event_type="CAREER_APP_APPROVE")
    return oid_str(await db["career_applications"].find_one({"_id": doc["_id"]}))


@router.post("/applications/{aid}/send")
async def send_application(aid: str, body: dict,
                           email: str = Depends(require_admin)):
    """Send ONLY approved applications. Validated server-side; duplicate sends
    refused unless {"resend": true}. Never logs bodies or credentials."""
    from app.services import email_service
    db = get_db()
    doc = await _get_or_404("career_applications", aid, "Application")
    if doc.get("status") != "Approved" and not (body or {}).get("resend"):
        raise HTTPException(409, "Only Approved applications can be sent (approve first)")
    if doc.get("status") == "Sent" and not (body or {}).get("resend"):
        raise HTTPException(409, "Already sent — pass {resend: true} to resend")
    contact = None
    if doc.get("contact_id"):
        try:
            contact = await db["career_contacts"].find_one(
                {"_id": _oid(doc["contact_id"])})
        except HTTPException:
            contact = None
    to_email = ((contact or {}).get("email") or "").strip()
    if not to_email or not contact or contact.get("active") is False:
        raise HTTPException(400, "No active HR contact with a valid email on this application")
    subject = (doc.get("email_subject") or "").strip()
    content = (doc.get("email_body") or "").strip()
    if not subject or not content:
        raise HTTPException(400, "Subject and body are required before sending")
    try:
        result = email_service.send_application_email(to_email, subject, content)
    except email_service.EmailError as e:
        await log_error("career_send", f"send failed for application {aid}",
                        str(e)[:500], logger="app.routers.admin_career")
        raise HTTPException(502, f"Email failed: {e}")
    now = utcnow()
    await db["career_applications"].update_one(
        {"_id": doc["_id"]},
        {"$set": {"status": "Sent", "sent_at": now, "updated_at": now}})
    await audit(email, "CAREER_APP_SEND", aid,
                {"to_domain": result.get("to_domain"), "resend": bool((body or {}).get("resend"))},
                event_type="CAREER_APP_SEND")
    return {"ok": True, "to_domain": result.get("to_domain"), "sent_at": now}


@router.post("/applications/{aid}/status")
async def set_application_status(aid: str, body: dict,
                                 email: str = Depends(require_admin)):
    from app.schemas import CAREER_APP_STATUSES
    db = get_db()
    await _get_or_404("career_applications", aid, "Application")
    status = ((body or {}).get("status") or "").strip()
    if status not in CAREER_APP_STATUSES:
        raise HTTPException(400, "Invalid status")
    patch: dict = {"status": status, "updated_at": utcnow()}
    for key in ("followup_date", "notes"):
        if (body or {}).get(key) is not None:
            patch[key] = (body or {})[key]
    if status == "Response Received" and not (body or {}).get("response_at"):
        patch["response_at"] = utcnow()
    elif (body or {}).get("response_at"):
        patch["response_at"] = (body or {})["response_at"]
    await db["career_applications"].update_one({"_id": _oid(aid)}, {"$set": patch})
    await audit(email, "CAREER_APP_STATUS", aid, {"status": status},
                event_type="CAREER_APP_STATUS")
    return oid_str(await db["career_applications"].find_one({"_id": _oid(aid)}))


@router.delete("/applications/{aid}")
async def delete_application(aid: str, email: str = Depends(require_admin)):
    db = get_db()
    doc = await _get_or_404("career_applications", aid, "Application")
    if doc.get("status") == "Sent":
        raise HTTPException(409, "Sent applications are kept for history — use Closed instead")
    await db["career_applications"].delete_one({"_id": doc["_id"]})
    await audit(email, "CAREER_APP_DELETE", aid, event_type="CAREER_APP_DELETE")
    return {"ok": True}
