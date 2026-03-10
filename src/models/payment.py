import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from src.core.database import db


class TransactionModel(db.Base):
    __tablename__ = "transactions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(String, nullable=False, index=True)
    amount = Column(Float, nullable=False)
    currency = Column(String(10), nullable=False, default="USD")
    status = Column(
        Enum(
            "pending",
            "processing",
            "completed",
            "failed",
            "cancelled",
            name="transaction_status_enum",
        ),
        nullable=False,
        default="pending",
        index=True,
    )
    payout_method_id = Column(UUID(as_uuid=True), ForeignKey("payout_methods.id"))
    payout_method = relationship("PayoutMethodModel")

    external_transaction_id = Column(String, index=True)
    processor_response = Column(JSON)
    processing_fee = Column(Float, default=0.0)
    net_amount = Column(Float, default=0.0)
    failure_reason = Column(Text)

    created_at = Column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    processed_at = Column(DateTime(timezone=True))

    def __repr__(self):
        return f"<TransactionModel {self.id} [User: {self.user_id}] - {self.status}>"


class PayoutMethodModel(db.Base):
    __tablename__ = "payout_methods"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True
    )
    user = relationship("UserModel", back_populates="payout_methods")
    method_type = Column(
        Enum("paypal", "stripe", "crypto", "bank_transfer", name="payout_method_enum"),
        nullable=False,
    )
    payout_details = Column(JSON, nullable=False)
    is_default = Column(Boolean, default=True)
    is_active = Column(Boolean, default=True)

    created_at = Column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    updated_at = Column(
        DateTime(timezone=True), onupdate=lambda: datetime.now(timezone.utc)
    )

    def __repr__(self):
        return (
            f"<PayoutMethodModel {self.id} [User: {self.user_id}] - {self.method_type}>"
        )
