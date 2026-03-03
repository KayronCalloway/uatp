"""
Attribution Aggregator for UATP 7.2 Workflow Chains

Aggregates attribution data from multiple workflow steps into a combined
attribution record for the complete workflow.
"""

from collections import defaultdict
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

# SECURITY: Maximum attribution caps to prevent gaming
# These limits prevent a single contributor from claiming excessive attribution
MAX_CONTRIBUTOR_WEIGHT = 0.50  # No single contributor can exceed 50%
MIN_CONTRIBUTOR_WEIGHT = 0.01  # Minimum attribution floor (1%)
MAX_CONTRIBUTORS = 100  # Maximum number of contributors tracked


def aggregate_attributions(
    step_attributions: List[Dict[str, Any]],
    aggregation_method: str = "weighted_sum",
    max_contributor_weight: float = MAX_CONTRIBUTOR_WEIGHT,
) -> Dict[str, Any]:
    """
    Aggregate attributions from multiple workflow steps.

    Args:
        step_attributions: List of attribution dicts from individual steps
        aggregation_method: Method to combine attributions
            - "weighted_sum": Sum weights per contributor
            - "equal": Equal weight to all contributors
            - "time_decay": Recent contributions weighted higher

    Returns:
        Aggregated attribution dictionary
    """
    if not step_attributions:
        return {
            "contributors": [],
            "weights": {},
            "aggregation_method": aggregation_method,
            "step_count": 0,
        }

    # Collect all contributors across steps
    contributor_weights: Dict[str, float] = defaultdict(float)
    contributor_roles: Dict[str, set] = defaultdict(set)
    contributor_timestamps: Dict[str, List[str]] = defaultdict(list)
    upstream_capsules: set = set()

    for step_attr in step_attributions:
        if not step_attr:
            continue

        # Process contributors
        contributors = step_attr.get("contributors", [])
        for contrib in contributors:
            agent_id = contrib.get("agent_id", "unknown")
            weight = contrib.get("weight", 1.0)
            role = contrib.get("role", "contributor")
            timestamp = contrib.get("timestamp")

            if aggregation_method == "weighted_sum":
                contributor_weights[agent_id] += weight
            elif aggregation_method == "equal":
                contributor_weights[agent_id] += 1.0
            elif aggregation_method == "time_decay":
                # More recent contributions get higher weight using exponential decay
                decay_factor = 1.0
                if timestamp:
                    try:
                        contrib_time = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
                        age_hours = (datetime.now(timezone.utc) - contrib_time).total_seconds() / 3600
                        # Half-life of 24 hours: contributions lose half their weight per day
                        decay_factor = 0.5 ** (age_hours / 24)
                    except (ValueError, TypeError):
                        decay_factor = 0.5  # Default decay for unparseable timestamps
                contributor_weights[agent_id] += weight * decay_factor

            contributor_roles[agent_id].add(role)
            if timestamp:
                contributor_timestamps[agent_id].append(timestamp)

        # Collect upstream capsules
        for upstream in step_attr.get("upstream_capsules", []):
            upstream_capsules.add(upstream)

    # SECURITY: Apply per-contributor caps before normalization to prevent gaming
    # This prevents any single contributor from claiming excessive attribution
    capped_weights = {}
    excess_weight = 0.0

    # First pass: cap individual weights and track excess
    raw_total = sum(contributor_weights.values()) or 1.0
    for agent_id, weight in contributor_weights.items():
        raw_proportion = weight / raw_total
        if raw_proportion > max_contributor_weight:
            capped_weights[agent_id] = max_contributor_weight * raw_total
            excess_weight += weight - capped_weights[agent_id]
        else:
            capped_weights[agent_id] = weight

    # Redistribute excess weight proportionally to uncapped contributors
    if excess_weight > 0:
        uncapped_total = sum(
            w for aid, w in capped_weights.items()
            if contributor_weights[aid] / raw_total <= max_contributor_weight
        )
        if uncapped_total > 0:
            for agent_id in capped_weights:
                if contributor_weights[agent_id] / raw_total <= max_contributor_weight:
                    bonus = (capped_weights[agent_id] / uncapped_total) * excess_weight
                    capped_weights[agent_id] += bonus

    # Normalize weights
    total_weight = sum(capped_weights.values()) or 1.0
    normalized_weights = {
        agent_id: weight / total_weight
        for agent_id, weight in capped_weights.items()
    }

    # SECURITY: Limit number of contributors tracked
    if len(normalized_weights) > MAX_CONTRIBUTORS:
        # Keep top contributors by weight
        sorted_contributors = sorted(
            normalized_weights.items(), key=lambda x: x[1], reverse=True
        )[:MAX_CONTRIBUTORS]
        normalized_weights = dict(sorted_contributors)
        # Re-normalize after truncation
        total_weight = sum(normalized_weights.values())
        normalized_weights = {k: v / total_weight for k, v in normalized_weights.items()}

    # Build aggregated contributor list
    aggregated_contributors = []
    for agent_id, weight in normalized_weights.items():
        roles = list(contributor_roles.get(agent_id, {"contributor"}))
        timestamps = contributor_timestamps.get(agent_id, [])
        latest_timestamp = max(timestamps) if timestamps else None

        aggregated_contributors.append({
            "agent_id": agent_id,
            "role": roles[0] if len(roles) == 1 else "multi_role",
            "roles": roles,
            "weight": weight,
            "contribution_count": len(timestamps),
            "latest_timestamp": latest_timestamp,
        })

    # Sort by weight descending
    aggregated_contributors.sort(key=lambda x: x["weight"], reverse=True)

    return {
        "contributors": aggregated_contributors,
        "weights": normalized_weights,
        "upstream_capsules": list(upstream_capsules),
        "aggregation_method": aggregation_method,
        "step_count": len(step_attributions),
        "aggregated_at": datetime.now(timezone.utc).isoformat(),
    }


