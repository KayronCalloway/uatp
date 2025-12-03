"""
Safety API Routes

Provides HTTP endpoints for safety validation, approval workflows, and emergency stops.

Endpoints:
- POST /api/v1/safety/validate-decision - Validate a high-stakes decision
- GET /api/v1/safety/approval-requests - List pending approval requests
- POST /api/v1/safety/approve-decision - Approve a pending decision
- POST /api/v1/safety/reject-decision - Reject a pending decision
- POST /api/v1/safety/emergency-stop - Trigger emergency stop
- GET /api/v1/safety/consensus-requests - List pending consensus requests
- POST /api/v1/safety/consensus-vote - Submit consensus vote
"""

from quart import Blueprint, request, jsonify
from typing import Dict, Any
import logging

from src.safety import decision_safety_validator, ApprovalStatus
from src.auth.agent_auth import agent_auth_manager

logger = logging.getLogger(__name__)

safety_bp = Blueprint("safety", __name__, url_prefix="/api/v1/safety")


@safety_bp.route("/validate-decision", methods=["POST"])
async def validate_decision():
    """
    Validate a high-stakes decision before execution.

    Request Body:
    {
        "decision": {
            "domain": "medical",
            "type": "diagnosis",
            "recommendation": "...",
            "confidence": 0.92,
            "explanation": "...",
            "decision_id": "dec_123"
        },
        "agent_id": "agent_456",
        "context": {
            "patient_severity": "high",
            "patient_id": "p_789"
        }
    }

    Response:
    {
        "validation_id": "val_abc",
        "approved": false,
        "approval_status": "pending_human",
        "risk_level": "high",
        "confidence": 0.92,
        "requires_human_approval": true,
        "approval_request_id": "approval_xyz",
        "reason": "HIGH risk decision requires human approval",
        "warnings": []
    }
    """
    try:
        data = await request.get_json()

        decision = data.get("decision")
        agent_id = data.get("agent_id")
        context = data.get("context", {})

        if not decision or not agent_id:
            return jsonify({"error": "decision and agent_id required"}), 400

        # Validate decision
        validation = await decision_safety_validator.validate_decision(
            decision=decision, agent_id=agent_id, context=context
        )

        # Convert to dict for JSON response
        response = {
            "validation_id": validation.validation_id,
            "approved": validation.approved,
            "approval_status": validation.approval_status.value,
            "risk_level": validation.risk_level.value,
            "confidence": validation.confidence,
            "requires_human_approval": validation.requires_human_approval,
            "requires_consensus": validation.requires_consensus,
            "approval_request_id": validation.approval_request_id,
            "reason": validation.reason,
            "warnings": validation.warnings,
            "timestamp": validation.timestamp,
            "metadata": validation.metadata,
        }

        status_code = (
            200 if validation.approved else 202
        )  # 202 Accepted (pending approval)

        return jsonify(response), status_code

    except Exception as e:
        logger.error(f"Decision validation error: {e}")
        return jsonify({"error": "Decision validation failed", "message": str(e)}), 500


