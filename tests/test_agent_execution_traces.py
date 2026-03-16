"""
Test suite for UATP 7.4 Agent Execution Traces

Tests:
- All 5 payload validations (AgentSession, ToolCall, ActionTrace, DecisionPoint, EnvironmentSnapshot)
- Tool categories (terminal, file, browser, api, mcp, custom)
- Action types (terminal, browser, file, api)
- Decision reasoning capture with confidence
- Environment snapshot with git state
- UATP 7.4 envelope version detection
- Integration tests for complete agent flows
"""

from datetime import datetime, timezone
from typing import Any, Dict

import pytest
from pydantic import ValidationError

from src.capsule_schema import (
    ActionTraceCapsule,
    ActionTracePayload,
    AgentSessionCapsule,
    AgentSessionPayload,
    CapsuleStatus,
    CapsuleType,
    DecisionPointCapsule,
    DecisionPointPayload,
    EnvironmentSnapshotCapsule,
    EnvironmentSnapshotPayload,
    ToolCallCapsule,
    ToolCallPayload,
    Verification,
)
from src.utils.uatp_envelope import (
    create_agent_context,
    create_tool_trace_context,
    detect_capsule_version,
    wrap_in_uatp_envelope,
)

# --- Test Fixtures ---


def create_verification() -> Verification:
    """Create a test verification object."""
    return Verification(
        signature=f"ed25519:{'0' * 128}",
        merkle_root=f"sha256:{'0' * 64}",
    )


def create_capsule_id() -> str:
    """Create a valid test capsule ID."""
    return f"caps_2026_03_03_{'a' * 16}"


def now() -> datetime:
    """Get current UTC time."""
    return datetime.now(timezone.utc)


# --- AgentSessionPayload Tests ---


class TestAgentSessionPayload:
    """Test AgentSessionPayload validation."""

    def test_valid_claude_code_session(self):
        """Test valid Claude Code agent session."""
        payload = AgentSessionPayload(
            session_id="agent_20260303_abc123",
            agent_type="claude_code",
            agent_version="1.0.0",
            scheduler_type="on_demand",
            trigger_message="Help me fix the authentication bug",
            trigger_source="cli",
            user_id_hash="sha256:" + "a" * 56,
            goals=["Fix authentication bug", "Add tests"],
            started_at=now(),
            status="running",
        )
        assert payload.agent_type == "claude_code"
        assert payload.status == "running"
        assert len(payload.goals) == 2

    def test_valid_openclaw_session(self):
        """Test valid OpenClaw agent session with heartbeat scheduler."""
        payload = AgentSessionPayload(
            session_id="agent_20260303_xyz789",
            agent_type="openclaw",
            scheduler_type="heartbeat",
            trigger_message="Daily report generation",
            trigger_source="whatsapp",
            goals=["Generate daily report", "Send to stakeholders"],
            started_at=now(),
            status="running",
        )
        assert payload.agent_type == "openclaw"
        assert payload.scheduler_type == "heartbeat"

    def test_completed_session(self):
        """Test completed agent session with outcome."""
        started = now()
        payload = AgentSessionPayload(
            session_id="agent_20260303_done01",
            agent_type="custom",
            started_at=started,
            completed_at=now(),
            status="completed",
            tool_call_count=15,
            action_count=42,
            decision_count=8,
            total_duration_ms=45000,
            outcome_summary="Successfully fixed authentication and added 5 tests",
        )
        assert payload.status == "completed"
        assert payload.tool_call_count == 15
        assert payload.total_duration_ms == 45000

    def test_failed_session(self):
        """Test failed agent session with error."""
        payload = AgentSessionPayload(
            session_id="agent_20260303_fail01",
            agent_type="claude_code",
            started_at=now(),
            status="failed",
            error_message="Permission denied: cannot write to /etc/passwd",
        )
        assert payload.status == "failed"
        assert "Permission denied" in payload.error_message

    def test_invalid_negative_counts(self):
        """Test that negative counts fail validation."""
        with pytest.raises(ValidationError):
            AgentSessionPayload(
                session_id="agent_20260303_bad01",
                agent_type="claude_code",
                started_at=now(),
                status="running",
                tool_call_count=-1,  # Invalid
            )


# --- ToolCallPayload Tests ---


