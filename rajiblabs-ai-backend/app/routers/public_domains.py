"""Public domains — published professional domains (no auth)."""
from fastapi import APIRouter, HTTPException
from app.database import get_db
from app.models import oid_str

router = APIRouter(prefix="/api")

@router.get("/domains")
async def list_domains():
    db = get_db()
    cur = db["professional_domains"].find({"status": "active"}).sort([("featured", -1), ("confidence_score", -1), ("display_order", 1)])
    out = []
    async for d in cur:
        d = oid_str(d)
        # hide internal fields
        d.pop("evidence_hash", None)
        d.pop("previous_confidence", None)
        d.pop("source_ids", None)
        out.append(d)
    return out

@router.get("/domains/{slug}")
async def get_domain(slug: str):
    db = get_db()
    d = await db["professional_domains"].find_one({"slug": slug, "status": "active"})
    if not d:
        raise HTTPException(404, "Domain not found")
    d = oid_str(d)
    d.pop("evidence_hash", None)
    # Enrich with related live portfolio items (resolve slugs to full docs)
    related = []
    for ps in d.get("portfolio_items", [])[:4]:
        p = await db["portfolio"].find_one({"slug": ps, "status": "published"})
        if p:
            related.append(oid_str(p))
    d["_related_portfolio"] = related
    return d
