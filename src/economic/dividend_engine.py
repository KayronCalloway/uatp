"""
Capsule Dividend Engine

Implements UATP's economic attribution system:
1. Distributes 50% of capsule value to direct contributors
2. Allocates 50% to parent capsule contributors
3. Integrates with Common Attribution Fund
"""
from typing import Dict, List
from ..engine.capsule_compat import get_capsule_id, get_parent_id, get_contributors


def calculate_dividends(chain: List) -> Dict[str, float]:
    """
    Calculate dividend allocations for a capsule chain.

    Args:
        chain: List of capsules in chronological order

    Returns:
        Mapping of contributor IDs to dividend amounts
    """
    # Build contributor map and parent map
    contributors_map = {}
    parent_map = {}
    for capsule in chain:
        capsule_id = get_capsule_id(capsule)
        contributors_map[capsule_id] = get_contributors(capsule)
        parent_map[capsule_id] = get_parent_id(capsule)

    # Initialize dividends
    dividends = {}
    # Track value to propagate through ancestry
    value_to_propagate = {get_capsule_id(capsule): 1.0 for capsule in chain}

    # Process in reverse chronological order
    for capsule in reversed(chain):
        capsule_id = get_capsule_id(capsule)
        current_value = value_to_propagate[capsule_id]
        contributors = contributors_map[capsule_id]

        if contributors:
            # Direct contributors get 50% of current value
            direct_share = current_value * 0.5 / len(contributors)
            for contributor in contributors:
                dividends[contributor] = dividends.get(contributor, 0) + direct_share

            # Propagate 50% to parent
            parent_id = parent_map[capsule_id]
            if parent_id and parent_id in value_to_propagate:
                value_to_propagate[parent_id] += current_value * 0.5

    return dividends
