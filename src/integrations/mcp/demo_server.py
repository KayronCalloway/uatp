"""
UATP MCP Demo Server
====================

A simple upstream MCP server for testing the certifying gateway.

Exposes three tools:
- read_file: read a file (safe)
- write_file: write a file (policy-scoped)
- run_command: run a shell command (policy-scoped)

This is NOT a production server. It exists to demonstrate:
1. Tool calls being certified
2. Policy blocking a bad path
3. Graph reconstruction from capsules

Usage:
    python -m src.integrations.mcp.demo_server
"""

from __future__ import annotations

import asyncio
import json
import logging
import sys
from pathlib import Path

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import TextContent, Tool

logger = logging.getLogger(__name__)


class DemoMCPServer:
    """
    Simple MCP server with file and shell tools for demo purposes.
    """

    def __init__(self) -> None:
        self.server = Server("uatp-demo-upstream")

        @self.server.list_tools()
        async def list_tools() -> list[Tool]:
            return [
                Tool(
                    name="read_file",
                    description="Read the contents of a file",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "path": {
                                "type": "string",
                                "description": "Absolute or relative path to file",
                            }
                        },
                        "required": ["path"],
                    },
                ),
                Tool(
                    name="write_file",
                    description="Write content to a file",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "path": {
                                "type": "string",
                                "description": "Path to write",
                            },
                            "content": {
                                "type": "string",
                                "description": "Content to write",
                            },
                        },
                        "required": ["path", "content"],
                    },
                ),
                Tool(
                    name="run_command",
                    description="Run a shell command",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "command": {
                                "type": "string",
                                "description": "Shell command to execute",
                            }
                        },
                        "required": ["command"],
                    },
                ),
            ]

        @self.server.call_tool()
        async def call_tool(name: str, arguments: dict) -> list[TextContent]:
            if name == "read_file":
                return await self._read_file(arguments)
            elif name == "write_file":
                return await self._write_file(arguments)
            elif name == "run_command":
                return await self._run_command(arguments)
            else:
                return [TextContent(type="text", text=f"Unknown tool: {name}")]

    async def _read_file(self, arguments: dict) -> list[TextContent]:
        path = Path(arguments["path"]).expanduser()
        try:
            content = path.read_text()
            return [TextContent(type="text", text=f"Content of {path}:\n{content}")]
        except Exception as e:
            return [TextContent(type="text", text=f"Error reading {path}: {e}")]

    async def _write_file(self, arguments: dict) -> list[TextContent]:
        path = Path(arguments["path"]).expanduser()
        content = arguments["content"]
        try:
            path.write_text(content)
            return [
                TextContent(type="text", text=f"Wrote {len(content)} bytes to {path}")
            ]
        except Exception as e:
            return [TextContent(type="text", text=f"Error writing {path}: {e}")]

    async def _run_command(self, arguments: dict) -> list[TextContent]:
        import shlex
        import subprocess

        command = arguments["command"].strip()

        # ------------------------------------------------------------------
        # Sandbox: only a tiny allowlist of safe, read-only commands
        # ------------------------------------------------------------------
        ALLOWED_COMMANDS = {"pwd", "ls", "cat", "echo", "whoami", "uname"}
        BLOCKED_CHARS = {";", "|", "&", "$(", "`", "$", "<", ">", "\n"}

        if any(ch in command for ch in BLOCKED_CHARS):
            return [
                TextContent(
                    type="text",
                    text="[SANDBOX] Command blocked: shell metacharacters not allowed",
                )
            ]

        try:
            parts = shlex.split(command)
        except ValueError:
            return [
                TextContent(
                    type="text",
                    text="[SANDBOX] Command blocked: invalid shell syntax",
                )
            ]

        if not parts:
            return [TextContent(type="text", text="[SANDBOX] Empty command")]

        base_cmd = parts[0]
        if base_cmd not in ALLOWED_COMMANDS:
            return [
                TextContent(
                    type="text",
                    text=f"[SANDBOX] Command '{base_cmd}' not in allowlist. "
                    f"Allowed: {', '.join(sorted(ALLOWED_COMMANDS))}",
                )
            ]

        try:
            result = subprocess.run(
                parts,
                shell=False,
                capture_output=True,
                text=True,
                timeout=10,
            )
            output = result.stdout or "(no output)"
            if result.stderr:
                output += f"\nstderr: {result.stderr}"
            return [
                TextContent(
                    type="text",
                    text=f"Command: {command}\nExit: {result.returncode}\n{output}",
                )
            ]
        except Exception as e:
            return [TextContent(type="text", text=f"Error running command: {e}")]

    async def run(self) -> None:
        async with stdio_server() as (read_stream, write_stream):
            await self.server.run(
                read_stream,
                write_stream,
                self.server.create_initialization_options(),
            )


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
        stream=sys.stderr,
    )
    server = DemoMCPServer()
    asyncio.run(server.run())


if __name__ == "__main__":
    main()
