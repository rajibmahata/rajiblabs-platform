"""Admin Learning — paths, blocks, dashboard (JWT required). Reuses existing learning infra."""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional
from app.auth.dependencies import require_admin
from app.database import get_db, utcnow
from app.models import oid_str

router = APIRouter(prefix="/api/admin/learning")

class PathIn(BaseModel):
    topic: str
    duration: int
    goal: Optional[str] = None
    level: Optional[str] = None

@router.post("/paths")
async def create_path(body: PathIn, email: str = Depends(require_admin)):
    if not body.topic.strip():
        raise HTTPException(400, "Topic required")
    if not (1 <= body.duration <= 60):
        raise HTTPException(400, "Duration must be 1-60 days")
    from app.services.learning_agent import create_learning_path
    doc = await create_learning_path(body.topic.strip(), body.duration, body.goal or "", body.level or "beginner", created_by=email)
    return oid_str(doc)

@router.get("/paths")
async def list_paths(status: Optional[str]=None, email: str = Depends(require_admin)):
    db=get_db()
    q={}
    if status: q["status"]=status
    cur=db["learning_paths"].find(q).sort("updated_at",-1).limit(100)
    return [oid_str(d) async for d in cur]

@router.get("/paths/{slug}")
async def get_path(slug: str, email: str = Depends(require_admin)):
    db=get_db()
    d=await db["learning_paths"].find_one({"slug": slug})
    if not d: raise HTTPException(404, "Not found")
    return oid_str(d)

@router.patch("/paths/{slug}")
async def patch_path(slug: str, body: dict, email: str = Depends(require_admin)):
    db=get_db()
    allowed={"status","goal","level","prerequisites"}
    patch={k:v for k,v in (body or {}).items() if k in allowed}
    if not patch: raise HTTPException(400, "Nothing to update")
    if "status" in patch:
        from app.services.learning_agent import normalize_path_status
        try:
            # Accept live/published/draft synonyms; store the canonical form
            # (live/published → active, draft → planned) so the public site
            # picks the path up without any further step.
            patch["status"] = normalize_path_status(patch["status"])
        except ValueError:
            raise HTTPException(400, "Invalid status")
    patch["updated_at"]=utcnow()
    res=await db["learning_paths"].update_one({"slug":slug},{"$set":patch})
    if not res.matched_count: raise HTTPException(404,"Not found")
    return oid_str(await db["learning_paths"].find_one({"slug":slug}))

@router.get("/paths/{slug}/blocks")
async def list_blocks(slug: str, email: str = Depends(require_admin)):
    db=get_db()
    path=await db["learning_paths"].find_one({"slug":slug})
    if not path: raise HTTPException(404,"Not found")
    cur=db["learning_blocks"].find({"path_id": path["_id"]}).sort("day_number",1)
    return [oid_str(d) async for d in cur]

@router.get("/paths/{slug}/blocks/{day}")
async def get_block(slug: str, day: int, email: str = Depends(require_admin)):
    db=get_db()
    path=await db["learning_paths"].find_one({"slug":slug})
    if not path: raise HTTPException(404,"Not found")
    d=await db["learning_blocks"].find_one({"path_id": path["_id"], "day_number": day})
    if not d: raise HTTPException(404,"Not found")
    return oid_str(d)

@router.post("/paths/{slug}/run")
async def run_path(slug: str, email: str = Depends(require_admin)):
    from app.services.learning_agent import run_daily as run_learning
    # Trigger single path run: temporarily set only this path to active
    db=get_db()
    # Ensure path is active
    await db["learning_paths"].update_one({"slug":slug},{"$set":{"status":"active","updated_at":utcnow()}})
    res=await run_learning(triggered_by=f"admin:{email}")
    return res

@router.get("/dashboard")
async def dashboard(email: str = Depends(require_admin)):
    db=get_db()
    total=await db["learning_paths"].count_documents({})
    active=await db["learning_paths"].count_documents({"status":"active"})
    blocks_total=await db["learning_blocks"].count_documents({})
    blocks_pub=await db["learning_blocks"].count_documents({"status":"published"})
    last_run=await db["learning_agent_runs"].find_one(sort=[("started_at",-1)])
    return {
        "total_paths": total, "active_paths": active,
        "blocks_total": blocks_total, "blocks_published": blocks_pub,
        "last_run": oid_str(last_run) if last_run else None,
        "next_run": "06:00 Asia/Kolkata"
    }

