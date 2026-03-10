"""Patch for SpecializedCapsuleEngine to integrate specialized verification.

This patch extends the SpecializedCapsuleEngine class with enhanced verification
for UATP 7.0 capsule types. Copy these methods into the SpecializedCapsuleEngine
class or use monkey patching to apply them.
"""

from typing import List, Tuple

from engine.specialized_verification import (
    verify_specialized_capsule,
    verify_specialized_chain,
)
from src.capsule_schema import Capsule


def verify_capsule(self, capsule: Capsule) -> bool:
    """Verify a capsule's cryptographic signature and structure.

    This method overrides the base CapsuleEngine's verify_capsule method
    to provide specialized verification for UATP 7.0 capsule types.

    Args:
        capsule: The capsule to verify

    Returns:
        bool: True if the capsule is valid, False otherwise
    """
    return verify_specialized_capsule(capsule)


def verify_chain(self, capsules: List[Capsule]) -> Tuple[bool, str]:
    """Verify a chain of capsules.

    This method extends the base verification to add specialized checks
    between capsules in the chain.

    Args:
        capsules: List of capsules in the chain

    Returns:
        Tuple[bool, str]: (is_valid, message)
    """
    return verify_specialized_chain(capsules)
