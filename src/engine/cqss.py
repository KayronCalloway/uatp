"""
cqss.py - Chain Quality and Security Score (CQSS) simulation for UATP Capsule Engine.
Computes comprehensive chain quality/security metrics for a given capsule chain.
"""

import asyncio
import math
import statistics
from collections import defaultdict
from datetime import datetime
from typing import Dict, List

import networkx as nx

from src.capsule_schema import Capsule


class CQSSResult:
    def __init__(self, metrics: Dict):
        self.metrics = metrics

    def as_dict(self):
        return self.metrics

    def get_overall_score(self):
        """Calculate a weighted overall score from individual metrics

        Returns:
            float: A weighted overall score normalized to 0.0-1.0 range, or None if metrics are missing
        """
        # Weights for different metric categories
        weights = {
            "integrity_score": 0.3,
            "verification_ratio": 0.2,
            "trust_score": 0.2,
            "complexity_score": 0.15,
            "diversity_score": 0.15,
        }

        weighted_sum = 0.0
        weight_total = 0.0

        try:
            for key, weight in weights.items():
                if key in self.metrics and self.metrics[key] is not None:
                    # Normalize scores that are on a 0-100 scale down to 0-1 scale
                    value = self.metrics[key]
                    if key != "verification_ratio":  # verification_ratio is already 0-1
                        value = value / 100.0
                    weighted_sum += value * weight
                    weight_total += weight

            if weight_total > 0:
                return weighted_sum / weight_total
            return None
        except Exception as e:
            print(f"Error calculating overall score: {e}")
            return None


def build_chain_graph(chain: List[Capsule]) -> nx.DiGraph:
    """Build a directed graph from the capsule chain"""
    G = nx.DiGraph()

    # Add all capsules as nodes
    for c in chain:
        G.add_node(c.capsule_id, capsule=c)

    # Add edges for parent-child relationships (robust for legacy and new capsules)
    for c in chain:
        parent_id = None
        capsule_id = None

        if isinstance(c, dict):
            # Handle dictionary-based capsules
            capsule_id = c.get("capsule_id")
            parent_id = c.get("parent_capsule") or c.get("previous_capsule_id")
        else:
            # Handle object-based capsules (both modern and legacy SimpleCapsule)
            capsule_id = getattr(c, "capsule_id", None)
            if hasattr(c, "parent_capsule"):
                parent_id = getattr(c, "parent_capsule", None)
            elif hasattr(c, "previous_capsule_id"):
                parent_id = getattr(c, "previous_capsule_id", None)

        if parent_id and capsule_id and parent_id in G:
            G.add_edge(parent_id, capsule_id)

    return G


