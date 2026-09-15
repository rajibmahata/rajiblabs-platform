"""RajibLabs Content Intelligence MCP Server — main entry point.

Uses the official MCP Python SDK (v2.x) with MCPServer.
Exposes tools via SSE transport for agent integration.
"""

from __future__ import annotations

import asyncio
import logging
import sys
import time
from contextlib import asynccontextmanager
from typing import Any

from app.config import settings
from app.database import connect_db, disconnect_db
from app.redis import connect_redis, disconnect_redis
from app.tools import TOOL_REGISTRY

logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("rajiblabs-mcp")


@asynccontextmanager
async def lifespan(server: Any):
    logger.info("Starting RajibLabs Content Intelligence MCP v2.0.0")
    await connect_db()
    await connect_redis()
    logger.info("MCP server ready — %d tools registered", len(TOOL_REGISTRY))
    yield
    await disconnect_redis()
    await disconnect_db()
    logger.info("MCP server stopped")


def _build_mcp_server():
    from mcp.server.mcpserver import MCPServer

    server = MCPServer(
        name="rajiblabs-mcp",
        version="2.0.0",
        lifespan=lifespan,
    )

    for tool_name, tool_info in TOOL_REGISTRY.items():
        fn = tool_info["function"]
        server.add_tool(
            fn,
            name=tool_name,
            title=tool_name.replace("_", " ").title(),
            description=tool_info["description"],
        )

    return server


mcp_server = _build_mcp_server()


async def main():
    if settings.MCP_TRANSPORT == "sse":
        await mcp_server.run_sse_async(
            host=settings.MCP_HOST,
            port=settings.MCP_PORT,
            sse_path="/sse",
            message_path="/messages/",
        )
    elif settings.MCP_TRANSPORT == "streamable-http":
        await mcp_server.run_streamable_http_async(
            host=settings.MCP_HOST,
            port=settings.MCP_PORT,
            streamable_http_path="/mcp",
        )
    else:
        await mcp_server.run_stdio_async()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Interrupted")
        sys.exit(0)
