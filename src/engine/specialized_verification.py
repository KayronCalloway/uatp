"""Integration module for specialized verification in the UATP 7.0 engine.

This module extends the SpecializedCapsuleEngine with verification methods
that leverage the specialized verifier for UATP 7.0 capsule types.
"""

import logging
from typing import List, Tuple, Union

from verifier.specialized_verifier import SpecializedCapsuleVerifier

from capsules.specialized_capsules import SpecializedCapsule
from src.capsule_schema import Capsule

logger = logging.getLogger("uatp.engine.verification")


def verify_specialized_capsule(capsule: Union[Capsule, SpecializedCapsule]) -> bool:
    """Verify a specialized capsule using the appropriate verifier.

    This is intended to be used by the SpecializedCapsuleEngine as its
    verify_capsule implementation.

    Args:
        capsule: The capsule to verify

    Returns:
        bool: True if verification succeeded, False otherwise
    """
    # Use the specialized verifier for all capsules
    valid, message = SpecializedCapsuleVerifier.verify_capsule(capsule)

    if not valid:
        logger.warning(f"Capsule verification failed: {message}")

    return valid


def verify_specialized_chain(capsules: List[Capsule]) -> Tuple[bool, str]:
    """Verify a chain of specialized capsules.

    Args:
        capsules: List of capsules in the chain

    Returns:
        Tuple[bool, str]: (is_valid, message)
    """
    return SpecializedCapsuleVerifier.verify_chain(capsules)
