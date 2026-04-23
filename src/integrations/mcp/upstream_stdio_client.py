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

import asyncio
import json
import logging
import subprocess
import sys
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class UpstreamStdioClient:
    """
    Client for an upstream MCP server over stdio.
    """

    def __init__(self, command: list[str]):
        self.command = command
        self.process: subprocess.Popen | None = None
        self._request_id = 0
        self._tools: list[dict[str, Any]] = []

    async def connect(self) -> None:
        """Start the upstream subprocess."""
        logger.info(f"Starting upstream MCP server: {' '.join(self.command)}")
        self.process = subprocess.Popen(
            self.command,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
        )
        # Give it a moment to initialize
        await asyncio.sleep(0.5)
        logger.info("Upstream MCP server started")

    async def list_tools(self) -> list[dict[str, Any]]:
        """List available tools from the upstream server."""
        if self.process is None or self.process.poll() is not None:
            raise RuntimeError("Upstream process not running")

        # For MVP, we use a simple JSON-RPC request
        response = await self._send_request("tools/list", {})
        tools = response.get("tools", [])
        self._tools = tools
        logger.debug(f"Discovered {len(tools)} tools from upstream")
        return tools

    async def call_tool(self, name: str, arguments: dict[str, Any]) -> Any:
        """Call a tool on the upstream server."""
        if self.process is None or self.process.poll() is not None:
            raise RuntimeError("Upstream process not running")

        response = await self._send_request(
            "tools/call",
            {"name": name, "arguments": arguments},
        )
        return response.get("result")

    async def _send_request(
        self, method: str, params: dict[str, Any]
    ) -> dict[str, Any]:
        """Send a JSON-RPC request and read the response."""
        self._request_id += 1
        request = {
            "jsonrpc": "2.0",
            "id": self._request_id,
            "method": method,
            "params": params,
        }

        if self.process is None or self.process.stdin is None:
            raise RuntimeError("Upstream process not initialized")

        # Write request
        line = json.dumps(request) + "\n"
        self.process.stdin.write(line)
        self.process.stdin.flush()

        # Read response
        if self.process.stdout is None:
            raise RuntimeError("Upstream stdout not available")

        response_line = self.process.stdout.readline()
        if not response_line:
            raise RuntimeError("Upstream closed connection")

        response = json.loads(response_line)

        if "error" in response:
            raise RuntimeError(f"Upstream error: {response['error']}")

        return response.get("result", {})

    async def close(self) -> None:
        """Terminate the upstream process."""
        if self.process is not None and self.process.poll() is None:
            self.process.terminate()
            try:
                self.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.process.kill()
            logger.info("Upstream MCP server terminated")
