"""
simulator.py - CQSS Simulation Module for UATP Capsule Engine.

This module provides simulation capabilities for the Capsule Quality Scoring System,
allowing users to predict how changes to capsule content would affect quality scores.
"""

import os
import sys

sys.path.append(os.getcwd())

from copy import deepcopy
from typing import Any, Dict, List, Optional, Tuple

from src.capsule_schema import Capsule
from cqss.scorer import CQSSScorer


def simulate_cqss_for_capsule(capsule, target_score=90.0):
    """Wrapper function to simulate CQSS optimization for a capsule.

    Args:
        capsule: The capsule to optimize
        target_score: Target score to achieve (default: 90.0)

    Returns:
        Dict containing simulation results
    """
    return CQSSSimulator.optimize_capsule(capsule, target_score)


class CQSSSimulator:
    """
    Simulates CQSS scores for hypothetical changes to capsules.
    Allows prediction of how modifications would affect quality scores.
    """

    @staticmethod
    def simulate_confidence_change(
        capsule: Capsule, new_confidence: float
    ) -> Dict[str, Any]:
        """
        Simulate how changing the confidence value would affect the CQSS score.

        Args:
            capsule: The original capsule
            new_confidence: New confidence value between 0.0 and 1.0

        Returns:
            Dict containing original and simulated scores with breakdown
        """
        if not 0.0 <= new_confidence <= 1.0:
            raise ValueError("Confidence must be between 0.0 and 1.0")

        # Create a copy to avoid modifying the original
        sim_capsule = deepcopy(capsule)
        sim_capsule.confidence = new_confidence

        # Calculate scores
        original_score = CQSSScorer.calculate_score(capsule)
        simulated_score = CQSSScorer.calculate_score(sim_capsule)

        return {
            "original": original_score,
            "simulated": simulated_score,
            "difference": simulated_score["total_score"]
            - original_score["total_score"],
            "modified_attribute": "confidence",
        }

    @staticmethod
    def simulate_reasoning_trace_change(
        capsule: Capsule, new_trace: List[str]
    ) -> Dict[str, Any]:
        """
        Simulate how changing the reasoning trace would affect the CQSS score.

        Args:
            capsule: The original capsule
            new_trace: New reasoning trace as a list of strings

        Returns:
            Dict containing original and simulated scores with breakdown
        """
        # Create a copy to avoid modifying the original
        sim_capsule = deepcopy(capsule)
        sim_capsule.reasoning_trace = new_trace

        # Calculate scores
        original_score = CQSSScorer.calculate_score(capsule)
        simulated_score = CQSSScorer.calculate_score(sim_capsule)

        return {
            "original": original_score,
            "simulated": simulated_score,
            "difference": simulated_score["total_score"]
            - original_score["total_score"],
            "modified_attribute": "reasoning_trace",
        }

    @staticmethod
    def simulate_ethical_policy_change(
        capsule: Capsule, new_policy_id: str
    ) -> Dict[str, Any]:
        """
        Simulate how changing the ethical policy would affect the CQSS score.

        Args:
            capsule: The original capsule
            new_policy_id: New ethical policy ID

        Returns:
            Dict containing original and simulated scores with breakdown
        """
        # Create a copy to avoid modifying the original
        sim_capsule = deepcopy(capsule)
        sim_capsule.ethical_policy_id = new_policy_id

        # Calculate scores
        original_score = CQSSScorer.calculate_score(capsule)
        simulated_score = CQSSScorer.calculate_score(sim_capsule)

        return {
            "original": original_score,
            "simulated": simulated_score,
            "difference": simulated_score["total_score"]
            - original_score["total_score"],
            "modified_attribute": "ethical_policy_id",
        }

    @staticmethod
    def simulate_signature_change(
        capsule: Capsule, valid_signature: bool
    ) -> Dict[str, Any]:
        """
        Simulate how changing the signature validity would affect the CQSS score.

        Args:
            capsule: The original capsule
            valid_signature: Whether the signature should be considered valid

        Returns:
            Dict containing original and simulated scores with breakdown
        """
        # Create a copy to avoid modifying the original
        sim_capsule = deepcopy(capsule)

        # This is a bit of a hack since we can't directly modify signature verification
        # Instead, we'll modify the signature to a known invalid value if needed
        if not valid_signature and sim_capsule.signature:
            sim_capsule.signature = "invalid_signature_for_simulation"

        # Calculate scores
        original_score = CQSSScorer.calculate_score(capsule)
        simulated_score = CQSSScorer.calculate_score(sim_capsule)

        return {
            "original": original_score,
            "simulated": simulated_score,
            "difference": simulated_score["total_score"]
            - original_score["total_score"],
            "modified_attribute": "signature",
        }

    @staticmethod
    def simulate_multiple_changes(
        capsule: Capsule,
        new_confidence: Optional[float] = None,
        new_trace: Optional[List[str]] = None,
        new_policy_id: Optional[str] = None,
        valid_signature: Optional[bool] = None,
    ) -> Dict[str, Any]:
        """
        Simulate multiple changes to a capsule at once.

        Args:
            capsule: The original capsule
            new_confidence: Optional new confidence value
            new_trace: Optional new reasoning trace
            new_policy_id: Optional new ethical policy ID
            valid_signature: Optional signature validity flag

        Returns:
            Dict containing original and simulated scores with breakdown
        """
        # Create a copy to avoid modifying the original
        sim_capsule = deepcopy(capsule)

        # Apply changes
        changes = []

        if new_confidence is not None:
            if not 0.0 <= new_confidence <= 1.0:
                raise ValueError("Confidence must be between 0.0 and 1.0")
            sim_capsule.confidence = new_confidence
            changes.append("confidence")

        if new_trace is not None:
            sim_capsule.reasoning_trace = new_trace
            changes.append("reasoning_trace")

        if new_policy_id is not None:
            sim_capsule.ethical_policy_id = new_policy_id
            changes.append("ethical_policy_id")

        if (
            valid_signature is not None
            and not valid_signature
            and sim_capsule.signature
        ):
            sim_capsule.signature = "invalid_signature_for_simulation"
            changes.append("signature")

        # Calculate scores
        original_score = CQSSScorer.calculate_score(capsule)
        simulated_score = CQSSScorer.calculate_score(sim_capsule)

        return {
            "original": original_score,
            "simulated": simulated_score,
            "difference": simulated_score["total_score"]
            - original_score["total_score"],
            "modified_attributes": changes,
        }

    @staticmethod
    def optimize_capsule(
        capsule: Capsule, target_score: float = 90.0, fixed_attributes: List[str] = None
    ) -> Tuple[Dict[str, Any], Capsule]:
        """
        Attempt to optimize a capsule to reach a target CQSS score.

        Args:
            capsule: The original capsule
            target_score: Target CQSS score to achieve
            fixed_attributes: List of attributes that should not be changed

        Returns:
            Tuple of (optimization report, optimized capsule)
        """
        if fixed_attributes is None:
            fixed_attributes = []

        # Create a copy to avoid modifying the original
        optimized = deepcopy(capsule)
        original_score = CQSSScorer.calculate_score(capsule)["total_score"]

        changes = []

        # Try to optimize each attribute if not fixed
        if (
            "ethical_policy_id" not in fixed_attributes
            and not optimized.ethical_policy_id
        ):
            optimized.ethical_policy_id = "default_ethical_policy"
            changes.append("Added ethical policy reference")

        if "reasoning_trace" not in fixed_attributes:
            # If reasoning trace is too short, extend it
            current_trace_len = len(optimized.reasoning_trace)
            if current_trace_len < 5:  # 5+ steps gives max score
                additional_steps = 5 - current_trace_len
                for i in range(additional_steps):
                    optimized.reasoning_trace.append(
                        f"Additional reasoning step {i+1} for optimization"
                    )
                changes.append(
                    f"Extended reasoning trace from {current_trace_len} to 5 steps"
                )

        if "confidence" not in fixed_attributes and optimized.confidence < 0.9:
            optimized.confidence = 0.9  # High but not unrealistic
            changes.append(f"Increased confidence from {capsule.confidence} to 0.9")

        # Calculate final score
        final_score = CQSSScorer.calculate_score(optimized)["total_score"]

        report = {
            "original_score": original_score,
            "optimized_score": final_score,
            "target_score": target_score,
            "changes_made": changes,
            "target_achieved": final_score >= target_score,
        }

        return report, optimized
