"""
Integration tests for MCP Certifying Gateway.
"""

import os
import sys

import pytest
from mcp import ClientSession

from src.integrations.mcp.gateway import UATPMCPGateway
from src.integrations.mcp.policy_engine import PolicyEngine
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


# ---------------------------------------------------------------------------
# Policy engine - path security
# ---------------------------------------------------------------------------


class TestPolicyPathSecurity:
    """Policy engine must block path traversal, not just pattern match."""

    def test_dotdot_traversal_blocked(self):
        """write_file with ../ must be blocked even if pattern matches."""
        engine = PolicyEngine()

        result = engine.evaluate(
            "write_file",
            {"path": "~/project/../../etc/passwd", "content": "x"},
        )
        assert not result.allowed, (
            f"Expected blocked, got allowed. Reason: {result.reason}"
        )
        assert "path_not_in_allowlist" in (result.checks_failed or [])

    def test_symlink_escape_blocked(self, tmp_path):
        """Symlinks that escape the allowed root must be blocked."""
        allowed = tmp_path / "project"
        allowed.mkdir()

        outside = tmp_path / "outside"
        outside.mkdir()
        symlink = allowed / "escape_link"
        symlink.symlink_to(outside)

        rules = {
            "default_action": "deny",
            "tools": {
                "write_file": {
                    "action": "allow",
                    "constraints": {
                        "path_allowlist": [f"{allowed}/*"],
                        "path_denylist": [],
                    },
                },
            },
        }
        engine = PolicyEngine(rules=rules, version="test")

        result = engine.evaluate(
            "write_file",
            {"path": str(symlink / "secrets.txt"), "content": "leak"},
        )
        assert not result.allowed, (
            f"Symlink escape should be blocked. Got: allowed={result.allowed}"
        )

    def test_absolute_path_outside_allowlist_blocked(self):
        """Absolute paths outside allowed roots must be denied."""
        engine = PolicyEngine()
        result = engine.evaluate(
            "write_file",
            {"path": "/etc/passwd", "content": "x"},
        )
        assert not result.allowed
