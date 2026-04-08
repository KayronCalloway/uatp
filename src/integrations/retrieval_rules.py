#!/usr/bin/env python3
"""
Retrieval Rules - THE FILE GEMMA MODIFIES
==========================================

This file contains the knowledge retrieval optimization rules.
Gemma experiments with different rules to maximize retrieval_accuracy.

To run an experiment:
    python3 retrieval_evaluate.py

The metric is retrieval_accuracy (higher is better, max 1.0).
"""

from typing import Dict, List, Tuple

# ============================================================================
# RETRIEVAL RULES - Gemma modifies this section
# ============================================================================

# Query expansion: map vague queries to more specific terms
# Format: "trigger phrase" -> ["additional", "search", "terms"]
QUERY_EXPANSIONS: Dict[str, List[str]] = {
    "who am i": ["name", "called"],
    "where am i from": ["location", "city", "live", "from"],
    "my location": ["city", "from", "live"],
    "what city": ["location", "from", "live"],
    "what music": ["rappers", "artists", "favorite", "like", "love"],
    "music i like": ["rappers", "artists", "favorite"],
    "capsule signing": ["Ed25519", "cryptographic", "hash", "sign"],
    "how to sign": ["Ed25519", "cryptographic", "signature"],
    "what worked": ["fixed", "success", "resolved", "solved"],
}

# Failure patterns: responses matching these are demoted
# Lower confidence multiplier = more demotion
FAILURE_PATTERNS: List[Tuple[str, float]] = [
    ("i do not know", 0.3),
    ("i don't know", 0.3),
    ("i cannot", 0.3),
    ("i can't", 0.3),
    ("i apologize", 0.3),
    ("i'm sorry", 0.4),
    ("i am sorry", 0.4),
    ("i don't have access", 0.3),
    ("i do not have access", 0.3),
    ("not explicitly told me", 0.3),
    ("do not have the ability", 0.3),
    ("outside my capabilities", 0.3),
]

# Boost patterns: responses matching these get boosted
# Higher multiplier = more boost
# NOTE: Be specific! "you are" matches "You are analyzing UATP" which is wrong
BOOST_PATTERNS: List[Tuple[str, float]] = [
    ("your name is", 1.5),
    ("you mentioned", 1.3),
    ("you said", 1.3),
    ("you told me", 1.4),
    ("i remember you", 1.3),
    ("you live in", 1.5),
    ("you are from", 1.5),
    ("you like", 1.4),
    ("you love", 1.4),
    ("your favorite", 1.5),
    ("fantastic pairing", 1.3),
    ("incredible taste", 1.3),
    ("deeply personal", 1.3),
    ("Ed25519", 2.0),
    ("cryptographic assurance", 1.5),
    ("tamper-proof", 1.5),
]

# Demotion patterns: irrelevant content that should be ranked lower
DEMOTION_PATTERNS: List[Tuple[str, float]] = [
    ("you are analyzing", 0.3),  # Code analysis context, not personal facts
    ("## source files", 0.3),  # Code dumps
    ("```python", 0.5),  # Code blocks often irrelevant to personal queries
    ("```", 0.7),  # Any code block
]

# Relevance threshold: minimum score to include a result
# Lower = more results, higher = stricter filtering
RELEVANCE_THRESHOLD: float = 0.012

# Maximum results to consider for reranking
MAX_RESULTS: int = 10

# Response weight: how much to weight the response vs the prompt in embeddings
# Higher = response matters more (where facts typically are)
RESPONSE_WEIGHT: int = 2  # Response repeated this many times


class RetrievalOptimizer:
    """Optimizes retrieval based on the rules above."""

    def expand_query(self, query: str) -> str:
        """Expand query with additional search terms."""
        query_lower = query.lower()
        expansions = []

        for trigger, terms in QUERY_EXPANSIONS.items():
            if trigger in query_lower:
                expansions.extend(terms)

        if expansions:
            return f"{query} {' '.join(expansions)}"
        return query

    def score_result(self, content: str, base_score: float) -> float:
        """Apply boost/demotion based on content patterns."""
        content_lower = content.lower()
        multiplier = 1.0

        # Apply failure demotions (worst one wins)
        for pattern, factor in FAILURE_PATTERNS:
            if pattern in content_lower:
                multiplier *= factor
                break

        # Apply content demotions (irrelevant content)
        for pattern, factor in DEMOTION_PATTERNS:
            if pattern in content_lower:
                multiplier *= factor
                break  # Only apply worst demotion

        # Apply boosts (cumulative, but only if not already demoted)
        if multiplier >= 0.5:
            for pattern, factor in BOOST_PATTERNS:
                if pattern in content_lower:
                    multiplier *= factor

        return base_score * multiplier

    def should_include(self, score: float) -> bool:
        """Check if result meets relevance threshold."""
        return score >= RELEVANCE_THRESHOLD

    def get_response_weight(self) -> int:
        """Get response weight for embedding."""
        return RESPONSE_WEIGHT

    def get_max_results(self) -> int:
        """Get max results to retrieve."""
        return MAX_RESULTS


# ============================================================================
# DO NOT MODIFY BELOW THIS LINE
# ============================================================================


def get_optimizer() -> RetrievalOptimizer:
    """Get the retrieval optimizer instance."""
    return RetrievalOptimizer()
