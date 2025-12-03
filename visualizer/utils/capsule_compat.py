"""
Capsule compatibility utilities for handling both legacy and modern capsule formats.

This module provides robust attribute access for capsules that may be either:
- Dictionary objects (from JSONL files)
- Legacy SimpleCapsule objects 
- Modern Pydantic capsule objects
"""

from typing import Any, Optional, Union, Dict
import json


def get_capsule_attr(
    capsule: Any,
    attr_name: str,
    fallback_attrs: Optional[list] = None,
    default: Any = None,
) -> Any:
    """
    Robustly get an attribute from a capsule, handling dict vs object compatibility.

    Args:
        capsule: The capsule object or dict
        attr_name: Primary attribute name to look for
        fallback_attrs: List of fallback attribute names to try
        default: Default value if attribute not found

    Returns:
        The attribute value or default
    """
    if fallback_attrs is None:
        fallback_attrs = []

    # Try all attribute names in order
    all_attrs = [attr_name] + fallback_attrs

    for attr in all_attrs:
        if isinstance(capsule, dict):
            if attr in capsule:
                return capsule[attr]
        else:
            if hasattr(capsule, attr):
                return getattr(capsule, attr)

    return default


def get_capsule_id(capsule: Any) -> Optional[str]:
    """Get capsule ID from any capsule format."""
    return get_capsule_attr(capsule, "capsule_id", ["id"])


def get_capsule_type(capsule: Any) -> str:
    """Get capsule type from any capsule format."""
    return get_capsule_attr(capsule, "type", ["capsule_type"], "unknown")


def get_parent_capsule_id(capsule: Any) -> Optional[str]:
    """Get parent capsule ID from any capsule format."""
    return get_capsule_attr(capsule, "parent_capsule", ["previous_capsule_id"])


def get_capsule_metadata(capsule: Any) -> Optional[Dict]:
    """Get capsule metadata, parsing JSON if needed."""
    metadata = get_capsule_attr(capsule, "metadata")

    if metadata is None:
        return None

    if isinstance(metadata, str):
        try:
            return json.loads(metadata)
        except json.JSONDecodeError:
            return {"raw": metadata}

    return metadata


def get_confidence_score(capsule: Any) -> Optional[float]:
    """Get confidence score from capsule metadata."""
    metadata = get_capsule_metadata(capsule)
    if metadata and isinstance(metadata, dict):
        return metadata.get("confidence")
    return None


def get_reasoning_trace(capsule: Any) -> Optional[Any]:
    """Get reasoning trace from any capsule format."""
    return get_capsule_attr(capsule, "reasoning_trace", ["reasoning"])


def get_reasoning_steps(capsule: Any) -> Optional[list]:
    """Get reasoning steps as a list, parsing JSON if needed."""
    trace = get_reasoning_trace(capsule)

    if trace is None:
        return None

    if isinstance(trace, str):
        try:
            parsed = json.loads(trace)
            if isinstance(parsed, list):
                return parsed
        except json.JSONDecodeError:
            pass

    if isinstance(trace, list):
        return trace

    return None


def capsule_to_dict(capsule: Any) -> Dict[str, Any]:
    """Convert any capsule format to a dictionary for serialization."""
    if isinstance(capsule, dict):
        return capsule.copy()

    if hasattr(capsule, "model_dump"):
        # Pydantic object
        return capsule.model_dump()

    if hasattr(capsule, "__dict__"):
        # Regular object
        return capsule.__dict__.copy()

    # Fallback - try to extract key attributes
    result = {}
    for attr in [
        "capsule_id",
        "capsule_type",
        "type",
        "content",
        "metadata",
        "timestamp",
    ]:
        value = get_capsule_attr(capsule, attr)
        if value is not None:
            result[attr] = value

    return result


def is_valid_capsule(capsule: Any) -> bool:
    """Check if an object appears to be a valid capsule."""
    if capsule is None:
        return False

    # Must have either capsule_id or id
    capsule_id = get_capsule_id(capsule)
    if not capsule_id:
        return False

    # Must have some type identifier - allow 'unknown' for compatibility
    capsule_type = get_capsule_type(capsule)
    if not capsule_type:
        return False

    return True
