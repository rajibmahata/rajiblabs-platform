"""MCP project & portfolio tools router."""

from fastapi import APIRouter, Depends, Query

from app.auth import verify_api_key

router = APIRouter(prefix="/api/mcp/project", tags=["mcp-project"])


@router.get("/list")
async def get_projects(
    status: str = Query("published"),
    limit: int = Query(50, ge=1, le=200),
    api_key: str = Depends(verify_api_key),
):
    from app.tools.project import get_projects
    return await get_projects(status=status, limit=limit)


@router.get("/analyze/{project_id}")
async def analyze_project(project_id: str, api_key: str = Depends(verify_api_key)):
    from app.tools.project import analyze_project
    return await analyze_project(project_id=project_id)


@router.get("/improve/{project_id}")
async def improve_project(project_id: str, api_key: str = Depends(verify_api_key)):
    from app.tools.project import improve_project
    return await improve_project(project_id=project_id)


@router.get("/organize")
async def organize_projects(api_key: str = Depends(verify_api_key)):
    from app.tools.project import organize_projects
    return await organize_projects()


@router.get("/rank")
async def rank_projects(api_key: str = Depends(verify_api_key)):
    from app.tools.project import rank_projects
    return await rank_projects()


@router.get("/portfolio")
async def get_portfolio(
    limit: int = Query(10, ge=1, le=50),
    api_key: str = Depends(verify_api_key),
):
    from app.tools.project import get_portfolio
    return await get_portfolio(limit=limit)


@router.get("/portfolio/analyze")
async def analyze_portfolio(api_key: str = Depends(verify_api_key)):
    from app.tools.project import analyze_portfolio
    return await analyze_portfolio()
