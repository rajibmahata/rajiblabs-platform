"""Admin domains + sources + health (profile intelligence)."""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from typing import Optional
from app.auth.dependencies import require_admin
from app.database import get_db, utcnow
from app.models import oid_str

router = APIRouter(prefix="/api/admin/domains")

class DomainPatch(BaseModel):
    featured: Optional[bool] = None
    display_order: Optional[int] = None
    status: Optional[str] = None
    seo: Optional[dict] = None
    short_description: Optional[str] = None
    detailed_description: Optional[str] = None

class SourceIn(BaseModel):
    type: str = Field(..., max_length=40)
    name: Optional[str] = None
    url: Optional[str] = None
    enabled: bool = True
    public_source: bool = True
    linkedin_text: Optional[str] = None

@router.get("")
async def admin_list_domains(status: Optional[str]=None, q: Optional[str]=None, email: str=Depends(require_admin)):
    db=get_db()
    query={}
    if status: query["status"]=status
    if q:
        import re
        rx={"$regex": re.escape(q[:100]), "$options":"i"}
        query["$or"]=[{"name":rx},{"slug":rx},{"short_description":rx}]
    cur=db["professional_domains"].find(query).sort([("confidence_score",-1),("updated_at",-1)])
    return [oid_str(d) async for d in cur]

@router.get("/health/overview")
async def health_overview(email: str=Depends(require_admin)):
    db=get_db()
    total=await db["professional_domains"].count_documents({})
    active=await db["professional_domains"].count_documents({"status":"active"})
    weak=await db["professional_domains"].count_documents({"confidence_score":{"$lt":50}})
    from datetime import timedelta
    cutoff=utcnow()-timedelta(days=30)
    stale=await db["professional_domains"].count_documents({"last_verified_at":{"$lt":cutoff}})
    sources=await db["professional_sources"].count_documents({})
    return {"total":total,"active":active,"weak":weak,"stale":stale,"sources":sources}

@router.get("/sources/list")
async def list_sources(email: str=Depends(require_admin)):
    db=get_db()
    cur=db["professional_sources"].find({})
    return [oid_str(d) async for d in cur]

@router.post("/sources")
async def upsert_source(body: SourceIn, email: str=Depends(require_admin)):
    db=get_db()
    if body.type=="linkedin" and body.url:
        if "linkedin.com/feed" in body.url:
            raise HTTPException(400,"Use public profile URL https://www.linkedin.com/in/... not /feed")
        if body.linkedin_text and len(body.linkedin_text)>6000:
            body.linkedin_text=body.linkedin_text[:6000]
    doc={"type":body.type,"name":body.name or body.type,"url":body.url,"enabled":body.enabled,"public_source":body.public_source,
         "status":"active","updated_at":utcnow()}
    if body.linkedin_text is not None: doc["linkedin_text"]=body.linkedin_text[:6000]
    res=await db["professional_sources"].update_one({"type":body.type},{"$set":doc},upsert=True)
    from app.services.notify import audit
    try: await audit(email,"SOURCE_UPSERT",body.type,{"type":body.type})
    except: pass
    return oid_str(await db["professional_sources"].find_one({"type":body.type}))

@router.post("/sources/validate")
async def validate_sources(email: str=Depends(require_admin)):
    from app.services.domain_intelligence import validate_portfolio_urls
    res=await validate_portfolio_urls(get_db())
    return {"checks": res}

@router.post("/run")
async def admin_run_domains(email: str=Depends(require_admin)):
    from app.services.domain_intelligence import run_domain_discovery
    res=await run_domain_discovery(triggered_by=f"admin:{email}")
    return res

@router.get("/{slug}")
async def admin_get_domain(slug: str, email: str=Depends(require_admin)):
    db=get_db()
    d=await db["professional_domains"].find_one({"slug":slug})
    if not d: raise HTTPException(404,"Not found")
    return oid_str(d)

@router.patch("/{slug}")
async def admin_patch_domain(slug: str, body: DomainPatch, email: str=Depends(require_admin)):
    db=get_db()
    patch={k:v for k,v in body.model_dump(exclude_unset=True).items() if v is not None}
    if not patch: raise HTTPException(400,"Nothing to update")
    patch["updated_at"]=utcnow()
    res=await db["professional_domains"].update_one({"slug":slug},{"$set": patch})
    if not res.matched_count: raise HTTPException(404,"Not found")
    from app.services.notify import audit
    try: await audit(email,"DOMAIN_UPDATE",slug,{"fields":sorted(patch.keys())})
    except: pass
    return oid_str(await db["professional_domains"].find_one({"slug":slug}))
