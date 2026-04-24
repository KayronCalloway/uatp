"""
UATP MCP Upstream Stdio Client
==============================

Manages a subprocess MCP server and exposes its tools.

This is the simplest transport for MVP. The client:
1. Spawns an upstream MCP server as a subprocess
2. Communicates over stdin/stdout using JSON-RPC
3. Lists available tools
4. Invokes tools and returns results

Production would add:
- HTTP/SSE transport
- Connection pooling
- Health checks and restart
- Multi-upstream routing
"""

from __future__ import annotations

import logging
from typing import Any

from mcp import ClientSession
from mcp.client.stdio import StdioServerParameters, stdio_client

logger = logging.getLogger(__name__)


class UpstreamStdioClient:
    """
    Client for an upstream MCP server over stdio.
    """

    def __init__(self, command: list[str]):
        self.command = command
        self._stdio_ctx: Any | None = None
        self._session_ctx: Any | None = None
        self.session: ClientSession | None = None
        self._tools: list[dict[str, Any]] = []

    async def connect(self) -> None:
        """Start the upstream subprocess and perform MCP handshake."""
        logger.info(f"Starting upstream MCP server: {' '.join(self.command)}")
        params = StdioServerParameters(
            command=self.command[0],
            args=self.command[1:],
        )
        self._stdio_ctx = stdio_client(params)
        read_stream, write_stream = await self._stdio_ctx.__aenter__()
        self._session_ctx = ClientSession(read_stream, write_stream)
        self.session = await self._session_ctx.__aenter__()
        await self.session.initialize()
        logger.info("Upstream MCP server initialized")

    async def list_tools(self) -> list[dict[str, Any]]:
        """List available tools from the upstream server."""
        if self.session is None:
            raise RuntimeError("Upstream session not initialized")

        result = await self.session.list_tools()
        tools: list[dict[str, Any]] = [tool.model_dump() for tool in result.tools]
        self._tools = tools
        logger.debug(f"Discovered {len(tools)} tools from upstream")
        return tools

    async def call_tool(self, name: str, arguments: dict[str, Any]) -> Any:
        """Call a tool on the upstream server."""
        if self.session is None:
            raise RuntimeError("Upstream session not initialized")

        result = await self.session.call_tool(name, arguments)
        return result

    async def close(self) -> None:
        """Terminate the upstream process."""
        if self._session_ctx is not None:
            await self._session_ctx.__aexit__(None, None, None)
            self._session_ctx = None
            self.session = None
        if self._stdio_ctx is not None:
            await self._stdio_ctx.__aexit__(None, None, None)
            self._stdio_ctx = None
            logger.info("Upstream MCP server terminated")
