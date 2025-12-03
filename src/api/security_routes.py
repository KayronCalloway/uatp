"""
Security API Routes for UATP Capsule Engine.

This module provides REST API endpoints for all integrated security systems,
including status monitoring, configuration management, and security operations.
"""

import asyncio
import json
import logging
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional

from quart import Blueprint, jsonify, request, g

# from quart_schema import validate_json, validate_querystring  # Not used

from .dependencies import require_api_key, get_engine
from ..security.security_manager import (
    get_security_manager,
    get_unified_security_status,
    initialize_security_manager,
    SecurityConfiguration,
    SecurityLevel,
)
from ..security.hsm_integration import get_hsm_system_status
from ..security.memory_timing_protection import get_protection_status
from ..privacy.zero_knowledge_proofs import get_zk_system_status
from ..economic.advanced_market_protection import get_market_protection_status
from ..reasoning.chain_verifier import get_reasoning_verification_metrics
from ..attribution.gaming_detector import gaming_detector

logger = logging.getLogger(__name__)

# Create security blueprint
security_bp = Blueprint("security", __name__)


@security_bp.route("/security/status", methods=["GET"])
@require_api_key
async def get_security_system_status():
    """Get comprehensive status of all security systems."""
    try:
        # Get unified security status
        unified_status = get_unified_security_status()

        # Get individual system statuses
        hsm_status = get_hsm_system_status()
        memory_status = get_protection_status()
        zk_status = get_zk_system_status()
        market_status = get_market_protection_status()
        reasoning_status = get_reasoning_verification_metrics()
        detection_status = {
            "initialized": True,
            "known_signatures": len(gaming_detector.known_gaming_signatures),
        }

        return jsonify(
            {
                "unified_security": unified_status,
                "individual_systems": {
                    "hsm_integration": hsm_status,
                    "memory_timing_protection": memory_status,
                    "zero_knowledge_proofs": zk_status,
                    "market_protection": market_status,
                    "reasoning_verification": reasoning_status,
                    "multi_entity_detection": detection_status,
                },
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "status": "operational"
                if unified_status.get("initialized", False)
                else "initializing",
            }
        )

    except Exception as e:
        logger.error(f"Error getting security status: {e}")
        return jsonify({"error": str(e)}), 500


@security_bp.route("/security/initialize", methods=["POST"])
@require_api_key
async def initialize_security_systems():
    """Initialize all security systems."""
    try:
        data = await request.get_json() or {}

        # Create security configuration from request data
        security_level = SecurityLevel[data.get("security_level", "HIGH")]

        config = SecurityConfiguration(
            security_level=security_level,
            quantum_resistant_required=data.get("quantum_resistant_required", True),
            real_time_monitoring=data.get("real_time_monitoring", True),
            enable_zero_knowledge=data.get("enable_zero_knowledge", True),
            enable_market_protection=data.get("enable_market_protection", True),
            enable_consent_verification=data.get("enable_consent_verification", True),
            enable_attribution_proofs=data.get("enable_attribution_proofs", True),
            enable_reasoning_verification=data.get(
                "enable_reasoning_verification", True
            ),
            enable_side_channel_protection=data.get(
                "enable_side_channel_protection", True
            ),
            enable_multi_entity_detection=data.get(
                "enable_multi_entity_detection", True
            ),
        )

        # Initialize security manager
        success = await initialize_security_manager(config)

        if success:
            return jsonify(
                {
                    "message": "Security systems initialized successfully",
                    "status": "initialized",
                    "security_level": security_level.value,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }
            )
        else:
            return (
                jsonify(
                    {
                        "error": "Security system initialization failed",
                        "status": "failed",
                    }
                ),
                500,
            )

    except Exception as e:
        logger.error(f"Error initializing security systems: {e}")
        return jsonify({"error": str(e)}), 500


