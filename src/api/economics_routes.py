"""
Economics API Routes
===================

API endpoints for economic features including metrics, attribution models, and economic analytics.
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from uuid import uuid4

from quart import Blueprint, jsonify, request, g
from quart_schema import validation

from ..database.models import generate_id, utc_now
from .dependencies import require_api_key

economics_bp = Blueprint("economics", __name__)


@economics_bp.route("/metrics", methods=["GET"])
@require_api_key(["read"])
async def get_economic_metrics():
    """Get economic metrics and statistics."""
    try:
        # In a real implementation, this would query the database
        # For now, we'll return mock data that matches the frontend expectations
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
                {
                    "transaction_id": "tx_003",
                    "agent_id": "agent-003",
                    "amount": 156.75,
                    "type": "quality_bonus",
                    "timestamp": (datetime.now() - timedelta(hours=6)).isoformat(),
                    "capsule_id": "cap_12347",
                    "description": "Quality bonus for exceptional output",
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
                {
                    "month": "2024-01",
                    "total_value": 892456.20,
                    "transactions": 4123,
                    "unique_agents": 67,
                },
                {
                    "month": "2024-02",
                    "total_value": 945678.30,
                    "transactions": 4456,
                    "unique_agents": 72,
                },
                {
                    "month": "2024-03",
                    "total_value": 1087234.50,
                    "transactions": 4789,
                    "unique_agents": 78,
                },
                {
                    "month": "2024-04",
                    "total_value": 1156789.20,
                    "transactions": 5012,
                    "unique_agents": 83,
                },
                {
                    "month": "2024-05",
                    "total_value": 1247892.50,
                    "transactions": 5438,
                    "unique_agents": 89,
                },
            ],
        }

        return jsonify(metrics)

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@economics_bp.route("/attribution/models", methods=["GET"])
@require_api_key(["read"])
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
                "parameters": {
                    "base_rate": 0.1,
                    "quality_multiplier": 1.5,
                    "collaboration_bonus": 0.2,
                },
                "accuracy": 0.85,
                "fairness_score": 0.78,
                "transparency": 0.95,
                "usage_stats": {
                    "total_attributions": 15234,
                    "success_rate": 0.94,
                    "avg_processing_time": 0.045,
                },
            },
            {
                "model_id": "shapley_v2",
                "name": "Shapley Value Attribution",
                "description": "Game-theoretic attribution using Shapley values",
                "version": "2.1.0",
                "status": "active",
                "parameters": {
                    "coalition_size": 10,
                    "sampling_iterations": 1000,
                    "convergence_threshold": 0.001,
                },
                "accuracy": 0.92,
                "fairness_score": 0.89,
                "transparency": 0.72,
                "usage_stats": {
                    "total_attributions": 8967,
                    "success_rate": 0.89,
                    "avg_processing_time": 0.234,
                },
            },
            {
                "model_id": "attention_v1",
                "name": "Attention-Based Attribution",
                "description": "Attribution based on attention mechanisms in AI models",
                "version": "1.2.0",
                "status": "experimental",
                "parameters": {
                    "attention_layers": 12,
                    "head_aggregation": "mean",
                    "threshold": 0.05,
                },
                "accuracy": 0.88,
                "fairness_score": 0.81,
                "transparency": 0.68,
                "usage_stats": {
                    "total_attributions": 2456,
                    "success_rate": 0.82,
                    "avg_processing_time": 0.156,
                },
            },
            {
                "model_id": "hybrid_v1",
                "name": "Hybrid Attribution Model",
                "description": "Combines multiple attribution methods for optimal results",
                "version": "1.0.0",
                "status": "beta",
                "parameters": {
                    "linear_weight": 0.3,
                    "shapley_weight": 0.5,
                    "attention_weight": 0.2,
                },
                "accuracy": 0.94,
                "fairness_score": 0.86,
                "transparency": 0.79,
                "usage_stats": {
                    "total_attributions": 1234,
                    "success_rate": 0.91,
                    "avg_processing_time": 0.189,
                },
            },
        ]

        return jsonify(models)

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@economics_bp.route("/attribution/analysis", methods=["GET"])
@require_api_key(["read"])
async def get_attribution_analysis():
    """Get attribution analysis and insights."""
    try:
        analysis = {
            "summary": {
                "total_attributions": 27891,
                "total_value_attributed": 1247892.50,
                "unique_contributors": 89,
                "average_attribution_value": 44.78,
                "attribution_accuracy": 0.89,
            },
            "model_performance": {
                "linear_v1": {
                    "attributions": 15234,
                    "accuracy": 0.85,
                    "avg_processing_time": 0.045,
                    "user_satisfaction": 0.82,
                },
                "shapley_v2": {
                    "attributions": 8967,
                    "accuracy": 0.92,
                    "avg_processing_time": 0.234,
                    "user_satisfaction": 0.89,
                },
                "attention_v1": {
                    "attributions": 2456,
                    "accuracy": 0.88,
                    "avg_processing_time": 0.156,
                    "user_satisfaction": 0.79,
                },
                "hybrid_v1": {
                    "attributions": 1234,
                    "accuracy": 0.94,
                    "avg_processing_time": 0.189,
                    "user_satisfaction": 0.91,
                },
            },
            "fairness_metrics": {
                "gini_coefficient": 0.34,
                "equal_opportunity": 0.87,
                "demographic_parity": 0.82,
                "individual_fairness": 0.79,
            },
            "contributor_distribution": {
                "top_1_percent": 0.23,
                "top_5_percent": 0.45,
                "top_10_percent": 0.67,
                "bottom_50_percent": 0.12,
            },
            "temporal_analysis": {
                "attribution_growth_rate": 0.23,
                "value_growth_rate": 0.31,
                "contributor_growth_rate": 0.15,
                "seasonal_patterns": {
                    "peak_months": ["March", "September"],
                    "low_months": ["July", "December"],
                },
            },
            "quality_indicators": {
                "dispute_rate": 0.03,
                "appeal_success_rate": 0.15,
                "user_satisfaction": 0.86,
                "system_reliability": 0.94,
            },
        }

        return jsonify(analysis)

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@economics_bp.route("/attribution/compute", methods=["POST"])
@require_api_key(["write"])
async def compute_attribution():
    """Compute attribution for a specific scenario."""
    try:
        data = await request.get_json()

        # Validate required fields
        required_fields = ["capsule_id", "contributors", "model_id"]
        for field in required_fields:
            if field not in data:
                return jsonify({"error": f"Missing required field: {field}"}), 400

        # Simulate attribution computation
        attribution_id = generate_id()

        # Mock attribution computation results
        attribution_results = {
            "attribution_id": attribution_id,
            "capsule_id": data["capsule_id"],
            "model_id": data["model_id"],
            "computed_at": utc_now().isoformat(),
            "processing_time": 0.156,
            "total_value": 245.30,
            "attributions": [
                {
                    "contributor_id": "agent-001",
                    "contribution_score": 0.45,
                    "attribution_value": 110.39,
                    "contribution_type": "primary",
                    "evidence": {
                        "interaction_count": 23,
                        "quality_score": 0.89,
                        "novelty_score": 0.76,
                    },
                },
                {
                    "contributor_id": "agent-002",
                    "contribution_score": 0.35,
                    "attribution_value": 85.86,
                    "contribution_type": "collaborative",
                    "evidence": {
                        "interaction_count": 18,
                        "quality_score": 0.82,
                        "novelty_score": 0.68,
                    },
                },
                {
                    "contributor_id": "agent-003",
                    "contribution_score": 0.20,
                    "attribution_value": 49.05,
                    "contribution_type": "supportive",
                    "evidence": {
                        "interaction_count": 12,
                        "quality_score": 0.78,
                        "novelty_score": 0.45,
                    },
                },
            ],
            "model_confidence": 0.89,
            "fairness_score": 0.83,
            "transparency_data": {
                "factors_considered": [
                    "interaction_frequency",
                    "quality_metrics",
                    "novelty_contribution",
                    "collaboration_quality",
                ],
                "model_parameters": data.get("parameters", {}),
                "computation_steps": [
                    "Data preprocessing",
                    "Feature extraction",
                    "Model application",
                    "Result validation",
                ],
            },
        }

        # In a real implementation, this would:
        # 1. Load the specified attribution model
        # 2. Process the capsule and contributor data
        # 3. Compute fair attribution values
        # 4. Store results in database

        return jsonify(attribution_results), 201

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@economics_bp.route("/transactions", methods=["GET"])
@require_api_key(["read"])
async def get_transactions():
    """Get economic transactions."""
    try:
        # Parse query parameters
        limit = request.args.get("limit", 50, type=int)
        offset = request.args.get("offset", 0, type=int)
        transaction_type = request.args.get("type")
        agent_id = request.args.get("agent_id")

        # Mock transaction data
        transactions = [
            {
                "transaction_id": "tx_001",
                "agent_id": "agent-001",
                "amount": 245.30,
                "type": "attribution_reward",
                "timestamp": (datetime.now() - timedelta(hours=2)).isoformat(),
                "capsule_id": "cap_12345",
                "description": "Attribution reward for AI assistance",
                "status": "completed",
                "metadata": {
                    "attribution_id": "attr_001",
                    "quality_score": 0.89,
                    "processing_time": 0.156,
                },
            },
            {
                "transaction_id": "tx_002",
                "agent_id": "agent-002",
                "amount": 189.50,
                "type": "collaboration_bonus",
                "timestamp": (datetime.now() - timedelta(hours=4)).isoformat(),
                "capsule_id": "cap_12346",
                "description": "Collaboration bonus for multi-agent task",
                "status": "completed",
                "metadata": {
                    "collaboration_id": "collab_001",
                    "partner_count": 3,
                    "synergy_score": 0.82,
                },
            },
            {
                "transaction_id": "tx_003",
                "agent_id": "agent-003",
                "amount": 156.75,
                "type": "quality_bonus",
                "timestamp": (datetime.now() - timedelta(hours=6)).isoformat(),
                "capsule_id": "cap_12347",
                "description": "Quality bonus for exceptional output",
                "status": "completed",
                "metadata": {
                    "quality_threshold": 0.85,
                    "actual_quality": 0.94,
                    "bonus_multiplier": 1.2,
                },
            },
        ]

        # Apply filters
        if transaction_type:
            transactions = [t for t in transactions if t["type"] == transaction_type]

        if agent_id:
            transactions = [t for t in transactions if t["agent_id"] == agent_id]

        # Apply pagination
        total = len(transactions)
        transactions = transactions[offset : offset + limit]

        return jsonify(
            {
                "transactions": transactions,
                "pagination": {
                    "offset": offset,
                    "limit": limit,
                    "total": total,
                    "has_more": offset + limit < total,
                },
            }
        )

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@economics_bp.route("/payments", methods=["GET"])
@require_api_key(["read"])
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
                "completed_at": (datetime.now() - timedelta(days=5)).isoformat(),
                "transaction_fee": 12.48,
                "net_amount": 1235.02,
                "metadata": {
                    "bank_reference": "BT123456789",
                    "processing_partner": "Stripe",
                },
            },
            {
                "payment_id": "pay_002",
                "agent_id": "agent-002",
                "amount": 892.30,
                "currency": "USD",
                "status": "pending",
                "payment_method": "paypal",
                "initiated_at": (datetime.now() - timedelta(days=1)).isoformat(),
                "completed_at": None,
                "transaction_fee": 8.92,
                "net_amount": 883.38,
                "metadata": {
                    "paypal_email": "agent002@example.com",
                    "processing_partner": "PayPal",
                },
            },
            {
                "payment_id": "pay_003",
                "agent_id": "agent-003",
                "amount": 567.80,
                "currency": "USD",
                "status": "failed",
                "payment_method": "crypto",
                "initiated_at": (datetime.now() - timedelta(days=3)).isoformat(),
                "completed_at": None,
                "transaction_fee": 5.68,
                "net_amount": 562.12,
                "error_message": "Insufficient wallet balance",
                "metadata": {
                    "wallet_address": "0x742d35Cc6634C0532925a3b8D904F1231",
                    "cryptocurrency": "ETH",
                },
            },
        ]

        return jsonify(payments)

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@economics_bp.route("/reports/revenue", methods=["GET"])
@require_api_key(["read"])
async def get_revenue_report():
    """Get revenue report."""
    try:
        # Parse query parameters
        period = request.args.get("period", "monthly")
        start_date = request.args.get("start_date")
        end_date = request.args.get("end_date")

        report = {
            "period": period,
            "generated_at": utc_now().isoformat(),
            "summary": {
                "total_revenue": 1247892.50,
                "total_attributions": 27891,
                "unique_contributors": 89,
                "average_attribution_value": 44.78,
            },
            "breakdown_by_type": {
                "attribution_rewards": {
                    "amount": 567892.30,
                    "percentage": 45.5,
                    "transactions": 15234,
                },
                "collaboration_bonuses": {
                    "amount": 234567.80,
                    "percentage": 18.8,
                    "transactions": 8967,
                },
                "quality_bonuses": {
                    "amount": 189432.40,
                    "percentage": 15.2,
                    "transactions": 2456,
                },
                "governance_rewards": {
                    "amount": 156000.00,
                    "percentage": 12.5,
                    "transactions": 1234,
                },
                "referral_bonuses": {
                    "amount": 99000.00,
                    "percentage": 8.0,
                    "transactions": 567,
                },
            },
            "temporal_data": [
                {
                    "period": "2024-01",
                    "revenue": 892456.20,
                    "attributions": 4123,
                    "growth_rate": 0.15,
                },
                {
                    "period": "2024-02",
                    "revenue": 945678.30,
                    "attributions": 4456,
                    "growth_rate": 0.06,
                },
                {
                    "period": "2024-03",
                    "revenue": 1087234.50,
                    "attributions": 4789,
                    "growth_rate": 0.15,
                },
                {
                    "period": "2024-04",
                    "revenue": 1156789.20,
                    "attributions": 5012,
                    "growth_rate": 0.06,
                },
                {
                    "period": "2024-05",
                    "revenue": 1247892.50,
                    "attributions": 5438,
                    "growth_rate": 0.08,
                },
            ],
        }

        return jsonify(report)

    except Exception as e:
        return jsonify({"error": str(e)}), 500
