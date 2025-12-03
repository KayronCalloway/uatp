"""
Privacy module for UATP Capsule Engine.
Provides zero-knowledge proofs and privacy-preserving capsule operations.
"""

from .capsule_privacy import (
    DEFAULT_PRIVACY_POLICIES,
    CapsulePrivacyEngine,
    PrivacyLevel,
    PrivacyPolicy,
    PrivateCapsule,
    privacy_engine,
)

__all__ = [
    "CapsulePrivacyEngine",
    "PrivacyPolicy",
    "PrivacyLevel",
    "PrivateCapsule",
    "privacy_engine",
    "DEFAULT_PRIVACY_POLICIES",
]
