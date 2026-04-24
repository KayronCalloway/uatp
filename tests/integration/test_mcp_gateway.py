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

from src.integrations.mcp.gateway import UATPMCPGateway
from src.integrations.mcp.store import CapsuleStore
from src.integrations.mcp.upstream_stdio_client import UpstreamStdioClient


@pytest.fixture
def upstream_command():
    return [sys.executable, "-m", "src.integrations.mcp.demo_server"]


@pytest.fixture
def temp_store_path(tmp_path):
    return str(tmp_path / "mcp_store.db")


@pytest.fixture
def temp_key_dir(tmp_path):
    d = tmp_path / ".uatp_keys"
    d.mkdir()
    return str(d)


# ---------------------------------------------------------------------------
# Upstream client - protocol compliance
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_connect_performs_mcp_initialize_handshake(tmp_path):
    """
    connect() should create an mcp.ClientSession and call initialize()
    so that capability exchange happens before any tool calls.
    """
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


# ---------------------------------------------------------------------------
# Gateway - content type preservation
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_text_content_preserved_as_separate_block(
    upstream_command, temp_store_path, temp_key_dir
):
    """Original upstream TextContent must pass through as its own block."""
    gateway = UATPMCPGateway(
        upstream_command=upstream_command,
        store_path=temp_store_path,
        key_dir=temp_key_dir,
    )
    await gateway.initialize()

    result = await gateway._handle_tool_call("read_file", {"path": "/dev/null"})

    # result must be a list of content blocks, not a single flattened string
    assert isinstance(result, list)
    assert len(result) >= 2, (
        f"Expected at least 2 blocks (original content + proof), got {len(result)}"
    )

    # At least one block should be original content (not the proof)
    from mcp.types import TextContent

    non_proof_blocks = [
        b
        for b in result
        if isinstance(b, TextContent) and "[UATP Certified]" not in b.text
    ]
    assert len(non_proof_blocks) >= 1, "Original content block missing"

    await gateway.shutdown()


@pytest.mark.asyncio
async def test_result_hash_is_stable(upstream_command, temp_store_path, temp_key_dir):
    """TOOL_CALL capsule must contain a stable sha256 hash of the result."""
    gateway = UATPMCPGateway(
        upstream_command=upstream_command,
        store_path=temp_store_path,
        key_dir=temp_key_dir,
    )
    await gateway.initialize()

    await gateway._handle_tool_call("read_file", {"path": "/dev/null"})

    store = CapsuleStore(temp_store_path)
    caps = store.get_session_graph(gateway._session_id)
    tool_caps = [c for c in caps if c["capsule_type"] == "TOOL_CALL"]
    assert len(tool_caps) >= 1

    payload = tool_caps[0]["payload"]
    content_hash = payload["output"]["content_hash"]["value"]
    assert content_hash.startswith("sha256:")
    assert len(content_hash) == 71  # "sha256:" + 64 hex chars

    await gateway.shutdown()
