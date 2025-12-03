"""
Enhanced Auto-Capture API Routes
Provides endpoints for the enhanced universal auto-capture system
"""

import logging
from datetime import datetime
from typing import Dict, Any, List
from quart import Blueprint, request, jsonify, g
from quart_schema import validate_json, validate_querystring

from src.auto_capture.enhanced_universal_capture import (
    universal_auto_capture,
    analyze_content_significance,
    analyze_conversation_significance,
    get_auto_capture_analytics,
)

logger = logging.getLogger(__name__)

auto_capture_bp = Blueprint("auto_capture", __name__)


@auto_capture_bp.route("/auto-capture/analyze/content", methods=["POST"])
@validate_json(
    {
        "type": "object",
        "properties": {
            "content": {"type": "string"},
            "source": {"type": "string"},
            "platform": {"type": "string"},
            "metadata": {"type": "object"},
        },
        "required": ["content", "source"],
    }
)
async def analyze_content():
    """Analyze content significance and auto-capture if warranted."""
    try:
        data = await request.get_json()
        content = data["content"]
        source = data["source"]
        platform = data.get("platform")
        metadata = data.get("metadata", {})

        # Add request context to metadata
        metadata.update(
            {
                "api_request": True,
                "timestamp": datetime.utcnow().isoformat(),
                "content_length": len(content),
            }
        )

        decision = await analyze_content_significance(
            content=content, source=source, platform=platform, metadata=metadata
        )

        logger.info(
            f"Content significance analysis: {decision['significance_score']:.2f} from {source}"
        )

        return (
            jsonify(
                {
                    "success": True,
                    "analysis": decision,
                    "message": "Content significance analysis completed",
                }
            ),
            200,
        )

    except Exception as e:
        logger.error(f"Content significance analysis failed: {e}")
        return jsonify({"success": False, "error": f"Analysis failed: {str(e)}"}), 500


@auto_capture_bp.route("/auto-capture/analyze/conversation", methods=["POST"])
@validate_json(
    {
        "type": "object",
        "properties": {
            "messages": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "role": {"type": "string"},
                        "content": {"type": "string"},
                        "metadata": {"type": "object"},
                    },
                    "required": ["role", "content"],
                },
            },
            "source": {"type": "string"},
            "platform": {"type": "string"},
            "metadata": {"type": "object"},
        },
        "required": ["messages", "source"],
    }
)
async def analyze_conversation():
    """Analyze conversation significance and auto-capture if warranted."""
    try:
        data = await request.get_json()
        messages = data["messages"]
        source = data["source"]
        platform = data.get("platform")
        metadata = data.get("metadata", {})

        # Add request context to metadata
        metadata.update(
            {
                "api_request": True,
                "timestamp": datetime.utcnow().isoformat(),
                "message_count": len(messages),
                "total_content_length": sum(
                    len(msg.get("content", "")) for msg in messages
                ),
            }
        )

        decision = await analyze_conversation_significance(
            messages=messages, source=source, platform=platform, metadata=metadata
        )

        logger.info(
            f"Conversation significance analysis: {decision['significance_score']:.2f} from {source} ({len(messages)} messages)"
        )

        return (
            jsonify(
                {
                    "success": True,
                    "analysis": decision,
                    "message": f"Conversation significance analysis completed for {len(messages)} messages",
                }
            ),
            200,
        )

    except Exception as e:
        logger.error(f"Conversation significance analysis failed: {e}")
        return jsonify({"success": False, "error": f"Analysis failed: {str(e)}"}), 500


@auto_capture_bp.route("/auto-capture/thresholds", methods=["GET", "POST"])
async def manage_thresholds():
    """Get or update auto-capture significance thresholds."""
    try:
        if request.method == "GET":
            thresholds = universal_auto_capture.significance_engine.thresholds
            return (
                jsonify(
                    {
                        "success": True,
                        "thresholds": thresholds,
                        "message": "Auto-capture thresholds retrieved",
                    }
                ),
                200,
            )

        else:  # POST - update thresholds
            data = await request.get_json()
            new_thresholds = data.get("thresholds", {})

            # Validate threshold values
            for key, value in new_thresholds.items():
                if not isinstance(value, (int, float)) or not 0 <= value <= 1:
                    return (
                        jsonify(
                            {
                                "success": False,
                                "error": f"Invalid threshold value for {key}: must be between 0 and 1",
                            }
                        ),
                        400,
                    )

            # Update thresholds
            universal_auto_capture.significance_engine.thresholds.update(new_thresholds)

            logger.info(f"Updated auto-capture thresholds: {new_thresholds}")

            return (
                jsonify(
                    {
                        "success": True,
                        "updated_thresholds": universal_auto_capture.significance_engine.thresholds,
                        "message": "Thresholds updated successfully",
                    }
                ),
                200,
            )

    except Exception as e:
        logger.error(f"Threshold management failed: {e}")
        return (
            jsonify(
                {"success": False, "error": f"Threshold operation failed: {str(e)}"}
            ),
            500,
        )