async def compute_cqss(chain: List[Capsule], verify_capsule_fn) -> CQSSResult:
    """
    Compute comprehensive CQSS metrics for a capsule chain.
    Args:
        chain (List[Capsule]): List of capsules in the chain.
        verify_capsule_fn (callable): Function to verify capsule signatures.
    Returns:
        CQSSResult: Metrics object with detailed chain quality scores.
    """
    if not chain:
        return CQSSResult({})

    # Build a directed graph representation of the chain
    G = build_chain_graph(chain)

    # Basic metrics
    chain_length = len(chain)
    unique_agents = len({c.agent_id for c in chain})

    # Signature verification (asynchronously)
    verification_results = await asyncio.gather(*[verify_capsule_fn(c) for c in chain])
    valid_signatures = sum(1 for is_valid, reason in verification_results if is_valid)
    verification_ratio = valid_signatures / chain_length if chain_length > 0 else 0.0
    integrity_score = verification_ratio * 100

    # Calculate fork metrics
    roots = [node for node, in_degree in G.in_degree() if in_degree == 0]
    leaves = [node for node, out_degree in G.out_degree() if out_degree == 0]
    fork_points = [node for node, out_degree in G.out_degree() if out_degree > 1]
    join_points = [node for node, in_degree in G.in_degree() if in_degree > 1]
    fork_count = len(fork_points)

    # Calculate depth metrics
    longest_path_length = 0
    avg_path_length = 0
    path_lengths = []

    if roots and leaves:
        try:
            for source in roots:
                for target in leaves:
                    if nx.has_path(G, source, target):
                        paths = list(nx.all_simple_paths(G, source, target))
                        if paths:
                            path_lengths.extend([len(p) for p in paths])
                            longest_path_length = max(
                                longest_path_length, max(len(p) for p in paths)
                            )
        except nx.NetworkXNoPath:
            pass

    avg_path_length = statistics.mean(path_lengths) if path_lengths else 0

    # Trust metrics
    capsule_types = defaultdict(int)
    for c in chain:
        capsule_types[c.capsule_type] += 1

    joint_capsule_ratio = (
        capsule_types.get("Joint", 0) / chain_length if chain_length > 0 else 0
    )
    introspective_ratio = (
        capsule_types.get("Introspective", 0) / chain_length if chain_length > 0 else 0
    )

    # Compute confidence stats
    confidences = [c.confidence for c in chain if c.confidence is not None]
    avg_confidence = statistics.mean(confidences) if confidences else 0

    # Calculate complexity score based on fork/join structure (0-100) with quality impact
    complexity_base = min(100, (fork_count + len(join_points)) * 10)
    complexity_score = complexity_base * (1 - 0.5 * math.exp(-chain_length / 10))

    # Apply fork quality penalty to complexity score
    complexity_score = max(0, complexity_score - (fork_quality_impact * 100))

    # Calculate trust score based on joint capsules and verification (0-100)
    trust_base = (joint_capsule_ratio * 50) + (verification_ratio * 50)
    trust_score = trust_base * (1 - 0.2 * math.exp(-chain_length / 5))

    # Apply fork penalty to trust score (forks can indicate coordination issues)
    trust_score = max(0, trust_score - (fork_quality_impact * 50))

    # Calculate diversity score based on agent diversity (0-100)
    diversity_score = (
        min(100, (unique_agents / chain_length) * 100) if chain_length > 0 else 0
    )

    # Bonus for good diversity in presence of forks (shows healthy disagreement)
    if fork_count > 0 and diversity_score > 50:
        diversity_score = min(100, diversity_score * 1.1)

    # Calculate timestamp consistency (lower is better)
    timestamp_consistency = 0
    if chain_length > 1:
        try:
            timestamps = [datetime.fromisoformat(c.timestamp) for c in chain]
            timestamp_diffs = [
                (timestamps[i] - timestamps[i - 1]).total_seconds()
                for i in range(1, len(timestamps))
            ]
            if timestamp_diffs:
                timestamp_consistency = (
                    statistics.stdev(timestamp_diffs) if len(timestamp_diffs) > 1 else 0
                )
        except (ValueError, TypeError):
            timestamp_consistency = None

    metrics = {
        # Basic metrics
        "chain_length": chain_length,
        "valid_signatures": valid_signatures,
        "fork_count": fork_count,
        "unique_agents": unique_agents,
        # Advanced metrics
        "verification_ratio": round(verification_ratio, 2),
        "integrity_score": round(integrity_score, 1),
        "complexity_score": round(complexity_score, 1),
        "trust_score": round(trust_score, 1),
        "diversity_score": round(diversity_score, 1),
        # Chain structure metrics
        "root_count": len(roots),
        "leaf_count": len(leaves),
        "join_points": len(join_points),
        "longest_path": longest_path_length,
        "avg_path_length": round(avg_path_length, 2),
        # Capsule type metrics
        "joint_capsule_ratio": round(joint_capsule_ratio, 2),
        "introspective_ratio": round(introspective_ratio, 2),
        "avg_confidence": round(avg_confidence, 2),
        # Time metrics
        "timestamp_consistency": (
            round(timestamp_consistency, 2)
            if timestamp_consistency is not None
            else None
        ),
    }

    return CQSSResult(metrics)