@safety_bp.route("/approval-requests", methods=["GET"])
async def list_approval_requests():
    """
    List pending human approval requests.

    Query Parameters:
    - status: Filter by status (pending, approved, rejected, expired)
    - domain: Filter by domain (medical, financial, legal, etc.)
    - risk_level: Filter by risk level (low, medium, high, critical)

    Response:
    {
        "requests": [
            {
                "request_id": "approval_abc",
                "decision_id": "dec_123",
                "domain": "medical",
                "risk_level": "high",
                "decision_summary": "...",
                "ai_confidence": 0.92,
                "created_at": "2025-01-06T...",
                "expires_at": "2025-01-07T...",
                "status": "pending"
            }
        ],
        "total": 5
    }
    """
    try:
        # Get query parameters
        status_filter = request.args.get("status")
        domain_filter = request.args.get("domain")
        risk_filter = request.args.get("risk_level")

        # Get all pending requests
        requests = list(decision_safety_validator.pending_approvals.values())

        # Apply filters
        if status_filter:
            requests = [r for r in requests if r.status == status_filter]

        if domain_filter:
            requests = [r for r in requests if r.domain.value == domain_filter]

        if risk_filter:
            requests = [r for r in requests if r.risk_level.value == risk_filter]

        # Convert to dict for JSON
        response_data = [
            {
                "request_id": r.request_id,
                "decision_id": r.decision_id,
                "agent_id": r.agent_id,
                "domain": r.domain.value,
                "risk_level": r.risk_level.value,
                "decision_summary": r.decision_summary,
                "ai_confidence": r.ai_confidence,
                "ai_explanation": r.ai_explanation,
                "created_at": r.created_at,
                "expires_at": r.expires_at,
                "status": r.status,
            }
            for r in requests
        ]

        return jsonify({"requests": response_data, "total": len(response_data)}), 200

    except Exception as e:
        logger.error(f"Error listing approval requests: {e}")
        return (
            jsonify({"error": "Failed to list approval requests", "message": str(e)}),
            500,
        )


@safety_bp.route("/approve-decision", methods=["POST"])
async def approve_decision():
    """
    Approve a pending high-stakes decision.

    Request Body:
    {
        "request_id": "approval_abc",
        "approved_by": "human_reviewer_123",
        "notes": "Reviewed and approved based on..."
    }

    Response:
    {
        "success": true,
        "request_id": "approval_abc",
        "decision_id": "dec_123",
        "approved_at": "2025-01-06T...",
        "approved_by": "human_reviewer_123"
    }
    """
    try:
        data = await request.get_json()

        request_id = data.get("request_id")
        approved_by = data.get("approved_by")
        notes = data.get("notes", "")

        if not request_id or not approved_by:
            return jsonify({"error": "request_id and approved_by required"}), 400

        # Get approval request
        approval_request = decision_safety_validator.pending_approvals.get(request_id)

        if not approval_request:
            return jsonify({"error": "Approval request not found"}), 404

        if approval_request.status != "pending":
            return jsonify({"error": f"Request already {approval_request.status}"}), 400

        # Update request
        from datetime import datetime, timezone

        approval_request.status = "approved"
        approval_request.approved_by = approved_by
        approval_request.approved_at = datetime.now(timezone.utc).isoformat()

        # Save updated request
        decision_safety_validator._save_approval_request(approval_request)

        logger.info(
            f"✅ Decision approved: {approval_request.decision_id} "
            f"(request: {request_id}, by: {approved_by})"
        )

        # Emit audit event
        try:
            from src.audit.events import audit_emitter

            audit_emitter.emit_security_event(
                event_name="high_stakes_decision_approved",
                metadata={
                    "request_id": request_id,
                    "decision_id": approval_request.decision_id,
                    "approved_by": approved_by,
                    "risk_level": approval_request.risk_level.value,
                    "domain": approval_request.domain.value,
                    "notes": notes,
                },
            )
        except Exception as e:
            logger.error(f"Failed to emit audit event: {e}")

        return (
            jsonify(
                {
                    "success": True,
                    "request_id": request_id,
                    "decision_id": approval_request.decision_id,
                    "approved_at": approval_request.approved_at,
                    "approved_by": approved_by,
                }
            ),
            200,
        )

    except Exception as e:
        logger.error(f"Error approving decision: {e}")
        return jsonify({"error": "Failed to approve decision", "message": str(e)}), 500


