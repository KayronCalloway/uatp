import uuid
from datetime import datetime
from enum import Enum

from sqlalchemy import (
    JSON,
    Column,
    DateTime,
    ForeignKey,
    Numeric,
    String,
)
from sqlalchemy import (
    Enum as SQLEnum,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from src.core.database import db


class PolicyStatus(str, Enum):
    ACTIVE = "active"
    EXPIRED = "expired"
    PAID_OUT = "paid_out"
    CANCELLED = "cancelled"


class ClaimStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    PAID = "paid"


class InsurancePolicy(db.Base):
    __tablename__ = "insurance_policies"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    policy_number = Column(String, unique=True, nullable=False, index=True)
    premium_amount = Column(Numeric(10, 2), nullable=False)
    coverage_amount = Column(Numeric(10, 2), nullable=False)
    policy_type = Column(String, nullable=False, default="flight_delay")
    status = Column(SQLEnum(PolicyStatus), nullable=False, default=PolicyStatus.ACTIVE)
    start_date = Column(DateTime(timezone=True), nullable=False)
    end_date = Column(DateTime(timezone=True), nullable=False)
    parameters = Column(
        JSON, nullable=False
    )  # e.g., {'flight_number': 'UA123', 'departure_date': '2025-12-25'}
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(
        DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow
    )

    user = relationship("UserModel", back_populates="policies")
    claims = relationship(
        "InsuranceClaim", back_populates="policy", cascade="all, delete-orphan"
    )


class AILiabilityEventLog(db.Base):
    __tablename__ = "ai_liability_event_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    claim_id = Column(
        UUID(as_uuid=True), ForeignKey("insurance_claims.id"), nullable=False
    )
    source_entity_id = Column(
        String, nullable=False, index=True
    )  # e.g., Robotaxi Vehicle ID
    event_type = Column(
        String, nullable=False
    )  # e.g., 'sensor_reading', 'decision_log'
    event_timestamp = Column(DateTime(timezone=True), nullable=False)
    payload = Column(JSON, nullable=False)  # The raw data from the event
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    claim = relationship("InsuranceClaim", back_populates="event_logs")


class InsuranceClaim(db.Base):
    __tablename__ = "insurance_claims"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    policy_id = Column(
        UUID(as_uuid=True), ForeignKey("insurance_policies.id"), nullable=False
    )
    claim_status = Column(
        SQLEnum(ClaimStatus), nullable=False, default=ClaimStatus.PENDING
    )
    payout_amount = Column(Numeric(10, 2), nullable=True)
    event_timestamp = Column(DateTime(timezone=True), nullable=False)
    capsule_id = Column(
        String, nullable=True, index=True
    )  # Link to the UATP capsule that triggered the claim
    reason = Column(String, nullable=True)  # e.g., 'Flight delayed by 3 hours'
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(
        DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow
    )

    policy = relationship("InsurancePolicy", back_populates="claims")
    event_logs = relationship(
        "AILiabilityEventLog", back_populates="claim", cascade="all, delete-orphan"
    )
