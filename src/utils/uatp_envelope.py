"""
UATP 7.2 Envelope Wrapper

This module provides functions to wrap capsule payloads in the standard UATP envelope structure,
ensuring all capsules have consistent metadata, attribution, lineage, and chain context fields.

UATP 7.2 adds optional sections for:
- training_context: Training provenance data
- workflow_context: Agentic workflow chain data
- hardware_attestation: Hardware attestation data
- model_registry_ref: Reference to registered model

All new sections are optional to maintain backward compatibility with 7.1 capsules.
"""

import hashlib
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


def compute_chain_merkle_root(capsule_ids: List[str]) -> str:
    """
    Compute a Merkle root hash from a list of capsule IDs.

    This provides a compact cryptographic commitment to the chain contents.
    For simplicity, we use a linear hash chain (not a true Merkle tree),
    which is sufficient for chains under ~1000 capsules.

    Args:
        capsule_ids: List of capsule IDs in chain order

    Returns:
        Hex-encoded SHA-256 hash representing the chain
    """
    if not capsule_ids:
        return hashlib.sha256(b"empty_chain").hexdigest()

    # Build hash chain: H(H(...H(H(id0) || id1) || id2)... || idN)
    current_hash = hashlib.sha256(capsule_ids[0].encode()).digest()
    for capsule_id in capsule_ids[1:]:
        combined = current_hash + capsule_id.encode()
        current_hash = hashlib.sha256(combined).digest()

    return current_hash.hex()


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
    # Chain merkle root (computed externally or from capsule_ids_in_chain)
    merkle_root: Optional[str] = None,
    capsule_ids_in_chain: Optional[List[str]] = None,
    # UATP 7.2 optional sections
    training_context: Optional[Dict[str, Any]] = None,
    workflow_context: Optional[Dict[str, Any]] = None,
    hardware_attestation: Optional[Dict[str, Any]] = None,
    model_registry_ref: Optional[str] = None,
    # UATP 7.3 optional sections
    ane_context: Optional[Dict[str, Any]] = None,
    kernel_trace: Optional[Dict[str, Any]] = None,
    # UATP 7.4 optional sections
    agent_context: Optional[Dict[str, Any]] = None,
    tool_trace: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Wraps a capsule payload in the standard UATP 7.2 envelope structure.

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
        merkle_root: Pre-computed Merkle root hash (optional)
        capsule_ids_in_chain: List of capsule IDs to compute merkle_root (if merkle_root not provided)
        training_context: UATP 7.2 - Training provenance context (optional)
        workflow_context: UATP 7.2 - Workflow chain context (optional)
        hardware_attestation: UATP 7.2 - Hardware attestation data (optional)
        model_registry_ref: UATP 7.2 - Model registry reference (optional)
        ane_context: UATP 7.3 - ANE training context (optional)
        kernel_trace: UATP 7.3 - Kernel execution trace (optional)
        agent_context: UATP 7.4 - Agent execution context (optional)
        tool_trace: UATP 7.4 - Tool call trace (optional)

    Returns:
        Dict containing the full UATP envelope structure
    """
    # Determine version based on presence of 7.4, 7.3, or 7.2 features
    has_74_features = any(
        [
            agent_context,
            tool_trace,
        ]
    )
    has_73_features = any(
        [
            ane_context,
            kernel_trace,
        ]
    )
    has_72_features = any(
        [
            training_context,
            workflow_context,
            hardware_attestation,
            model_registry_ref,
        ]
    )

    if has_74_features:
        envelope_version = "7.4"
    elif has_73_features:
        envelope_version = "7.3"
    elif has_72_features:
        envelope_version = "7.2"
    else:
        envelope_version = "7.1"

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

    # Add envelope metadata (won't overwrite existing fields)
    envelope["_envelope"] = {
        "version": envelope_version,
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
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        ],
        "weights": {agent_id or "unknown": 1.0},
        "compensation_rules": {
            "distribution_model": "equal",
            "minimum_contribution_threshold": 0.01,
        },
        "upstream_capsules": parent_capsules or [],
    }

    # Lineage - Derivation and transformation history
    envelope["lineage"] = {
        "parent_capsules": parent_capsules or [],
        "derivation_method": "direct_creation",
        "transformation_log": [
            {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "operation": "envelope_wrapping",
                "version": envelope_version,
            }
        ],
        "generation": len(parent_capsules) + 1 if parent_capsules else 1,
    }

    # Chain Context - Blockchain/chain information
    # Compute merkle_root if capsule_ids_in_chain provided and merkle_root not pre-computed
    computed_merkle_root = merkle_root
    if not computed_merkle_root and capsule_ids_in_chain:
        computed_merkle_root = compute_chain_merkle_root(capsule_ids_in_chain)

    envelope["chain_context"] = {
        "chain_id": chain_id or f"chain-{capsule_id[:8]}",
        "position": chain_position or 0,
        "previous_hash": previous_hash or "genesis",
        "merkle_root": computed_merkle_root,  # Now computed when chain data available
        "consensus_method": "proof-of-attribution",
    }

    # Extract parent_capsule_id for lineage if present
    if isinstance(payload_data, dict):
        if "parent_capsule_id" in payload_data and payload_data["parent_capsule_id"]:
            parent_id = payload_data["parent_capsule_id"]
            if parent_id not in envelope["lineage"]["parent_capsules"]:
                envelope["lineage"]["parent_capsules"].append(parent_id)
            if parent_id not in envelope["attribution"]["upstream_capsules"]:
                envelope["attribution"]["upstream_capsules"].append(parent_id)

    # UATP 7.2 Optional Sections
    if training_context:
        envelope["training_context"] = training_context

    if workflow_context:
        envelope["workflow_context"] = workflow_context

    if hardware_attestation:
        envelope["hardware_attestation"] = hardware_attestation

    if model_registry_ref:
        envelope["model_registry_ref"] = model_registry_ref

    # UATP 7.3 Optional Sections
    if ane_context:
        envelope["ane_context"] = ane_context

    if kernel_trace:
        envelope["kernel_trace"] = kernel_trace

    # UATP 7.4 Optional Sections
    if agent_context:
        envelope["agent_context"] = agent_context

    if tool_trace:
        envelope["tool_trace"] = tool_trace

    return envelope


def extract_from_envelope(envelope: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extracts the original payload data from a UATP envelope.

    Args:
        envelope: The full UATP envelope structure

    Returns:
        The original payload data
    """
    if "content" in envelope and "data" in envelope["content"]:
        return envelope["content"]["data"]
    # Fallback: if envelope is already just the payload
    return envelope


