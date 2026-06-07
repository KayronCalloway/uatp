"""
Integration tests for MCP Certifying Gateway.
"""

import json
import os
import sys

import pytest
from click.testing import CliRunner
from mcp import ClientSession

from src.agent_receipts.signing import Ed25519ReceiptSigner
from src.agent_receipts.verifier import verify_agent_receipt_bundle
from src.cli.main import cli
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


@pytest.mark.asyncio
async def test_gateway_exports_offline_verifiable_receipt_bundle(
    upstream_command, temp_store_path, temp_key_dir
):
    """A real MCP boundary call should export an offline-verifiable receipt bundle."""
    gateway = UATPMCPGateway(
        upstream_command=upstream_command,
        store_path=temp_store_path,
        key_dir=temp_key_dir,
    )
    await gateway.initialize()

    await gateway._handle_tool_call("read_file", {"path": "/dev/null"})

    bundle = gateway.export_receipt_bundle()
    report = verify_agent_receipt_bundle(bundle)

    assert report.valid is True
    assert report.receipt_count == 2
    assert [
        receipt["event"]["event_type"] for receipt in bundle["signed_receipts"]
    ] == [
        "decision.point",
        "tool_call.completed",
    ]
    assert [draft["capsule_type"] for draft in bundle["capsule_drafts"]] == [
        "decision_point",
        "tool_call",
    ]

    await gateway.shutdown()


@pytest.mark.asyncio
async def test_cli_exports_and_verifies_mcp_receipt_bundle(
    upstream_command, temp_store_path, temp_key_dir, tmp_path, monkeypatch
):
    """The MCP demo path should produce a bundle accepted by verify-receipts."""
    gateway = UATPMCPGateway(
        upstream_command=upstream_command,
        store_path=temp_store_path,
        key_dir=temp_key_dir,
    )
    await gateway.initialize()

    await gateway._handle_tool_call("read_file", {"path": "/dev/null"})
    assert gateway._session_id is not None

    bundle_path = tmp_path / "mcp_receipts.json"
    signer = Ed25519ReceiptSigner.generate(signer_id="uatp-mcp-gateway")
    monkeypatch.setenv("UATP_MCP_RECEIPT_SIGNING_KEY", signer.signing_key_hex)
    runner = CliRunner()
    export_result = runner.invoke(
        cli,
        [
            "export-mcp-receipts",
            temp_store_path,
            "--session-id",
            gateway._session_id,
            "--output",
            str(bundle_path),
            "--signing-key-env",
            "UATP_MCP_RECEIPT_SIGNING_KEY",
        ],
    )
    verify_result = runner.invoke(
        cli,
        [
            "verify-receipts",
            str(bundle_path),
            "--strict",
            "--trusted-signer",
            f"uatp-mcp-gateway={signer.public_key_hex}",
            "--no-color",
        ],
    )

    assert export_result.exit_code == 0, export_result.output
    assert "Exported MCP receipt bundle" in export_result.output
    assert "Signer: uatp-mcp-gateway" in export_result.output
    assert f"Public key: {signer.public_key_hex}" in export_result.output
    assert signer.signing_key_hex not in export_result.output
    assert verify_result.exit_code == 0, verify_result.output
    assert "Agent receipt verification PASSED" in verify_result.output

    wrong_trust_result = runner.invoke(
        cli,
        [
            "verify-receipts",
            str(bundle_path),
            "--strict",
            "--trusted-signer",
            f"uatp-mcp-gateway={'b' * 64}",
            "--no-color",
        ],
    )
    assert wrong_trust_result.exit_code == 1, wrong_trust_result.output
    assert "public key is not trusted" in wrong_trust_result.output

    bundle = json.loads(bundle_path.read_text())
    assert bundle["source"] == {
        "boundary": "mcp_gateway",
        "session_id": gateway._session_id,
    }
    assert "store_path" not in bundle["source"]

    tampered_path = tmp_path / "mcp_receipts_tampered.json"
    tampered_bundle = json.loads(bundle_path.read_text())
    tampered_bundle["signed_receipts"][0]["event"]["payload"]["selected_action"] = (
        "changed_after_export"
    )
    tampered_path.write_text(json.dumps(tampered_bundle))
    tampered_result = runner.invoke(
        cli,
        [
            "verify-receipts",
            str(tampered_path),
            "--strict",
            "--trusted-signer",
            f"uatp-mcp-gateway={signer.public_key_hex}",
            "--no-color",
        ],
    )
    assert tampered_result.exit_code == 1, tampered_result.output
    assert "event_hash does not match signed event payload" in tampered_result.output

    await gateway.shutdown()


