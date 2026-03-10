"""
Capsule Outcome Models
Tracks actual outcomes of capsules to validate predictions and improve confidence calibration
"""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field
from sqlalchemy import ARRAY, Column, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB

from src.core.database import db


class CapsuleOutcomeModel(db.Base):
    """Database model for capsule outcomes."""

    __tablename__ = "capsule_outcomes"

    id = Column(Integer, primary_key=True)
    capsule_id = Column(
        String, ForeignKey("capsules.capsule_id", ondelete="CASCADE"), nullable=False
    )

    predicted_outcome = Column(Text)
    actual_outcome = Column(Text, nullable=False)
    outcome_quality_score = Column(Float)  # 0.0-1.0

    outcome_timestamp = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    validation_method = Column(
        String(50)
    )  # user_feedback, automated_test, system_metric
    validator_id = Column(String)

    notes = Column(Text)

    created_at = Column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )


class ConfidenceCalibrationModel(db.Base):
    """Database model for confidence calibration data."""

    __tablename__ = "confidence_calibration"

    id = Column(Integer, primary_key=True)

    domain = Column(String(100))  # backend-api, frontend-ui, etc.
    confidence_bucket = Column(Float, nullable=False)  # 0.0-1.0

    predicted_count = Column(Integer, default=0)
    actual_success_count = Column(Integer, default=0)

    calibration_error = Column(Float)  # predicted - actual
    recommended_adjustment = Column(Float)

    sample_capsule_ids = Column(ARRAY(String))

    last_updated = Column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )


class ReasoningPatternModel(db.Base):
    """Database model for discovered reasoning patterns."""

    __tablename__ = "reasoning_patterns"

    pattern_id = Column(String, primary_key=True)

    pattern_type = Column(String(50))  # sequence, decision_tree, failure_mode
    pattern_name = Column(String(200))
    pattern_description = Column(Text)

    pattern_structure = Column(JSONB)  # Detailed pattern structure

    success_rate = Column(Float)  # 0.0-1.0
    usage_count = Column(Integer, default=0)

    applicable_domains = Column(ARRAY(String))
    example_capsule_ids = Column(ARRAY(String))

    confidence_impact = Column(Float)  # +/- adjustment to confidence

    created_at = Column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )


# Pydantic schemas for API


class OutcomeCreate(BaseModel):
    """Schema for creating an outcome."""

    capsule_id: str = Field(..., description="ID of the capsule this outcome is for")
    predicted_outcome: Optional[str] = Field(None, description="What was predicted")
    actual_outcome: str = Field(..., description="What actually happened")
    outcome_quality_score: Optional[float] = Field(
        None, ge=0, le=1, description="Quality score 0-1"
    )
    validation_method: Optional[str] = Field(
        None, description="How outcome was validated"
    )
    validator_id: Optional[str] = Field(None, description="Who validated")
    notes: Optional[str] = Field(None, description="Additional notes")


class OutcomeResponse(BaseModel):
    """Schema for outcome response."""

    id: int
    capsule_id: str
    predicted_outcome: Optional[str]
    actual_outcome: str
    outcome_quality_score: Optional[float]
    outcome_timestamp: datetime
    validation_method: Optional[str]
    validator_id: Optional[str]
    notes: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


class OutcomeListResponse(BaseModel):
    """Schema for list of outcomes."""

    outcomes: List[OutcomeResponse]
    total: int


class CalibrationDataResponse(BaseModel):
    """Schema for calibration data."""

    domain: Optional[str]
    confidence_bucket: float
    predicted_count: int
    actual_success_count: int
    calibration_error: Optional[float]
    recommended_adjustment: Optional[float]
    success_rate: float  # actual_success / predicted_count

    class Config:
        from_attributes = True


class ReasoningPatternResponse(BaseModel):
    """Schema for reasoning pattern."""

    pattern_id: str
    pattern_type: str
    pattern_name: str
    pattern_description: str
    pattern_structure: Dict[str, Any]
    success_rate: float
    usage_count: int
    applicable_domains: List[str]
    example_capsule_ids: List[str]
    confidence_impact: Optional[float]
    created_at: datetime

    class Config:
        from_attributes = True


class ReasoningPatternListResponse(BaseModel):
    """Schema for list of patterns."""

    patterns: List[ReasoningPatternResponse]
    total: int
