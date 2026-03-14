"""
UATP Python SDK - Cryptographically verifiable AI decisions
"""

from .client import UATP, CapsuleProof, CertificationResult
from .crypto import (
    LocalSigner,
    SignedCapsule,
    UserKeyManager,
    UserKeyPair,
    get_user_key_manager,
    verify_capsule_standalone,
)
from .models import (
    Alternative,
    DataSource,
    Outcome,
    OutcomeStatus,
    PlainLanguageSummary,
    ReasoningStep,
    RiskAssessment,
    create_rich_reasoning_step,
    create_simple_reasoning_step,
)

__version__ = "0.3.0"
__all__ = [
    "UATP",
    "CertificationResult",
    "CapsuleProof",
    # Zero-trust local signing
    "LocalSigner",
    "SignedCapsule",
    "UserKeyManager",
    "UserKeyPair",
    "get_user_key_manager",
    "verify_capsule_standalone",
    # Rich data models
    "DataSource",
    "Alternative",
    "RiskAssessment",
    "ReasoningStep",
    "Outcome",
    "OutcomeStatus",
    "PlainLanguageSummary",
    # Helpers
    "create_simple_reasoning_step",
    "create_rich_reasoning_step",
]