@pytest.mark.asyncio
async def test_cli_exports_and_verifies_refused_mcp_receipt_bundle(
    upstream_command, temp_store_path, temp_key_dir, tmp_path, monkeypatch
):
    """Denied MCP calls should export as verifiable decision -> refusal receipts."""
    gateway = UATPMCPGateway(
        upstream_command=upstream_command,
        store_path=temp_store_path,
        key_dir=temp_key_dir,
    )
    await gateway.initialize()

    await gateway._handle_tool_call("delete_database", {"confirm": "yes"})
    assert gateway._session_id is not None

    bundle_path = tmp_path / "mcp_refusal_receipts.json"
    signer = Ed25519ReceiptSigner.generate(signer_id="uatp-mcp-gateway")
    monkeypatch.setenv("UATP_MCP_RECEIPT_SIGNING_KEY", signer.signing_key_hex)
    runner = CliRunner()
    export_result = runner.invoke(
        cli,
        [
            "export-mcp-receipts",
            temp_store_path,
            "--session-id",
            gateway._session_id,
            "--output",
            str(bundle_path),
            "--signing-key-env",
            "UATP_MCP_RECEIPT_SIGNING_KEY",
        ],
    )
    verify_result = runner.invoke(
        cli,
        [
            "verify-receipts",
            str(bundle_path),
            "--strict",
            "--trusted-signer",
            f"uatp-mcp-gateway={signer.public_key_hex}",
            "--no-color",
        ],
    )

    assert export_result.exit_code == 0, export_result.output
    assert "Signer: uatp-mcp-gateway" in export_result.output
    assert f"Public key: {signer.public_key_hex}" in export_result.output
    assert signer.signing_key_hex not in export_result.output
    assert verify_result.exit_code == 0, verify_result.output

    bundle = json.loads(bundle_path.read_text())
    assert [
        receipt["event"]["event_type"] for receipt in bundle["signed_receipts"]
    ] == [
        "decision.point",
        "refusal",
    ]
    assert [draft["capsule_type"] for draft in bundle["capsule_drafts"]] == [
        "decision_point",
        "refusal",
    ]
    refusal_draft = bundle["capsule_drafts"][1]
    assert refusal_draft["refusal"]["refused_capsule_id"].startswith("ref_")
    assert "tool_not_in_allowlist" in refusal_draft["refusal"]["violations"]

    await gateway.shutdown()


def test_cli_export_mcp_receipts_rejects_invalid_signing_key_without_leaking_value(
    monkeypatch, tmp_path
):
    """Invalid export signing keys should fail cleanly without printing secrets."""
    secret_value = "not-a-valid-private-key"
    monkeypatch.setenv("UATP_BAD_MCP_SIGNING_KEY", secret_value)
    store_path = tmp_path / "empty.db"
    store_path.write_bytes(b"")
    runner = CliRunner()

    result = runner.invoke(
        cli,
        [
            "export-mcp-receipts",
            str(store_path),
            "--session-id",
            "sess_missing",
            "--output",
            str(tmp_path / "bundle.json"),
            "--signing-key-env",
            "UATP_BAD_MCP_SIGNING_KEY",
        ],
    )

    assert result.exit_code != 0
    assert "invalid signing key" in result.output
    assert secret_value not in result.output


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


# ---------------------------------------------------------------------------
# Gateway - deny-by-default for unknown tools
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_unknown_tool_denied(upstream_command, temp_store_path, temp_key_dir):
    """Calls to tools not in the allowlist must be blocked."""
    gateway = UATPMCPGateway(
        upstream_command=upstream_command,
        store_path=temp_store_path,
        key_dir=temp_key_dir,
    )
    await gateway.initialize()

    result = await gateway._handle_tool_call("delete_database", {"confirm": "yes"})

    from mcp.types import TextContent

    assert isinstance(result, list)
    assert len(result) >= 1
    assert isinstance(result[0], TextContent)
    assert "blocked" in result[0].text.lower()

    store = CapsuleStore(temp_store_path)
    caps = store.get_session_graph(gateway._session_id)

    decision_caps = [c for c in caps if c["capsule_type"] == "DECISION_POINT"]
    refusal_caps = [c for c in caps if c["capsule_type"] == "REFUSAL"]

    assert len(decision_caps) >= 1
    assert len(refusal_caps) >= 1

    refusal_payload = refusal_caps[0]["payload"]
    policy_checks = refusal_payload.get("policy_checks", {})
    checks_failed = policy_checks.get("checks_failed", [])
    assert any("tool_not_in_allowlist" in str(f) for f in checks_failed), (
        f"Expected tool_not_in_allowlist in {checks_failed}"
    )

    await gateway.shutdown()