class TestToolCallPayload:
    """Test ToolCallPayload for all tool categories."""

    @pytest.mark.parametrize(
        "tool_category",
        [
            "terminal",
            "file",
            "browser",
            "api",
            "mcp",
            "custom",
        ],
    )
    def test_all_tool_categories(self, tool_category):
        """Test all tool categories."""
        payload = ToolCallPayload(
            call_id=f"tool_{tool_category}_001",
            session_id="agent_20260303_test01",
            tool_name="TestTool",
            tool_category=tool_category,
            tool_inputs={"param": "value"},
            started_at=now(),
            status="success",
            step_index=0,
        )
        assert payload.tool_category == tool_category

    def test_bash_tool_call(self):
        """Test Bash tool call with command."""
        payload = ToolCallPayload(
            call_id="tool_bash_001",
            session_id="agent_20260303_test01",
            tool_name="Bash",
            tool_category="terminal",
            tool_inputs={"command": "git status"},
            tool_outputs={"exit_code": 0, "stdout_length": 256},
            started_at=now(),
            completed_at=now(),
            duration_ms=150,
            status="success",
            step_index=0,
        )
        assert payload.tool_name == "Bash"
        assert payload.duration_ms == 150

    def test_read_tool_call(self):
        """Test Read tool call with file path."""
        payload = ToolCallPayload(
            call_id="tool_read_001",
            session_id="agent_20260303_test01",
            tool_name="Read",
            tool_category="file",
            tool_inputs={"file_path": "/src/main.py", "offset": 0, "limit": 100},
            tool_outputs={"lines_read": 100},
            started_at=now(),
            status="success",
            step_index=1,
        )
        assert payload.tool_name == "Read"
        assert payload.tool_category == "file"

    def test_webfetch_tool_call(self):
        """Test WebFetch tool call."""
        payload = ToolCallPayload(
            call_id="tool_web_001",
            session_id="agent_20260303_test01",
            tool_name="WebFetch",
            tool_category="browser",
            tool_inputs={"url": "https://example.com", "prompt": "Extract title"},
            started_at=now(),
            status="success",
            step_index=2,
        )
        assert payload.tool_name == "WebFetch"

    def test_nested_tool_call(self):
        """Test nested tool call with parent."""
        payload = ToolCallPayload(
            call_id="tool_nested_001",
            session_id="agent_20260303_test01",
            tool_name="Task",
            tool_category="custom",
            tool_inputs={"subagent_type": "Explore"},
            parent_call_id="tool_parent_001",
            started_at=now(),
            status="pending",
            step_index=3,
        )
        assert payload.parent_call_id == "tool_parent_001"

    def test_error_tool_call(self):
        """Test tool call with error."""
        payload = ToolCallPayload(
            call_id="tool_error_001",
            session_id="agent_20260303_test01",
            tool_name="Bash",
            tool_category="terminal",
            tool_inputs={"command": "rm -rf /"},
            started_at=now(),
            status="error",
            error_message="Command blocked by security policy",
            step_index=4,
        )
        assert payload.status == "error"
        assert "blocked" in payload.error_message

    def test_invalid_negative_duration(self):
        """Test that negative duration fails validation."""
        with pytest.raises(ValidationError):
            ToolCallPayload(
                call_id="tool_bad_001",
                session_id="agent_20260303_test01",
                tool_name="Bash",
                tool_category="terminal",
                tool_inputs={},
                started_at=now(),
                duration_ms=-100,  # Invalid
                step_index=0,
            )


# --- ActionTracePayload Tests ---


class TestActionTracePayload:
    """Test ActionTracePayload for all action types."""

    def test_terminal_action(self):
        """Test terminal action trace with command."""
        payload = ActionTracePayload(
            action_id="act_term_001",
            session_id="agent_20260303_test01",
            action_type="terminal",
            command="git commit -m 'Fix bug'",
            exit_code=0,
            stdout_hash="sha256:" + "a" * 56,
            stderr_hash="sha256:" + "b" * 56,
            executed_at=now(),
            duration_ms=250,
        )
        assert payload.action_type == "terminal"
        assert payload.exit_code == 0

    def test_browser_action(self):
        """Test browser action trace with navigation."""
        payload = ActionTracePayload(
            action_id="act_browser_001",
            session_id="agent_20260303_test01",
            action_type="browser",
            url="https://docs.python.org",
            browser_action="navigate",
            executed_at=now(),
            duration_ms=1500,
        )
        assert payload.action_type == "browser"
        assert payload.browser_action == "navigate"

    def test_browser_click_action(self):
        """Test browser click action with selector."""
        payload = ActionTracePayload(
            action_id="act_browser_002",
            session_id="agent_20260303_test01",
            action_type="browser",
            url="https://example.com/form",
            selector="#submit-button",
            browser_action="click",
            executed_at=now(),
            duration_ms=100,
        )
        assert payload.selector == "#submit-button"
        assert payload.browser_action == "click"

    def test_file_read_action(self):
        """Test file read action."""
        payload = ActionTracePayload(
            action_id="act_file_001",
            session_id="agent_20260303_test01",
            action_type="file",
            file_path="/src/utils/helper.py",
            file_operation="read",
            bytes_affected=4096,
            executed_at=now(),
            duration_ms=5,
        )
        assert payload.action_type == "file"
        assert payload.file_operation == "read"

    def test_file_edit_action(self):
        """Test file edit action."""
        payload = ActionTracePayload(
            action_id="act_file_002",
            session_id="agent_20260303_test01",
            tool_call_id="tool_edit_001",
            action_type="file",
            file_path="/src/main.py",
            file_operation="edit",
            bytes_affected=150,
            executed_at=now(),
            duration_ms=10,
        )
        assert payload.tool_call_id == "tool_edit_001"
        assert payload.file_operation == "edit"

    def test_api_action(self):
        """Test API action trace."""
        payload = ActionTracePayload(
            action_id="act_api_001",
            session_id="agent_20260303_test01",
            action_type="api",
            url="https://api.github.com/repos/owner/repo",
            executed_at=now(),
            duration_ms=350,
        )
        assert payload.action_type == "api"


