"""MCP knowledge tools router."""

from fastapi import APIRouter, Depends, Query

from app.auth import verify_api_key, verify_admin_key

router = APIRouter(prefix="/api/mcp/knowledge", tags=["mcp-knowledge"])


@router.get("/search")
async def search_knowledge(
    query: str = Query(...),
    top_k: int = Query(6, ge=1, le=20),
    api_key: str = Depends(verify_api_key),
):
    from app.tools.knowledge import search_knowledge
    return await search_knowledge(query=query, top_k=top_k)


@router.get("/list")
async def get_knowledge(
    source_type: str | None = Query(None),
    limit: int = Query(50, ge=1, le=200),
    api_key: str = Depends(verify_api_key),
):
    from app.tools.knowledge import get_knowledge
    return await get_knowledge(source_type=source_type, limit=limit)


@router.get("/validate")
async def validate_knowledge(api_key: str = Depends(verify_api_key)):
    from app.tools.knowledge import validate_knowledge
    return await validate_knowledge()


@router.get("/stale")
async def detect_stale(
    days: int = Query(90, ge=1),
    api_key: str = Depends(verify_api_key),
):
    from app.tools.knowledge import detect_stale_knowledge
    return await detect_stale_knowledge(days_threshold=days)


@router.post("/index/{entry_id}")
async def index_knowledge(entry_id: str, api_key: str = Depends(verify_admin_key)):
    from app.tools.knowledge import index_knowledge
    return await index_knowledge(entry_id=entry_id)
