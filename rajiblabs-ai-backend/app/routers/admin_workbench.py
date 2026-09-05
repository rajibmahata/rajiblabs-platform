"""Admin AI Proposal Studio API (§27, §33).

All routes require admin JWT (require_admin). Private sessions/documents are
never exposed via public APIs. Every AI call flows through the existing AI
orchestrator inside app.services.workbench — never direct provider calls.
"""
from fastapi import APIRouter, Depends, HTTPException
from app.auth.dependencies import require_admin
from app.database import get_db, utcnow
from app.models import oid_str
from app.schemas import (
    AnalyzeIn, GenerateIn, ProposalSaveIn, ProposalStatusIn, RefineIn,
    WorkbenchChatIn,
)
from app.services import workbench as wb
from app.services.workbench import validate_url

router = APIRouter(prefix="/api/admin/ai")


def _oid(pid: str):
    from bson import ObjectId
    try:
        return ObjectId(pid)
    except Exception:
        raise HTTPException(400, "Invalid id")


async def _session(db, session_id: str | None, email: str) -> dict:
    if session_id:
        s = await wb.get_session(db, session_id[:16])
        if s:
            return s
    s = {"session_id": wb.new_session_id(), "messages": [], "artifacts": {},
         "analysis": {}, "sources": [], "job_description": "", "mode": "freelance_proposal",
         "created_at": utcnow(), "created_by": email}
    await wb.save_session(db, s)
    return s


@router.post("/proposal/analyze")
async def analyze(body: AnalyzeIn, email: str = Depends(require_admin)):
    """§4: structure the pasted opportunity. Rules always work; AI enriches."""
    import time
    db = get_db()
    t0 = time.monotonic()
    analysis, ai_used = await wb.analyze_requirements(body.job_description, db)
    if (body.company or "").strip():
        analysis.company = body.company.strip()[:200]
    elapsed_ms = int((time.monotonic() - t0) * 1000)
    sess = await _session(db, body.session_id, email)
    sess.update({"job_description": body.job_description[:20000], "mode": body.mode,
                 "analysis": analysis.model_dump(), "messages": []})
    await wb.save_session(db, sess)
    await wb.audit_workbench(email, "WORKBENCH_ANALYZE", sess["session_id"],
                             {"mode": body.mode, "ai_used": ai_used,
                              "techs": analysis.technologies[:10]},
                             session_id=sess["session_id"])
    return {"analysis": analysis.model_dump(), "ai_used": ai_used,
            "elapsed_ms": elapsed_ms, "session_id": sess["session_id"]}


