"""
hermes_capture.py — Converts a Hermes session into a signed UATP capsule.

Routes through the full RichCaptureEnhancer pipeline so Hermes capsules
get the same quality as Claude Code capsules: critical path analysis,
uncertainty quantification, quality assessment, confidence explanations,
trust posture, etc.

Reads messages from ~/.hermes/state.db, converts them to UATP's
ConversationMessage/ConversationSession objects, runs them through
RichCaptureEnhancer, signs with Ed25519 via UATPCryptoV7, writes
to ~/uatp-capsule-engine/uatp_dev.db.

Usage:
    python3 hermes_capture.py <session_id>
    python3 hermes_capture.py --latest
    python3 hermes_capture.py --list
"""

import hashlib
import json
import logging
import os
import re
import shlex
import sqlite3
import sys
from collections import Counter
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from src.agent_receipts.artifacts import ArtifactStore
from src.agent_receipts.events import (
    ActionTraceEvent,
    AgentReceiptEvent,
    DecisionPointEvent,
    EnvironmentSnapshotEvent,
    SessionEnded,
    SessionStarted,
    ToolCallCompleted,
)
from src.agent_receipts.redaction import redact_value
from src.agent_receipts.signing import Ed25519ReceiptSigner
from src.agent_receipts.sink import build_signed_receipt_bundle

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

HERMES_HOME = Path(os.environ.get("HERMES_HOME", Path.home() / ".hermes"))
STATE_DB = HERMES_HOME / "state.db"
UATP_ROOT = Path.home() / "uatp-capsule-engine"
UATP_DB = UATP_ROOT / "uatp_dev.db"

MIN_MESSAGES = 4


# ---------------------------------------------------------------------------
# UATP imports (lazy, from the UATP codebase)
# ---------------------------------------------------------------------------

_uatp_loaded = False


def _ensure_uatp_imports():
    """Add UATP to sys.path and import what we need. Cached after first call."""
    global _uatp_loaded
    if _uatp_loaded:
        return
    if str(UATP_ROOT) not in sys.path:
        sys.path.insert(0, str(UATP_ROOT))
    _uatp_loaded = True


def _get_capture_classes():
    """Import ConversationMessage, ConversationSession from UATP."""
    _ensure_uatp_imports()
    from src.live_capture.claude_code_capture import (
        ConversationMessage,
        ConversationSession,
    )

    return ConversationMessage, ConversationSession


def _get_rich_enhancer():
    """Import RichCaptureEnhancer."""
    _ensure_uatp_imports()
    from src.live_capture.rich_capture_integration import RichCaptureEnhancer

    return RichCaptureEnhancer


def _get_signal_detector():
    """Import SignalDetector."""
    _ensure_uatp_imports()
    from src.live_capture.signal_detector import SignalDetector

    return SignalDetector()


def _get_crypto():
    """Import UATPCryptoV7."""
    _ensure_uatp_imports()
    from src.security.uatp_crypto_v7 import UATPCryptoV7

    return UATPCryptoV7(
        key_dir=str(UATP_ROOT / ".uatp_keys"),
        signer_id="hermes_capture",
    )


# ---------------------------------------------------------------------------
# Secret redaction (Phase H1.2)
# ---------------------------------------------------------------------------

# Patterns are applied in order. Each captures a secret-like substring and
# replaces it with [REDACTED]. Designed to err on the side of redacting
# anything that looks like an API key, token, password, or signing seed.
_REDACTION_PATTERNS = [
    # JWT-shaped tokens: three base64url segments separated by dots.
    re.compile(r"eyJ[A-Za-z0-9_\-]+\.[A-Za-z0-9_\-]+\.[A-Za-z0-9_\-]+"),
    # AWS access key IDs.
    re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
    # Google API keys.
    re.compile(r"AIza[0-9A-Za-z_\-]{35,}"),
    # Key/secret/token/password assignments. The value runs until whitespace,
    # quote, comma, or close-brace/bracket — covering both `k=v` and `k: v`,
    # quoted and unquoted, with optional quote around the key (JSON-style).
    re.compile(
        r"(?i)['\"]?("
        r"api[_-]?key|apikey|secret|password|passwd|token|"
        r"signing[_-]?key|private[_-]?key|access[_-]?token|"
        r"bearer"
        r")['\"]?"
        r"\s*[:=]\s*"
        r"['\"]?"
        r"([^\s'\"\,\}\]]{6,})"
        r"['\"]?"
    ),
]


def _redact_secrets(text: Any) -> tuple:
    """Replace secret-like substrings with [REDACTED]. Returns (text, count).

    Non-string inputs return ("", 0). Benign text returns unchanged with count 0.
    """
    if not isinstance(text, str) or not text:
        return ("" if text is None else (text if isinstance(text, str) else ""), 0)

    redacted = text
    count = 0

    for pattern in _REDACTION_PATTERNS:
        if pattern.groups >= 2:
            # Assignment pattern: keep key, redact value.
            def _sub(match: "re.Match") -> str:
                nonlocal count
                count += 1
                return f"{match.group(1)}=[REDACTED]"

            redacted = pattern.sub(_sub, redacted)
        else:
            # Standalone-token pattern: redact the whole match.
            def _sub_full(match: "re.Match") -> str:
                nonlocal count
                count += 1
                return "[REDACTED]"

            redacted = pattern.sub(_sub_full, redacted)

    return (redacted, count)


# ---------------------------------------------------------------------------
# File artifact manifest (Phase H1.1)
# ---------------------------------------------------------------------------

# Tool names that map to file write/patch/read operations. Match Hermes-recorded
# tool names exactly; we do not normalize case.
_FILE_WRITE_TOOLS = {"write_file", "Write"}
_FILE_PATCH_TOOLS = {"patch", "Edit", "MultiEdit"}
_FILE_READ_TOOLS = {"read_file", "Read"}
_COMMAND_TOOLS = {"terminal", "Bash"}
_ARTIFACT_PREVIEW_CHARS = 2000
_LEARNING_RECEIPT_V2_SCHEMA = "2026-06-04.artifact-verification.v1"
_QUALITY_TRIGGER_TERMS = (
    "gold standard",
    "no ai slop",
    "no regression",
    "my standard",
    "standard",
)
_ACTION_DIRECTIVE_TERMS = (
    "fix",
    "apply",
    "continue",
    "do it",
    "commit",
    "push",
    "run",
    "test",
    "verify",
)
_PROJECT_MARKER_TERMS = ("uatp", "portfolio", "resume", "residuals", "hermes")
_VISUAL_TERMS = (
    "look at page",
    "screenshot",
    "visual",
    "higher",
    "lower",
    "left",
    "right",
    "border",
    "spacing",
    "from scratch",
)
_LOCAL_STATE_TERMS = ("local", "file", "repo", "can you see", "where is", "path")


def _sha256_hex(text: str) -> str:
    """SHA-256 hex digest of UTF-8 encoded text."""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _parse_args(arguments: Any) -> Optional[Dict[str, Any]]:
    """Parse tool arguments which may be a JSON string or already a dict."""
    if isinstance(arguments, dict):
        return arguments
    if not isinstance(arguments, str):
        return None
    try:
        parsed = json.loads(arguments)
    except (json.JSONDecodeError, ValueError):
        return None
    return parsed if isinstance(parsed, dict) else None


def _build_artifact_preview(text: str) -> Dict[str, Any]:
    """Build a redacted, size-bounded artifact preview with metadata."""
    redacted_text, redactions = _redact_secrets(text)
    original_length = len(text)
    truncated = len(redacted_text) > _ARTIFACT_PREVIEW_CHARS
    preview = redacted_text[:_ARTIFACT_PREVIEW_CHARS] if truncated else redacted_text
    return {
        "preview": preview,
        "truncated": truncated,
        "original_length": original_length,
        "redactions": redactions,
        "redacted_text": redacted_text,
    }


def _parse_tool_result(result: Any) -> Dict[str, Any]:
    """Parse a Hermes tool result preview into output/exit-code fields."""
    if isinstance(result, dict):
        return result
    if not isinstance(result, str):
        return {"output": "", "exit_code": None}
    try:
        parsed = json.loads(result)
    except (json.JSONDecodeError, ValueError):
        return {"output": result, "exit_code": None}
    return parsed if isinstance(parsed, dict) else {"output": result, "exit_code": None}


def _classify_verification_command(
    command: str,
    exit_code: Optional[int],
    output: str = "",
) -> Dict[str, Optional[str] | bool]:
    """Classify commands that verify correctness rather than mutate state."""
    output_lower = output.lower()
    verification_type: Optional[str] = None

    try:
        tokens = shlex.split(command)
    except ValueError:
        tokens = command.split()

    # Ignore environment assignments before the executable, e.g.
    # PYTHONPATH=. .venv/bin/python -m pytest tests -q
    while tokens and re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*=.*", tokens[0]):
        tokens = tokens[1:]

    executable = Path(tokens[0]).name.lower() if tokens else ""
    lowered = [token.lower() for token in tokens]

    if executable in {"pytest"}:
        verification_type = "test"
    elif executable in {"ruff"} and len(lowered) > 1 and lowered[1] == "check":
        verification_type = "lint"
    elif executable == "git" and lowered[1:3] == ["diff", "--check"]:
        verification_type = "diff_check"
    elif executable in {"python", "python3"} and "-m" in lowered:
        module_index = lowered.index("-m") + 1
        module = lowered[module_index] if module_index < len(lowered) else ""
        module_args = lowered[module_index + 1 :]
        if module == "pytest":
            verification_type = "test"
        elif module == "ruff" and module_args[:1] == ["check"]:
            verification_type = "lint"
        elif module == "py_compile":
            verification_type = "compile"

    if verification_type is None:
        return {
            "is_verification": False,
            "verification_type": None,
            "verification_status": None,
        }

    status = "passed" if exit_code == 0 else "failed"
    if exit_code is None and verification_type == "test":
        failure_markers = (" failed", " error", " errors", " failures")
        status = (
            "failed"
            if any(marker in f" {output_lower}" for marker in failure_markers)
            else "passed"
        )

    return {
        "is_verification": True,
        "verification_type": verification_type,
        "verification_status": status,
    }