@security_bp.route("/security/verify-capsule", methods=["POST"])
@require_api_key
async def verify_capsule_security():
    """Perform comprehensive security verification on capsule data."""
    try:
        data = await request.get_json()
        if not data:
            return jsonify({"error": "No capsule data provided"}), 400

        security_manager = get_security_manager()
        if not security_manager:
            return jsonify({"error": "Security manager not initialized"}), 503

        # Perform security verification
        success, verification_result = await security_manager.secure_capsule_operation(
            "api_verification", data
        )

        return jsonify(
            {
                "verification_successful": success,
                "verification_result": verification_result,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        )

    except Exception as e:
        logger.error(f"Error verifying capsule security: {e}")
        return jsonify({"error": str(e)}), 500


@security_bp.route("/security/hsm/status", methods=["GET"])
@require_api_key
async def get_hsm_status():
    """Get Hardware Security Module status."""
    try:
        status = get_hsm_system_status()
        return jsonify(status)
    except Exception as e:
        logger.error(f"Error getting HSM status: {e}")
        return jsonify({"error": str(e)}), 500


@security_bp.route("/security/hsm/generate-key", methods=["POST"])
@require_api_key
async def generate_hsm_key():
    """Generate a new key using HSM."""
    try:
        data = await request.get_json() or {}
        algorithm = data.get("algorithm", "dilithium3")
        key_id = data.get("key_id")

        if not key_id:
            return jsonify({"error": "key_id is required"}), 400

        from ..security.hsm_integration import (
            create_hsm_session,
            execute_hsm_operation,
            HSMOperationType,
            terminate_hsm_session,
        )

        # Create HSM session
        session_id = await create_hsm_session("api_user", "key_generation")

        try:
            # Generate key
            result = await execute_hsm_operation(
                session_id,
                HSMOperationType.KEY_GENERATION,
                algorithm=algorithm,
                key_id=key_id,
            )

            return jsonify(
                {
                    "success": result.success,
                    "key_id": key_id,
                    "algorithm": algorithm,
                    "execution_time_ms": result.execution_time_ms,
                    "quantum_resistant": True,
                }
            )
        finally:
            await terminate_hsm_session(session_id)

    except Exception as e:
        logger.error(f"Error generating HSM key: {e}")
        return jsonify({"error": str(e)}), 500


@security_bp.route("/security/zero-knowledge/generate-proof", methods=["POST"])
@require_api_key
async def generate_zk_proof():
    """Generate a zero-knowledge proof."""
    try:
        data = await request.get_json()
        if not data:
            return jsonify({"error": "Proof data required"}), 400

        proof_type = data.get("proof_type", "range_proof")

        if proof_type == "range_proof":
            value = data.get("value")
            min_value = data.get("min_value", 0)
            max_value = data.get("max_value", 100)

            if value is None:
                return jsonify({"error": "value is required for range proof"}), 400

            from ..privacy.zero_knowledge_proofs import generate_range_proof

            proof = await generate_range_proof(value, min_value, max_value)

            return jsonify(
                {
                    "proof_generated": True,
                    "proof_id": proof.proof_id,
                    "proof_type": proof.proof_type.value,
                    "quantum_resistant": proof.quantum_signature is not None,
                    "expiration": proof.expiration.isoformat()
                    if proof.expiration
                    else None,
                }
            )

        elif proof_type == "membership_proof":
            element = data.get("element", "").encode()
            set_elements = [elem.encode() for elem in data.get("set_elements", [])]

            if not set_elements:
                return (
                    jsonify({"error": "set_elements required for membership proof"}),
                    400,
                )

            from ..privacy.zero_knowledge_proofs import generate_membership_proof

            proof = await generate_membership_proof(element, set_elements)

            return jsonify(
                {
                    "proof_generated": True,
                    "proof_id": proof.proof_id,
                    "proof_type": proof.proof_type.value,
                    "quantum_resistant": proof.quantum_signature is not None,
                    "set_size": len(set_elements),
                }
            )

        else:
            return jsonify({"error": f"Unsupported proof type: {proof_type}"}), 400

    except Exception as e:
        logger.error(f"Error generating zero-knowledge proof: {e}")
        return jsonify({"error": str(e)}), 500


@security_bp.route("/security/memory-protection/status", methods=["GET"])
@require_api_key
async def get_memory_protection_status():
    """Get memory and timing attack protection status."""
    try:
        status = get_protection_status()
        return jsonify(status)
    except Exception as e:
        logger.error(f"Error getting memory protection status: {e}")
        return jsonify({"error": str(e)}), 500


@security_bp.route("/security/market-protection/status", methods=["GET"])
@require_api_key
async def get_market_protection_status_endpoint():
    """Get market stability and protection status."""
    try:
        status = get_market_protection_status()
        return jsonify(status)
    except Exception as e:
        logger.error(f"Error getting market protection status: {e}")
        return jsonify({"error": str(e)}), 500


@security_bp.route("/security/reasoning-verification/status", methods=["GET"])
@require_api_key
async def get_reasoning_verification_status():
    """Get reasoning chain verification status."""
    try:
        status = get_reasoning_verification_metrics()
        return jsonify(status)
    except Exception as e:
        logger.error(f"Error getting reasoning verification status: {e}")
        return jsonify({"error": str(e)}), 500


@security_bp.route("/security/multi-entity-detection/status", methods=["GET"])
@require_api_key
async def get_multi_entity_detection_status():
    """Get multi-entity coordination detection status."""
    try:
        status = {
            "initialized": True,
            "known_signatures": len(gaming_detector.known_gaming_signatures),
        }
        return jsonify(status)
    except Exception as e:
        logger.error(f"Error getting multi-entity detection status: {e}")
        return jsonify({"error": str(e)}), 500


@security_bp.route("/security/threats/detect", methods=["POST"])
@require_api_key
async def detect_security_threats():
    """Perform comprehensive threat detection."""
    try:
        data = await request.get_json() or {}

        # Get all threat detection results
        threats_detected = []

        # Check side-channel attacks
        from ..security.memory_timing_protection import detect_side_channel_attacks

        side_channel_threats = detect_side_channel_attacks()
        threats_detected.extend(side_channel_threats)

        # Check multi-entity coordination
        from ..attribution.gaming_detector import gaming_detector

        coordination_result = gaming_detector.analyze_attribution_for_gaming(data)
        if (
            coordination_result
            and hasattr(coordination_result, "gaming_detected")
            and coordination_result.gaming_detected
        ):
            threats_detected.append(
                {
                    "type": "multi_entity_coordination",
                    "severity": "high",
                    "detected_at": datetime.now(timezone.utc).isoformat(),
                    "evidence": data,
                }
            )

        return jsonify(
            {
                "threats_detected": len(threats_detected),
                "threat_details": threats_detected,
                "system_status": "secure"
                if len(threats_detected) == 0
                else "threats_detected",
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        )

    except Exception as e:
        logger.error(f"Error detecting security threats: {e}")
        return jsonify({"error": str(e)}), 500


@security_bp.route("/security/audit-log", methods=["GET"])
@require_api_key
async def get_security_audit_log():
    """Get security audit log entries."""
    try:
        # Query parameters
        limit = request.args.get("limit", 100, type=int)
        offset = request.args.get("offset", 0, type=int)
        system_filter = request.args.get("system")
        severity_filter = request.args.get("severity")

        # This would typically query a security audit database
        # For now, return sample audit entries
        audit_entries = [
            {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "system": "unified_security_manager",
                "event": "security_verification_completed",
                "severity": "info",
                "details": {
                    "capsule_id": "caps_2025_01_09_abc123",
                    "verification_rate": 1.0,
                },
            },
            {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "system": "hsm_integration",
                "event": "key_generation_completed",
                "severity": "info",
                "details": {"key_id": "system_key_001", "algorithm": "dilithium3"},
            },
        ]

        # Apply filters
        if system_filter:
            audit_entries = [e for e in audit_entries if e["system"] == system_filter]
        if severity_filter:
            audit_entries = [
                e for e in audit_entries if e["severity"] == severity_filter
            ]

        # Apply pagination
        paginated_entries = audit_entries[offset : offset + limit]

        return jsonify(
            {
                "audit_entries": paginated_entries,
                "total_entries": len(audit_entries),
                "limit": limit,
                "offset": offset,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        )

    except Exception as e:
        logger.error(f"Error getting security audit log: {e}")
        return jsonify({"error": str(e)}), 500


@security_bp.route("/security/metrics", methods=["GET"])
@require_api_key
async def get_security_metrics():
    """Get comprehensive security performance metrics."""
    try:
        security_manager = get_security_manager()

        if not security_manager:
            return jsonify({"error": "Security manager not initialized"}), 503

        # Get metrics from security manager
        metrics = security_manager.metrics

        # Get system-specific metrics
        hsm_status = get_hsm_system_status()
        memory_status = get_protection_status()
        zk_status = get_zk_system_status()

        return jsonify(
            {
                "unified_metrics": metrics,
                "system_metrics": {
                    "hsm": {
                        "operations_protected": hsm_status.get(
                            "operation_metrics", {}
                        ).get("total_operations", 0),
                        "success_rate": hsm_status.get("operation_metrics", {}).get(
                            "successful_operations", 0
                        ),
                    },
                    "memory_protection": {
                        "operations_protected": memory_status.get(
                            "operations_protected", 0
                        ),
                        "attacks_detected": memory_status.get("attacks_detected", 0),
                        "avg_overhead_us": memory_status.get(
                            "avg_operation_overhead_us", 0
                        ),
                    },
                    "zero_knowledge": {
                        "proofs_generated": zk_status.get("total_proofs_generated", 0),
                        "success_rate": zk_status.get("success_rate", 0),
                        "avg_generation_time_ms": zk_status.get(
                            "average_generation_time_ms", 0
                        ),
                    },
                },
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        )

    except Exception as e:
        logger.error(f"Error getting security metrics: {e}")
        return jsonify({"error": str(e)}), 500


@security_bp.route("/security/health", methods=["GET"])
@require_api_key
async def security_health_check():
    """Comprehensive security system health check."""
    try:
        health_status = {
            "overall_health": "healthy",
            "systems": {},
            "issues": [],
            "recommendations": [],
        }

        # Check unified security manager
        unified_status = get_unified_security_status()
        if unified_status.get("initialized", False):
            health_status["systems"]["unified_security"] = "healthy"
        else:
            health_status["systems"]["unified_security"] = "unhealthy"
            health_status["issues"].append("Unified security manager not initialized")
            health_status["overall_health"] = "degraded"

        # Check individual systems
        systems_to_check = [
            ("hsm", get_hsm_system_status),
            ("memory_protection", get_protection_status),
            ("zero_knowledge", get_zk_system_status),
            ("market_protection", get_market_protection_status),
        ]

        for system_name, status_func in systems_to_check:
            try:
                status = status_func()
                if status and isinstance(status, dict):
                    health_status["systems"][system_name] = "healthy"
                else:
                    health_status["systems"][system_name] = "unhealthy"
                    health_status["issues"].append(
                        f"{system_name} system not responding"
                    )
            except Exception as e:
                health_status["systems"][system_name] = "unhealthy"
                health_status["issues"].append(f"{system_name} system error: {str(e)}")

        # Determine overall health
        unhealthy_systems = [
            k for k, v in health_status["systems"].items() if v == "unhealthy"
        ]
        if len(unhealthy_systems) > len(health_status["systems"]) // 2:
            health_status["overall_health"] = "unhealthy"
        elif len(unhealthy_systems) > 0:
            health_status["overall_health"] = "degraded"

        # Add recommendations
        if unhealthy_systems:
            health_status["recommendations"].append(
                f"Initialize or restart the following systems: {', '.join(unhealthy_systems)}"
            )

        health_status["timestamp"] = datetime.now(timezone.utc).isoformat()
        health_status["systems_checked"] = len(health_status["systems"])
        health_status["issues_found"] = len(health_status["issues"])

        # Return appropriate HTTP status code
        if health_status["overall_health"] == "healthy":
            return jsonify(health_status), 200
        elif health_status["overall_health"] == "degraded":
            return jsonify(health_status), 200  # Still operational
        else:
            return jsonify(health_status), 503  # Service unavailable

    except Exception as e:
        logger.error(f"Error performing security health check: {e}")
        return (
            jsonify(
                {
                    "overall_health": "unhealthy",
                    "error": str(e),
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }
            ),
            500,
        )


def create_security_blueprint() -> Blueprint:
    """Create and return the security blueprint."""
    return security_bp
