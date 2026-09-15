"""MCP SEO tools router."""

from fastapi import APIRouter, Depends, Query

from app.auth import verify_api_key

router = APIRouter(prefix="/api/mcp/seo", tags=["mcp-seo"])


@router.get("/analyze")
async def analyze_seo(
    url: str | None = Query(None),
    api_key: str = Depends(verify_api_key),
):
    from app.tools.seo import analyze_seo
    return await analyze_seo(url=url)


@router.get("/metadata/generate")
async def generate_metadata(
    page_type: str = Query(...),
    page_id: str = Query(...),
    api_key: str = Depends(verify_api_key),
):
    from app.tools.seo import generate_metadata
    return await generate_metadata(page_type=page_type, page_id=page_id)


@router.get("/metadata/validate")
async def validate_metadata(
    page_type: str = Query(...),
    page_id: str = Query(...),
    api_key: str = Depends(verify_api_key),
):
    from app.tools.seo import validate_metadata
    return await validate_metadata(page_type=page_type, page_id=page_id)


@router.get("/missing")
async def find_missing_metadata(api_key: str = Depends(verify_api_key)):
    from app.tools.seo import find_missing_metadata
    return await find_missing_metadata()


@router.get("/internal-links")
async def find_internal_links(api_key: str = Depends(verify_api_key)):
    from app.tools.seo import find_internal_link_opportunities
    return await find_internal_link_opportunities()


@router.get("/content-quality")
async def analyze_content_quality(api_key: str = Depends(verify_api_key)):
    from app.tools.seo import analyze_content_quality
    return await analyze_content_quality()