@router.get("/agent/runs")
async def agent_runs(email: str = Depends(require_admin)):
    db=get_db()
    cur=db["learning_agent_runs"].find({}).sort("started_at",-1).limit(20)
    return [oid_str(d) async for d in cur]

@router.post("/run")
async def run_all(email: str = Depends(require_admin)):
    from app.services.learning_agent import run_daily as run_learning
    res=await run_learning(triggered_by=f"admin:{email}")
    return res

@router.get("/paths/{slug}/validate")
async def validate_path(slug: str, email: str = Depends(require_admin)):
    """Run block-level + path-level validation on a learning path. Returns detailed results."""
    from app.services.learning_agent import validate_block_quality, validate_path_coherence
    db=get_db()
    path=await db["learning_paths"].find_one({"slug":slug})
    if not path: raise HTTPException(404,"Not found")
    blocks=[b async for d in [db["learning_blocks"].find({"path_id": path["_id"]}).sort("day_number",1)] for b in d]
    # Block-level validation
    block_results = []
    prev_block = None
    for b in blocks:
        q_passed, q_issues, q_improvements = validate_block_quality(
            b, day=b.get("day_number",0), topic=path.get("topic",""), prev_block=prev_block
        )
        block_results.append({
            "day": b.get("day_number"),
            "title": b.get("title") or b.get("topic"),
            "status": b.get("status"),
            "passed": q_passed,
            "issues": q_issues,
            "improvements": q_improvements,
        })
        prev_block = b
    # Path-level validation
    path_ok, path_issues = validate_path_coherence(path, blocks)
    # Store results
    await db["learning_paths"].update_one({"_id": path["_id"]}, {"$set": {
        "path_validation_issues": path_issues,
        "block_validation_results": block_results,
        "last_validated_at": utcnow(),
        "updated_at": utcnow(),
    }})
    return {
        "path_passed": path_ok,
        "path_issues": path_issues,
        "blocks": block_results,
        "total_blocks": len(blocks),
        "passed_blocks": sum(1 for b in block_results if b["passed"]),
        "failed_blocks": sum(1 for b in block_results if not b["passed"]),
        "blocks_with_improvements": sum(1 for b in block_results if b["improvements"]),
    }


# ── Universal Content Validation Engine endpoints ──

@router.post("/validate")
async def validate_universal_content(body: dict, email: str = Depends(require_admin)):
    """Validate any learning content using the universal engine."""
    from app.services.content_validator import (
        validate_and_save_block, validate_and_save_path,
        should_skip_revalidation, plan_improvements,
    )
    db = get_db()
    content_type = body.get("content_type", "lesson")
    force = body.get("force", False)
    slug = body.get("slug")
    day = body.get("day")

    if content_type == "learning_path":
        if not slug:
            raise HTTPException(400, "slug required for learning_path validation")
        path = await db["learning_paths"].find_one({"slug": slug})
        if not path:
            raise HTTPException(404, f"Path '{slug}' not found")
        blocks = [b async for b in db["learning_blocks"].find(
            {"path_id": path["_id"]}).sort("day_number", 1)]
        if not blocks:
            raise HTTPException(400, f"Path '{slug}' has no blocks to validate")
        result = await validate_and_save_path(db, path, blocks)
        # Also validate each block
        block_results = []
        for b in blocks:
            br = await validate_and_save_block(db, b, path, blocks)
            block_results.append({"day": b.get("day_number"), "score": br.get("overall_score"), "status": br.get("status")})
        result["block_results"] = block_results
        return result
    else:
        # Single block validation
        if not slug:
            raise HTTPException(400, "slug required for block validation")
        path_doc = await db["learning_paths"].find_one({"slug": slug})
        blocks = []
        if path_doc:
            blocks = [b async for b in db["learning_blocks"].find(
                {"path_id": path_doc["_id"]}).sort("day_number", 1)]
        block = None
        if day is not None and path_doc:
            block = await db["learning_blocks"].find_one(
                {"path_id": path_doc["_id"], "day_number": day})
        if not block and blocks:
            # Validate first block if none specified
            block = blocks[0]
        if not block:
            raise HTTPException(404, "Block not found")
        # Skip check
        if not force:
            from app.services.content_validator import normalize_lesson_block
            nc = normalize_lesson_block(block, path_doc)
            if await should_skip_revalidation(db, str(block.get("_id", "")), nc.content_hash):
                return {"skipped": True, "reason": "Content unchanged", "content_hash": nc.content_hash}
        result = await validate_and_save_block(db, block, path_doc, blocks)
        # Add improvement plans
        result["improvement_plan"] = plan_improvements(result)
        return result


