"""Public Learning — structured mentor experience (published only)."""
from fastapi import APIRouter, HTTPException
from app.database import get_db
from app.models import oid_str

router = APIRouter(prefix="/api/learning")

def _public_path(d):
    d=oid_str(d)
    # hide internal hashes
    d.pop("content_hash", None)
    return d

def _public_block(d):
    d=oid_str(d)
    d.pop("content_hash", None)
    d.pop("validation_issues", None)
    return d

@router.get("/paths")
async def list_paths():
    db=get_db()
    cur=db["learning_paths"].find({"status": {"$in": ["active","completed"]}}).sort("updated_at",-1)
    return [_public_path(d) async for d in cur]

@router.get("/paths/{slug}")
async def get_path(slug: str):
    db=get_db()
    d=await db["learning_paths"].find_one({"slug": slug, "status": {"$in": ["active","completed","planned"]}})
    if not d: raise HTTPException(404, "Not found")
    return _public_path(d)

@router.get("/paths/{slug}/blocks")
async def list_blocks(slug: str):
    db=get_db()
    path=await db["learning_paths"].find_one({"slug": slug})
    if not path: raise HTTPException(404, "Not found")
    cur=db["learning_blocks"].find({"path_id": path["_id"], "status": {"$in": ["published","completed"]}}).sort("day_number",1)
    return [_public_block(d) async for d in cur]

@router.get("/paths/{slug}/blocks/{day}")
async def get_block(slug: str, day: int):
    db=get_db()
    path=await db["learning_paths"].find_one({"slug": slug})
    if not path: raise HTTPException(404, "Not found")
    d=await db["learning_blocks"].find_one({"path_id": path["_id"], "day_number": day, "status": {"$in": ["published","completed","ready"]}})
    if not d: raise HTTPException(404, "Not found")
    return _public_block(d)

@router.get("/active")
async def active_learning():
    db=get_db()
    d=await db["learning_paths"].find_one({"status":"active"}, sort=[("updated_at",-1)])
    if not d: return {"active": False}
    blocks=await db["learning_blocks"].count_documents({"path_id": d["_id"]})
    published=await db["learning_blocks"].count_documents({"path_id": d["_id"], "status": "published"})
    return {"active": True, "path": _public_path(d), "blocks_total": blocks, "blocks_published": published, "progress": int((published/blocks*100) if blocks else 0)}

@router.get("/topics")
async def topics():
    db=get_db()
    cur=db["learning_paths"].find({"status": {"$in": ["active","completed"]}})
    seen=set()
    async for d in cur:
        seen.add(d.get("topic",""))
    return sorted(seen)

@router.post("/paths/{slug}/progress")
async def update_progress(slug: str, body: dict):
    # Simple progress tracking per IP/session — lightweight, no auth
    # body: {day: int, exercise_done: bool, homework_done: bool}
    db=get_db()
    path=await db["learning_paths"].find_one({"slug": slug})
    if not path: raise HTTPException(404, "Not found")
    day=body.get("day")
    if not isinstance(day,int) or not (1 <= day <= int(path.get("duration",60))):
        raise HTTPException(400, "Invalid day")
    # Upsert progress doc (anonymous, by path)
    # Use a simple collection for demo; real would be per-user
    await db["learning_progress"].update_one(
        {"path_id": path["_id"], "day_number": day},
        {"$set": {"status": "completed", "updated_at": __import__("app.database", fromlist=["utcnow"]).utcnow(), "exercise_done": bool(body.get("exercise_done")), "homework_done": bool(body.get("homework_done"))}},
        upsert=True
    )
    published=await db["learning_blocks"].count_documents({"path_id": path["_id"], "status": "published"})
    completed=await db["learning_progress"].count_documents({"path_id": path["_id"]})
    progress=int((completed/published*100) if published else 0)
    return {"ok": True, "progress": progress, "completed": completed}
