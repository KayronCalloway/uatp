"""
UATP MCP Capsule Builder
========================

Converts MCP tool calls into UATP capsules with evidence-class tagging.

Key design: separate proxy-observed facts from model-asserted context.

Evidence classes:
- observed   : hard facts the proxy can verify (timestamps, hashes, tool name)
- asserted   : self-reported by model or upstream (intent, confidence, rationale)
- derived    : computed by the gateway (latency, status classification)
- policy     : emitted by the policy engine (allow/deny, constraint checks)

Source layers:
- proxy  : gateway itself
- model  : upstream LLM or agent
- policy : policy engine
- human  : human-in-the-loop approvals or overrides

This distinction matters because it prevents critics from saying UATP
blurred hard evidence with self-reported narrative. Different trust
classes. Different evidentiary weight.
"""

from __future__ import annotations

import hashlib
import json
import logging
from datetime import datetime, timezone
from typing import Any

from src.integrations.mcp.policy_engine import PolicyResult
from src.integrations.mcp.store import CapsuleStore
from src.security.uatp_crypto_v7 import UATPCryptoV7

logger = logging.getLogger(__name__)


class CapsuleBuilder:
    """
    Builds UATP capsules for MCP tool calls, decisions, and refusals.
    """

    def __init__(
        self,
        store: CapsuleStore,
        crypto: UATPCryptoV7,
        signer_id: str = "uatp-mcp-gateway",
    ):
        self.store = store
        self.crypto = crypto
        self.signer_id = signer_id

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def emit_decision_point(
        self,
        session_id: str,
        selected_action: str,
        candidate_actions: list[str],
        trigger_message_hash: str | None,
        policy_checks: PolicyResult,
    ) -> str:
        """
        Emit a DECISION_POINT capsule.

        LIMITATION (MVP): The proxy only sees the selected action, not the
        full deliberation of the model. candidate_actions is usually a
        single-item list at the proxy boundary. Future versions can enrich
        this via client-side instrumentation or model introspection hooks.
        """
        capsule_id = self.store.generate_id("dec")

        payload = {
            "session_id": session_id,
            "trigger": {
                "source": "model_tool_selection",
                "message_hash": {
                    "value": trigger_message_hash,
                    "evidence_class": "observed",
                    "source_layer": "proxy",
                },
            },
            "decision": {
                "selected_action": {
                    "value": selected_action,
                    "evidence_class": "observed",
                    "source_layer": "proxy",
                },
                "candidate_actions": {
                    "value": candidate_actions,
                    "evidence_class": "asserted",
                    "source_layer": "model",
                    "limitation": "proxy_only_sees_selected_action",
                },
            },
            "policy": {
                "policy_version": {
                    "value": policy_checks.policy_version,
                    "evidence_class": "policy",
                    "source_layer": "policy",
                },
                "checks_passed": {
                    "value": policy_checks.checks_passed,
                    "evidence_class": "policy",
                    "source_layer": "policy",
                },
                "checks_failed": {
                    "value": policy_checks.checks_failed,
                    "evidence_class": "policy",
                    "source_layer": "policy",
                },
            },
        }

        signature = self._sign_payload(payload)

        self.store.insert(
            capsule_id=capsule_id,
            session_id=session_id,
            capsule_type="DECISION_POINT",
            payload=payload,
            signature=signature,
        )

        logger.debug(f"Emitted DECISION_POINT {capsule_id}")
        return capsule_id

    def emit_tool_call(
        self,
        session_id: str,
        parent_decision_id: str,
        tool_name: str,
        upstream_server_id: str,
        arguments: dict[str, Any],
        result: Any,
        started_at: datetime,
        ended_at: datetime,
        status: str,
        error_message: str | None,
    ) -> str:
        """
        Emit a TOOL_CALL capsule.
        """
        capsule_id = self.store.generate_id("tool")
        latency_ms = int((ended_at - started_at).total_seconds() * 1000)

        # Hash sensitive arguments
        args_json = json.dumps(arguments, sort_keys=True)
        args_hash = "sha256:" + hashlib.sha256(args_json.encode()).hexdigest()

        # Hash result (may be large, so hash only)
        result_json = json.dumps(result, sort_keys=True, default=str)
        result_hash = "sha256:" + hashlib.sha256(result_json.encode()).hexdigest()

        # Build preview (non-sensitive only)
        preview = self._build_preview(tool_name, arguments, result)

        payload = {
            "session_id": session_id,
            "parent_decision_id": {
                "value": parent_decision_id,
                "evidence_class": "observed",
                "source_layer": "proxy",
            },
            "tool": {
                "name": {
                    "value": tool_name,
                    "evidence_class": "observed",
                    "source_layer": "proxy",
                },
                "upstream_server_id": {
                    "value": upstream_server_id,
                    "evidence_class": "observed",
                    "source_layer": "proxy",
                },
                "arguments_hash": {
                    "value": args_hash,
                    "evidence_class": "observed",
                    "source_layer": "proxy",
                },
                "arguments_preview": {
                    "value": preview.get("args_preview"),
                    "evidence_class": "observed",
                    "source_layer": "proxy",
                },
            },
            "execution": {
                "started_at": {
                    "value": started_at.isoformat(),
                    "evidence_class": "observed",
                    "source_layer": "proxy",
                },
                "ended_at": {
                    "value": ended_at.isoformat(),
                    "evidence_class": "observed",
                    "source_layer": "proxy",
                },
                "latency_ms": {
                    "value": latency_ms,
                    "evidence_class": "derived",
                    "source_layer": "proxy",
                },
                "status": {
                    "value": status,
                    "evidence_class": "observed",
                    "source_layer": "proxy",
                },
                "error_message": {
                    "value": error_message,
                    "evidence_class": "observed",
                    "source_layer": "proxy",
                },
            },
            "output": {
                "content_hash": {
                    "value": result_hash,
                    "evidence_class": "observed",
                    "source_layer": "proxy",
                },
                "preview": {
                    "value": preview.get("result_preview"),
                    "evidence_class": "observed",
                    "source_layer": "proxy",
                },
            },
        }

        signature = self._sign_payload(payload)

        self.store.insert(
            capsule_id=capsule_id,
            session_id=session_id,
            capsule_type="TOOL_CALL",
            payload=payload,
            signature=signature,
            parent_id=parent_decision_id,
            upstream_server_id=upstream_server_id,
        )

        logger.debug(f"Emitted TOOL_CALL {capsule_id}")
        return capsule_id

    def emit_refusal(
        self,
        session_id: str,
        parent_decision_id: str,
        attempted_tool: str,
        policy_result: PolicyResult,
    ) -> str:
        """
        Emit a REFUSAL / POLICY_BLOCK capsule.
        """
        capsule_id = self.store.generate_id("ref")

        payload = {
            "session_id": session_id,
            "parent_decision_id": {
                "value": parent_decision_id,
                "evidence_class": "observed",
                "source_layer": "proxy",
            },
            "attempted_tool": {
                "value": attempted_tool,
                "evidence_class": "observed",
                "source_layer": "proxy",
            },
            "reason": {
                "value": policy_result.reason,
                "evidence_class": "policy",
                "source_layer": "policy",
            },
            "policy_checks": {
                "checks_passed": policy_result.checks_passed,
                "checks_failed": policy_result.checks_failed,
                "evidence_class": "policy",
                "source_layer": "policy",
            },
            "policy_version": {
                "value": policy_result.policy_version,
                "evidence_class": "policy",
                "source_layer": "policy",
            },
            "escalation": {
                "value": "human_approval_required",
                "evidence_class": "derived",
                "source_layer": "proxy",
            },
        }

        signature = self._sign_payload(payload)

        self.store.insert(
            capsule_id=capsule_id,
            session_id=session_id,
            capsule_type="REFUSAL",
            payload=payload,
            signature=signature,
            parent_id=parent_decision_id,
        )

        logger.debug(f"Emitted REFUSAL {capsule_id}")
        return capsule_id

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _sign_payload(self, payload: dict[str, Any]) -> str:
        """Sign a capsule payload using UATPCryptoV7."""
        if not self.crypto.enabled:
            logger.warning("Crypto disabled; returning empty signature")
            return ""

        # sign_capsule returns a full verification dict; we extract the signature
        verification: dict[str, Any] = self.crypto.sign_capsule(
            payload, timestamp_mode="none"
        )
        sig: str = verification.get("signature", "")
        return sig

    def _build_preview(
        self, tool_name: str, arguments: dict[str, Any], result: Any
    ) -> dict[str, Any]:
        """
        Build non-sensitive previews for display.
        Never include full file contents, passwords, keys, etc.
        """
        preview: dict[str, Any] = {}

        # Arguments preview
        if tool_name == "read_file":
            path = arguments.get("path", "?")
            preview["args_preview"] = f"read_file(path={path})"
        elif tool_name == "write_file":
            path = arguments.get("path", "?")
            content = arguments.get("content", "")
            preview["args_preview"] = (
                f"write_file(path={path}, content_len={len(content)})"
            )
        elif tool_name == "run_command":
            cmd = arguments.get("command", "?")
            preview["args_preview"] = f"run_command(command={cmd})"
        else:
            preview["args_preview"] = f"{tool_name}(...)"

        # Result preview
        if isinstance(result, dict):
            preview["result_preview"] = f"dict_keys={list(result.keys())}"
        elif isinstance(result, list):
            preview["result_preview"] = f"list_len={len(result)}"
        elif isinstance(result, str):
            preview["result_preview"] = result[:200]
        else:
            preview["result_preview"] = str(result)[:200]

        return preview
