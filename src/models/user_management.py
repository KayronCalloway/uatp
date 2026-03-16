"""
User Management Models for UATP Capsule Engine

This module defines SQLAlchemy models for user session and identity verification.
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import JSON, Column, DateTime, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from src.core.database import db


class UserSessionModel(db.Base):
    __tablename__ = "user_sessions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    session_token = Column(String, unique=True, index=True, nullable=False)
    created_at = Column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    expires_at = Column(DateTime(timezone=True), nullable=False)
    user_agent = Column(String)
    ip_address = Column(String)

    user = relationship("UserModel", back_populates="sessions")


class IdentityVerificationModel(db.Base):
    __tablename__ = "identity_verifications"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    verification_token = Column(String, unique=True, index=True, nullable=False)
    method = Column(String, nullable=False)  # e.g., 'email', 'sms'
    status = Column(String, default="pending")  # e.g., 'pending', 'verified', 'failed'
    created_at = Column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    expires_at = Column(DateTime(timezone=True), nullable=False)
    verified_at = Column(DateTime(timezone=True), nullable=True)
    details = Column(JSON)  # For storing additional details like attempts, etc.

    user = relationship("UserModel", back_populates="verifications")