# --- DecisionPointPayload Tests ---


class TestDecisionPointPayload:
    """Test DecisionPointPayload for agent reasoning capture."""

    def test_valid_decision_with_confidence(self):
        """Test valid decision point with confidence score."""
        payload = DecisionPointPayload(
            decision_id="dec_001",
            session_id="agent_20260303_test01",
            step_index=5,
            reasoning="The error message indicates a type mismatch. Looking at the function signature reveals an incorrect parameter type.",
            alternatives_considered=[
                "Refactor the entire module",
                "Add a type conversion wrapper",
                "Update the calling code to pass correct type",
            ],
            selected_action="Update the calling code to pass correct type",
            confidence=0.85,
            context_summary="Working on bug fix for authentication module",
            constraints_applied=[
                "No breaking changes",
                "Maintain backward compatibility",
            ],
            timestamp=now(),
        )
        assert payload.confidence == 0.85
        assert len(payload.alternatives_considered) == 3

    def test_decision_without_confidence(self):
        """Test decision point without confidence (uncertain)."""
        payload = DecisionPointPayload(
            decision_id="dec_002",
            session_id="agent_20260303_test01",
            step_index=6,
            reasoning="Multiple valid approaches exist; user preference unknown.",
            selected_action="Ask user for clarification",
            timestamp=now(),
        )
        assert payload.confidence is None

    def test_decision_with_safety_constraints(self):
        """Test decision with safety constraints."""
        payload = DecisionPointPayload(
            decision_id="dec_003",
            session_id="agent_20260303_test01",
            step_index=7,
            reasoning="User requested file deletion but path appears to be system critical.",
            alternatives_considered=[
                "Delete the file as requested",
                "Refuse and explain the risk",
            ],
            selected_action="Refuse and explain the risk",
            confidence=0.99,
            constraints_applied=[
                "NEVER delete system files",
                "Ask for confirmation on destructive operations",
            ],
            timestamp=now(),
        )
        assert "NEVER delete system files" in payload.constraints_applied

    def test_invalid_confidence_over_1(self):
        """Test that confidence over 1.0 fails validation."""
        with pytest.raises(ValidationError):
            DecisionPointPayload(
                decision_id="dec_bad",
                session_id="agent_20260303_test01",
                step_index=0,
                reasoning="Test",
                selected_action="Test",
                confidence=1.5,  # Invalid: must be <= 1.0
                timestamp=now(),
            )

    def test_invalid_confidence_negative(self):
        """Test that negative confidence fails validation."""
        with pytest.raises(ValidationError):
            DecisionPointPayload(
                decision_id="dec_bad",
                session_id="agent_20260303_test01",
                step_index=0,
                reasoning="Test",
                selected_action="Test",
                confidence=-0.5,  # Invalid: must be >= 0.0
                timestamp=now(),
            )


# --- EnvironmentSnapshotPayload Tests ---