@router.post("/proposal/generate")
async def generate(body: GenerateIn, email: str = Depends(require_admin)):
    """§5–§13 + §19–§20: full pipeline → validated ProposalResult.

    Returns per-stage timings so the UI shows real progress data.
    """
    import time
    db = get_db()
    stages: list[dict] = []

    def _stage(key: str, label: str, start: float):
        stages.append({"key": key, "label": label,
                       "ms": int((time.monotonic() - start) * 1000)})

    t = time.monotonic()
    analysis = body.analysis
    if analysis is None:
        analysis, _ = await wb.analyze_requirements(body.job_description, db)
    if (body.company or "").strip():
        analysis.company = body.company.strip()[:200]
    _stage("analyze", "Requirements analyzed", t)
    t = time.monotonic()
    evidence = await wb.retrieve_evidence(
        analysis, source_ids=body.source_ids or None, db=db)
    _stage("retrieve", "RAG evidence retrieved", t)
    t = time.monotonic()
    selected = await wb.select_examples(analysis, evidence)
    _stage("match", "Examples selected", t)
    t = time.monotonic()
    matches = await wb.match_requirements(analysis, selected, evidence)
    report = wb.match_score(analysis, matches, selected, evidence)
    known = await wb.collect_known_urls(db)
    # Match URLs must also be allowlisted (§32).
    for m in matches:
        m.url = validate_url(m.url, known)
    _stage("score", "Matches scored", t)
    t = time.monotonic()
    artifacts, ai_used = await wb.generate_artifacts(
        analysis, matches, selected, body.mode, body.tone, body.length, known, db,
        language=body.language or "en", company=body.company,
        instructions=body.instructions)
    _stage("generate", "Content generated", t)
    t = time.monotonic()
    quality = wb.quality_check(artifacts["proposal"], artifacts["cover_letter"],
                                artifacts["short_summary"], selected, known,
                                mode=body.mode)
    # §31: one automatic fix pass for auto-fixable issues when AI is available.
    if not quality["passed"] and ai_used and any(
            i in ("generic_opener", "hype_language", "missing_call_to_action")
            for i in quality["issues"]):
        fix = ("Remove any generic opener and hype language, keep every fact, "
               "project name and URL exactly, and end with a clear call to action.")
        try:
            fixed, _ = await wb.refine_text(artifacts["proposal"], fix)
            fixed = wb._scrub_urls(fixed, known)
            q2 = wb.quality_check(fixed, artifacts["cover_letter"],
                                  artifacts["short_summary"], selected, known,
                                  mode=body.mode)
            if q2["score"] >= quality["score"]:
                artifacts["proposal"] = fixed
                quality = q2
        except Exception as e:
            wb.log.warning("workbench auto-fix failed: %s", e)
    _stage("validate", "Quality validated", t)
    sess = await _session(db, body.session_id, email)
    sess.update({"job_description": body.job_description[:20000], "mode": body.mode,
                 "analysis": analysis.model_dump(),
                 "sources": artifacts["sources"],
                 "artifacts": {k: artifacts[k] for k in ("proposal", "cover_letter", "short_summary") if k in artifacts}})
    if artifacts.get("explanation"):
        sess["artifacts"]["explanation"] = artifacts["explanation"]
    await wb.save_session(db, sess)
    await wb.audit_workbench(email, "WORKBENCH_GENERATE", sess["session_id"],
                             {"mode": body.mode, "match_score": report.match_score,
                              "quality": quality, "ai_used": ai_used,
                              "stages": stages},
                             session_id=sess["session_id"])
    total_ms = sum(s["ms"] for s in stages)
    return {"analysis": analysis.model_dump(), "match": report.model_dump(),
            "relevant_experience": [m.model_dump() for m in matches],
            "proposal": artifacts["proposal"], "cover_letter": artifacts["cover_letter"],
            "short_summary": artifacts["short_summary"],
            "explanation": artifacts.get("explanation", ""),
            "sources": artifacts["sources"],
            "quality": quality, "ai_generated": ai_used,
            "stages": stages, "total_ms": total_ms,
            "session_id": sess["session_id"]}


@router.post("/proposal/refine")
async def refine(body: RefineIn, email: str = Depends(require_admin)):
    """§22: modify an existing artifact, never restart the workflow."""
    db = get_db()
    if body.target not in ("proposal", "cover_letter", "summary", "explanation"):
        raise HTTPException(400, "target must be proposal|cover_letter|summary|explanation")
    key = {"summary": "short_summary"}.get(body.target, body.target)
    text, sess = "", None
    if body.document_id:
        doc = await db["proposal_documents"].find_one({"_id": _oid(body.document_id)})
        if not doc:
            raise HTTPException(404, "Document not found")
        field = {"proposal": "proposal", "cover_letter": "cover_letter",
                 "summary": "summary", "explanation": "explanation"}[body.target]
        text = doc.get(field, "")
        if body.session_id:
            sess = await wb.get_session(db, body.session_id[:16])
    elif body.session_id:
        sess = await wb.get_session(db, body.session_id[:16])
        if not sess:
            raise HTTPException(404, "Session not found")
        text = (sess.get("artifacts") or {}).get(key, "")
    if not text:
        raise HTTPException(400, "No artifact to refine yet — generate first")
    extra = ""
    cmd = wb.parse_refine_instruction(body.instruction)
    if cmd["kind"] == "add_project" and cmd["extra"] and sess:
        extra = "\n".join(
            f"- {c.get('doc_title')}: {(c.get('content') or '')[:600]}"
            for c in await wb.retrieve_evidence(
                wb.RequirementAnalysis.model_validate(sess.get("analysis") or {}),
                top_k=12, db=db)
            if cmd["extra"].lower() in (c.get("doc_title") or "").lower())
    known = await wb.collect_known_urls(db)
    new_text, command = await wb.refine_text(text, body.instruction, extra)
    new_text = wb._scrub_urls(new_text, known)
    if sess:
        sess.setdefault("artifacts", {})[key] = new_text
        sess.setdefault("messages", []).append(
            {"role": "user", "content": body.instruction[:500], "created_at": utcnow().isoformat()})
        await wb.save_session(db, sess)
    await wb.audit_workbench(email, "WORKBENCH_REFINE", (sess or {}).get("session_id", ""),
                             {"target": body.target, "command": command},
                             session_id=(sess or {}).get("session_id"))
    return {"text": new_text, "command": command,
            "session_id": (sess or {}).get("session_id")}


