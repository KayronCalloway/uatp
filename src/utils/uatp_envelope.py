"""
UATP 7.0 Envelope Wrapper

This module provides functions to wrap capsule payloads in the standard UATP 7.0 envelope structure,
ensuring all capsules have consistent metadata, attribution, lineage, and chain context fields.
"""

from datetime import datetime, timezone
from typing import Any, Dict, Optional, List
import json


def wrap_in_uatp_envelope(
    payload_data: Dict[str, Any],
    capsule_id: str,
    capsule_type: str,
    agent_id: Optional[str] = None,
    session_id: Optional[str] = None,
    parent_capsules: Optional[List[str]] = None,
    chain_id: Optional[str] = None,
    chain_position: Optional[int] = None,
    previous_hash: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Wraps a capsule payload in the standard UATP 7.0 envelope structure.

    Args:
        payload_data: The type-specific payload data (reasoning_trace, economic_transaction, etc.)
        capsule_id: Unique identifier for the capsule
        capsule_type: Type of capsule (reasoning_trace, economic_transaction, etc.)
        agent_id: ID of the agent/system creating the capsule
        session_id: Optional session identifier
        parent_capsules: List of parent capsule IDs for lineage
        chain_id: Optional chain identifier
        chain_position: Position in the capsule chain
        previous_hash: Hash of the previous capsule in chain

    Returns:
        Dict containing the full UATP 7.0 envelope structure
    """

    # Extract significance score if present in payload
    significance_score = 0.0
    if isinstance(payload_data, dict):
        # Check various locations where significance might be stored
        if "significance_score" in payload_data:
            significance_score = payload_data.get("significance_score", 0.0)
        elif "metadata" in payload_data and isinstance(payload_data["metadata"], dict):
            significance_score = payload_data["metadata"].get("significance_score", 0.0)

    # Build the standardized envelope
    envelope = {
        # Content - The actual capsule data
        "content": {
            "capsule_type": capsule_type,
            "data": payload_data,
            "format": "json",
            "encoding": "utf-8"
        },

        # Metadata - Creation and context information
        "metadata": {
            "created_at": datetime.now(timezone.utc).isoformat(),
            "created_by": agent_id or "unknown",
            "capsule_id": capsule_id,
            "platform": "uatp-7.0",
            "session_id": session_id or "default",
            "significance_score": significance_score,
            "envelope_version": "7.0"
        },

        # Trace - Reasoning and decision tracking
        "trace": {
            "reasoning_steps": [],
            "decision_points": [],
            "confidence_levels": {},
            "extracted_from_payload": True
        },

        # Attribution - Contribution tracking
        "attribution": {
            "contributors": [
                {
                    "agent_id": agent_id or "unknown",
                    "role": "creator",
                    "weight": 1.0,
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }
            ],
            "weights": {
                agent_id or "unknown": 1.0
            },
            "compensation_rules": {
                "distribution_model": "equal",
                "minimum_contribution_threshold": 0.01
            },
            "upstream_capsules": parent_capsules or []
        },

        # Lineage - Derivation and transformation history
        "lineage": {
            "parent_capsules": parent_capsules or [],
            "derivation_method": "direct_creation",
            "transformation_log": [
                {
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "operation": "envelope_wrapping",
                    "version": "7.0"
                }
            ],
            "generation": len(parent_capsules) + 1 if parent_capsules else 1
        },

        # Chain Context - Blockchain/chain information
        "chain_context": {
            "chain_id": chain_id or f"chain-{capsule_id[:8]}",
            "position": chain_position or 0,
            "previous_hash": previous_hash or "genesis",
            "merkle_root": None,  # To be computed during sealing
            "consensus_method": "proof-of-attribution"
        }
    }

    # Enhanced trace extraction from payload if available
    if isinstance(payload_data, dict):
        # Extract reasoning steps if present
        if "steps" in payload_data and isinstance(payload_data["steps"], list):
            envelope["trace"]["reasoning_steps"] = [
                {
                    "step": i,
                    "content": step.get("content", ""),
                    "step_type": step.get("step_type", "unknown"),
                    "metadata": step.get("metadata", {})
                }
                for i, step in enumerate(payload_data["steps"])
            ]

        # Extract reasoning_steps field if present
        if "reasoning_steps" in payload_data and isinstance(payload_data["reasoning_steps"], list):
            envelope["trace"]["reasoning_steps"] = payload_data["reasoning_steps"]

        # Extract confidence if present
        if "confidence" in payload_data:
            envelope["trace"]["confidence_levels"]["overall"] = payload_data["confidence"]

        # Extract parent_capsule_id for lineage
        if "parent_capsule_id" in payload_data and payload_data["parent_capsule_id"]:
            parent_id = payload_data["parent_capsule_id"]
            if parent_id not in envelope["lineage"]["parent_capsules"]:
                envelope["lineage"]["parent_capsules"].append(parent_id)
            if parent_id not in envelope["attribution"]["upstream_capsules"]:
                envelope["attribution"]["upstream_capsules"].append(parent_id)

    return envelope


def extract_from_envelope(
    envelope: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Extracts the original payload data from a UATP 7.0 envelope.

    Args:
        envelope: The full UATP 7.0 envelope structure

    Returns:
        The original payload data
    """
    if "content" in envelope and "data" in envelope["content"]:
        return envelope["content"]["data"]
    # Fallback: if envelope is already just the payload
    return envelope


def is_envelope_format(payload: Dict[str, Any]) -> bool:
    """
    Checks if a payload is already in UATP 7.0 envelope format.

    Args:
        payload: The payload to check

    Returns:
        True if payload has envelope structure, False otherwise
    """
    required_fields = {"content", "metadata", "trace", "attribution", "lineage", "chain_context"}
    return all(field in payload for field in required_fields)
