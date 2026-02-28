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
    # Start with original payload data for backwards compatibility
    envelope = dict(payload_data) if isinstance(payload_data, dict) else {}

    # Add v7 envelope metadata (won't overwrite existing fields)
    envelope["_envelope"] = {
        "version": "7.1",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "capsule_type": capsule_type,
    }

    # Attribution - Contribution tracking
    envelope["attribution"] = {
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
    }

    # Lineage - Derivation and transformation history
    envelope["lineage"] = {
        "parent_capsules": parent_capsules or [],
        "derivation_method": "direct_creation",
        "transformation_log": [
            {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "operation": "envelope_wrapping",
                "version": "7.1"
            }
        ],
        "generation": len(parent_capsules) + 1 if parent_capsules else 1
    }

    # Chain Context - Blockchain/chain information
    envelope["chain_context"] = {
        "chain_id": chain_id or f"chain-{capsule_id[:8]}",
        "position": chain_position or 0,
        "previous_hash": previous_hash or "genesis",
        "merkle_root": None,  # To be computed during sealing
        "consensus_method": "proof-of-attribution"
    }

    # Extract parent_capsule_id for lineage if present
    if isinstance(payload_data, dict):
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
    # Check for v7 envelope marker or v7 fields
    if "_envelope" in payload:
        return True
    # Also check for the v7 specific fields
    v7_fields = {"attribution", "lineage", "chain_context"}
    return all(field in payload for field in v7_fields)
