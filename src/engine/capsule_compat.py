"""
Capsule Compatibility Interface

Provides a unified interface for accessing capsule attributes across:
- Legacy SimpleCapsule objects
- Modern Capsule objects
- Raw dictionary representations
"""
import json
import hashlib
from typing import List, Dict, Union

# Import crypto module locally to avoid circular dependencies
# from . import crypto  # Actual import would be uncommented in real implementation


def get_capsule_id(capsule) -> str:
    """Get capsule ID from any capsule representation."""
    if isinstance(capsule, dict):
        return capsule.get("capsule_id")
    return getattr(capsule, "capsule_id", None)


def get_parent_id(capsule) -> str:
    """Get parent capsule ID from any representation."""
    if isinstance(capsule, dict):
        return capsule.get("parent_capsule") or capsule.get("previous_capsule_id")

    # Try modern attribute first
    if hasattr(capsule, "parent_capsule"):
        return capsule.parent_capsule
    # Fallback to legacy attribute
    if hasattr(capsule, "previous_capsule_id"):
        return capsule.previous_capsule_id
    return None


def get_timestamp(capsule):
    """Get timestamp from any capsule representation."""
    if isinstance(capsule, dict):
        return capsule.get("timestamp")
    return getattr(capsule, "timestamp", None)


def is_valid_capsule(capsule) -> bool:
    """Validate capsule structure meets minimum requirements."""
    required = ["capsule_id", "content", "timestamp"]

    if isinstance(capsule, dict):
        return all(key in capsule for key in required)

    return all(hasattr(capsule, attr) for attr in required)


def to_unified_dict(capsule) -> dict:
    """Convert any capsule representation to a unified dictionary."""
    if isinstance(capsule, dict):
        return capsule
    return {
        "capsule_id": get_capsule_id(capsule),
        "content": getattr(capsule, "content", None),
        "timestamp": get_timestamp(capsule),
        "parent_capsule": get_parent_id(capsule),
        "capsule_type": getattr(capsule, "capsule_type", None),
        "agent_id": getattr(capsule, "agent_id", None),
    }


def get_confidence_score(capsule) -> float:
    """Normalize confidence scores across capsule types."""
    if isinstance(capsule, dict):
        return capsule.get("confidence_score", 0.0)
    return getattr(capsule, "confidence_score", 0.0)


def get_reasoning_steps(capsule) -> List[dict]:
    """Extract reasoning traces in standardized format."""
    if isinstance(capsule, dict):
        return capsule.get("reasoning_steps", [])

    # Handle legacy reasoning format
    if hasattr(capsule, "reasoning_steps"):
        return capsule.reasoning_steps
    elif hasattr(capsule, "reasoning_chain"):
        return [
            {"step": i, "content": step}
            for i, step in enumerate(capsule.reasoning_chain)
        ]
    return []


def get_signature(capsule) -> str:
    """Extract cryptographic signature."""
    if isinstance(capsule, dict):
        return capsule.get("signature")
    return getattr(capsule, "signature", None)


def verify_signature(capsule, public_key: str) -> bool:
    """Verify cryptographic signature using UATP standards."""
    # Local import to avoid circular dependencies
    from .crypto import verify_signature as crypto_verify

    signature = get_signature(capsule)
    if not signature:
        return False

    # Create unified content hash
    unified_dict = to_unified_dict(capsule)
    # Remove signature for hashing
    if "signature" in unified_dict:
        del unified_dict["signature"]
    content_str = json.dumps(unified_dict, sort_keys=True)
    content_hash = hashlib.sha256(content_str.encode()).hexdigest()

    return crypto_verify(content_hash, signature, public_key)


def get_contributors(capsule) -> List[str]:
    """Extract contributor IDs for attribution tracking."""
    if isinstance(capsule, dict):
        return capsule.get("contributors", [])
    return getattr(capsule, "contributors", [])


def get_licensing_terms(capsule) -> dict:
    """Extract remix/royalty terms."""
    if isinstance(capsule, dict):
        return capsule.get("licensing", {})
    return getattr(capsule, "licensing_terms", {})
