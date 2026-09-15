"""MCP content intelligence tools router."""

from fastapi import APIRouter, Depends, Query

from app.auth import verify_api_key, verify_admin_key

router = APIRouter(prefix="/api/mcp/content", tags=["mcp-content"])


@router.get("/health")
async def get_content_health(api_key: str = Depends(verify_api_key)):
    from app.tools.content import get_content_health
    return await get_content_health()


@router.get("/freshness")
async def get_content_freshness(api_key: str = Depends(verify_api_key)):
    from app.tools.content import get_content_freshness
    return await get_content_freshness()


@router.get("/validate/{content_type}/{content_id}")
async def validate_content(
    content_type: str, content_id: str,
    api_key: str = Depends(verify_api_key),
):
    from app.tools.content import validate_content
    return await validate_content(content_type=content_type, content_id=content_id)


@router.post("/version/{content_type}/{content_id}")
async def version_content(
    content_type: str, content_id: str,
    reason: str = Query(""),
    api_key: str = Depends(verify_api_key),
):
    from app.tools.content import version_content
    return await version_content(
        content_type=content_type, content_id=content_id, reason=reason)


@router.post("/rollback/{content_type}/{content_id}")
async def rollback_content(
    content_type: str, content_id: str,
    target_version: int = Query(...),
    api_key: str = Depends(verify_admin_key),
):
    from app.tools.content import rollback_content
    return await rollback_content(
        content_type=content_type, content_id=content_id,
        target_version=target_version)
