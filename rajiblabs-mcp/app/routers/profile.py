"""MCP profile tools router."""

from fastapi import APIRouter, Depends

from app.auth import verify_api_key

router = APIRouter(prefix="/api/mcp/profile", tags=["mcp-profile"])


@router.get("/get")
async def get_profile(api_key: str = Depends(verify_api_key)):
    from app.tools.profile import get_profile
    return await get_profile()


@router.get("/analyze")
async def analyze_profile(api_key: str = Depends(verify_api_key)):
    from app.tools.profile import analyze_profile
    return await analyze_profile()


@router.get("/validate")
async def validate_profile(api_key: str = Depends(verify_api_key)):
    from app.tools.profile import validate_profile
    return await validate_profile()


@router.get("/optimize")
async def optimize_profile(api_key: str = Depends(verify_api_key)):
    from app.tools.profile import optimize_profile
    return await optimize_profile()


@router.get("/positioning")
async def get_positioning(api_key: str = Depends(verify_api_key)):
    from app.tools.profile import get_professional_positioning
    return await get_professional_positioning()
