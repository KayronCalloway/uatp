"""
Economics API Routes (FastAPI)
===============================

API endpoints for economic features including metrics, attribution models, and economic analytics.

Converted from Quart to FastAPI for compatibility with current application architecture.
"""

from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from uuid import uuid4

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from src.utils.timezone_utils import utc_now

# Router configuration
router = APIRouter(prefix="/economics", tags=["Economics"])


# Pydantic models
class AttributionComputeRequest(BaseModel):
    capsule_id: str
    contributors: List[Dict[str, Any]]
    model_id: str
    parameters: Dict[str, Any] = {}


def generate_id() -> str:
    """Generate a unique ID"""
    return str(uuid4())[:8]


def utc_now() -> datetime:
    """Get current UTC datetime"""
    return utc_now()


@router.get("/metrics")
async def get_economic_metrics():
    """Get economic metrics and statistics."""
    try:
        metrics = {
            "total_attribution_value": 1247892.50,
            "monthly_growth": 0.23,
            "active_contributors": 89,
            "total_transactions": 5438,
            "average_transaction_value": 229.45,
            "top_earners": [
                {
                    "agent_id": "agent-001",
                    "name": "GPT-4 Assistant",
                    "total_earnings": 45892.30,
                    "monthly_earnings": 5234.50,
                    "transactions": 234,
                    "avg_contribution_score": 0.89,
                },
                {
                    "agent_id": "agent-002",
                    "name": "Claude Research",
                    "total_earnings": 38467.20,
                    "monthly_earnings": 4123.80,
                    "transactions": 189,
                    "avg_contribution_score": 0.85,
                },
                {
                    "agent_id": "agent-003",
                    "name": "Gemini Analytics",
                    "total_earnings": 32156.75,
                    "monthly_earnings": 3567.90,
                    "transactions": 156,
                    "avg_contribution_score": 0.82,
                },
            ],
            "recent_transactions": [
                {
                    "transaction_id": "tx_001",
                    "agent_id": "agent-001",
                    "amount": 245.30,
                    "type": "attribution_reward",
                    "timestamp": (datetime.now() - timedelta(hours=2)).isoformat(),
                    "capsule_id": "cap_12345",
                    "description": "Attribution reward for AI assistance",
                },
                {
                    "transaction_id": "tx_002",
                    "agent_id": "agent-002",
                    "amount": 189.50,
                    "type": "collaboration_bonus",
                    "timestamp": (datetime.now() - timedelta(hours=4)).isoformat(),
                    "capsule_id": "cap_12346",
                    "description": "Collaboration bonus for multi-agent task",
                },
            ],
            "distribution_by_type": {
                "attribution_rewards": 567892.30,
                "collaboration_bonuses": 234567.80,
                "quality_bonuses": 189432.40,
                "governance_rewards": 156000.00,
                "referral_bonuses": 99000.00,
            },
            "monthly_trend": [
                {"month": "2024-01", "total_value": 892456.20, "transactions": 4123},
                {"month": "2024-02", "total_value": 945678.30, "transactions": 4456},
                {"month": "2024-03", "total_value": 1087234.50, "transactions": 4789},
                {"month": "2024-04", "total_value": 1156789.20, "transactions": 5012},
                {"month": "2024-05", "total_value": 1247892.50, "transactions": 5438},
            ],
        }
        return metrics
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/attribution/models")
async def get_attribution_models():
    """Get available attribution models."""
    try:
        models = [
            {
                "model_id": "linear_v1",
                "name": "Linear Attribution Model",
                "description": "Simple linear attribution based on contribution percentage",
                "version": "1.0.0",
                "status": "active",
                "accuracy": 0.85,
                "fairness_score": 0.78,
            },
            {
                "model_id": "shapley_v2",
                "name": "Shapley Value Attribution",
                "description": "Game-theoretic attribution using Shapley values",
                "version": "2.1.0",
                "status": "active",
                "accuracy": 0.92,
                "fairness_score": 0.89,
            },
            {
                "model_id": "attention_v1",
                "name": "Attention-Based Attribution",
                "description": "Attribution based on attention mechanisms in AI models",
                "version": "1.2.0",
                "status": "experimental",
                "accuracy": 0.88,
                "fairness_score": 0.81,
            },
        ]
        return models
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/attribution/analysis")
async def get_attribution_analysis():
    """Get attribution analysis and insights."""
    try:
        analysis = {
            "summary": {
                "total_attributions": 27891,
                "total_value_attributed": 1247892.50,
                "unique_contributors": 89,
                "average_attribution_value": 44.78,
            },
            "fairness_metrics": {
                "gini_coefficient": 0.34,
                "equal_opportunity": 0.87,
                "demographic_parity": 0.82,
            },
            "quality_indicators": {
                "dispute_rate": 0.03,
                "user_satisfaction": 0.86,
                "system_reliability": 0.94,
            },
        }
        return analysis
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/attribution/compute")
async def compute_attribution(request: AttributionComputeRequest):
    """Compute attribution for a specific scenario."""
    try:
        attribution_id = generate_id()
        results = {
            "attribution_id": attribution_id,
            "capsule_id": request.capsule_id,
            "model_id": request.model_id,
            "computed_at": utc_now().isoformat(),
            "processing_time": 0.156,
            "total_value": 245.30,
            "attributions": [
                {
                    "contributor_id": "agent-001",
                    "contribution_score": 0.45,
                    "attribution_value": 110.39,
                },
                {
                    "contributor_id": "agent-002",
                    "contribution_score": 0.35,
                    "attribution_value": 85.86,
                },
            ],
            "model_confidence": 0.89,
        }
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/transactions")
async def get_transactions(
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    type: Optional[str] = None,
    agent_id: Optional[str] = None,
):
    """Get economic transactions."""
    try:
        transactions = [
            {
                "transaction_id": "tx_001",
                "agent_id": "agent-001",
                "amount": 245.30,
                "type": "attribution_reward",
                "timestamp": (datetime.now() - timedelta(hours=2)).isoformat(),
                "status": "completed",
            },
            {
                "transaction_id": "tx_002",
                "agent_id": "agent-002",
                "amount": 189.50,
                "type": "collaboration_bonus",
                "timestamp": (datetime.now() - timedelta(hours=4)).isoformat(),
                "status": "completed",
            },
        ]

        # Apply filters
        if type:
            transactions = [t for t in transactions if t["type"] == type]
        if agent_id:
            transactions = [t for t in transactions if t["agent_id"] == agent_id]

        total = len(transactions)
        transactions = transactions[offset : offset + limit]

        return {
            "transactions": transactions,
            "pagination": {
                "offset": offset,
                "limit": limit,
                "total": total,
                "has_more": offset + limit < total,
            },
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/payments")
async def get_payments():
    """Get payment history and status."""
    try:
        payments = [
            {
                "payment_id": "pay_001",
                "agent_id": "agent-001",
                "amount": 1247.50,
                "currency": "USD",
                "status": "completed",
                "payment_method": "bank_transfer",
                "initiated_at": (datetime.now() - timedelta(days=7)).isoformat(),
            },
            {
                "payment_id": "pay_002",
                "agent_id": "agent-002",
                "amount": 892.30,
                "currency": "USD",
                "status": "pending",
                "payment_method": "paypal",
                "initiated_at": (datetime.now() - timedelta(days=1)).isoformat(),
            },
        ]
        return payments
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/reports/revenue")
async def get_revenue_report(
    period: str = Query("monthly"),
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
):
    """Get revenue report."""
    try:
        report = {
            "period": period,
            "generated_at": utc_now().isoformat(),
            "summary": {
                "total_revenue": 1247892.50,
                "total_attributions": 27891,
                "unique_contributors": 89,
            },
            "breakdown_by_type": {
                "attribution_rewards": {"amount": 567892.30, "percentage": 45.5},
                "collaboration_bonuses": {"amount": 234567.80, "percentage": 18.8},
                "quality_bonuses": {"amount": 189432.40, "percentage": 15.2},
            },
            "temporal_data": [
                {"period": "2024-01", "revenue": 892456.20, "growth_rate": 0.15},
                {"period": "2024-02", "revenue": 945678.30, "growth_rate": 0.06},
                {"period": "2024-03", "revenue": 1087234.50, "growth_rate": 0.15},
            ],
        }
        return report
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