def is_envelope_format(payload: Dict[str, Any]) -> bool:
    """
    Checks if a payload is already in UATP envelope format.

    Args:
        payload: The payload to check

    Returns:
        True if payload has envelope structure, False otherwise
    """
    # Check for envelope marker
    if "_envelope" in payload:
        return True
    # Also check for the v7 specific fields
    v7_fields = {"attribution", "lineage", "chain_context"}
    return all(field in payload for field in v7_fields)


def detect_capsule_version(envelope: Dict[str, Any]) -> str:
    """
    Detects the UATP version of a capsule envelope.

    UATP 7.4 capsules have at least one of:
    - agent_context
    - tool_trace

    UATP 7.3 capsules have at least one of:
    - ane_context
    - kernel_trace

    UATP 7.2 capsules have at least one of:
    - training_context
    - workflow_context
    - hardware_attestation
    - model_registry_ref

    Args:
        envelope: The capsule envelope to check

    Returns:
        Version string: "7.4", "7.3", "7.2", "7.1", or "7.0"
    """
    # Check for explicit version in envelope
    if "_envelope" in envelope and "version" in envelope["_envelope"]:
        return envelope["_envelope"]["version"]

    # Check for 7.4 features
    v74_fields = {
        "agent_context",
        "tool_trace",
    }
    if any(field in envelope for field in v74_fields):
        return "7.4"

    # Check for 7.3 features
    v73_fields = {
        "ane_context",
        "kernel_trace",
    }
    if any(field in envelope for field in v73_fields):
        return "7.3"

    # Check for 7.2 features
    v72_fields = {
        "training_context",
        "workflow_context",
        "hardware_attestation",
        "model_registry_ref",
    }
    if any(field in envelope for field in v72_fields):
        return "7.2"

    # Check for 7.1/7.0 features
    v7_fields = {"attribution", "lineage", "chain_context"}
    if all(field in envelope for field in v7_fields):
        return "7.1"

    return "7.0"