@router.get("/validate/{slug}")
async def get_validation_history(slug: str, limit: int = 20, email: str = Depends(require_admin)):
    """Get validation history for a path."""
    from app.services.content_validator import get_validation_history
    db = get_db()
    path = await db["learning_paths"].find_one({"slug": slug})
    if not path:
        raise HTTPException(404, f"Path '{slug}' not found")
    history = await get_validation_history(db, str(path.get("_id", "")), limit)
    return {"slug": slug, "history": history, "total": len(history)}


@router.post("/validate-all")
async def validate_all_content(body: dict | None = None, email: str = Depends(require_admin)):
    """Validate all learning paths using the universal engine."""
    from app.services.content_validator import validate_all_paths
    db = get_db()
    result = await validate_all_paths(db)
    return result


@router.get("/rules")
async def get_validation_rules(email: str = Depends(require_admin)):
    """List all available validation rules."""
    from app.services.content_validator import RULES
    return {
        "total": len(RULES),
        "rules": [
            {
                "rule_id": r.rule_id,
                "name": r.name,
                "category": r.category,
                "severity": r.severity,
                "applies_to": r.applies_to,
                "description": r.description,
                "enabled": r.enabled,
            }
            for r in RULES
        ],
    }


@router.get("/score/{slug}")
async def get_content_scores(slug: str, email: str = Depends(require_admin)):
    """Get current scores for all blocks in a path."""
    db = get_db()
    path = await db["learning_paths"].find_one({"slug": slug})
    if not path:
        raise HTTPException(404, f"Path '{slug}' not found")
    blocks = [b async for b in db["learning_blocks"].find(
        {"path_id": path["_id"]}).sort("day_number", 1)]
    scores = []
    for b in blocks:
        scores.append({
            "day": b.get("day_number"),
            "title": b.get("title") or b.get("topic"),
            "validation_score": b.get("validation_score", 0),
            "validation_status": b.get("validation_status", ""),
            "validation_issues_count": b.get("validation_issues_count", 0),
            "validation_mode": b.get("validation_mode", ""),
            "last_validated_at": str(b.get("last_validated_at", "")),
        })
    path_score = path.get("validation_score", 0)
    path_status = path.get("validation_status", "")
    return {
        "slug": slug,
        "path_score": path_score,
        "path_status": path_status,
        "blocks": scores,
        "total_blocks": len(blocks),
        "passing": sum(1 for s in scores if s["validation_status"] == "PASS"),
        "failing": sum(1 for s in scores if s["validation_status"] == "FAIL"),
    }


@router.post("/rollback/{slug}")
async def rollback_content(slug: str, body: dict | None = None, email: str = Depends(require_admin)):
    """Find the last known-good version for content rollback guidance."""
    from app.services.content_validator import rollback_content
    db = get_db()
    day = (body or {}).get("day")
    if day is not None:
        path = await db["learning_paths"].find_one({"slug": slug})
        if not path:
            raise HTTPException(404, f"Path '{slug}' not found")
        block = await db["learning_blocks"].find_one(
            {"path_id": path["_id"], "day_number": day})
        if not block:
            raise HTTPException(404, f"Block day {day} not found")
        result = await rollback_content(db, "lesson", str(block.get("_id", "")))
    else:
        path = await db["learning_paths"].find_one({"slug": slug})
        if not path:
            raise HTTPException(404, f"Path '{slug}' not found")
        result = await rollback_content(db, "learning_path", str(path.get("_id", "")))
    return {"slug": slug, "day": day, **result}
