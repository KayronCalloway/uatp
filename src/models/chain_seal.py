"""
ChainSealModel - SQLAlchemy ORM model for chain seal records.

UATP 7.2: Persists cryptographic chain seals that provide legal admissibility
and tamper-evidence for capsule chains.

Design Decision:
    Chain seals capture a point-in-time cryptographic commitment to a chain's
    state. The signature can be verified independently to prove chain integrity.
"""

from datetime import datetime, timezone
from typing import TYPE_CHECKING

from sqlalchemy import (
    Column,
    DateTime,
    Index,
    Integer,
    String,
    Text,
)

from src.core.database import db

if TYPE_CHECKING:
    pass


class ChainSealModel(db.Base):
    """
    Persisted chain seal record.

    Each seal captures a cryptographic commitment to the state of a capsule chain
    at a specific point in time. Seals provide:
    - Legal admissibility (timestamped, signed evidence)
    - Tamper detection (chain_state_hash comparison)
    - Audit trail (who sealed, when, why)
    """

    __tablename__ = "chain_seals"
    __table_args__ = (
        Index("ix_chain_seal_id", "seal_id"),
        Index("ix_chain_seal_chain_id", "chain_id"),
        Index("ix_chain_seal_timestamp", "timestamp"),
        Index("ix_chain_seal_signer", "signer_id"),
        {"extend_existing": True},
    )

    id = Column(Integer, primary_key=True)

    # Seal identification
    seal_id = Column(
        String(64),
        unique=True,
        nullable=False,
        comment="Unique seal identifier (seal-{timestamp}-{uuid})",
    )

    chain_id = Column(
        String(64),
        nullable=False,
        comment="Identifier for the chain being sealed",
    )

    # Seal timing
    timestamp = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        comment="When the seal was created",
    )

    # Signer information
    signer_id = Column(
        String(128),
        nullable=False,
        comment="Identifier for the sealing entity (user, org, system)",
    )

    # Cryptographic data
    chain_state_hash = Column(
        String(64),
        nullable=False,
        comment="SHA-256 hash of the canonicalized chain state at seal time",
    )

    signature = Column(
        Text,
        nullable=False,
        comment="Base64-encoded Ed25519 signature of the seal data",
    )

    verify_key = Column(
        String(128),
        nullable=False,
        comment="Hex-encoded Ed25519 verification key",
    )

    # Metadata
    note = Column(
        String(500),
        nullable=True,
        comment="Optional note about the purpose of this seal",
    )

    capsule_count = Column(
        Integer,
        default=0,
        nullable=False,
        comment="Number of capsules in the chain at seal time",
    )

    # Capsule IDs included in this seal (JSON list stored as text for simplicity)
    capsule_ids = Column(
        Text,
        nullable=True,
        comment="JSON list of capsule IDs included in this seal",
    )

    def __repr__(self) -> str:
        return (
            f"<ChainSeal("
            f"seal_id='{self.seal_id}', "
            f"chain_id='{self.chain_id}', "
            f"signer='{self.signer_id}')>"
        )

    def to_dict(self) -> dict:
        """Convert to dictionary representation."""
        import json

        return {
            "id": self.id,
            "seal_id": self.seal_id,
            "chain_id": self.chain_id,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "signer_id": self.signer_id,
            "chain_state_hash": self.chain_state_hash,
            "signature": self.signature,
            "verify_key": self.verify_key,
            "note": self.note,
            "capsule_count": self.capsule_count,
            "capsule_ids": json.loads(self.capsule_ids) if self.capsule_ids else [],
        }
