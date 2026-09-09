"""Admin Profile Intelligence Agent — config, dashboard, runs, proposals."""
from fastapi import APIRouter, Depends, HTTPException
from app.auth.dependencies import require_admin
from app.config import get_settings
from app.database import get_db, utcnow
from app.models import oid_str
from app.services.notify import audit

router = APIRouter(prefix="/api/admin/profile-agent")

ALLOWED_TOOLS = [
    "get_profile","update_profile_draft","get_resume","analyze_resume",
    "sync_github","get_github_repositories","get_repository_details",
    "create_project_draft","update_project_draft","create_portfolio_draft",
    "create_product_draft","validate_urls","search_knowledge","update_knowledge",
    "check_configuration","check_content_completeness","create_admin_task","request_approval"
]

@router.get("/config")
async def get_config(email: str = Depends(require_admin)):
    from app.services import agent_config
    db = get_db()
    cfg = await agent_config.get_agent(db, agent_config.PROFILE_SLUG)
    return oid_str(cfg) if cfg else cfg

@router.put("/config")
async def update_config(body: dict, email: str = Depends(require_admin)):
    from app.services import agent_config
    db = get_db()
    cfg = await agent_config.get_agent(db, agent_config.PROFILE_SLUG)
    if not cfg:
        raise HTTPException(404, "Agent not found")
    # whitelist
    patch = {}
    if "enabled" in body:
        patch["enabled"] = bool(body["enabled"])
    if "policy" in body and isinstance(body["policy"], dict):
        # validate policy keys
        allowed_policy_keys = {"auto_create_drafts","auto_update_metadata","auto_translation","auto_publish","github_sync","knowledge_sync","health_check_frequency","run_frequency","approval_required_for"}
        patch["policy"] = {k:v for k,v in body["policy"].items() if k in allowed_policy_keys}
        # merge with existing
        existing_policy = cfg.get("policy",{})
        merged = {**existing_policy, **patch["policy"]}
        patch["policy"] = merged
    if "allowed_tools" in body:
        patch["allowed_tools"] = [t for t in body["allowed_tools"] if t in ALLOWED_TOOLS][:30]
    if "schedule" in body and isinstance(body["schedule"], dict):
        patch["schedule"] = body["schedule"]
    if not patch:
        raise HTTPException(400, "No valid fields")
    patch["updated_at"] = utcnow()
    await db["ai_agents"].update_one({"slug": agent_config.PROFILE_SLUG}, {"$set": patch})
    await audit(email, "PROFILE_AGENT_CONFIG", agent_config.PROFILE_SLUG, {"fields": list(patch.keys())})
    return await agent_config.get_agent(db, agent_config.PROFILE_SLUG)

@router.get("/dashboard")
async def dashboard(email: str = Depends(require_admin)):
    from app.services.profile_agent import get_dashboard
    db = get_db()
    return await get_dashboard(db)

@router.get("/runs")
async def list_runs(email: str = Depends(require_admin)):
    db = get_db()
    cur = db["profile_agent_runs"].find().sort("started_at", -1).limit(20)
    return [oid_str(d) async for d in cur]

@router.get("/proposals")
async def list_proposals(status: str | None = None, email: str = Depends(require_admin)):
    db = get_db()
    q = {}
    if status:
        q["status"] = status
    cur = db["profile_agent_proposals"].find(q).sort("created_at", -1).limit(100)
    return [oid_str(d) async for d in cur]

@router.post("/proposals/{pid}/approve")
async def approve_proposal(pid: str, email: str = Depends(require_admin)):
    from app.services.profile_agent import apply_proposal
    from bson import ObjectId
    db = get_db()
    try:
        oid = ObjectId(pid)
    except Exception:
        raise HTTPException(400, "Invalid id")
    prop = await db["profile_agent_proposals"].find_one({"_id": oid})
    if not prop:
        raise HTTPException(404, "Proposal not found")
    if prop.get("status") != "pending":
        raise HTTPException(400, "Already decided")
    # check approval required - if policy requires approval, ensure actor is admin (already)
    await db["profile_agent_proposals"].update_one({"_id": oid}, {"$set": {"status":"approved", "decided_at": utcnow(), "decided_by": email}})
    # auto-apply if safe? No, require explicit apply step for audit
    # But for demo, we apply immediately after approve
    try:
        result = await apply_proposal(pid, email)
    except Exception as e:
        await db["profile_agent_proposals"].update_one({"_id": oid}, {"$set": {"status":"pending", "error": str(e)[:500]}})
        raise HTTPException(400, str(e))
    await audit(email, "PROFILE_PROPOSAL_APPROVE", pid)
    return result

@router.post("/proposals/{pid}/reject")
async def reject_proposal(pid: str, email: str = Depends(require_admin)):
    from bson import ObjectId
    db = get_db()
    try:
        oid = ObjectId(pid)
    except Exception:
        raise HTTPException(400, "Invalid id")
    prop = await db["profile_agent_proposals"].find_one({"_id": oid})
    if not prop:
        raise HTTPException(404, "Proposal not found")
    await db["profile_agent_proposals"].update_one({"_id": oid}, {"$set": {"status":"rejected", "decided_at": utcnow(), "decided_by": email}})
    await audit(email, "PROFILE_PROPOSAL_REJECT", pid)
    return {"ok": True}

@router.post("/run")
async def run_now(email: str = Depends(require_admin)):
    from app.services.profile_agent import run_profile_agent
    result = await run_profile_agent(triggered_by=email)
    await audit(email, "PROFILE_AGENT_RUN", "manual", {"result": str(result)[:500]})
    return result

@router.post("/proposals/{pid}/apply")
async def apply_now(pid: str, email: str = Depends(require_admin)):
    from app.services.profile_agent import apply_proposal
    # must be approved
    from bson import ObjectId
    db = get_db()
    prop = await db["profile_agent_proposals"].find_one({"_id": ObjectId(pid)})
    if not prop or prop.get("status") != "approved":
        raise HTTPException(400, "Proposal must be approved first")
    return await apply_proposal(pid, email)
