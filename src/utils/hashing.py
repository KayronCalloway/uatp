import hashlib
from typing import Any, Dict

import orjson

# Use orjson for high-performance, deterministic JSON serialization
# OPT_SORT_KEYS is critical for ensuring that the output is consistent
# for hashing purposes.


def get_deterministic_hash(data: Dict[str, Any]) -> str:
    """
    Generates a SHA-256 hash of a dictionary in a deterministic way.

    Args:
        data: The dictionary to hash.

    Returns:
        A hexadecimal string representing the SHA-256 hash.
    """
    # The `option=orjson.OPT_SORT_KEYS` is crucial for determinism.
    serialized_data = orjson.dumps(data, option=orjson.OPT_SORT_KEYS)
    return hashlib.sha256(serialized_data).hexdigest()