@auto_capture_bp.route("/auto-capture/analytics", methods=["GET"])
async def get_analytics():
    """Get comprehensive auto-capture analytics and performance metrics."""
    try:
        analytics = get_auto_capture_analytics()

        # Add real-time status
        analytics["system_status"] = {
            "running": universal_auto_capture.running,
            "active_monitors": len(universal_auto_capture.active_monitors),
            "significance_engine_ready": True,
            "thresholds": universal_auto_capture.significance_engine.thresholds,
        }

        return (
            jsonify(
                {
                    "success": True,
                    "analytics": analytics,
                    "message": "Auto-capture analytics retrieved",
                }
            ),
            200,
        )

    except Exception as e:
        logger.error(f"Analytics retrieval failed: {e}")
        return (
            jsonify({"success": False, "error": f"Failed to get analytics: {str(e)}"}),
            500,
        )


@auto_capture_bp.route("/auto-capture/stats", methods=["GET"])
async def get_capture_stats():
    """Get current auto-capture statistics."""
    try:
        stats = universal_auto_capture.capture_stats.copy()

        # Add derived metrics
        total = stats.get("total_captured", 0)
        auto = stats.get("auto_captured", 0)

        stats.update(
            {
                "auto_capture_rate": (auto / total * 100) if total > 0 else 0,
                "capsule_creation_rate": (stats.get("capsules_created", 0) / auto * 100)
                if auto > 0
                else 0,
                "high_priority_rate": (
                    stats.get("high_priority_captures", 0) / auto * 100
                )
                if auto > 0
                else 0,
                "system_uptime": "active",  # Could track actual uptime
                "significance_engine": {
                    "cache_size": len(
                        universal_auto_capture.significance_engine.significance_cache
                    ),
                    "learning_samples": len(
                        universal_auto_capture.significance_engine.learning_data
                    ),
                },
            }
        )

        return (
            jsonify(
                {
                    "success": True,
                    "stats": stats,
                    "message": "Auto-capture stats retrieved",
                }
            ),
            200,
        )

    except Exception as e:
        logger.error(f"Stats retrieval failed: {e}")
        return (
            jsonify({"success": False, "error": f"Failed to get stats: {str(e)}"}),
            500,
        )


@auto_capture_bp.route("/auto-capture/test", methods=["POST"])
@validate_json(
    {
        "type": "object",
        "properties": {
            "content": {"type": "string"},
            "type": {"type": "string", "enum": ["content", "conversation"]},
            "messages": {"type": "array"},
        },
        "required": ["type"],
    }
)
async def test_significance():
    """Test significance detection without triggering actual capture."""
    try:
        data = await request.get_json()
        test_type = data["type"]

        if test_type == "content":
            content = data.get("content", "")
            if not content:
                return (
                    jsonify(
                        {
                            "success": False,
                            "error": "Content is required for content test",
                        }
                    ),
                    400,
                )

            # Test content significance (dry run - no actual capture)
            significance = universal_auto_capture.significance_engine.calculate_content_significance(
                content, {"test_mode": True}
            )

            decision = universal_auto_capture.significance_engine.should_auto_capture(
                content=content, metadata={"test_mode": True}
            )

        else:  # conversation
            messages = data.get("messages", [])
            if not messages:
                return (
                    jsonify(
                        {
                            "success": False,
                            "error": "Messages are required for conversation test",
                        }
                    ),
                    400,
                )

            # Test conversation significance (dry run - no actual capture)
            significance = universal_auto_capture.significance_engine.calculate_conversation_significance(
                messages, {"test_mode": True}
            )

            decision = universal_auto_capture.significance_engine.should_auto_capture(
                messages=messages, metadata={"test_mode": True}
            )

        return (
            jsonify(
                {
                    "success": True,
                    "test_results": {
                        "significance_score": significance,
                        "decision": decision,
                        "test_type": test_type,
                    },
                    "message": f"Significance test completed for {test_type}",
                }
            ),
            200,
        )

    except Exception as e:
        logger.error(f"Significance test failed: {e}")
        return jsonify({"success": False, "error": f"Test failed: {str(e)}"}), 500


@auto_capture_bp.route("/auto-capture/status", methods=["GET"])
async def get_system_status():
    """Get overall system status and health check."""
    try:
        # Health checks
        health_checks = {
            "significance_engine": True,  # Always available
            "database_connection": True,  # Check if we can write to tracking DB
            "capture_systems": True,  # Check if capture systems are available
            "api_endpoints": True,  # This endpoint is working
        }

        # Test database connection
        try:
            analytics = get_auto_capture_analytics()
            health_checks["database_connection"] = True
        except:
            health_checks["database_connection"] = False

        # Test capture systems
        try:
            from src.live_capture.claude_code_capture import capture_system
            from src.integrations.cursor_ide_capture import cursor_capture_system

            health_checks["capture_systems"] = True
        except:
            health_checks["capture_systems"] = False

        overall_health = all(health_checks.values())

        return (
            jsonify(
                {
                    "success": True,
                    "system_status": {
                        "overall_health": "healthy" if overall_health else "degraded",
                        "components": health_checks,
                        "auto_capture_enabled": True,
                        "significance_thresholds": universal_auto_capture.significance_engine.thresholds,
                        "capture_stats": universal_auto_capture.capture_stats,
                        "uptime": "active",  # Could track actual uptime
                    },
                    "message": "System status retrieved",
                }
            ),
            200,
        )

    except Exception as e:
        logger.error(f"Status check failed: {e}")
        return (
            jsonify({"success": False, "error": f"Status check failed: {str(e)}"}),
            500,
        )
