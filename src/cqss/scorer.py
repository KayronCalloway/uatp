"""
CQSS Capsule Quality Scoring System

This module provides the CQSSScorer class for calculating the quality score of a UATP capsule.
"""

import os
import sys

sys.path.append(os.getcwd())

from src.capsule_schema import Capsule
from crypto_utils import hash_for_signature, verify_capsule


class CQSSScorer:
    """Calculates the Capsule Quality Scoring System (CQSS) score for a capsule."""

    # Define weights for each scoring component
    WEIGHTS = {
        "signature_verification": 0.4,
        "confidence": 0.3,
        "reasoning_depth": 0.2,
        "ethical_policy": 0.1,
    }

    @staticmethod
    def calculate_score(capsule):
        """Calculate the CQSS score and provide a breakdown."""

        # Handle both dictionary and Capsule objects
        def get_attr(obj, attr_name, default=None):
            if isinstance(obj, dict):
                return obj.get(attr_name, default)
            else:
                return getattr(obj, attr_name, default)

        scores = {}

        # 1. Confidence Score (0-100)
        confidence = get_attr(capsule, "confidence", 0)
        # Handle confidence in metadata if not directly available
        if confidence == 0:
            metadata = get_attr(capsule, "metadata", {})
            if isinstance(metadata, dict):
                confidence = metadata.get("confidence", 0)
        scores["confidence"] = confidence * 100

        # 2. Reasoning Depth Score (0-100)
        reasoning_trace = get_attr(capsule, "reasoning_trace", [])
        depth = len(reasoning_trace) if isinstance(reasoning_trace, list) else 0
        if depth == 0:
            scores["reasoning_depth"] = 0
        elif depth <= 2:
            scores["reasoning_depth"] = 50
        elif depth <= 5:
            scores["reasoning_depth"] = 75
        else:
            scores["reasoning_depth"] = 100

        # 3. Ethical Policy Score (0-100)
        scores["ethical_policy"] = (
            100 if get_attr(capsule, "ethical_policy_id", None) else 0
        )

        # 4. Signature Verification Score (0-100)
        try:
            metadata = get_attr(capsule, "metadata", {}) or {}
            verify_key_hex = (
                metadata.get("verify_key") if isinstance(metadata, dict) else None
            )
            signature = get_attr(capsule, "signature", None)
            if not verify_key_hex or not signature:
                scores["signature_verification"] = 0
            else:
                capsule_hash = hash_for_signature(capsule)
                is_valid = verify_capsule(capsule_hash, signature, verify_key_hex)
                scores["signature_verification"] = 100 if is_valid else 0
        except Exception:
            scores["signature_verification"] = 0  # Fail safely

        # Calculate final weighted score
        total_score = (
            scores.get("signature_verification", 0)
            * CQSSScorer.WEIGHTS["signature_verification"]
            + scores.get("confidence", 0) * CQSSScorer.WEIGHTS["confidence"]
            + scores.get("reasoning_depth", 0) * CQSSScorer.WEIGHTS["reasoning_depth"]
            + scores.get("ethical_policy", 0) * CQSSScorer.WEIGHTS["ethical_policy"]
        )

        return {"total_score": round(total_score, 2), "breakdown": scores}

    # Alias for compatibility
    @staticmethod
    def score_capsule(capsule):
        """Alias for calculate_score."""
        return CQSSScorer.calculate_score(capsule)