@router.post("/proposal/save")
async def save_proposal(body: ProposalSaveIn, email: str = Depends(require_admin)):
    """§23: persist a proposal document (private collection)."""
    db = get_db()
    now = utcnow()
    doc = body.model_dump()
    doc.update({"created_at": now, "updated_at": now, "created_by": email})
    res = await db["proposal_documents"].insert_one(doc)
    await wb.audit_workbench(email, "WORKBENCH_SAVE", str(res.inserted_id),
                             {"title": body.title, "type": body.type, "status": body.status})
    return {"id": str(res.inserted_id)}


@router.get("/proposal/{doc_id}")
async def get_proposal(doc_id: str, email: str = Depends(require_admin)):
    db = get_db()
    doc = await db["proposal_documents"].find_one({"_id": _oid(doc_id)})
    if not doc:
        raise HTTPException(404, "Document not found")
    return oid_str(doc)


@router.get("/proposals")
async def list_proposals(status: str | None = None, search: str | None = None,
                         limit: int = 50, email: str = Depends(require_admin)):
    """§24: history — date/title/client/type/score/status (summaries only)."""
    db = get_db()
    q: dict = {}
    if status:
        q["status"] = status
    if search:
        q["$or"] = [{"title": {"$regex": search[:80], "$options": "i"}},
                    {"job_description": {"$regex": search[:80], "$options": "i"}}]
    cur = db["proposal_documents"].find(
        q, {"proposal": 0, "cover_letter": 0, "job_description": 0}
    ).sort("created_at", -1).limit(min(max(limit, 1), 100))
    out = []
    async for d in cur:
        d = oid_str(d)
        a = d.get("analysis") or {}
        d["client"] = a.get("company", "")
        d["job_title"] = a.get("title", "")
        d["match_score"] = (d.get("match") or {}).get("match_score", 0)
        out.append(d)
    return out


@router.put("/proposal/{doc_id}")
async def update_proposal(doc_id: str, body: ProposalSaveIn,
                          email: str = Depends(require_admin)):
    """Edit any field incl. status (§21, §24)."""
    db = get_db()
    oid = _oid(doc_id)
    if not await db["proposal_documents"].find_one({"_id": oid}):
        raise HTTPException(404, "Document not found")
    patch = body.model_dump()
    patch.update({"updated_at": utcnow()})
    await db["proposal_documents"].update_one({"_id": oid}, {"$set": patch})
    await wb.audit_workbench(email, "WORKBENCH_UPDATE", doc_id, {"status": body.status})
    return {"ok": True}


@router.post("/proposal/{doc_id}/duplicate")
async def duplicate_proposal(doc_id: str, email: str = Depends(require_admin)):
    db = get_db()
    doc = await db["proposal_documents"].find_one({"_id": _oid(doc_id)})
    if not doc:
        raise HTTPException(404, "Document not found")
    doc.pop("_id", None)
    now = utcnow()
    doc.update({"title": f"{doc.get('title', '')} (copy)"[:200], "status": "draft",
                "created_at": now, "updated_at": now, "created_by": email})
    res = await db["proposal_documents"].insert_one(doc)
    await wb.audit_workbench(email, "WORKBENCH_DUPLICATE", str(res.inserted_id))
    return {"id": str(res.inserted_id)}


@router.delete("/proposal/{doc_id}")
async def delete_proposal(doc_id: str, email: str = Depends(require_admin)):
    db = get_db()
    res = await db["proposal_documents"].delete_one({"_id": _oid(doc_id)})
    if not res.deleted_count:
        raise HTTPException(404, "Document not found")
    await wb.audit_workbench(email, "WORKBENCH_DELETE", doc_id)
    return {"ok": True}