# ---------------------------------------------------------------------------
# Session graph integrity
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_session_graph_returns_parent_child_chain(
    upstream_command, temp_store_path, temp_key_dir
):
    """
    A DECISION_POINT → TOOL_CALL chain must link parent → child
    through parent_decision_id so get_session_graph reconstructs the tree.
    """
    gateway = UATPMCPGateway(
        upstream_command=upstream_command,
        store_path=temp_store_path,
        key_dir=temp_key_dir,
    )
    await gateway.initialize()

    await gateway._handle_tool_call("read_file", {"path": "/dev/null"})

    store = CapsuleStore(temp_store_path)
    caps = store.get_session_graph(gateway._session_id)

    decision_caps = [c for c in caps if c["capsule_type"] == "DECISION_POINT"]
    tool_caps = [c for c in caps if c["capsule_type"] == "TOOL_CALL"]

    assert len(decision_caps) >= 1
    assert len(tool_caps) >= 1

    decision_id = decision_caps[0]["capsule_id"]
    tool_parent_id = tool_caps[0]["parent_id"]
    assert tool_parent_id == decision_id, (
        f"TOOL_CALL parent_id {tool_parent_id} should match "
        f"DECISION_POINT capsule_id {decision_id}"
    )

    await gateway.shutdown()


# ---------------------------------------------------------------------------
# Evidence-class tagging correctness
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_evidence_class_tagging_correctness(
    upstream_command, temp_store_path, temp_key_dir
):
    """
    TOOL_CALL capsule fields must be tagged with correct evidence_class and
    source_layer so downstream consumers know what to trust.
    """
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

    # Proxy-observed hard facts
    assert payload["tool"]["name"]["evidence_class"] == "observed"
    assert payload["tool"]["name"]["source_layer"] == "proxy"

    assert payload["tool"]["arguments_hash"]["evidence_class"] == "observed"
    assert payload["tool"]["arguments_hash"]["source_layer"] == "proxy"

    assert payload["execution"]["status"]["evidence_class"] == "observed"
    assert payload["execution"]["status"]["source_layer"] == "proxy"

    assert payload["output"]["content_hash"]["evidence_class"] == "observed"
    assert payload["output"]["content_hash"]["source_layer"] == "proxy"

    # Derived / proxy latency
    assert payload["execution"]["latency_ms"]["evidence_class"] == "derived"
    assert payload["execution"]["latency_ms"]["source_layer"] == "proxy"

    await gateway.shutdown()


# ---------------------------------------------------------------------------
# Demo server - sandboxed run_command
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_sandboxed_run_command_blocks_shell_metacharacters(
    upstream_command, temp_store_path, temp_key_dir
):
    """run_command must reject shell metacharacters to prevent injection."""
    gateway = UATPMCPGateway(
        upstream_command=upstream_command,
        store_path=temp_store_path,
        key_dir=temp_key_dir,
    )
    await gateway.initialize()

    result = await gateway._handle_tool_call("run_command", {"command": "ls; rm -rf /"})

    from mcp.types import TextContent

    assert isinstance(result, list)
    assert len(result) >= 1
    assert isinstance(result[0], TextContent)
    assert "SANDBOX" in result[0].text or "blocked" in result[0].text.lower()

    await gateway.shutdown()


@pytest.mark.asyncio
async def test_sandboxed_run_command_blocks_unknown_command(
    upstream_command, temp_store_path, temp_key_dir
):
    """run_command must reject commands not in the allowlist."""
    gateway = UATPMCPGateway(
        upstream_command=upstream_command,
        store_path=temp_store_path,
        key_dir=temp_key_dir,
    )
    await gateway.initialize()

    result = await gateway._handle_tool_call(
        "run_command", {"command": "python -c 'print(1)'"}
    )

    from mcp.types import TextContent

    assert isinstance(result, list)
    assert len(result) >= 1
    assert isinstance(result[0], TextContent)
    assert "SANDBOX" in result[0].text or "not in allowlist" in result[0].text

    await gateway.shutdown()