def create_training_context(
    model_id: str,
    session_id: Optional[str] = None,
    base_model_id: Optional[str] = None,
    training_type: Optional[str] = None,
    dataset_refs: Optional[List[Dict[str, Any]]] = None,
    hyperparameters: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Creates a UATP 7.2 training_context section.

    Args:
        model_id: The model being referenced
        session_id: Training session ID if applicable
        base_model_id: Parent model ID for lineage
        training_type: Type of training (pre_training, fine_tuning, etc.)
        dataset_refs: List of dataset references
        hyperparameters: Training hyperparameters

    Returns:
        Training context dictionary
    """
    context = {
        "model_id": model_id,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }

    if session_id:
        context["session_id"] = session_id
    if base_model_id:
        context["base_model_id"] = base_model_id
    if training_type:
        context["training_type"] = training_type
    if dataset_refs:
        context["dataset_refs"] = dataset_refs
    if hyperparameters:
        context["hyperparameters"] = hyperparameters

    return context


def create_workflow_context(
    workflow_id: str,
    workflow_name: str,
    step_index: Optional[int] = None,
    step_type: Optional[str] = None,
    depends_on: Optional[List[int]] = None,
    aggregated_attribution: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Creates a UATP 7.2 workflow_context section.

    Args:
        workflow_id: Parent workflow capsule ID
        workflow_name: Human-readable workflow name
        step_index: Current step index (if step capsule)
        step_type: Type of step (plan, tool_call, inference, etc.)
        depends_on: Step indices this step depends on
        aggregated_attribution: Combined attribution from workflow

    Returns:
        Workflow context dictionary
    """
    context = {
        "workflow_id": workflow_id,
        "workflow_name": workflow_name,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }

    if step_index is not None:
        context["step_index"] = step_index
    if step_type:
        context["step_type"] = step_type
    if depends_on:
        context["depends_on"] = depends_on
    if aggregated_attribution:
        context["aggregated_attribution"] = aggregated_attribution

    return context


def create_hardware_attestation_context(
    attestation_type: str,
    device_id_hash: str,
    verified: bool = False,
    measurements: Optional[Dict[str, str]] = None,
) -> Dict[str, Any]:
    """
    Creates a UATP 7.2 hardware_attestation section.

    Args:
        attestation_type: Type (apple_secure_enclave, android_tee, nvidia_cc, etc.)
        device_id_hash: SHA-256 hash of device identifier
        verified: Whether attestation has been verified
        measurements: Platform measurements (PCRs, etc.)

    Returns:
        Hardware attestation context dictionary
    """
    return {
        "attestation_type": attestation_type,
        "device_id_hash": device_id_hash,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "verified": verified,
        "measurements": measurements or {},
    }


def create_ane_context(
    session_id: str,
    hardware_profile_id: str,
    chip_identifier: str,
    ane_available: bool = True,
    ane_tops: Optional[float] = None,
    private_apis_used: Optional[List[str]] = None,
    dmca_1201f_claim: bool = False,
) -> Dict[str, Any]:
    """
    Creates a UATP 7.3 ane_context section.

    Args:
        session_id: ANE training session ID
        hardware_profile_id: Reference to hardware profile capsule
        chip_identifier: Apple chip identifier (M1, M2, M3, M4, etc.)
        ane_available: Whether ANE is available on device
        ane_tops: ANE performance in TOPS
        private_apis_used: List of private APIs used (_ANEClient, _ANECompiler, etc.)
        dmca_1201f_claim: Whether DMCA 1201(f) interoperability claim applies

    Returns:
        ANE context dictionary
    """
    context = {
        "session_id": session_id,
        "hardware_profile_id": hardware_profile_id,
        "chip_identifier": chip_identifier,
        "ane_available": ane_available,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "dmca_1201f_claim": dmca_1201f_claim,
    }

    if ane_tops is not None:
        context["ane_tops"] = ane_tops
    if private_apis_used:
        context["private_apis_used"] = private_apis_used

    return context


def create_kernel_trace_context(
    session_id: str,
    step_index: int,
    kernel_executions: List[Dict[str, Any]],
    total_execution_time_us: Optional[int] = None,
    ane_percentage: Optional[float] = None,
    cpu_percentage: Optional[float] = None,
) -> Dict[str, Any]:
    """
    Creates a UATP 7.3 kernel_trace section.

    Args:
        session_id: ANE training session ID
        step_index: Training step index
        kernel_executions: List of kernel execution records
        total_execution_time_us: Total execution time in microseconds
        ane_percentage: Percentage of compute on ANE
        cpu_percentage: Percentage of compute on CPU

    Returns:
        Kernel trace context dictionary
    """
    context = {
        "session_id": session_id,
        "step_index": step_index,
        "kernel_executions": kernel_executions,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "kernel_count": len(kernel_executions),
    }

    if total_execution_time_us is not None:
        context["total_execution_time_us"] = total_execution_time_us
    if ane_percentage is not None:
        context["ane_percentage"] = ane_percentage
    if cpu_percentage is not None:
        context["cpu_percentage"] = cpu_percentage

    return context


def create_agent_context(
    session_id: str,
    agent_type: str,
    goals: Optional[List[str]] = None,
    agent_version: Optional[str] = None,
    scheduler_type: Optional[str] = None,
    trigger_message: Optional[str] = None,
    trigger_source: Optional[str] = None,
    user_id_hash: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Creates a UATP 7.4 agent_context section.

    Args:
        session_id: Agent session ID
        agent_type: Type of agent (openclaw, claude_code, custom)
        goals: List of goals the agent is trying to achieve
        agent_version: Version of the agent
        scheduler_type: Scheduler type (heartbeat, on_demand, scheduled)
        trigger_message: Message that initiated the session
        trigger_source: Source of trigger (whatsapp, telegram, cli, api)
        user_id_hash: Privacy-preserving hash of user ID

    Returns:
        Agent context dictionary
    """
    context = {
        "session_id": session_id,
        "agent_type": agent_type,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "goals": goals or [],
    }

    if agent_version:
        context["agent_version"] = agent_version
    if scheduler_type:
        context["scheduler_type"] = scheduler_type
    if trigger_message:
        context["trigger_message"] = trigger_message
    if trigger_source:
        context["trigger_source"] = trigger_source
    if user_id_hash:
        context["user_id_hash"] = user_id_hash

    return context


def create_tool_trace_context(
    session_id: str,
    tool_calls: List[Dict[str, Any]],
    total_tool_calls: Optional[int] = None,
    total_duration_ms: Optional[int] = None,
    tool_categories: Optional[Dict[str, int]] = None,
) -> Dict[str, Any]:
    """
    Creates a UATP 7.4 tool_trace section.

    Args:
        session_id: Agent session ID
        tool_calls: List of tool call records
        total_tool_calls: Total number of tool calls in session
        total_duration_ms: Total time spent in tool calls
        tool_categories: Breakdown of tool calls by category

    Returns:
        Tool trace context dictionary
    """
    context = {
        "session_id": session_id,
        "tool_calls": tool_calls,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "tool_count": len(tool_calls),
    }

    if total_tool_calls is not None:
        context["total_tool_calls"] = total_tool_calls
    if total_duration_ms is not None:
        context["total_duration_ms"] = total_duration_ms
    if tool_categories:
        context["tool_categories"] = tool_categories

    return context
