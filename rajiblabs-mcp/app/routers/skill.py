"""MCP skill tools router."""

from fastapi import APIRouter, Depends, Query

from app.auth import verify_api_key

router = APIRouter(prefix="/api/mcp/skill", tags=["mcp-skill"])


@router.get("/list")
async def get_skills(
    category: str | None = Query(None),
    api_key: str = Depends(verify_api_key),
):
    from app.tools.skill import get_skills
    return await get_skills(category=category)


@router.post("/extract")
async def extract_skills(api_key: str = Depends(verify_api_key)):
    from app.tools.skill import extract_skills
    return await extract_skills()


@router.get("/validate/{skill_name}")
async def validate_skill(skill_name: str, api_key: str = Depends(verify_api_key)):
    from app.tools.skill import validate_skill
    return await validate_skill(skill_name=skill_name)