@router.post("/chat")
async def workbench_chat(body: WorkbenchChatIn, email: str = Depends(require_admin)):
    """§28: session-aware admin chat — retains JD/analysis/sources/artifacts."""
    from app.services import lead_ai as orchestrator
    db = get_db()
    sess = await _session(db, body.session_id, email)
    sess["mode"] = body.mode
    history = sess.get("messages", [])[-12:]
    msg = body.message.strip()
    history.append({"role": "user", "content": msg[:2000], "created_at": utcnow().isoformat()})
    reply, artifacts = "", dict(sess.get("artifacts") or {})
    analysis = wb.RequirementAnalysis.model_validate(sess.get("analysis") or {})

    if len(msg) >= 300 and not sess.get("job_description"):
        # Pasted a fresh opportunity into chat → analyze it.
        analysis, ai_used = await wb.analyze_requirements(msg, db)
        sess.update({"job_description": msg[:20000], "analysis": analysis.model_dump()})
        techs = ", ".join(analysis.technologies[:6]) or "general"
        reply = (f"Analyzed: {analysis.title or 'opportunity'}"
                 f"{(' at ' + analysis.company) if analysis.company else ''} "
                 f"({analysis.industry or 'industry TBD'}). Key tech: {techs}. "
                 f"Say 'generate proposal' when ready, or refine the brief first.")
    elif any(k in msg.lower() for k in ("generate proposal", "create proposal", "generate cover",
                                        "write proposal", "generate")) and sess.get("job_description"):
        gen = await generate(GenerateIn(job_description=sess["job_description"], mode=body.mode,
                                        analysis=analysis,
                                        language=body.language or "en"), email)
        artifacts = {k: gen[k] for k in ("proposal", "cover_letter", "short_summary")}
        sess.update({"analysis": gen["analysis"], "sources": gen["sources"], "artifacts": artifacts})
        reply = (f"Generated ({body.mode}, AI relevance estimate {gen['match']['match_score']}%). "
                 f"Top evidence: {', '.join(s['title'] for s in gen['sources'][:3]) or 'none indexed'}. "
                 f"Review it on the right, then refine or save.")
    elif artifacts and not any(k in msg.lower() for k in ("analyze", "job description")):
        # Default once artifacts exist: treat the message as a refinement.
        target = "cover_letter" if "cover" in msg.lower() else ("summary" if "summary" in msg.lower() else "proposal")
        new_text, command = await wb.refine_text(
            artifacts.get(target, artifacts.get("proposal", "")), msg)
        known = await wb.collect_known_urls(db)
        artifacts[target] = wb._scrub_urls(new_text, known)
        sess["artifacts"] = artifacts
        reply = f"Updated the {target.replace('_', ' ')} ({command['kind']}). Review it on the right."
    else:
        # Grounded Q&A over the session context (§26) — no artifact change.
        ctx = (f"Opportunity: {(sess.get('job_description') or '')[:1500]}\n"
               f"Analysis: {analysis.model_dump()}\nSources: "
               + "; ".join(f"{s.get('title')} ({s.get('type')})" for s in (sess.get("sources") or [])))
        try:
            svc = orchestrator.AIService()
            if not svc.configured:
                raise orchestrator.AIError("AI not configured")
            try:
                from app.services import lang_service as _wls
                _, _wlang = await _wls.response_instruction(body.language or "en", db)
            except Exception:
                _wlang = ""
            out = await svc._complete(
                [{"role": "system", "content": (
                    "You are Rajib's private proposal assistant. Answer using ONLY the "
                    "session context below; never invent projects, URLs or experience. "
                    "Keep replies under 120 words. Return JSON key: reply.")},
                 *([{"role": "system", "content": _wlang}] if _wlang else []),
                 {"role": "system", "content": ctx[:4000]},
                 *[{"role": m["role"], "content": m["content"][:500]} for m in history[-6:]],
                 {"role": "user", "content": msg[:2000]}],
                max_tokens=300, temperature=0.4, tag="workbench-chat")
            reply = str(out["data"].get("reply", "")).strip() or "Noted."
        except Exception:
            reply = ("AI is not configured right now — paste the job description and use "
                     "Analyze / Generate, which work from verified evidence.")
    history.append({"role": "assistant", "content": reply[:2000],
                    "created_at": utcnow().isoformat()})
    sess["messages"] = history[-50:]
    await wb.save_session(db, sess)
    await wb.audit_workbench(email, "WORKBENCH_CHAT", sess["session_id"],
                             {"len": len(msg)}, session_id=sess["session_id"])
    return {"session_id": sess["session_id"], "reply": reply,
            "artifacts": artifacts, "analysis": analysis.model_dump(),
            "sources": sess.get("sources", [])}
