"""
Integration tests proving UpstreamStdioClient lacks proper MCP initialize handshake.

These tests are expected to FAIL against the current implementation because
UpstreamStdioClient.connect() spawns a subprocess but does NOT use
mcp.ClientSession or call session.initialize().

Once the client is fixed to perform the proper MCP handshake, these tests
should pass.
"""

import sys

import pytest
from mcp import ClientSession

from src.integrations.mcp.upstream_stdio_client import UpstreamStdioClient


@pytest.mark.asyncio
async def test_connect_performs_mcp_initialize_handshake(tmp_path):
    """
    connect() should create an mcp.ClientSession and call initialize()
    so that capability exchange happens before any tool calls.
    """
    _store_path = tmp_path / "mcp_store.db"
    _keys_dir = tmp_path / "keys"
    _keys_dir.mkdir()

    client = UpstreamStdioClient(
        command=[sys.executable, "-m", "src.integrations.mcp.demo_server"]
    )

    await client.connect()

    try:
        assert hasattr(client, "session"), (
            "UpstreamStdioClient should expose a session attribute after connect()"
        )
        assert isinstance(client.session, ClientSession), (
            "session must be an mcp.ClientSession instance"
        )
        # initialize() sets _server_capabilities from the server's InitializeResult
        assert getattr(client.session, "_server_capabilities", None) is not None, (
            "connect() must call session.initialize() to exchange capabilities"
        )
    finally:
        await client.close()


@pytest.mark.asyncio
async def test_list_tools_works_after_proper_initialization(tmp_path):
    """
    list_tools() should succeed after a properly initialized MCP session.
    Currently it fails because raw JSON-RPC is sent without the handshake.
    """
    _store_path = tmp_path / "mcp_store.db"
    _keys_dir = tmp_path / "keys"
    _keys_dir.mkdir()

    client = UpstreamStdioClient(
        command=[sys.executable, "-m", "src.integrations.mcp.demo_server"]
    )

    await client.connect()

    try:
        tools = await client.list_tools()
        assert isinstance(tools, list)
        tool_names = {t.get("name") for t in tools}
        assert "read_file" in tool_names
        assert "write_file" in tool_names
        assert "run_command" in tool_names
    finally:
        await client.close()
