import uuid
from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, Optional

from pydantic import BaseModel, ConfigDict, Field

from src.insurance.models import ClaimStatus, PolicyStatus


# Base Schemas
class InsurancePolicyBase(BaseModel):
    user_id: uuid.UUID
    premium_amount: Decimal = Field(..., gt=0)
    coverage_amount: Decimal = Field(..., gt=0)
    policy_type: str = "flight_delay"
    start_date: datetime
    end_date: datetime
    parameters: Dict[str, Any] = Field(
        ..., description="Parameters for the policy, e.g., {'flight_number': 'UA123'}"
    )


class InsuranceClaimBase(BaseModel):
    policy_id: uuid.UUID
    event_timestamp: datetime
    reason: Optional[str] = None


class AILiabilityEventLogBase(BaseModel):
    source_entity_id: str
    event_type: str
    event_timestamp: datetime
    payload: Dict[str, Any]


# Schemas for Creating new objects
class InsurancePolicyCreate(InsurancePolicyBase):
    pass


class AILiabilityEventLogCreate(AILiabilityEventLogBase):
    pass


class InsuranceClaimCreate(InsuranceClaimBase):
    pass


# Schemas for Reading/Returning data from API
class InsurancePolicyResponse(InsurancePolicyBase):
    id: uuid.UUID
    policy_number: str
    status: PolicyStatus
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AILiabilityEventLogResponse(AILiabilityEventLogBase):
    id: uuid.UUID
    claim_id: uuid.UUID
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class InsuranceClaimResponse(InsuranceClaimBase):
    id: uuid.UUID
    claim_status: ClaimStatus
    payout_amount: Optional[Decimal]
    capsule_id: Optional[str]
    created_at: datetime
    updated_at: datetime
    event_logs: list[AILiabilityEventLogResponse] = []

    model_config = ConfigDict(from_attributes=True)


# Schema for full policy details including claims
class FullInsurancePolicyResponse(InsurancePolicyResponse):
    claims: list[InsuranceClaimResponse] = []
