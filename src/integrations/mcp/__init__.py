"""
UATP MCP Integration
====================

Certifying proxy for Model Context Protocol (MCP) tool calls.

Turns agent tool execution into signed, queryable memory at the action
boundary, while preserving linkage to decision context and policy state.

Modules:
- gateway: Main MCP certifying server
- upstream_stdio_client: Subprocess MCP server management
- capsule_builder: UATP capsule construction with evidence classes
- policy_engine: Thin, scoped policy evaluation
- store: Append-only local storage
- proof_attachment: Proof formatting for MCP responses
- demo_server: Simple upstream server for testing

Usage:
    # Terminal 1: start the demo upstream
    python -m src.integrations.mcp.demo_server

    # Terminal 2: start the certifying gateway
    python -m src.integrations.mcp.gateway \
        --upstream-cmd python -m src.integrations.mcp.demo_server

    # Then configure your MCP client to use the gateway.
"""

from src.integrations.mcp.gateway import UATPMCPGateway

__all__ = ["UATPMCPGateway"]