def _extract_file_artifacts(
    invocations: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """Extract structured file-operation artifacts from tool invocations.

    Returns a list of `{operation, path, ...hashes/sizes}` dicts. Operations:
    - write: full content known; records content_hash_after, content_size_after
    - patch: old/new string known; records hashes and sizes for both
    - read: only path/offset/limit known; no content hash
    """
    manifest: List[Dict[str, Any]] = []

    for inv in invocations:
        tool = inv.get("tool")
        if not tool:
            continue

        args = _parse_args(inv.get("arguments"))
        if args is None:
            continue

        path = args.get("path") or args.get("file_path")
        if not path:
            continue

        base_entry: Dict[str, Any] = {
            "path": path,
            "call_id": inv.get("call_id"),
            "tool": tool,
        }
        if inv.get("timestamp"):
            base_entry["timestamp"] = inv.get("timestamp")

        if tool in _FILE_WRITE_TOOLS:
            content = args.get("content")
            if content is None:
                continue
            content_str = content if isinstance(content, str) else str(content)
            preview = _build_artifact_preview(content_str)
            entry = {
                **base_entry,
                "operation": "write",
                "content_hash_after": _sha256_hex(content_str),
                "content_size_after": len(content_str),
                "content_preview": preview["preview"],
                "content_preview_truncated": preview["truncated"],
                "content_preview_original_length": preview["original_length"],
                "redactions": preview["redactions"],
            }
            manifest.append(entry)
        elif tool in _FILE_PATCH_TOOLS:
            old_str = args.get("old_string")
            new_str = args.get("new_string")
            entry = {
                **base_entry,
                "operation": "patch",
            }
            if isinstance(old_str, str):
                entry["old_string_hash"] = _sha256_hex(old_str)
                entry["old_string_size"] = len(old_str)
            if isinstance(new_str, str):
                entry["new_string_hash"] = _sha256_hex(new_str)
                entry["new_string_size"] = len(new_str)
            manifest.append(entry)
        elif tool in _FILE_READ_TOOLS:
            entry = {
                **base_entry,
                "operation": "read",
            }
            for opt_key in ("offset", "limit"):
                if opt_key in args:
                    entry[opt_key] = args[opt_key]
            manifest.append(entry)

    return manifest


def _extract_command_artifacts(
    invocations: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """Extract command execution proof from terminal/Bash tool invocations."""
    commands: List[Dict[str, Any]] = []

    for inv in invocations:
        tool = inv.get("tool")
        if tool not in _COMMAND_TOOLS:
            continue

        args = _parse_args(inv.get("arguments"))
        if args is None:
            continue

        command = args.get("command")
        if not command:
            continue

        result = _parse_tool_result(inv.get("result_preview"))
        exit_code = result.get("exit_code")
        output = result.get("output") or result.get("stdout") or ""
        output_text = output if isinstance(output, str) else str(output)
        preview = _build_artifact_preview(output_text)
        redacted_output = preview["redacted_text"]
        verification = _classify_verification_command(command, exit_code, output_text)

        entry: Dict[str, Any] = {
            "tool": tool,
            "call_id": inv.get("call_id"),
            "command": command,
            "exit_code": exit_code,
            "stdout_hash": _sha256_hex(redacted_output),
            "stdout_size": len(redacted_output),
            "stdout_preview": preview["preview"],
            "stdout_preview_truncated": preview["truncated"],
            "stdout_preview_original_length": preview["original_length"],
            "redactions": preview["redactions"],
            **verification,
        }
        if args.get("workdir"):
            entry["workdir"] = args.get("workdir")
        if inv.get("timestamp"):
            entry["timestamp"] = inv.get("timestamp")
        commands.append(entry)

    return commands


def _summarize_command_verifications(
    commands: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """Summarize verification command results for quick capsule review."""
    verifications = [cmd for cmd in commands if cmd.get("is_verification") is True]
    by_type = Counter(
        cmd.get("verification_type")
        for cmd in verifications
        if cmd.get("verification_type")
    )
    by_status = Counter(
        cmd.get("verification_status")
        for cmd in verifications
        if cmd.get("verification_status")
    )
    return {
        "verification_commands_total": len(verifications),
        "verification_commands_passed": by_status.get("passed", 0),
        "verification_commands_failed": by_status.get("failed", 0),
        "verification_commands_by_type": dict(by_type.most_common()),
        "verification_commands_by_status": dict(by_status.most_common()),
    }


def _user_text_from_messages(messages: List[Dict[str, Any]] | None) -> str:
    """Join user text from Hermes messages for deterministic task-intent labels."""
    if not messages:
        return ""
    return "\n".join(
        str(message.get("content") or "")
        for message in messages
        if message.get("role") == "user"
    ).lower()


def _matched_terms(text: str, terms: tuple[str, ...]) -> List[str]:
    """Return deterministic phrase matches without guessing intent."""
    return [term for term in terms if term in text]


def _build_learning_receipt_v2(
    tool_invocations: List[Dict[str, Any]] | None,
    messages: List[Dict[str, Any]] | None = None,
) -> Dict[str, Any]:
    """Build an additive learning receipt from tools, artifacts, and verification.

    The receipt is intentionally conservative: it records what tools prove and
    only derives lightweight intent labels from user text. It does not infer
    completion, satisfaction, or outcomes.
    """
    invocations = tool_invocations or []
    file_artifacts = _extract_file_artifacts(invocations)
    command_artifacts = _extract_command_artifacts(invocations)
    verification_summary = _summarize_command_verifications(command_artifacts)

    last_write_index = None
    last_verification_index = None
    for index, invocation in enumerate(invocations):
        tool = invocation.get("tool")
        if tool in _FILE_WRITE_TOOLS | _FILE_PATCH_TOOLS:
            last_write_index = index
        if tool in _COMMAND_TOOLS:
            args = _parse_args(invocation.get("arguments")) or {}
            parsed_result = _parse_tool_result(invocation.get("result_preview"))
            command = args.get("command") or ""
            output = parsed_result.get("output") or parsed_result.get("stdout") or ""
            verification = _classify_verification_command(
                command,
                parsed_result.get("exit_code"),
                output if isinstance(output, str) else str(output),
            )
            if verification.get("is_verification") is True:
                last_verification_index = index

    ran_after_last_write = last_verification_index is not None and (
        last_write_index is None or last_verification_index > last_write_index
    )

    user_text = _user_text_from_messages(messages)
    task_intent = {
        "quality_triggers": _matched_terms(user_text, _QUALITY_TRIGGER_TERMS),
        "action_directives": _matched_terms(user_text, _ACTION_DIRECTIVE_TERMS),
        "project_markers": _matched_terms(user_text, _PROJECT_MARKER_TERMS),
        "requires_visual_qa": bool(_matched_terms(user_text, _VISUAL_TERMS)),
        "requires_local_state": bool(_matched_terms(user_text, _LOCAL_STATE_TERMS)),
    }

    modified_artifacts = any(
        artifact.get("operation") in {"write", "patch"} for artifact in file_artifacts
    )
    verified_changes = verification_summary["verification_commands_total"] > 0

    return {
        "schema_version": _LEARNING_RECEIPT_V2_SCHEMA,
        "artifact_manifest": {
            "files": file_artifacts,
            "commands": command_artifacts,
            "tool_frequency": dict(
                Counter(
                    invocation.get("tool")
                    for invocation in invocations
                    if invocation.get("tool")
                ).most_common()
            ),
            "tool_call_count": len(invocations),
        },
        "verification_evidence": {
            **verification_summary,
            "ran_after_last_write": ran_after_last_write,
            "last_write_index": last_write_index,
            "last_verification_index": last_verification_index,
        },
        "task_intent": task_intent,
        "learning_flags": {
            "acted_with_tools": bool(invocations),
            "modified_artifacts": modified_artifacts,
            "verified_changes": verified_changes,
            "verification_after_change": bool(
                modified_artifacts and ran_after_last_write
            ),
            "possible_explanation_bias": bool(
                task_intent["action_directives"] and not invocations
            ),
        },
    }


# ---------------------------------------------------------------------------
# Read Hermes session
# ---------------------------------------------------------------------------


def read_session(session_id: str) -> Optional[Dict[str, Any]]:
    """Read a session and its messages from state.db."""
    if not STATE_DB.exists():
        logger.error("state.db not found at %s", STATE_DB)
        return None

    conn = sqlite3.connect(str(STATE_DB))
    conn.row_factory = sqlite3.Row
    try:
        row = conn.execute(
            "SELECT * FROM sessions WHERE id = ?", (session_id,)
        ).fetchone()
        if not row:
            logger.error("Session %s not found", session_id)
            return None

        messages = conn.execute(
            "SELECT * FROM messages WHERE session_id = ? ORDER BY id",
            (session_id,),
        ).fetchall()

        return {
            "session": dict(row),
            "messages": [dict(m) for m in messages],
        }
    finally:
        conn.close()


def list_recent_sessions(limit: int = 10) -> List[Dict]:
    """List recent sessions from state.db."""
    if not STATE_DB.exists():
        return []
    conn = sqlite3.connect(str(STATE_DB))
    conn.row_factory = sqlite3.Row
    try:
        rows = conn.execute(
            "SELECT id, model, message_count, title, started_at "
            "FROM sessions ORDER BY started_at DESC LIMIT ?",
            (limit,),
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Convert Hermes messages -> UATP dataclasses
# ---------------------------------------------------------------------------


def _ts_from_epoch(epoch) -> Optional[datetime]:
    """Convert epoch float to datetime."""
    if epoch is None:
        return None
    try:
        return datetime.fromtimestamp(float(epoch), tz=timezone.utc)
    except (ValueError, TypeError, OSError):
        return None


def _ts_from_iso(value: Any) -> Optional[datetime]:
    """Parse an ISO datetime string to an aware datetime when possible."""
    if not isinstance(value, str) or not value:
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed


def _get_agent_receipt_signer() -> Ed25519ReceiptSigner:
    """Load or create the persistent Hermes agent-receipt Ed25519 key."""
    key_path = UATP_ROOT / ".uatp_keys" / "hermes_agent_receipts_ed25519.hex"
    key_path.parent.mkdir(parents=True, exist_ok=True)
    if key_path.exists():
        return Ed25519ReceiptSigner.from_hex(
            key_path.read_text().strip(), signer_id="hermes_agent_receipts"
        )

    signer = Ed25519ReceiptSigner.generate(signer_id="hermes_agent_receipts")
    key_path.write_text(signer.signing_key_hex)
    try:
        key_path.chmod(0o600)
    except OSError:
        logger.warning("Could not chmod agent receipt signing key at %s", key_path)
    return signer


def _get_agent_receipt_artifact_store() -> ArtifactStore:
    """Return the local content-addressed store for Hermes receipt artifacts."""
    return ArtifactStore(UATP_ROOT / ".uatp_artifacts" / "agent_receipts")


def _redaction_metadata(redactions: int) -> Dict[str, Any]:
    return {
        "status": "redacted" if redactions else "none",
        "redactions": redactions,
    }


def _store_text_artifact(
    artifact_store: ArtifactStore,
    text: str,
    *,
    redactions: int,
    media_type: str = "text/plain",
) -> Dict[str, Any]:
    return artifact_store.store_bytes(
        text.encode("utf-8"),
        media_type=media_type,
        redaction=_redaction_metadata(redactions),
    ).to_dict()


def _store_redacted_text_artifact(
    artifact_store: ArtifactStore,
    text: Any,
    *,
    media_type: str = "text/plain",
) -> Dict[str, Any]:
    """Redact text, store redacted bytes, and return a content-addressed ref."""
    text_value = text if isinstance(text, str) else str(text)
    preview = _build_artifact_preview(text_value)
    return _store_text_artifact(
        artifact_store,
        preview["redacted_text"],
        redactions=preview["redactions"],
        media_type=media_type,
    )


def _redact_error_message(message: str) -> str:
    """Redact sensitive-looking path segments and secret assignments from errors."""
    redacted, _count = _redact_secrets(message)
    parts = redacted.split("/")
    sensitive_words = ("secret", "token", "password", "private_key", "signing_key")
    for index, part in enumerate(parts):
        if any(word in part.lower() for word in sensitive_words):
            parts[index] = "[REDACTED]"
    return "/".join(parts)


def _tool_category(tool_name: str | None) -> str:
    if tool_name in _COMMAND_TOOLS:
        return "command"
    if tool_name in _FILE_WRITE_TOOLS | _FILE_PATCH_TOOLS | _FILE_READ_TOOLS:
        return "file"
    return "custom"


def _as_text(value: Any) -> str:
    """Return text for payload fields where None means absent/empty."""
    if value is None:
        return ""
    return value if isinstance(value, str) else str(value)


def _file_path_from_args(arguments: Dict[str, Any]) -> Any:
    return arguments.get("path") or arguments.get("file_path")


def _joined_edit_strings(arguments: Dict[str, Any], key: str) -> str:
    edits = arguments.get("edits")
    if not isinstance(edits, list):
        return ""
    return "".join(edit.get(key, "") for edit in edits if isinstance(edit, dict))


def _file_action_payload(
    tool_name: str | None,
    arguments: Dict[str, Any],
    result_preview: Any,
) -> Optional[Dict[str, Any]]:
    """Build an ActionTrace payload for Hermes file tools."""
    if tool_name in _FILE_WRITE_TOOLS:
        content = _as_text(arguments.get("content"))
        return {
            "action_type": "file.write",
            "file_path": _file_path_from_args(arguments),
            "file_operation": "write",
            "bytes_affected": len(content),
            "after_hash": _sha256_hex(content),
        }

    if tool_name in _FILE_PATCH_TOOLS:
        before_content = _as_text(
            arguments.get("old_string") or _joined_edit_strings(arguments, "old_string")
        )
        after_content = _as_text(
            arguments.get("new_string") or _joined_edit_strings(arguments, "new_string")
        )
        return {
            "action_type": "file.edit",
            "file_path": _file_path_from_args(arguments),
            "file_operation": "edit",
            "bytes_affected": len(after_content),
            "before_hash": _sha256_hex(before_content),
            "after_hash": _sha256_hex(after_content),
        }

    if tool_name in _FILE_READ_TOOLS:
        parsed_result = _parse_tool_result(result_preview)
        content = _as_text(parsed_result.get("content") or parsed_result.get("output"))
        return {
            "action_type": "file.read",
            "file_path": _file_path_from_args(arguments),
            "file_operation": "read",
            "bytes_affected": len(content),
            "after_hash": _sha256_hex(content),
        }

    return None


def _command_action_payload(
    arguments: Dict[str, Any],
    result_preview: Any,
) -> Dict[str, Any]:
    parsed_result = _parse_tool_result(result_preview)
    stdout = parsed_result.get("stdout") or parsed_result.get("output") or ""
    stderr = parsed_result.get("stderr") or ""
    command = arguments.get("command")
    output = f"{stdout}\n{stderr}"
    return {
        "action_type": "terminal.command",
        "command": _public_command_value(
            command, parsed_result.get("exit_code"), output
        ),
        "command_hash": _sha256_hex(command) if isinstance(command, str) else None,
        "cwd": arguments.get("workdir"),
        "exit_code": parsed_result.get("exit_code"),
        "stdout_hash": _sha256_hex(stdout if isinstance(stdout, str) else str(stdout)),
        "stderr_hash": _sha256_hex(stderr if isinstance(stderr, str) else str(stderr)),
    }


def _tool_action_payload(
    tool_name: str | None,
    arguments: Dict[str, Any],
    result_preview: Any,
) -> Optional[Dict[str, Any]]:
    if tool_name in _COMMAND_TOOLS:
        return _command_action_payload(arguments, result_preview)
    return _file_action_payload(tool_name, arguments, result_preview)


def _fallback_call_id(session_id: str, index: int) -> str:
    """Build a deterministic, session-scoped fallback call ID under legacy DB limits."""
    candidate = f"{session_id}:tool_{index}"
    if len(candidate) <= 64:
        return candidate
    return f"tool_{_sha256_hex(candidate)[:59]}"


def _redacted_receipt_value(value: Any) -> Any:
    """Redact public signed-receipt payload values before persistence."""
    return redact_value(value)


def _omitted_text_summary(value: Any) -> str | None:
    """Return a non-content summary for text that must not enter public receipts."""
    if value is None:
        return None
    text = (
        value
        if isinstance(value, str)
        else json.dumps(value, sort_keys=True, default=str)
    )
    return f"[omitted:sha256:{_sha256_hex(text)}:length:{len(text)}]"


def _public_command_value(
    command: Any, exit_code: Optional[int], output: str = ""
) -> str | None:
    """Preserve only verification commands; hide arbitrary shell text from public receipts."""
    if not isinstance(command, str):
        return None
    verification = _classify_verification_command(command, exit_code, output)
    return command if verification.get("is_verification") else None


def _public_tool_arguments(
    tool_name: str | None,
    arguments: Dict[str, Any],
    *,
    exit_code: Optional[int] = None,
    output: str = "",
) -> Dict[str, Any]:
    """Build a public-safe tool argument summary without raw content bodies."""
    if tool_name in _COMMAND_TOOLS:
        command = arguments.get("command")
        return {
            "command": _public_command_value(command, exit_code, output),
            "command_hash": _sha256_hex(command) if isinstance(command, str) else None,
            "workdir": arguments.get("workdir"),
            "content_redaction": "omitted_non_verification_command"
            if _public_command_value(command, exit_code, output) is None
            else "verification_command_preserved",
        }

    public: Dict[str, Any] = {}
    for key in ("path", "file_path", "offset", "limit"):
        if key in arguments:
            public[key] = arguments[key]
    omitted_fields = sorted(
        key for key in arguments if key not in public and arguments.get(key) is not None
    )
    if omitted_fields:
        public["omitted_fields"] = omitted_fields
        public["content_redaction"] = "omitted"
    return public


def _public_tool_result_summary(result_preview: Any) -> Dict[str, Any]:
    """Summarize tool result shape/size without embedding raw output/content."""
    if result_preview is None:
        return {"preview": None, "length": None, "content_redaction": "none"}
    serialized = (
        result_preview
        if isinstance(result_preview, str)
        else json.dumps(result_preview, sort_keys=True, default=str)
    )
    return {
        "preview": "[omitted]",
        "length": len(serialized),
        "content_redaction": "omitted",
        "preview_hash": _sha256_hex(serialized),
    }


def _sha256_prefixed(value: Any) -> str:
    """Return a UATP-style sha256:<hex> digest for redacted structured state."""
    rendered = json.dumps(redact_value(value), sort_keys=True, default=str)
    return f"sha256:{_sha256_hex(rendered)}"


def _session_goals(session: Dict, messages: List[Dict]) -> List[str]:
    """Build audit-safe goals without embedding raw user text in public receipts."""
    goals: List[str] = []
    title_summary = _omitted_text_summary(session.get("title"))
    if title_summary:
        goals.append(f"session_title:{title_summary}")

    first_user_message = next(
        ((msg.get("content") or "") for msg in messages if msg.get("role") == "user"),
        None,
    )
    trigger_summary = _omitted_text_summary(first_user_message)
    if trigger_summary and trigger_summary not in goals:
        goals.append(f"trigger:{trigger_summary}")
    return goals


def _safe_list(value: Any) -> List[Any]:
    return value if isinstance(value, list) else []


def _safe_digest(value: Any) -> str:
    if isinstance(value, str):
        if re.fullmatch(r"sha256:[a-f0-9]{64}", value):
            return value
        if re.fullmatch(r"[a-f0-9]{64}", value):
            return f"sha256:{value}"
    return _sha256_prefixed(value)


def _safe_loaded_skills(value: Any) -> List[Dict[str, Any]]:
    """Normalize Hermes skill state to schema-safe, non-content skill refs."""
    safe: List[Dict[str, Any]] = []
    for index, item in enumerate(_safe_list(value)):
        if isinstance(item, dict):
            content_hash = item.get("content_hash")
            name = item.get("name") or item.get("skill") or f"skill_{index}"
        else:
            content_hash = None
            name = str(item)
        safe.append(
            {
                "name_hash": _sha256_prefixed(name),
                "content_hash": _safe_digest(content_hash or name),
            }
        )
    return safe


def _safe_path_summaries(value: Any) -> List[str]:
    """Represent local paths as opaque digests so public receipts do not leak them."""
    summaries: List[str] = []
    for item in _safe_list(value):
        summaries.append(_omitted_text_summary(item) or "[omitted:empty]")
    return summaries


def _environment_snapshot_payload(
    session_id: str,
    session: Dict,
    tool_invocations: List[Dict[str, Any]],
    *,
    model: Optional[str],
    platform: str,
    timestamp: datetime,
) -> Dict[str, Any]:
    """Capture runtime context as hashes and bounded metadata, not raw env/config."""
    enabled_tools = sorted(
        invocation["tool"]
        for invocation in tool_invocations
        if isinstance(invocation.get("tool"), str)
    )
    cwd = session.get("working_directory") or session.get("cwd") or os.getcwd()
    env_fingerprint = {
        "hermes_home": str(HERMES_HOME),
        "uatp_root": str(UATP_ROOT),
        "platform": session.get("source", platform),
        "model": model or session.get("model"),
        "model_provider": session.get("model_provider"),
    }
    return {
        "snapshot_id": f"{session_id}:environment:0",
        "working_directory": _omitted_text_summary(cwd) or "[omitted:empty]",
        "env_vars_hash": _sha256_prefixed(env_fingerprint),
        "git_branch": session.get("git_branch"),
        "git_commit_hash": session.get("git_commit_hash"),
        "git_dirty": session.get("git_dirty"),
        "open_files": _safe_path_summaries(session.get("open_files")),
        "system_load": session.get("system_load"),
        "memory_available_gb": session.get("memory_available_gb"),
        "timestamp": timestamp,
        "agent_framework": "hermes",
        "adapter": "hermes_capture",
        "model_provider": session.get("model_provider"),
        "model": model or session.get("model"),
        "enabled_tools": enabled_tools,
        "enabled_toolsets": _safe_list(session.get("enabled_toolsets")),
        "loaded_skills": _safe_loaded_skills(session.get("loaded_skills")),
        "platform": session.get("source", platform),
        "gateway_source": _omitted_text_summary(session.get("gateway_source")),
        "terminal_backend": _omitted_text_summary(session.get("terminal_backend")),
    }


def _decision_payload_for_tool_invocation(
    session_id: str,
    invocation: Dict[str, Any],
    index: int,
    *,
    session: Dict,
    timestamp: datetime,
) -> Dict[str, Any]:
    """Build an audit-safe decision point for a tool choice.

    Do not inline raw private chain-of-thought. If Hermes captured reasoning,
    bind it as a digest while keeping the public reasoning to the externally
    auditable choice: which tool was selected at this step.
    """
    tool_name = invocation.get("tool") or "unknown"
    reasoning_before = invocation.get("reasoning_before") or ""
    call_id = invocation.get("call_id") or _fallback_call_id(session_id, index)
    payload = {
        "decision_id": f"{session_id}:decision:{index}",
        "step_index": index,
        "decision_summary": f"Selected tool `{tool_name}` for the next verifiable agent action.",
        "alternatives_considered": [],
        "selected_action": f"tool_call:{tool_name}",
        "confidence": None,
        "context_summary": _omitted_text_summary(session.get("title")),
        "constraints_applied": [
            "public receipts omit raw user/tool content by default",
            "artifact bodies are content-addressed and redacted where needed",
        ],
        "timestamp": timestamp,
        "evidence_refs": [call_id],
        "uncertainty_factors": [],
    }
    if reasoning_before:
        payload["reasoning_digest"] = _sha256_prefixed(reasoning_before)
    return payload


def _tool_status(invocation: Dict[str, Any], parsed_result: Dict[str, Any]) -> str:
    exit_code = parsed_result.get("exit_code")
    if isinstance(exit_code, str) and exit_code.strip().lstrip("-").isdigit():
        exit_code = int(exit_code.strip())
    if isinstance(exit_code, int) and exit_code != 0:
        return "error"
    if parsed_result.get("error") or invocation.get("error_message"):
        return "error"
    raw_status = str(invocation.get("status") or "").lower()
    status_map = {
        "success": "success",
        "succeeded": "success",
        "completed": "success",
        "complete": "success",
        "ok": "success",
        "pending": "pending",
        "running": "pending",
        "timeout": "timeout",
        "timed_out": "timeout",
        "error": "error",
        "failed": "error",
        "failure": "error",
    }
    if raw_status in status_map:
        return status_map[raw_status]
    return "success"


def _typed_hash_value(value: Any) -> Any:
    """Normalize `sha256:<hex>` digests for legacy typed columns sized to 64 chars."""
    if isinstance(value, str) and re.fullmatch(r"sha256:[a-f0-9]{64}", value):
        return value.removeprefix("sha256:")
    return value


def _build_event_native_receipt_bundle(
    session_id: str,
    session: Dict,
    messages: List[Dict],
    tool_invocations: List[Dict[str, Any]],
    *,
    model: Optional[str] = None,
    platform: str = "hermes-cli",
    signer: Optional[Ed25519ReceiptSigner] = None,
    artifact_store: Optional[ArtifactStore] = None,
) -> Dict[str, Any]:
    """Build signed framework-neutral receipts for a Hermes capture."""
    now = datetime.now(timezone.utc)
    started_at = _ts_from_epoch(session.get("started_at")) or now
    ended_at = (
        _ts_from_epoch(session.get("ended_at"))
        or _ts_from_epoch(session.get("updated_at"))
        or max(
            (_ts_from_epoch(msg.get("timestamp")) or started_at for msg in messages),
            default=started_at,
        )
    )

    first_user_message = next(
        ((msg.get("content") or "") for msg in messages if msg.get("role") == "user"),
        None,
    )
    safe_title = _omitted_text_summary(session.get("title"))

    events: List[AgentReceiptEvent] = [
        SessionStarted(
            event_id=f"{session_id}:session_started",
            session_id=session_id,
            adapter_name="hermes",
            agent_name="Hermes",
            timestamp=started_at,
            parent_event_hash=None,
            actor="system",
            payload={
                "agent_version": session.get("agent_version"),
                "platform": session.get("source", platform),
                "model_provider": session.get("model_provider"),
                "model": model or session.get("model"),
                "trigger_message": _omitted_text_summary(first_user_message),
                "trigger_source": "hermes_state_db",
                "goals": _session_goals(session, messages),
                "metadata": {
                    "title": safe_title,
                    "message_count": len(messages),
                },
            },
            redaction_summary={"secrets_removed": 0, "content_omitted": True},
            trust_level="local",
        )
    ]

    receipt_artifact_store = artifact_store or _get_agent_receipt_artifact_store()

    events.append(
        EnvironmentSnapshotEvent(
            event_id=f"{session_id}:environment_snapshot:0",
            session_id=session_id,
            adapter_name="hermes",
            agent_name="Hermes",
            timestamp=started_at,
            parent_event_hash=None,
            actor="system",
            payload=_environment_snapshot_payload(
                session_id,
                session,
                tool_invocations,
                model=model,
                platform=platform,
                timestamp=started_at,
            ),
            redaction_summary={"secrets_removed": 0, "content_omitted": True},
            trust_level="local",
        )
    )

    action_event_count = 0
    decision_event_count = 0

    for index, invocation in enumerate(tool_invocations):
        arguments = _parse_args(invocation.get("arguments"))
        if arguments is None:
            arguments = {"raw_arguments": invocation.get("arguments") or ""}

        artifact_refs: Dict[str, Any] = {}
        tool_name = invocation.get("tool")

        if tool_name in _COMMAND_TOOLS:
            parsed_result = _parse_tool_result(invocation.get("result_preview"))
            output = parsed_result.get("output") or parsed_result.get("stdout") or ""
            artifact_refs["stdout"] = _store_redacted_text_artifact(
                receipt_artifact_store,
                output,
            )
        elif tool_name in _FILE_WRITE_TOOLS:
            content = arguments.get("content")
            if content is not None:
                artifact_refs["content_after"] = _store_redacted_text_artifact(
                    receipt_artifact_store,
                    content,
                )
        elif tool_name in _FILE_PATCH_TOOLS:
            for ref_key, argument_key in (
                ("old_string", "old_string"),
                ("new_string", "new_string"),
                ("patch", "patch"),
            ):
                content = arguments.get(argument_key)
                if content is not None:
                    artifact_refs[ref_key] = _store_redacted_text_artifact(
                        receipt_artifact_store,
                        content,
                    )

            edits = arguments.get("edits")
            if isinstance(edits, list):
                edit_refs = []
                for edit in edits:
                    if not isinstance(edit, dict):
                        continue
                    refs_for_edit: Dict[str, Any] = {}
                    for ref_key, argument_key in (
                        ("old_string", "old_string"),
                        ("new_string", "new_string"),
                    ):
                        content = edit.get(argument_key)
                        if content is not None:
                            refs_for_edit[ref_key] = _store_redacted_text_artifact(
                                receipt_artifact_store,
                                content,
                            )
                    if refs_for_edit:
                        edit_refs.append(refs_for_edit)
                if edit_refs:
                    artifact_refs["edits"] = edit_refs
        elif tool_name in _FILE_READ_TOOLS:
            parsed_result = _parse_tool_result(invocation.get("result_preview"))
            content = parsed_result.get("content") or parsed_result.get("output") or ""
            if content:
                artifact_refs["content_read"] = _store_redacted_text_artifact(
                    receipt_artifact_store,
                    content,
                )

        started_timestamp = _ts_from_iso(invocation.get("timestamp")) or started_at
        completed_timestamp = (
            _ts_from_iso(invocation.get("completed_timestamp")) or started_timestamp
        )
        parsed_result_for_public = _parse_tool_result(invocation.get("result_preview"))
        result_output = (
            parsed_result_for_public.get("output")
            or parsed_result_for_public.get("stdout")
            or ""
        )
        result_stderr = parsed_result_for_public.get("stderr") or ""
        combined_output = f"{result_output}\n{result_stderr}"
        public_arguments = _public_tool_arguments(
            tool_name,
            arguments,
            exit_code=parsed_result_for_public.get("exit_code"),
            output=combined_output,
        )
        public_result = _public_tool_result_summary(invocation.get("result_preview"))
        duration_ms = int(
            (completed_timestamp - started_timestamp).total_seconds() * 1000
        )
        payload = {
            "call_id": invocation.get("call_id")
            or _fallback_call_id(session_id, index),
            "tool_name": tool_name or "unknown",
            "tool_category": _tool_category(tool_name),
            "arguments": public_arguments,
            "result": public_result,
            "started_at": started_timestamp,
            "completed_at": completed_timestamp,
            "duration_ms": max(0, duration_ms),
            "status": _tool_status(invocation, parsed_result_for_public),
            "error_message": invocation.get("error_message")
            or parsed_result_for_public.get("error"),
            "step_index": index,
        }
        if artifact_refs:
            payload["artifact_refs"] = artifact_refs

        events.append(
            DecisionPointEvent(
                event_id=f"{session_id}:decision_point:{index}",
                session_id=session_id,
                adapter_name="hermes",
                agent_name="Hermes",
                timestamp=started_timestamp,
                parent_event_hash=None,
                actor="assistant",
                payload=_decision_payload_for_tool_invocation(
                    session_id,
                    invocation,
                    index,
                    session=session,
                    timestamp=started_timestamp,
                ),
                redaction_summary={"secrets_removed": 0, "content_omitted": True},
                trust_level="local",
            )
        )
        decision_event_count += 1

        events.append(
            ToolCallCompleted(
                event_id=f"{session_id}:tool_completed:{index}",
                session_id=session_id,
                adapter_name="hermes",
                agent_name="Hermes",
                timestamp=completed_timestamp,
                parent_event_hash=None,
                actor="assistant",
                payload=payload,
                redaction_summary={"secrets_removed": 0, "content_omitted": True},
                trust_level="local",
            )
        )

        action_payload = _tool_action_payload(
            tool_name,
            arguments,
            invocation.get("result_preview"),
        )

        if action_payload is not None:
            action_event_count += 1
            events.append(
                ActionTraceEvent(
                    event_id=f"{session_id}:action_trace:{index}",
                    session_id=session_id,
                    adapter_name="hermes",
                    agent_name="Hermes",
                    timestamp=completed_timestamp,
                    parent_event_hash=None,
                    actor="assistant",
                    payload={
                        "action_id": f"{session_id}:action:{index}",
                        "tool_call_id": payload["call_id"],
                        "executed_at": completed_timestamp,
                        "duration_ms": payload.get("duration_ms") or 0,
                        **action_payload,
                    },
                    redaction_summary={"secrets_removed": 0, "content_omitted": True},
                    trust_level="local",
                )
            )

    events.append(
        SessionEnded(
            event_id=f"{session_id}:session_ended",
            session_id=session_id,
            adapter_name="hermes",
            agent_name="Hermes",
            timestamp=ended_at,
            parent_event_hash=None,
            actor="system",
            payload={
                "status": "completed",
                "tool_call_count": len(tool_invocations),
                "action_count": action_event_count,
                "decision_count": decision_event_count,
                "total_duration_ms": int(
                    (ended_at - started_at).total_seconds() * 1000
                ),
                "outcome_summary": safe_title,
            },
            redaction_summary={"secrets_removed": 0, "content_omitted": True},
            trust_level="local",
        )
    )

    receipt_signer = signer or _get_agent_receipt_signer()
    return build_signed_receipt_bundle(events, receipt_signer)


def _extract_topics(messages: List[Dict]) -> List[str]:
    """Pull rough topics from user messages."""
    user_text = " ".join(
        (m.get("content") or "")[:500] for m in messages if m["role"] == "user"
    ).lower()

    stop = {
        "the",
        "a",
        "an",
        "is",
        "it",
        "to",
        "and",
        "or",
        "of",
        "in",
        "for",
        "on",
        "with",
        "that",
        "this",
        "can",
        "you",
        "i",
        "my",
        "me",
        "do",
        "be",
        "have",
        "has",
        "had",
        "was",
        "were",
        "are",
        "not",
        "but",
        "so",
        "if",
        "at",
        "from",
        "by",
        "as",
        "up",
        "out",
        "about",
        "just",
        "what",
        "how",
        "all",
        "its",
        "let",
        "yes",
        "no",
        "ok",
        "make",
        "see",
        "get",
        "would",
        "could",
        "should",
        "will",
        "there",
        "here",
        "also",
        "then",
    }
    words = [w.strip(".,!?()[]{}\"'`") for w in user_text.split()]
    words = [w for w in words if len(w) > 2 and w not in stop and w.isalpha()]

    return [w for w, _ in Counter(words).most_common(8)]


def _convert_to_uatp_objects(
    session_id: str,
    session: Dict,
    messages: List[Dict],
    platform: str = "hermes-cli",
):
    """Convert Hermes session data into UATP ConversationMessage/Session objects."""
    ConversationMessage, ConversationSession = _get_capture_classes()
    detector = _get_signal_detector()

    now = datetime.now(timezone.utc)
    started = _ts_from_epoch(session.get("started_at")) or now

    # Run signal detection on user messages
    previous_user_msgs = []
    previous_assistant_response = None
    conv_messages = []

    for i, msg in enumerate(messages):
        role = msg["role"]
        content = msg.get("content") or ""
        visible_content = content
        ts = _ts_from_epoch(msg.get("timestamp")) or now

        # Only user and assistant messages map to ConversationMessage.
        # Tool messages get folded into the preceding assistant context.
        if role not in ("user", "assistant"):
            continue

        # For assistant messages, prepend the extended thinking if available.
        # RichCaptureEnhancer only sees ConversationMessage.content, so the
        # thinking must ride through the enhancer in-band, then build_capsule()
        # splits it back into separate `thinking` fields. Do not drop
        # reasoning-only assistant turns — those are valid reasoning steps.
        reasoning = msg.get("reasoning") or ""
        if role == "assistant" and reasoning.strip():
            content = f"[THINKING]\n{reasoning.strip()}\n[/THINKING]"
            if (visible_content or "").strip():
                content = f"{content}\n\n{visible_content.strip()}"

        # Skip assistant turns only when both visible content and thinking are
        # empty. Tool-dispatch turns with reasoning still matter for the action
        # graph; empty dispatch shells do not.
        if role == "assistant" and not content.strip() and not reasoning.strip():
            continue

        signal_type = "neutral"
        references_previous = False
        sentiment_delta = 0.0

        if role == "user" and content.strip():
            signal = detector.detect_signal(
                content, previous_user_msgs, "user", previous_assistant_response
            )
            signal_type = signal.signal_type
            references_previous = signal.references_previous
            sentiment_delta = signal.sentiment_delta

            # -----------------------------------------------------------------
            # Hermes signal guards — post-process detector output to fix false
            # positives that are common in CLI usage but rare in chat.
            # -----------------------------------------------------------------
            matched_phrases = signal.matched_phrases or []
            lower = content.lower().strip()
            words = lower.split()
            word_count = len(words)
            pa_len = len(previous_assistant_response or "")

            # ---- Guard A: "ok"/"okay" discourse markers ----
            # Real acceptances are short acknowledgments with gratitude.
            # Directives disguised as "ok" are the #1 false positive.
            if signal_type == "acceptance" and (
                lower.startswith("ok") or lower.startswith("okay")
            ):
                gratitude = (
                    "thanks",
                    "thank you",
                    "perfect",
                    "great",
                    "awesome",
                    "cool",
                    "nice",
                    "good",
                    "sounds good",
                    "makes sense",
                    "got it",
                    "i see",
                    "appreciate",
                )
                has_gratitude = any(g in lower for g in gratitude)
                directive_verbs = (
                    "fix",
                    "change",
                    "push",
                    "run",
                    "look",
                    "check",
                    "add",
                    "remove",
                    "delete",
                    "update",
                    "create",
                    "build",
                    "launch",
                    "audit",
                    "sweep",
                    "commit",
                    "merge",
                    "pull",
                    "apply",
                    "implement",
                    "write",
                    "edit",
                    "move",
                    "replace",
                    "restore",
                    "reset",
                    "kill",
                    "stop",
                    "start",
                    "restart",
                    "upload",
                    "download",
                    "generate",
                    "make",
                    "set",
                    "configure",
                    "deploy",
                    "verify",
                    "test",
                    "go",
                    "do",
                )
                has_directive = any(w in directive_verbs for w in words)
                if has_directive or (word_count > 5 and not has_gratitude):
                    signal_type = "neutral"
                    references_previous = False

            # ---- Guard B: substring-only acceptance false positives ----
            # The detector does substring matching on phrases like "great",
            # "fixed", "cool", "nice". In long CLI messages these appear inside
            # completely unrelated statements and create massive noise.
            if signal_type == "acceptance":
                pattern_triggered = any(
                    p.startswith("pattern:") for p in matched_phrases
                )
                phrase_triggered = any(
                    not p.startswith("pattern:") for p in matched_phrases
                )

                # If triggered ONLY by substring phrases (not regex), be very skeptical
                if phrase_triggered and not pattern_triggered:
                    if word_count > 10:
                        signal_type = "neutral"
                        references_previous = False
                    elif "?" in lower:
                        signal_type = "neutral"
                        references_previous = False
                    else:
                        # Medium length: require it starts with an acceptance word
                        if not re.search(
                            r"^(yes|yep|yeah|yea|sure|ok|okay|right|done|perfect|thanks|thank you|great|awesome|excellent|nice|cool|looks good|sounds good|it works|working now|fixed|solved|got it|makes sense|do it|go ahead|ship it|lgtm)\b",
                            lower,
                        ):
                            signal_type = "neutral"
                            references_previous = False

            # ---- Guard C: soft_rejection on legitimate follow-ups ----
            # Soft rejection means the user IGNORED the assistant. In CLI usage
            # this is almost never true — users pivot, clarify, or give new tasks.
            if signal_type == "soft_rejection":
                # Questions are never rejections
                if "?" in lower:
                    signal_type = "neutral"
                    references_previous = True
                # Bug reports are never rejections
                bug_phrases = (
                    "isn't",
                    "isnt",
                    "not working",
                    "doesn't work",
                    "doesnt work",
                    "didn't work",
                    "didnt work",
                    "still broken",
                    "still not",
                    "is gone",
                    "missing",
                    "can't find",
                    "cant find",
                    "error",
                    "bug",
                    "issue",
                    "problem",
                    "wrong",
                    "broken",
                    "fail",
                    "failed",
                    "doesn't",
                    "doesnt",
                    "didn't",
                    "didnt",
                    "can't",
                    "cant",
                    "won't",
                    "wont",
                )
                if any(p in lower for p in bug_phrases):
                    signal_type = "neutral"
                    references_previous = True
                # Directives are never rejections
                directive_starters = (
                    "lets ",
                    "let's ",
                    "please ",
                    "can you ",
                    "could you ",
                    "would you ",
                    "will you ",
                    "go ahead",
                    "do ",
                    "make ",
                    "run ",
                    "check ",
                    "verify ",
                    "push ",
                    "pull ",
                    "commit ",
                    "merge ",
                    "add ",
                    "remove ",
                    "delete ",
                    "update ",
                    "create ",
                    "build ",
                    "launch ",
                    "audit ",
                    "sweep ",
                    "apply ",
                    "implement ",
                    "write ",
                    "edit ",
                    "move ",
                    "replace ",
                    "restore ",
                    "reset ",
                    "kill ",
                    "stop ",
                    "start ",
                    "restart ",
                    "upload ",
                    "download ",
                    "generate ",
                    "set ",
                    "configure ",
                    "deploy ",
                    "test ",
                )
                if any(lower.startswith(w) for w in directive_starters):
                    signal_type = "neutral"
                    references_previous = True
                # Deferrals are neutral
                if lower in (
                    "whatever you think",
                    "whatever you think is best",
                    "up to you",
                    "you decide",
                    "your call",
                    "whatever",
                ):
                    signal_type = "neutral"
                    references_previous = True
                # Factual statements about state are neutral
                if any(
                    lower.startswith(w)
                    for w in (
                        "there are ",
                        "there is ",
                        "i have ",
                        "we have ",
                        "it has ",
                        "this has ",
                        "there's ",
                    )
                ):
                    signal_type = "neutral"
                    references_previous = True

            # ---- Guard D: catch missed corrections ----
            # Short imperatives after a long assistant response are very often
            # terse corrections that the detector missed.
            if signal_type == "neutral" and pa_len > 500 and word_count <= 5:
                correction_imperatives = (
                    "fix it",
                    "fix that",
                    "fix this",
                    "change it",
                    "change that",
                    "change this",
                    "do it again",
                    "try again",
                    "redo it",
                    "redo that",
                    "not quite",
                    "almost but",
                    "close but",
                    "still wrong",
                    "wrong",
                    "no",
                    "nope",
                    "not that",
                    "not this",
                    "not it",
                    "bad",
                    "worse",
                    "terrible",
                    "awful",
                )
                if any(lower.startswith(c) for c in correction_imperatives):
                    signal_type = "correction"
                    references_previous = True
                    sentiment_delta = -0.4

            # ---- Guard E: intent restatements are corrections ----
            # Messages that explicitly restate what the user wanted after the
            # assistant misunderstood are corrections, even if phrased politely.
            if signal_type == "neutral" and pa_len > 300:
                if re.search(
                    r"^(i asked|i meant|i said|i was asking|i was talking|i want|i need|the issue is|what i want|what i need|what i asked)",
                    lower,
                ):
                    signal_type = "correction"
                    references_previous = True
                    sentiment_delta = -0.3

            previous_user_msgs.append(content)
            # Reset after user message; next assistant will set this
            previous_assistant_response = None

        if role == "assistant" and visible_content.strip():
            previous_assistant_response = visible_content

        conv_msg = ConversationMessage(
            role=role,
            content=content,
            timestamp=ts,
            message_id=f"hermes_{session_id}_{i}",
            session_id=session_id,
            token_count=msg.get("token_count"),
            model_info=session.get("model"),
            signal_type=signal_type,
            references_previous=references_previous,
            sentiment_delta=sentiment_delta,
        )
        # Attach raw reasoning as custom attribute for downstream use
        conv_msg._hermes_thinking = (
            reasoning if (role == "assistant" and reasoning) else None
        )
        conv_messages.append(conv_msg)

    # Build session object
    total_tokens = (session.get("input_tokens") or 0) + (
        session.get("output_tokens") or 0
    )
    topics = _extract_topics(messages)

    # Aggregate non-neutral signals for downstream DPO/quality analysis
    sig_counts = Counter(
        m.signal_type
        for m in conv_messages
        if m.role == "user" and m.signal_type != "neutral"
    )
    total_user = len([m for m in conv_messages if m.role == "user"])
    feedback_signals = None
    if sig_counts:
        feedback_signals = {
            "correction_count": sig_counts.get("correction", 0),
            "requery_count": sig_counts.get("requery", 0),
            "refinement_count": sig_counts.get("refinement", 0),
            "acceptance_count": sig_counts.get("acceptance", 0),
            "abandonment_count": sig_counts.get("abandonment", 0),
            "soft_rejection_count": sig_counts.get("soft_rejection", 0),
            "code_execution_count": sig_counts.get("code_execution", 0),
            "total_non_neutral": sum(sig_counts.values()),
            "correction_rate": round(sig_counts.get("correction", 0) / total_user, 4)
            if total_user
            else 0.0,
            "acceptance_rate": round(sig_counts.get("acceptance", 0) / total_user, 4)
            if total_user
            else 0.0,
            "signal_breakdown": dict(sig_counts),
        }

    conv_session = ConversationSession(
        session_id=session_id,
        user_id="kay",
        start_time=started,
        platform=platform,
        end_time=now,
        messages=conv_messages,
        significance_score=0.0,  # will be recalculated by the enhancer
        total_tokens=total_tokens,
        topics=topics,
    )
    # Attach feedback summary for build_capsule to consume
    conv_session._hermes_feedback_signals = feedback_signals

    return conv_session


# ---------------------------------------------------------------------------
# Build capsule via RichCaptureEnhancer
# ---------------------------------------------------------------------------


def build_capsule(
    session_id: str,
    session: Dict,
    messages: List[Dict],
    model: Optional[str] = None,
    platform: str = "hermes-cli",
) -> Dict[str, Any]:
    """Build a full-quality UATP capsule through RichCaptureEnhancer."""

    conv_session = _convert_to_uatp_objects(session_id, session, messages, platform)

    RichCaptureEnhancer = _get_rich_enhancer()
    capsule = RichCaptureEnhancer.create_capsule_from_session_with_rich_metadata(
        conv_session, user_id="kay"
    )

    # Override type to distinguish from Claude Code captures
    capsule["type"] = "hermes-capture"
    capsule["payload"]["capsule_type"] = "hermes-capture"

    # --- Thinking field separation ---
    # Walk reasoning_steps and split out [THINKING] blocks into separate fields
    reasoning_steps = capsule.get("payload", {}).get("reasoning_steps", [])
    for step in reasoning_steps:
        content = step.get("content") or step.get("reasoning") or ""
        if "[THINKING]" in content:
            thinking_match = re.search(
                r"\[THINKING\]\s*(.*?)\s*\[/THINKING\]", content, re.DOTALL
            )
            if thinking_match:
                step["thinking"] = thinking_match.group(1).strip()
                cleaned = re.sub(
                    r"\[THINKING\].*?\[/THINKING\]\s*", "", content, flags=re.DOTALL
                ).strip()
                if "content" in step:
                    step["content"] = cleaned
                if "reasoning" in step:
                    step["reasoning"] = cleaned

    # Fix message counts — RichCaptureEnhancer doesn't populate these
    total_msgs = len(messages)
    user_msgs = [m for m in messages if m["role"] == "user"]
    asst_msgs = [m for m in messages if m["role"] == "assistant"]
    tool_msgs = [m for m in messages if m["role"] == "tool"]

    session_meta = capsule["payload"].setdefault("session_metadata", {})
    session_meta["message_count"] = total_msgs
    session_meta["user_message_count"] = len(user_msgs)
    session_meta["assistant_message_count"] = len(asst_msgs)
    session_meta["tool_message_count"] = len(tool_msgs)

    # Add Hermes-specific metadata that the Claude Code pipeline doesn't have
    session_meta["hermes_session_id"] = session_id
    session_meta["hermes_platform"] = session.get("source", platform)
    session_meta["hermes_model"] = model or session.get("model")
    session_meta["hermes_title"] = session.get("title")
    session_meta["input_tokens"] = session.get("input_tokens")
    session_meta["output_tokens"] = session.get("output_tokens")
    session_meta["cache_read_tokens"] = session.get("cache_read_tokens")
    session_meta["tool_call_count"] = session.get("tool_call_count")

    # --- Tool call graph ---
    # Extract structured tool invocations with arguments and results.
    # This maps the AI's decision-making: what it chose to do and what happened.
    tool_invocations = []
    pending_calls = {}  # tool_call_id -> call info

    for msg in messages:
        # Assistant messages with tool_calls = the AI deciding to invoke tools
        if msg["role"] == "assistant" and msg.get("tool_calls"):
            try:
                calls = (
                    json.loads(msg["tool_calls"])
                    if isinstance(msg["tool_calls"], str)
                    else msg["tool_calls"]
                )
                for call in calls or []:
                    fn = call.get("function", {})
                    call_id = call.get("call_id") or call.get("id")
                    args_str = fn.get("arguments", "")
                    # Truncate very large arguments
                    if len(args_str) > 2000:
                        args_str = args_str[:2000] + "..."
                    invocation = {
                        "tool": fn.get("name"),
                        "call_id": call_id,
                        "arguments": args_str,
                        "timestamp": _ts_from_epoch(msg.get("timestamp")).isoformat()
                        if msg.get("timestamp")
                        else None,
                        "reasoning_before": (msg.get("reasoning") or "")[:500] or None,
                    }
                    tool_invocations.append(invocation)
                    if call_id:
                        pending_calls[call_id] = invocation
            except (json.JSONDecodeError, TypeError) as e:
                logger.warning("Failed to parse tool_calls in message: %s", e)

        # Tool messages = results, matched back to invocations
        if msg["role"] == "tool":
            call_id = msg.get("tool_call_id")
            content = msg.get("content") or ""
            result_summary = content[:500] + ("..." if len(content) > 500 else "")
            if call_id and call_id in pending_calls:
                pending_calls[call_id]["result_length"] = len(content)
                pending_calls[call_id]["result_preview"] = result_summary
                completed_ts = _ts_from_epoch(msg.get("timestamp"))
                pending_calls[call_id]["completed_timestamp"] = (
                    completed_ts.isoformat() if completed_ts else None
                )
            else:
                # Orphaned tool result
                completed_ts = _ts_from_epoch(msg.get("timestamp"))
                tool_invocations.append(
                    {
                        "tool": msg.get("tool_name"),
                        "call_id": call_id,
                        "result_length": len(content),
                        "result_preview": result_summary,
                        "timestamp": completed_ts.isoformat() if completed_ts else None,
                        "completed_timestamp": completed_ts.isoformat()
                        if completed_ts
                        else None,
                    }
                )

    if tool_invocations:
        # Tool usage summary
        tool_counts = Counter(t["tool"] for t in tool_invocations if t.get("tool"))
        capsule["payload"]["tool_call_graph"] = {
            "invocations": tool_invocations,
            "tool_frequency": dict(tool_counts.most_common()),
            "total_tool_calls": len(tool_invocations),
            "unique_tools": len(tool_counts),
        }

        # --- File artifact manifest (Phase H1.1) ---
        # Bind file operations to verifiable hashes so a reviewer can later
        # confirm what the agent wrote/patched/read.
        file_artifacts = _extract_file_artifacts(tool_invocations)
        command_artifacts = _extract_command_artifacts(tool_invocations)
        if file_artifacts or command_artifacts:
            artifacts = capsule["payload"].setdefault("artifacts", {})
        if file_artifacts:
            artifacts["files"] = file_artifacts
            artifacts["files_total"] = len(file_artifacts)
            artifacts["files_by_operation"] = dict(
                Counter(f["operation"] for f in file_artifacts).most_common()
            )
        if command_artifacts:
            artifacts["commands"] = command_artifacts
            artifacts["commands_total"] = len(command_artifacts)
            artifacts.update(_summarize_command_verifications(command_artifacts))

        capsule["payload"]["learning_receipt_v2"] = _build_learning_receipt_v2(
            tool_invocations,
            messages,
        )

    # --- Cost economics ---
    # Real compute cost data: token usage, caching efficiency, billing.
    input_tokens = session.get("input_tokens") or 0
    output_tokens = session.get("output_tokens") or 0
    cache_read = session.get("cache_read_tokens") or 0
    cache_write = session.get("cache_write_tokens") or 0
    reasoning_tokens = session.get("reasoning_tokens") or 0
    estimated_cost = session.get("estimated_cost_usd") or 0.0
    actual_cost = session.get("actual_cost_usd")

    total_input = input_tokens + cache_read
    cache_hit_rate = round(cache_read / total_input, 4) if total_input > 0 else 0.0

    capsule["payload"]["economics"] = {
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "cache_read_tokens": cache_read,
        "cache_write_tokens": cache_write,
        "reasoning_tokens": reasoning_tokens,
        "total_tokens": input_tokens + output_tokens + cache_read,
        "cache_hit_rate": cache_hit_rate,
        "estimated_cost_usd": estimated_cost,
        "actual_cost_usd": actual_cost,
        "billing_provider": session.get("billing_provider"),
        "billing_mode": session.get("billing_mode"),
    }

    # --- Extended thinking archive ---
    # Raw chain-of-thought from the model, separate from the content.
    # This is the unfiltered reasoning the model did before each response.
    thinking_turns = []
    for msg in messages:
        reasoning = msg.get("reasoning")
        if reasoning and msg["role"] == "assistant":
            thinking_turns.append(
                {
                    "timestamp": _ts_from_epoch(msg.get("timestamp")).isoformat()
                    if msg.get("timestamp")
                    else None,
                    "thinking": reasoning,
                    "thinking_length": len(reasoning),
                    "response_length": len(msg.get("content") or ""),
                    "had_tool_calls": bool(msg.get("tool_calls")),
                }
            )
    if thinking_turns:
        capsule["payload"]["extended_thinking"] = {
            "turns": thinking_turns,
            "total_thinking_chars": sum(t["thinking_length"] for t in thinking_turns),
            "total_response_chars": sum(t["response_length"] for t in thinking_turns),
            "thinking_to_response_ratio": round(
                sum(t["thinking_length"] for t in thinking_turns)
                / max(1, sum(t["response_length"] for t in thinking_turns)),
                2,
            ),
            "turns_with_thinking": len(thinking_turns),
            "turns_total": len([m for m in messages if m["role"] == "assistant"]),
        }

    # --- Session lineage ---
    parent = session.get("parent_session_id")
    if parent:
        session_meta = capsule["payload"].setdefault("session_metadata", {})
        session_meta["parent_session_id"] = parent
        session_meta["is_continuation"] = True

    # --- Tool result archive ---
    # Full tool results for context preservation.
    tool_archive = []
    for msg in messages:
        if msg["role"] == "tool":
            content = msg.get("content") or ""
            if len(content) > 3000:
                content = content[:3000] + f"... [{len(content)} chars total]"
            tool_archive.append(
                {
                    "role": "tool",
                    "tool_name": msg.get("tool_name"),
                    "tool_call_id": msg.get("tool_call_id"),
                    "content": content,
                    "timestamp": _ts_from_epoch(msg.get("timestamp")).isoformat()
                    if msg.get("timestamp")
                    else None,
                }
            )
    if tool_archive:
        session_meta = capsule["payload"].setdefault("session_metadata", {})
        prompt_ctx = session_meta.setdefault("prompt_context", {})
        prompt_ctx["tool_results"] = tool_archive

    # --- Feedback signal summary ---
    # Aggregate message-level signals for DPO extraction and quality analysis.
    # Purely additive — no existing code reads this field.
    feedback_signals = getattr(conv_session, "_hermes_feedback_signals", None)
    if feedback_signals:
        capsule["payload"]["feedback_signals"] = feedback_signals

    # --- Event-native signed receipt bundle ---
    # Preserve the existing rich Hermes capture shape while adding a framework-
    # neutral, offline-verifiable receipt chain for new provenance consumers.
    try:
        receipt_artifact_store = _get_agent_receipt_artifact_store()
        receipt_bundle = _build_event_native_receipt_bundle(
            session_id,
            session,
            messages,
            tool_invocations,
            model=model,
            platform=platform,
            artifact_store=receipt_artifact_store,
        )
        bundle_artifact_ref = receipt_artifact_store.store_json(
            receipt_bundle["public"],
            media_type="application/vnd.uatp.agent-receipts.bundle+json",
            redaction=_redaction_metadata(0),
        ).to_dict()
        capsule["payload"]["agent_receipts"] = receipt_bundle["public"]
        capsule["payload"]["agent_receipts_bundle_ref"] = bundle_artifact_ref
        capsule["payload"]["agent_receipts_status"] = {
            "status": "attached",
            "bundle_artifact_ref": bundle_artifact_ref,
        }
    except Exception as e:
        redacted_error = _redact_error_message(str(e))
        logger.warning(
            "Failed to build event-native agent receipts: %s", redacted_error
        )
        capsule["payload"]["agent_receipts_status"] = {
            "status": "failed",
            "error_type": type(e).__name__,
            "message": redacted_error,
        }

    return capsule


# ---------------------------------------------------------------------------
# Sign + write
# ---------------------------------------------------------------------------


def sign_capsule(capsule: Dict) -> Dict:
    """Sign the capsule with UATPCryptoV7 (Ed25519 + optional PQ)."""
    try:
        crypto = _get_crypto()
        verification = crypto.sign_capsule(capsule)
        capsule["verification"] = verification
        logger.info("Capsule signed: hash=%s", verification.get("hash", "?")[:24])
    except Exception as e:
        logger.warning("Crypto signing failed (%s), using hash-only", e)
        content_str = json.dumps(
            {k: v for k, v in capsule.items() if k != "verification"},
            sort_keys=True,
            separators=(",", ":"),
        )
        content_hash = hashlib.sha256(content_str.encode()).hexdigest()
        capsule["verification"] = {
            "signer": "hermes_capture",
            "hash": f"sha256:{content_hash}",
            "signature": None,
            "method": "hash_only",
            "note": f"Signing unavailable: {e}",
        }
    return capsule


def _agent_receipt_capsule_draft_rows(capsule: Dict) -> List[Dict[str, Any]]:
    """Build first-class capsule-table rows for embedded agent receipt drafts."""
    payload = capsule.get("payload", {})
    agent_receipts = payload.get("agent_receipts", {})
    capsule_drafts = agent_receipts.get("capsule_drafts", [])
    if not isinstance(capsule_drafts, list):
        return []

    parent_capsule_id = capsule["capsule_id"]
    bundle_ref = payload.get("agent_receipts_bundle_ref")
    chain_report = agent_receipts.get("chain_report", {})
    rows = []
    for index, draft in enumerate(capsule_drafts):
        if not isinstance(draft, dict):
            continue
        capsule_type = draft.get("capsule_type")
        if not capsule_type:
            continue
        draft_payload = deepcopy(draft)
        receipt_metadata = draft_payload.setdefault("receipt_metadata", {})
        if bundle_ref is not None:
            receipt_metadata["bundle_artifact_ref"] = bundle_ref
        receipt_metadata["parent_hermes_capsule_id"] = parent_capsule_id
        receipt_metadata["receipt_chain_report"] = chain_report

        rows.append(
            {
                "capsule_id": f"{parent_capsule_id}:agent_receipt:{index}:{capsule_type}",
                "capsule_type": capsule_type,
                "version": agent_receipts.get("schema_version", "agent_receipts.v1"),
                "timestamp": capsule["timestamp"],
                "status": capsule.get("status", "active"),
                "verification": {
                    "method": "agent_receipt_draft",
                    "parent_capsule_id": parent_capsule_id,
                    "bundle_artifact_ref": bundle_ref,
                    "chain_tip_hash": chain_report.get("chain_tip_hash"),
                },
                "parent_capsule_id": parent_capsule_id,
                "payload": draft_payload,
            }
        )
    return rows


def _insert_agent_receipt_capsule_drafts(
    conn: sqlite3.Connection, capsule: Dict
) -> int:
    """Persist agent receipt capsule drafts as first-class capsule rows."""
    rows = _agent_receipt_capsule_draft_rows(capsule)
    for row in rows:
        conn.execute(
            """
            INSERT INTO capsules (
                capsule_id, capsule_type, version, timestamp, status,
                verification, parent_capsule_id, payload
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT (capsule_id) DO NOTHING
            """,
            (
                row["capsule_id"],
                row["capsule_type"],
                row["version"],
                row["timestamp"],
                row["status"],
                json.dumps(row["verification"]),
                row["parent_capsule_id"],
                json.dumps(row["payload"]),
            ),
        )
    return len(rows)


def _sqlite_table_exists(conn: sqlite3.Connection, table_name: str) -> bool:
    return (
        conn.execute(
            "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = ?",
            (table_name,),
        ).fetchone()
        is not None
    )


def _typed_row_verification(row: Dict[str, Any]) -> Dict[str, Any]:
    return {
        **row["verification"],
        "method": "agent_receipt_typed_row",
    }


def _insert_agent_session_typed_row(
    conn: sqlite3.Connection, row: Dict[str, Any]
) -> None:
    payload = row["payload"].get("agent_session", {})
    conn.execute(
        """
        INSERT INTO agent_sessions (
            session_id, agent_type, agent_version, scheduler_type,
            trigger_message, trigger_source, user_id_hash, goals, status,
            tool_call_count, action_count, decision_count, started_at,
            completed_at, total_duration_ms, outcome_summary, error_message,
            verification, capsule_id, created_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            payload["session_id"],
            payload["agent_type"],
            payload.get("agent_version"),
            payload.get("scheduler_type"),
            payload.get("trigger_message"),
            payload.get("trigger_source"),
            payload.get("user_id_hash"),
            json.dumps(payload.get("goals", [])),
            payload["status"],
            payload.get("tool_call_count"),
            payload.get("action_count"),
            payload.get("decision_count"),
            payload["started_at"],
            payload.get("completed_at"),
            payload.get("total_duration_ms"),
            payload.get("outcome_summary"),
            payload.get("error_message"),
            json.dumps(_typed_row_verification(row)),
            row["capsule_id"],
            datetime.now(timezone.utc).isoformat(),
        ),
    )


def _insert_tool_call_typed_row(conn: sqlite3.Connection, row: Dict[str, Any]) -> None:
    payload = row["payload"].get("tool_call", {})
    conn.execute(
        """
        INSERT INTO tool_calls (
            call_id, session_id, tool_name, tool_category, tool_inputs,
            tool_outputs, started_at, completed_at, duration_ms, status,
            error_message, step_index, parent_call_id, verification,
            capsule_id, created_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            payload["call_id"],
            payload["session_id"],
            payload["tool_name"],
            payload["tool_category"],
            json.dumps(payload.get("tool_inputs")),
            json.dumps(payload.get("tool_outputs")),
            payload["started_at"],
            payload.get("completed_at"),
            payload.get("duration_ms"),
            payload["status"],
            payload.get("error_message"),
            payload["step_index"],
            payload.get("parent_call_id"),
            json.dumps(_typed_row_verification(row)),
            row["capsule_id"],
            datetime.now(timezone.utc).isoformat(),
        ),
    )


def _insert_action_trace_typed_row(
    conn: sqlite3.Connection, row: Dict[str, Any]
) -> None:
    payload = row["payload"].get("action_trace", {})
    conn.execute(
        """
        INSERT INTO action_traces (
            action_id, session_id, tool_call_id, action_type, command,
            exit_code, stdout_hash, stderr_hash, url, selector,
            browser_action, file_path, file_operation, bytes_affected,
            executed_at, duration_ms, verification, capsule_id, created_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            payload["action_id"],
            payload["session_id"],
            payload.get("tool_call_id"),
            payload["action_type"],
            payload.get("command"),
            payload.get("exit_code"),
            _typed_hash_value(payload.get("stdout_hash")),
            _typed_hash_value(payload.get("stderr_hash")),
            payload.get("url"),
            payload.get("selector"),
            payload.get("browser_action"),
            payload.get("file_path"),
            payload.get("file_operation"),
            payload.get("bytes_affected"),
            payload["executed_at"],
            payload["duration_ms"],
            json.dumps(_typed_row_verification(row)),
            row["capsule_id"],
            datetime.now(timezone.utc).isoformat(),
        ),
    )


def _insert_agent_receipt_typed_rows(conn: sqlite3.Connection, capsule: Dict) -> int:
    """Fan agent receipt capsule drafts into typed provenance tables when present."""
    rows = _agent_receipt_capsule_draft_rows(capsule)
    inserted = 0
    has_agent_sessions = _sqlite_table_exists(conn, "agent_sessions")
    has_tool_calls = _sqlite_table_exists(conn, "tool_calls")
    has_action_traces = _sqlite_table_exists(conn, "action_traces")
    for row in rows:
        if row["capsule_type"] == "agent_session" and has_agent_sessions:
            _insert_agent_session_typed_row(conn, row)
            inserted += 1
        elif row["capsule_type"] == "tool_call" and has_tool_calls:
            _insert_tool_call_typed_row(conn, row)
            inserted += 1
        elif row["capsule_type"] == "action_trace" and has_action_traces:
            _insert_action_trace_typed_row(conn, row)
            inserted += 1
    return inserted


def write_capsule(capsule: Dict) -> bool:
    """Write signed capsule to uatp_dev.db."""
    if not UATP_DB.exists():
        logger.error("uatp_dev.db not found at %s", UATP_DB)
        return False
    conn = sqlite3.connect(str(UATP_DB))
    try:
        # Session deduplication: check if capsule already exists for this session
        session_id = capsule.get("payload", {}).get("session_metadata", {}).get(
            "hermes_session_id"
        ) or capsule.get("payload", {}).get("session_metadata", {}).get("session_id")
        if session_id:
            existing = conn.execute(
                """SELECT capsule_id FROM capsules
                   WHERE json_extract(payload, '$.session_metadata.hermes_session_id') = ?
                      OR json_extract(payload, '$.session_metadata.session_id') = ?""",
                (session_id, session_id),
            ).fetchone()
            if existing:
                logger.info(
                    "Capsule already exists for session %s (capsule_id=%s), skipping",
                    session_id,
                    existing[0],
                )
                return True

        conn.execute(
            """
            INSERT INTO capsules (capsule_id, capsule_type, version, timestamp, status, verification, payload)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT (capsule_id) DO NOTHING
            """,
            (
                capsule["capsule_id"],
                capsule["type"],
                capsule["version"],
                capsule["timestamp"],
                capsule["status"],
                json.dumps(capsule["verification"]),
                json.dumps(capsule["payload"]),
            ),
        )
        _insert_agent_receipt_capsule_drafts(conn, capsule)
        _insert_agent_receipt_typed_rows(conn, capsule)
        conn.commit()
        rows = conn.total_changes
        logger.info(
            "Wrote capsule %s to uatp_dev.db (%d rows)", capsule["capsule_id"], rows
        )
        return rows > 0
    except (sqlite3.Error, OSError):
        logger.exception("Failed to write capsule to uatp_dev.db")
        return False
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------


def capture_session(
    session_id: str,
    model: Optional[str] = None,
    platform: str = "hermes-cli",
) -> Optional[Dict]:
    """Full pipeline: read session -> RichCaptureEnhancer -> sign -> write."""
    data = read_session(session_id)
    if not data:
        return None

    session = data["session"]
    messages = data["messages"]

    if len(messages) < MIN_MESSAGES:
        logger.info(
            "Session %s has only %d messages, skipping", session_id, len(messages)
        )
        return None

    capsule = build_capsule(
        session_id, session, messages, model=model, platform=platform
    )
    capsule = sign_capsule(capsule)
    written = write_capsule(capsule)

    if written:
        return capsule
    return None


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def main():
    logging.basicConfig(level=logging.INFO, format="%(message)s")

    if len(sys.argv) < 2:
        print("Usage: python3 hermes_capture.py <session_id>")
        print("       python3 hermes_capture.py --latest")
        print("       python3 hermes_capture.py --list")
        sys.exit(1)

    arg = sys.argv[1]

    if arg == "--list":
        sessions = list_recent_sessions(15)
        if not sessions:
            print("No sessions found.")
            return
        print(f"{'Session ID':<30} {'Messages':>8}  {'Model':<30} {'Title'}")
        print("-" * 100)
        for s in sessions:
            title = s.get("title") or ""
            print(
                f"{s['id']:<30} {s.get('message_count', 0):>8}  {(s.get('model') or '?'):<30} {title[:30]}"
            )
        return

    if arg == "--latest":
        sessions = list_recent_sessions(1)
        if not sessions:
            print("No sessions found.")
            sys.exit(1)
        session_id = sessions[0]["id"]
        print(f"Capturing latest session: {session_id}")
    else:
        session_id = arg

    result = capture_session(session_id)
    if result:
        payload = result["payload"]
        sig = result["verification"]
        meta = payload.get("session_metadata", {})
        feedback = payload.get("feedback_signals", {})

        print(f"\nCapsule created: {result['capsule_id']}")
        print(f"Type:            {result['type']}")
        print(f"Signed:          {sig.get('signature') is not None}")
        print(f"Hash:            {sig.get('hash', 'none')[:40]}...")
        print(f"Confidence:      {payload.get('confidence', '?')}")
        print(
            f"Quality grade:   {payload.get('quality_assessment', {}).get('quality_grade', 'n/a')}"
        )
        print(
            f"Trust posture:   {payload.get('trust_posture', {}).get('level', 'n/a')}"
        )
        print(f"Corrections:     {feedback.get('correction_count', 0)}")
        print(f"Acceptances:     {feedback.get('acceptance_count', 0)}")
        print(f"Topics:          {', '.join(meta.get('topics', [])[:5])}")

        # Show what rich fields are present
        rich_fields = [
            k
            for k in payload
            if k
            not in (
                "prompt",
                "reasoning_steps",
                "final_answer",
                "confidence",
                "model_used",
                "created_by",
                "session_metadata",
                "schema_version",
                "capsule_type",
            )
        ]
        if rich_fields:
            print(f"Rich metadata:   {', '.join(rich_fields)}")
    else:
        print("No capsule created (session too short or not found).")
        sys.exit(1)


if __name__ == "__main__":
    main()
