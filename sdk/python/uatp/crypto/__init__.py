"""
UATP Crypto Package - Zero-Trust Local Signing

This package provides local cryptographic signing for UATP capsules.
Private keys never leave the user's device.
"""

from .local_signer import LocalSigner, SignedCapsule, verify_capsule_standalone
from .user_key_manager import UserKeyManager, UserKeyPair, get_user_key_manager

__all__ = [
    "LocalSigner",
    "SignedCapsule",
    "UserKeyManager",
    "UserKeyPair",
    "get_user_key_manager",
    "verify_capsule_standalone",
]
