"""
Verification Facet - Proof that signature was verified.

Records:
- Verification result
- Method used
- When verified
- Any errors encountered
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional

from src.schema.base import RunFacet, utc_now


@dataclass
class UATPVerificationRunFacet(RunFacet):
    """
    Verification proof attached to a capsule run.

    Records the result of cryptographic verification.
    """

    # Verification result
    is_verified: bool = False
    verification_method: str = "ed25519_rfc3161"  # Method used

    # Timing
    verified_at: datetime = field(default_factory=utc_now)

    # Verification context
    verifier_id: Optional[str] = None  # Who performed verification
    public_key_id: Optional[str] = None  # Which key was used

    # Chain verification (if part of workflow)
    chain_verified: bool = False
    chain_length: int = 0
    chain_position: int = 0

    # Errors (if verification failed)
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

    # Trust score (computed from verification)
    trust_score: Optional[float] = None  # 0.0 - 1.0

    def is_fully_verified(self) -> bool:
        """Check if all verification checks passed."""
        return self.is_verified and len(self.errors) == 0

    def add_error(self, error: str) -> None:
        """Add a verification error."""
        self.errors.append(error)
        self.is_verified = False

    def add_warning(self, warning: str) -> None:
        """Add a verification warning (doesn't fail verification)."""
        self.warnings.append(warning)
