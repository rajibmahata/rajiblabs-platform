"""MCP authentication and authorization."""

from fastapi import Depends, HTTPException, Security
from fastapi.security import APIKeyHeader

from app.config import settings

_api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)
_admin_api_key_header = APIKeyHeader(name="X-Admin-Key", auto_error=False)


async def verify_api_key(api_key: str = Security(_api_key_header)) -> str:
    """Verify the API key for MCP tool access."""
    if not settings.mcp_api_key:
        # No key configured — allow in development
        if settings.app_env == "development":
            return "dev-mode"
        raise HTTPException(status_code=401, detail="MCP API key required")
    if api_key != settings.mcp_api_key:
        raise HTTPException(status_code=401, detail="Invalid MCP API key")
    return api_key


async def verify_admin_key(admin_key: str = Security(_admin_api_key_header)) -> str:
    """Verify admin API key for sensitive MCP operations."""
    if not settings.admin_api_key:
        # No key configured — allow in development
        if settings.app_env == "development":
            return "dev-admin"
        raise HTTPException(status_code=401, detail="Admin API key required")
    if admin_key != settings.admin_api_key:
        raise HTTPException(status_code=401, detail="Invalid admin API key")
    return admin_key


def require_auth(func):
    """Decorator to require authentication on a tool."""
    func._requires_auth = True
    return func


def require_admin(func):
    """Decorator to require admin authorization on a tool."""
    func._requires_admin = True
    return func
