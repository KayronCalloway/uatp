import uuid
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.dependencies import get_db
from src.insurance import schemas, service

router = APIRouter(
    prefix="/insurance",
    tags=["insurance"],
    responses={404: {"description": "Not found"}},
)


@router.post("/policies", response_model=schemas.InsurancePolicyResponse)
async def create_policy(
    policy: schemas.InsurancePolicyCreate, db: AsyncSession = Depends(get_db)
):
    """Create a new insurance policy."""
    insurance_service = service.InsuranceService(db)
    return await insurance_service.create_policy(policy_data=policy)


@router.get("/policies/{policy_id}", response_model=schemas.FullInsurancePolicyResponse)
async def get_policy(policy_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    """Retrieve a policy and its associated claims."""
    insurance_service = service.InsuranceService(db)
    db_policy = await insurance_service.get_policy_by_id(policy_id)
    if db_policy is None:
        raise HTTPException(status_code=404, detail="Policy not found")
    return db_policy


@router.post("/claims", response_model=schemas.InsuranceClaimResponse)
async def create_claim(
    claim: schemas.InsuranceClaimCreate, db: AsyncSession = Depends(get_db)
):
    """Create a new insurance claim."""
    insurance_service = service.InsuranceService(db)
    return await insurance_service.create_claim(claim_data=claim)


@router.post(
    "/claims/{claim_id}/logs", response_model=schemas.AILiabilityEventLogResponse
)
async def add_event_log_to_claim(
    claim_id: uuid.UUID,
    event_log: schemas.AILiabilityEventLogCreate,
    db: AsyncSession = Depends(get_db),
):
    """Add an AI liability event log to an existing claim."""
    insurance_service = service.InsuranceService(db)
    return await insurance_service.add_event_log_to_claim(
        claim_id=claim_id, event_log_data=event_log
    )


@router.get("/claims/{claim_id}", response_model=schemas.InsuranceClaimResponse)
async def get_claim(claim_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    """Retrieve a claim and its associated event logs."""
    insurance_service = service.InsuranceService(db)
    db_claim = await insurance_service.get_claim_with_logs(claim_id)
    if db_claim is None:
        raise HTTPException(status_code=404, detail="Claim not found")
    return db_claim


@router.post("/claims/{claim_id}/adjudicate")
async def adjudicate_claim(claim_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    """Trigger the liability adjudication process for a claim."""
    insurance_service = service.InsuranceService(db)
    result = await insurance_service.adjudicate_claim(claim_id)
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return result