class TestEnvironmentSnapshotPayload:
    """Test EnvironmentSnapshotPayload for system state capture."""

    def test_full_environment_snapshot(self):
        """Test full environment snapshot with all fields."""
        payload = EnvironmentSnapshotPayload(
            snapshot_id="snap_001",
            session_id="agent_20260303_test01",
            working_directory="/Users/dev/project",
            env_vars_hash="sha256:" + "a" * 56,
            git_branch="feature/auth-fix",
            git_commit_hash="a1b2c3d4e5f6",
            git_dirty=True,
            open_files=["/src/main.py", "/tests/test_main.py"],
            system_load=2.5,
            memory_available_gb=8.0,
            timestamp=now(),
        )
        assert payload.git_branch == "feature/auth-fix"
        assert payload.git_dirty is True
        assert len(payload.open_files) == 2

    def test_minimal_snapshot(self):
        """Test minimal snapshot (required fields only)."""
        payload = EnvironmentSnapshotPayload(
            snapshot_id="snap_002",
            session_id="agent_20260303_test01",
            working_directory="/tmp/workspace",
            env_vars_hash="sha256:" + "b" * 56,
            timestamp=now(),
        )
        assert payload.git_branch is None
        assert len(payload.open_files) == 0

    def test_clean_git_state(self):
        """Test snapshot with clean git state."""
        payload = EnvironmentSnapshotPayload(
            snapshot_id="snap_003",
            session_id="agent_20260303_test01",
            working_directory="/project",
            env_vars_hash="sha256:" + "c" * 56,
            git_branch="main",
            git_commit_hash="abcdef123456",
            git_dirty=False,
            timestamp=now(),
        )
        assert payload.git_dirty is False


# --- Capsule Tests ---


class TestAgentSessionCapsule:
    """Test AgentSessionCapsule creation."""

    def test_create_capsule(self):
        """Test creating a valid AgentSessionCapsule."""
        capsule = AgentSessionCapsule(
            capsule_id=create_capsule_id(),
            version="7.4",
            timestamp=now(),
            status=CapsuleStatus.DRAFT,
            verification=create_verification(),
            agent_session=AgentSessionPayload(
                session_id="agent_20260303_test01",
                agent_type="claude_code",
                goals=["Fix bug"],
                started_at=now(),
                status="running",
            ),
        )
        assert capsule.capsule_type == CapsuleType.AGENT_SESSION
        assert capsule.version == "7.4"


class TestToolCallCapsule:
    """Test ToolCallCapsule creation."""

    def test_create_capsule(self):
        """Test creating a valid ToolCallCapsule."""
        capsule = ToolCallCapsule(
            capsule_id=create_capsule_id(),
            version="7.4",
            timestamp=now(),
            status=CapsuleStatus.DRAFT,
            verification=create_verification(),
            tool_call=ToolCallPayload(
                call_id="tool_001",
                session_id="agent_20260303_test01",
                tool_name="Bash",
                tool_category="terminal",
                tool_inputs={"command": "ls -la"},
                started_at=now(),
                status="success",
                step_index=0,
            ),
        )
        assert capsule.capsule_type == CapsuleType.TOOL_CALL


class TestDecisionPointCapsule:
    """Test DecisionPointCapsule creation."""

    def test_create_capsule(self):
        """Test creating a valid DecisionPointCapsule."""
        capsule = DecisionPointCapsule(
            capsule_id=create_capsule_id(),
            version="7.4",
            timestamp=now(),
            status=CapsuleStatus.DRAFT,
            verification=create_verification(),
            decision_point=DecisionPointPayload(
                decision_id="dec_001",
                session_id="agent_20260303_test01",
                step_index=0,
                reasoning="File needs to be edited",
                selected_action="Use Edit tool",
                timestamp=now(),
            ),
        )
        assert capsule.capsule_type == CapsuleType.DECISION_POINT


# --- UATP Envelope Tests ---


