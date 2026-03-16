import uuid
from datetime import datetime, timezone

from sqlalchemy import JSON, Boolean, Column, DateTime, Float, Integer, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from src.core.database import db


class UserModel(db.Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String, unique=True, nullable=False, index=True)
    username = Column(String, unique=True, nullable=False, index=True)
    full_name = Column(String, nullable=False)
    hashed_password = Column(String, nullable=False)

    status = Column(String, default="pending")
    verification_status = Column(String, default="unverified")

    # Relationships
    sessions = relationship(
        "UserSessionModel", back_populates="user", cascade="all, delete-orphan"
    )
    verifications = relationship(
        "IdentityVerificationModel", back_populates="user", cascade="all, delete-orphan"
    )
    capsules = relationship("CapsuleModel", back_populates="owner")

    # Attribution settings
    attribution_enabled = Column(Boolean, default=True)
    attribution_threshold = Column(Float, default=0.01)
    uba_participation = Column(Boolean, default=True)

    # Payment settings
    payout_threshold = Column(Float, default=10.0)

    # Privacy settings
    data_sharing_consent = Column(Boolean, default=False)
    analytics_consent = Column(Boolean, default=False)
    marketing_consent = Column(Boolean, default=False)

    # Attribution stats
    total_earnings = Column(Float, default=0.0)
    total_attributions = Column(Integer, default=0)
    average_confidence = Column(Float, default=0.0)

    # Metadata
    created_at = Column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    last_login = Column(DateTime(timezone=True))
    user_metadata = Column(JSON, default={})

    def __repr__(self):
        return f"<UserModel {self.id} - {self.username}>"