@safety_bp.route("/reject-decision", methods=["POST"])
async def reject_decision():
    """
    Reject a pending high-stakes decision.

    Request Body:
    {
        "request_id": "approval_abc",
        "rejected_by": "human_reviewer_123",
        "reason": "Insufficient evidence for diagnosis"
    }

    Response:
    {
        "success": true,
        "request_id": "approval_abc",
        "decision_id": "dec_123",
        "rejected_at": "2025-01-06T...",
        "rejected_by": "human_reviewer_123"
    }
    """
    try:
        data = await request.get_json()

        request_id = data.get("request_id")
        rejected_by = data.get("rejected_by")
        reason = data.get("reason", "")

        if not request_id or not rejected_by or not reason:
            return (
                jsonify({"error": "request_id, rejected_by, and reason required"}),
                400,
            )

        # Get approval request
        approval_request = decision_safety_validator.pending_approvals.get(request_id)

        if not approval_request:
            return jsonify({"error": "Approval request not found"}), 404

        if approval_request.status != "pending":
            return jsonify({"error": f"Request already {approval_request.status}"}), 400

        # Update request
        from datetime import datetime, timezone

        approval_request.status = "rejected"
        approval_request.rejection_reason = reason

        # Save updated request
        decision_safety_validator._save_approval_request(approval_request)

        logger.warning(
            f"❌ Decision rejected: {approval_request.decision_id} "
            f"(request: {request_id}, by: {rejected_by}, reason: {reason})"
        )

        # Emit audit event
        try:
            from src.audit.events import audit_emitter

            audit_emitter.emit_security_event(
                event_name="high_stakes_decision_rejected",
                metadata={
                    "request_id": request_id,
                    "decision_id": approval_request.decision_id,
                    "rejected_by": rejected_by,
                    "reason": reason,
                    "risk_level": approval_request.risk_level.value,
                    "domain": approval_request.domain.value,
                },
            )
        except Exception as e:
            logger.error(f"Failed to emit audit event: {e}")

        return (
            jsonify(
                {
                    "success": True,
                    "request_id": request_id,
                    "decision_id": approval_request.decision_id,
                    "rejected_at": datetime.now(timezone.utc).isoformat(),
                    "rejected_by": rejected_by,
                    "reason": reason,
                }
            ),
            200,
        )

    except Exception as e:
        logger.error(f"Error rejecting decision: {e}")
        return jsonify({"error": "Failed to reject decision", "message": str(e)}), 500


@safety_bp.route("/emergency-stop", methods=["POST"])
async def emergency_stop():
    """
    Trigger emergency stop for a decision.

    Request Body:
    {
        "decision_id": "dec_123",
        "agent_id": "agent_456",
        "reason": "Patient condition changed",
        "triggered_by": "human_reviewer_789"
    }

    Response:
    {
        "success": true,
        "stop_id": "stop_xyz",
        "decision_id": "dec_123",
        "timestamp": "2025-01-06T..."
    }
    """
    try:
        data = await request.get_json()

        decision_id = data.get("decision_id")
        agent_id = data.get("agent_id")
        reason = data.get("reason")
        triggered_by = data.get("triggered_by", "api_user")

        if not decision_id or not agent_id or not reason:
            return jsonify({"error": "decision_id, agent_id, and reason required"}), 400

        # Trigger emergency stop
        stop = await decision_safety_validator.trigger_emergency_stop(
            decision_id=decision_id,
            agent_id=agent_id,
            reason=reason,
            triggered_by=triggered_by,
        )

        return (
            jsonify(
                {
                    "success": True,
                    "stop_id": stop.stop_id,
                    "decision_id": stop.decision_id,
                    "timestamp": stop.timestamp,
                    "triggered_by": stop.triggered_by,
                }
            ),
            200,
        )

    except Exception as e:
        logger.error(f"Error triggering emergency stop: {e}")
        return (
            jsonify({"error": "Failed to trigger emergency stop", "message": str(e)}),
            500,
        )


@safety_bp.route("/health", methods=["GET"])
async def safety_health():
    """
    Safety system health check.

    Response:
    {
        "status": "healthy",
        "pending_approvals": 5,
        "pending_consensus": 2,
        "active_emergency_stops": 0
    }
    """
    return (
        jsonify(
            {
                "status": "healthy",
                "pending_approvals": len(decision_safety_validator.pending_approvals),
                "pending_consensus": len(decision_safety_validator.pending_consensus),
                "active_emergency_stops": len(
                    decision_safety_validator.emergency_stops
                ),
            }
        ),
        200,
    )