def merge_dag_definitions(
    step_capsules: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """
    Build a DAG definition from workflow step capsules.

    Args:
        step_capsules: List of step capsule data with step_index and depends_on_steps

    Returns:
        DAG definition with nodes and edges
    """
    if not step_capsules:
        return {"nodes": [], "edges": [], "entry_points": [], "exit_points": []}

    nodes = []
    edges = []
    has_incoming: set = set()
    has_outgoing: set = set()

    for step in step_capsules:
        step_index = step.get("step_index", 0)
        step_type = step.get("step_type", "unknown")
        capsule_id = step.get("capsule_id", "")
        depends_on = step.get("depends_on_steps", []) or []

        nodes.append({
            "step_index": step_index,
            "step_type": step_type,
            "capsule_id": capsule_id,
        })

        for dep_index in depends_on:
            edges.append({
                "from": dep_index,
                "to": step_index,
            })
            has_incoming.add(step_index)
            has_outgoing.add(dep_index)

    all_indices = {n["step_index"] for n in nodes}
    entry_points = [i for i in all_indices if i not in has_incoming]
    exit_points = [i for i in all_indices if i not in has_outgoing]

    return {
        "nodes": nodes,
        "edges": edges,
        "entry_points": entry_points,
        "exit_points": exit_points,
        "total_steps": len(nodes),
    }


def calculate_step_contribution(
    step_data: Dict[str, Any],
    workflow_context: Optional[Dict[str, Any]] = None,
) -> float:
    """
    Calculate the contribution weight for a workflow step.

    Args:
        step_data: Step capsule data
        workflow_context: Optional workflow metadata

    Returns:
        Contribution weight (0.0 to 1.0)
    """
    base_weight = 1.0

    # Step type weights
    type_weights = {
        "plan": 0.8,
        "tool_call": 1.0,
        "inference": 1.2,
        "output": 0.9,
        "human_input": 1.5,
        "verification": 0.7,
        "decision": 1.1,
        "aggregation": 0.6,
    }

    step_type = step_data.get("step_type", "unknown")
    base_weight = type_weights.get(step_type, 1.0)

    # Adjust for execution time if available
    execution_time_ms = step_data.get("execution_time_ms")
    if execution_time_ms:
        # Longer steps get slightly more weight (up to 20% bonus)
        time_factor = min(1.2, 1.0 + (execution_time_ms / 10000))
        base_weight *= time_factor

    # Adjust for confidence if available
    confidence = step_data.get("confidence")
    if confidence is not None:
        base_weight *= (0.5 + confidence * 0.5)  # Scale confidence impact

    return min(base_weight, 2.0)  # Cap at 2x
