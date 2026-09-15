"""MCP health check router."""

from fastapi import APIRouter

from app.database import get_db

router = APIRouter(tags=["health"])


@router.get("/health")
async def health_check():
    """MCP server health check."""
    status = {"status": "healthy", "service": "rajiblabs-mcp"}
    checks = {}

    # MongoDB
    try:
        db = get_db()
        await db.command("ping")
        checks["mongodb"] = "connected"
    except Exception as e:
        checks["mongodb"] = f"error: {str(e)[:100]}"
        status["status"] = "degraded"

    # Qdrant
    try:
        from app.config import settings
        import httpx
        async with httpx.AsyncClient(timeout=5) as client:
            resp = await client.get(f"{settings.qdrant_url}/healthz")
            checks["qdrant"] = "connected" if resp.status_code == 200 else "error"
    except Exception:
        checks["qdrant"] = "unavailable"
        # Qdrant is optional — don't degrade status

    status["checks"] = checks
    return status


@router.get("/tools")
async def list_tools():
    """List all registered MCP tools."""
    from app.tools import mcp_tool
    import app.tools.profile
    import app.tools.project
    import app.tools.skill
    import app.tools.github
    import app.tools.knowledge
    import app.tools.seo
    import app.tools.content

    tools = []
    # Collect all decorated functions
    import inspect
    for module in [app.tools.profile, app.tools.project, app.tools.skill,
                   app.tools.github, app.tools.knowledge, app.tools.seo,
                   app.tools.content]:
        for name, obj in inspect.getmembers(module, inspect.iscoroutinefunction):
            if hasattr(obj, "_mcp_tool_name"):
                tools.append({
                    "name": obj._mcp_tool_name,
                    "description": obj._mcp_description,
                    "category": obj._mcp_category,
                    "permission": obj._mcp_permission,
                    "timeout_seconds": obj._mcp_timeout,
                    "idempotent": obj._mcp_idempotent,
                })

    return {"tools": tools, "count": len(tools)}
