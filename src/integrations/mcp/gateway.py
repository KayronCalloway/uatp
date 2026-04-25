"""
UATP MCP Gateway
================

Certifying proxy for MCP tool calls.

Sits between an MCP client and a single upstream MCP server.
Every tool call is:
1. Evaluated by policy
2. Logged as a DECISION_POINT capsule
3. Either blocked (REFUSAL capsule) or executed (TOOL_CALL capsule)
4. Returned with proof reference

Usage:
    python -m src.integrations.mcp.gateway \
        --upstream-cmd "python -m src.integrations.mcp.demo_server"

Architecture:
- UATPMCPGateway: main server, re-exports upstream tools
- UpstreamStdioClient: manages subprocess MCP server
- CapsuleBuilder: converts calls to signed capsules
- PolicyEngine: thin allow/deny evaluation
- CapsuleStore: append-only local storage
"""

from __future__ import annotations

import argparse
import asyncio
import json
import logging
import sys
import uuid
from datetime import datetime, timezone
from typing import Any

from mcp.server import Server
from mcp.types import TextContent, Tool

from src.integrations.mcp.capsule_builder import CapsuleBuilder
from src.integrations.mcp.policy_engine import PolicyEngine
from src.integrations.mcp.proof_attachment import ProofAttachment
from src.integrations.mcp.store import CapsuleStore
from src.integrations.mcp.upstream_stdio_client import UpstreamStdioClient
from src.security.uatp_crypto_v7 import UATPCryptoV7

logger = logging.getLogger(__name__)


class UATPMCPGateway:
    """
    MCP server that wraps upstream servers and certifies tool calls.
    """

    def __init__(
        self,
        upstream_command: list[str],
        store_path: str = "uatp_mcp_store.db",
        key_dir: str = ".uatp_keys",
    ):
        self.upstream = UpstreamStdioClient(upstream_command)
        self.store = CapsuleStore(store_path)
        self.crypto = UATPCryptoV7(key_dir=key_dir, signer_id="uatp-mcp-gateway")
        self.builder = CapsuleBuilder(self.store, self.crypto)
        self.policy = PolicyEngine()
        self.server = Server("uatp-certifier")
        self._session_id: str | None = None

    async def initialize(self) -> None:
        """Connect to upstream and register handlers."""
        await self.upstream.connect()
        upstream_tools = await self.upstream.list_tools()

        # Generate a session id for this gateway lifetime
        self._session_id = f"sess_{uuid.uuid4().hex[:16]}"

        @self.server.list_tools()
        async def list_tools() -> list[Tool]:
            return upstream_tools

        @self.server.call_tool()
        async def call_tool(name: str, arguments: dict[str, Any]) -> list[TextContent]:
            return await self._handle_tool_call(name, arguments)

        logger.info(f"UATP MCP Gateway initialized. Session: {self._session_id}")

    async def _handle_tool_call(
        self, name: str, arguments: dict[str, Any]
    ) -> list[TextContent]:
        """
        Intercept, certify, and forward a tool call.
        """
        session_id = self._session_id or "unknown_session"

        # 1. Evaluate policy
        policy_result = self.policy.evaluate(name, arguments)

        # 2. Emit DECISION_POINT
        decision_id = self.builder.emit_decision_point(
            session_id=session_id,
            selected_action=name,
            candidate_actions=[name],
            trigger_message_hash=None,
            policy_checks=policy_result,
        )

        # 3. Block if policy says no
        if not policy_result.allowed:
            refusal_id = self.builder.emit_refusal(
                session_id=session_id,
                parent_decision_id=decision_id,
                attempted_tool=name,
                policy_result=policy_result,
            )
            refusal_text = ProofAttachment.refusal_text_block(
                refusal_id, policy_result.reason
            )
            return [
                TextContent(
                    type="text",
                    text=f"Policy blocked: {policy_result.reason}{refusal_text}",
                )
            ]

        # 4. Forward to upstream
        started = datetime.now(timezone.utc)
        try:
            result = await self.upstream.call_tool(name, arguments)
            status = "success"
            error_message = None
        except Exception as e:
            result = {"error": str(e)}
            status = "error"
            error_message = str(e)
        ended = datetime.now(timezone.utc)

        # 5. Emit TOOL_CALL capsule
        tool_capsule_id = self.builder.emit_tool_call(
            session_id=session_id,
            parent_decision_id=decision_id,
            tool_name=name,
            upstream_server_id="upstream_default",
            arguments=arguments,
            result=result,
            started_at=started,
            ended_at=ended,
            status=status,
            error_message=error_message,
        )

        # 6. Append proof as a separate content block
        proof_text = ProofAttachment.text_proof_block(tool_capsule_id)

        # Preserve original upstream content blocks
        if hasattr(result, "content") and result.content:
            # mcp.types.CallToolResult — extract content blocks
            content_blocks = list(result.content)
        elif hasattr(result, "model_dump"):
            # Fallback: serialized tool result
            dumped = result.model_dump()
            content_blocks = [TextContent(type="text", text=json.dumps(dumped))]
        elif isinstance(result, dict):
            # Legacy: plain dict from old upstream client
            text_val = result.get("text", str(result))
            content_blocks = [TextContent(type="text", text=text_val)]
        else:
            content_blocks = [TextContent(type="text", text=str(result))]

        # Append proof as separate TextContent block
        content_blocks.append(TextContent(type="text", text=proof_text))

        return content_blocks

    async def run(self) -> None:
        """Run the gateway server (stdio transport)."""
        from mcp.server.stdio import stdio_server

        async with stdio_server() as (read_stream, write_stream):
            await self.server.run(
                read_stream,
                write_stream,
                self.server.create_initialization_options(),
            )

    async def shutdown(self) -> None:
        """Clean up."""
        await self.upstream.close()
        logger.info("UATP MCP Gateway shut down")


# ------------------------------------------------------------------
# CLI
# ------------------------------------------------------------------


def main() -> None:
    parser = argparse.ArgumentParser(description="UATP MCP Certifying Gateway")
    parser.add_argument(
        "--upstream-cmd",
        required=True,
        nargs="+",
        help="Command to run the upstream MCP server (e.g., python demo_server.py)",
    )
    parser.add_argument(
        "--store",
        default="uatp_mcp_store.db",
        help="Path to capsule store database",
    )
    parser.add_argument(
        "--key-dir",
        default=".uatp_keys",
        help="Directory for UATP signing keys",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable debug logging",
    )
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    )

    gateway = UATPMCPGateway(
        upstream_command=args.upstream_cmd,
        store_path=args.store,
        key_dir=args.key_dir,
    )

    async def _run() -> None:
        await gateway.initialize()
        try:
            await gateway.run()
        finally:
            await gateway.shutdown()

    asyncio.run(_run())


if __name__ == "__main__":
    main()
