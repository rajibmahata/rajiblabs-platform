"""MCP client for calling RajibLabs MCP tools via HTTP."""

from __future__ import annotations

import logging
import time
from typing import Any

import httpx

from app.config import settings

logger = logging.getLogger(__name__)


class MCPClient:
    def __init__(self, base_url: str | None = None):
        self.base_url = (base_url or settings.MCP_URL).rstrip("/")
        self._client: httpx.AsyncClient | None = None

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                base_url=self.base_url,
                timeout=httpx.Timeout(60.0),
            )
        return self._client

    async def close(self):
        if self._client and not self._client.is_closed:
            await self._client.aclose()

    async def health(self) -> dict:
        client = await self._get_client()
        try:
            resp = await client.get("/health")
            return resp.json()
        except Exception as e:
            return {"status": "error", "error": str(e)}

    async def list_tools(self) -> list[dict]:
        client = await self._get_client()
        try:
            resp = await client.get("/tools")
            data = resp.json()
            return data.get("tools", [])
        except Exception as e:
            logger.warning("list_tools failed: %s", e)
            return []

    async def call_tool(
        self, tool_name: str, arguments: dict | None = None, agent_id: str = "orchestrator"
    ) -> dict:
        client = await self._get_client()
        start = time.monotonic()
        try:
            resp = await client.post(
                f"/tool/{tool_name}",
                json={"arguments": arguments or {}, "agent_id": agent_id},
            )
            duration = (time.monotonic() - start) * 1000
            result = resp.json()
            result["_mcp_duration_ms"] = round(duration, 2)
            return result
        except Exception as e:
            duration = (time.monotonic() - start) * 1000
            logger.warning("MCP tool %s failed (%.0fms): %s", tool_name, duration, e)
            return {
                "success": False,
                "error": {"code": "MCP_ERROR", "message": str(e)},
                "_mcp_duration_ms": round(duration, 2),
            }

    async def batch_call(
        self, calls: list[dict[str, Any]], agent_id: str = "orchestrator"
    ) -> list[dict]:
        results = []
        for call in calls:
            tool = call.get("tool", "")
            args = call.get("arguments", {})
            result = await self.call_tool(tool, args, agent_id)
            results.append({"tool": tool, "result": result})
        return results


mcp_client = MCPClient()
