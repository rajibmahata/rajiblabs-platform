"""MCP GitHub tools router."""

from fastapi import APIRouter, Depends, Query

from app.auth import verify_api_key, verify_admin_key

router = APIRouter(prefix="/api/mcp/github", tags=["mcp-github"])


@router.get("/repositories")
async def get_repositories(
    owner: str | None = Query(None),
    api_key: str = Depends(verify_api_key),
):
    from app.tools.github import get_repositories
    return await get_repositories(owner=owner)


@router.get("/analyze/{repo_name}")
async def analyze_repository(repo_name: str, api_key: str = Depends(verify_api_key)):
    from app.tools.github import analyze_repository
    return await analyze_repository(repo_name=repo_name)


@router.get("/evidence/{repo_name}")
async def extract_evidence(repo_name: str, api_key: str = Depends(verify_api_key)):
    from app.tools.github import extract_project_evidence
    return await extract_project_evidence(repo_name=repo_name)


@router.get("/extract-skills")
async def extract_skills_from_github(api_key: str = Depends(verify_api_key)):
    from app.tools.github import extract_skills_from_github
    return await extract_skills_from_github()


@router.post("/sync/{repo_name}")
async def sync_repository(repo_name: str, api_key: str = Depends(verify_admin_key)):
    from app.tools.github import sync_repository
    return await sync_repository(repo_name=repo_name)