class TestUATPEnvelopeVersion74:
    """Test UATP 7.4 envelope creation and version detection."""

    def test_detect_74_with_agent_context(self):
        """Test version detection with agent_context."""
        envelope = {
            "agent_context": {
                "session_id": "agent_001",
                "agent_type": "claude_code",
            }
        }
        version = detect_capsule_version(envelope)
        assert version == "7.4"

    def test_detect_74_with_tool_trace(self):
        """Test version detection with tool_trace."""
        envelope = {
            "tool_trace": {
                "session_id": "agent_001",
                "tool_calls": [],
            }
        }
        version = detect_capsule_version(envelope)
        assert version == "7.4"

    def test_create_agent_context(self):
        """Test create_agent_context helper."""
        context = create_agent_context(
            session_id="agent_20260303_test01",
            agent_type="claude_code",
            goals=["Fix bug", "Add tests"],
            scheduler_type="on_demand",
            trigger_message="Fix the authentication",
            trigger_source="cli",
        )
        assert context["session_id"] == "agent_20260303_test01"
        assert context["agent_type"] == "claude_code"
        assert len(context["goals"]) == 2
        assert "timestamp" in context

    def test_create_tool_trace_context(self):
        """Test create_tool_trace_context helper."""
        tool_calls = [
            {"call_id": "t1", "tool_name": "Bash"},
            {"call_id": "t2", "tool_name": "Read"},
        ]
        context = create_tool_trace_context(
            session_id="agent_20260303_test01",
            tool_calls=tool_calls,
            total_tool_calls=10,
            total_duration_ms=5000,
        )
        assert context["session_id"] == "agent_20260303_test01"
        assert context["tool_count"] == 2
        assert context["total_tool_calls"] == 10
        assert context["total_duration_ms"] == 5000

    def test_wrap_envelope_with_agent_context(self):
        """Test wrap_in_uatp_envelope with agent_context."""
        payload = {"test": "data"}
        agent_context = create_agent_context(
            session_id="agent_001",
            agent_type="claude_code",
        )
        envelope = wrap_in_uatp_envelope(
            payload_data=payload,
            capsule_id=create_capsule_id(),
            capsule_type="agent_session",
            agent_context=agent_context,
        )
        assert envelope["_envelope"]["version"] == "7.4"
        assert "agent_context" in envelope

    def test_wrap_envelope_with_tool_trace(self):
        """Test wrap_in_uatp_envelope with tool_trace."""
        payload = {"test": "data"}
        tool_trace = create_tool_trace_context(
            session_id="agent_001",
            tool_calls=[],
        )
        envelope = wrap_in_uatp_envelope(
            payload_data=payload,
            capsule_id=create_capsule_id(),
            capsule_type="tool_call",
            tool_trace=tool_trace,
        )
        assert envelope["_envelope"]["version"] == "7.4"
        assert "tool_trace" in envelope


# --- Integration Tests ---


class TestAgentExecutionIntegration:
    """Integration tests for complete agent execution flows."""

    def test_complete_session_flow(self):
        """Test a complete session with tools, actions, and decisions."""
        # Create session
        session_payload = AgentSessionPayload(
            session_id="agent_20260303_full01",
            agent_type="claude_code",
            goals=["Fix authentication bug"],
            started_at=now(),
            status="running",
        )

        # Record tool calls
        tool_calls = [
            ToolCallPayload(
                call_id="t1",
                session_id="agent_20260303_full01",
                tool_name="Read",
                tool_category="file",
                tool_inputs={"file_path": "/src/auth.py"},
                started_at=now(),
                status="success",
                step_index=0,
            ),
            ToolCallPayload(
                call_id="t2",
                session_id="agent_20260303_full01",
                tool_name="Edit",
                tool_category="file",
                tool_inputs={
                    "file_path": "/src/auth.py",
                    "old_string": "bug",
                    "new_string": "fix",
                },
                started_at=now(),
                status="success",
                step_index=1,
            ),
        ]

        # Record decision
        decision = DecisionPointPayload(
            decision_id="d1",
            session_id="agent_20260303_full01",
            step_index=1,
            reasoning="Found the bug in line 42. Simple fix needed.",
            selected_action="Edit the file to fix the bug",
            confidence=0.95,
            timestamp=now(),
        )

        # Verify all payloads are valid
        assert session_payload.session_id == "agent_20260303_full01"
        assert len(tool_calls) == 2
        assert decision.confidence == 0.95

    def test_multi_tool_session(self):
        """Test session with multiple tool categories."""
        categories_used = set()

        tool_calls = [
            ToolCallPayload(
                call_id="tc1",
                session_id="agent_multi",
                tool_name="Bash",
                tool_category="terminal",
                tool_inputs={},
                started_at=now(),
                status="success",
                step_index=0,
            ),
            ToolCallPayload(
                call_id="tc2",
                session_id="agent_multi",
                tool_name="Read",
                tool_category="file",
                tool_inputs={},
                started_at=now(),
                status="success",
                step_index=1,
            ),
            ToolCallPayload(
                call_id="tc3",
                session_id="agent_multi",
                tool_name="WebFetch",
                tool_category="browser",
                tool_inputs={},
                started_at=now(),
                status="success",
                step_index=2,
            ),
            ToolCallPayload(
                call_id="tc4",
                session_id="agent_multi",
                tool_name="Task",
                tool_category="custom",
                tool_inputs={},
                started_at=now(),
                status="success",
                step_index=3,
            ),
        ]

        for tc in tool_calls:
            categories_used.add(tc.tool_category)

        assert categories_used == {"terminal", "file", "browser", "custom"}
