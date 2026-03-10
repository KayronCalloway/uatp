"""
ML Dashboard API Router
Provides endpoints for viewing machine learning metrics: calibration, historical accuracy, and outcome tracking.
"""

import logging
from typing import Any, Dict

from fastapi import APIRouter, Query

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ml", tags=["Machine Learning"])


@router.get("/dashboard")
async def get_ml_dashboard() -> Dict[str, Any]:
    """
    Get comprehensive ML dashboard data.

    Returns:
        - calibration: Platt scaling calibration report with reliability diagram
        - outcomes: Outcome tracking statistics
        - historical_accuracy: Summary of historical accuracy learning
        - learning_loop: Status of the full learning loop
    """
    result = {
        "calibration": _get_calibration_data(),
        "outcomes": _get_outcome_data(),
        "historical_accuracy": _get_historical_accuracy_data(),
        "learning_loop": _get_learning_loop_status(),
    }
    return result


@router.get("/calibration")
async def get_calibration_report() -> Dict[str, Any]:
    """Get detailed calibration report with reliability diagram."""
    return _get_calibration_data()


@router.get("/calibration/table")
async def get_calibration_table() -> Dict[str, Any]:
    """Get formatted reliability table."""
    try:
        from src.ml.calibration_integration import get_capsule_calibrator

        calibrator = get_capsule_calibrator()

        # Bootstrap if needed
        if not calibrator._bootstrapped:
            calibrator.bootstrap_from_database()

        table_text = calibrator.get_reliability_table()

        return {
            "table": table_text,
            "format": "text",
        }
    except Exception as e:
        logger.warning(f"Failed to get calibration table: {e}")
        return {
            "table": "Calibration data not available",
            "format": "text",
            "error": str(e),
        }


@router.get("/outcomes/stats")
async def get_outcome_stats() -> Dict[str, Any]:
    """Get outcome tracking statistics."""
    return _get_outcome_data()


@router.get("/outcomes/recent")
async def get_recent_outcomes(
    limit: int = Query(default=10, ge=1, le=100),
) -> Dict[str, Any]:
    """Get recent outcome inferences."""
    try:
        from src.live_capture.outcome_integration import get_outcome_tracker

        tracker = get_outcome_tracker()
        outcomes = tracker.get_recent_outcomes(limit=limit)

        return {
            "outcomes": outcomes,
            "total": len(outcomes),
        }
    except Exception as e:
        logger.warning(f"Failed to get recent outcomes: {e}")
        return {
            "outcomes": [],
            "total": 0,
            "error": str(e),
        }


@router.get("/historical-accuracy")
async def get_historical_accuracy() -> Dict[str, Any]:
    """Get historical accuracy learning summary."""
    return _get_historical_accuracy_data()


@router.post("/calibration/test")
async def test_calibration(confidence: float = Query(ge=0.0, le=1.0)) -> Dict[str, Any]:
    """
    Test calibration on a specific confidence value.

    Args:
        confidence: Raw confidence value to calibrate (0-1)

    Returns:
        Calibrated confidence and calibration info
    """
    try:
        from src.ml.calibration_integration import calibrate_capsule_confidence

        calibrated, info = calibrate_capsule_confidence(confidence)

        return {
            "raw_confidence": confidence,
            "calibrated_confidence": calibrated,
            "adjustment": info.get("adjustment", 0),
            "calibration_status": info.get("calibration", "unknown"),
            "sample_size": info.get("sample_size", 0),
        }
    except Exception as e:
        logger.warning(f"Failed to test calibration: {e}")
        return {
            "raw_confidence": confidence,
            "calibrated_confidence": confidence,
            "error": str(e),
        }


# ============================================================================
# Helper functions
# ============================================================================


def _get_calibration_data() -> Dict[str, Any]:
    """Get calibration report data."""
    try:
        from src.ml.calibration_integration import get_capsule_calibrator

        calibrator = get_capsule_calibrator()

        # Bootstrap if needed
        if not calibrator._bootstrapped:
            stats = calibrator.bootstrap_from_database()
            logger.info(f"Bootstrapped calibration: {stats}")

        report = calibrator.get_calibration_report()

        # Parse reliability diagram for chart data
        reliability_data = []
        global_metrics = report.get("global_metrics", {})
        if global_metrics and global_metrics.get("reliability_diagram"):
            for bucket, actual in global_metrics["reliability_diagram"].items():
                reliability_data.append(
                    {
                        "predicted": float(bucket),
                        "actual": actual,
                        "bucket": bucket,
                    }
                )

        return {
            "status": "available",
            "global_metrics": global_metrics,
            "domains": report.get("domains", {}),
            "reliability_data": reliability_data,
            "recommendations": report.get("recommendations", []),
            "drift_alerts": report.get("drift_alerts", []),
        }

    except ImportError:
        return {
            "status": "not_available",
            "error": "Calibration module not installed",
        }
    except Exception as e:
        logger.warning(f"Failed to get calibration data: {e}")
        return {
            "status": "error",
            "error": str(e),
        }


def _get_outcome_data() -> Dict[str, Any]:
    """Get outcome tracking data."""
    try:
        from src.live_capture.outcome_integration import get_outcome_tracker

        tracker = get_outcome_tracker()
        stats = tracker.get_outcome_stats()

        # Build pie chart data for outcomes by status
        by_status_data = []
        if stats.get("by_status"):
            colors = {
                "success": "#10b981",  # green
                "partial": "#f59e0b",  # amber
                "failure": "#ef4444",  # red
            }
            for status, count in stats["by_status"].items():
                by_status_data.append(
                    {
                        "status": status,
                        "count": count,
                        "color": colors.get(status, "#6b7280"),
                    }
                )

        return {
            "status": "available",
            "total_with_outcomes": stats.get("total_with_outcomes", 0),
            "by_status": stats.get("by_status", {}),
            "by_status_data": by_status_data,
            "pending_count": stats.get("pending_count", 0),
            "success_rate": stats.get("success_rate"),
        }

    except ImportError:
        return {
            "status": "not_available",
            "error": "Outcome tracking module not installed",
        }
    except Exception as e:
        logger.warning(f"Failed to get outcome data: {e}")
        return {
            "status": "error",
            "error": str(e),
        }


def _get_historical_accuracy_data() -> Dict[str, Any]:
    """Get historical accuracy learning data."""
    try:
        import sqlite3

        from src.ml.historical_accuracy import get_historical_accuracy_engine

        engine = get_historical_accuracy_engine()

        # Query database directly for statistics
        conn = sqlite3.connect(engine.db_path)
        cursor = conn.cursor()

        # Total capsules
        cursor.execute("SELECT COUNT(*) FROM capsules")
        total_capsules = cursor.fetchone()[0]

        # Capsules with embeddings (stored in payload)
        cursor.execute(
            """
            SELECT COUNT(*) FROM capsules
            WHERE payload IS NOT NULL
            AND json_extract(payload, '$.embedding') IS NOT NULL
        """
        )
        capsules_with_embeddings = cursor.fetchone()[0]

        # Capsules with outcomes
        cursor.execute(
            """
            SELECT COUNT(*) FROM capsules
            WHERE outcome_status IS NOT NULL
        """
        )
        capsules_with_outcomes = cursor.fetchone()[0]

        # Outcome distribution
        cursor.execute(
            """
            SELECT outcome_status, COUNT(*) as count
            FROM capsules
            WHERE outcome_status IS NOT NULL
            GROUP BY outcome_status
        """
        )
        outcome_counts = {row[0]: row[1] for row in cursor.fetchall()}

        conn.close()

        return {
            "status": "available",
            "total_capsules": total_capsules,
            "capsules_with_outcomes": capsules_with_outcomes,
            "capsules_with_embeddings": capsules_with_embeddings,
            "outcome_distribution": outcome_counts,
            "similarity_threshold": engine.MIN_SIMILARITY_THRESHOLD,
            "max_similar_capsules": engine.MAX_SIMILAR_CAPSULES,
            "min_sample_size": engine.MIN_SAMPLE_SIZE,
            "historical_weight": engine.HISTORICAL_WEIGHT,
        }

    except ImportError:
        return {
            "status": "not_available",
            "error": "Historical accuracy module not installed",
        }
    except Exception as e:
        logger.warning(f"Failed to get historical accuracy data: {e}")
        return {
            "status": "error",
            "error": str(e),
        }


def _get_learning_loop_status() -> Dict[str, Any]:
    """Get status of the complete learning loop."""
    calibration = _get_calibration_data()
    outcomes = _get_outcome_data()
    historical = _get_historical_accuracy_data()

    # Determine overall loop health
    components = {
        "calibration": calibration.get("status") == "available",
        "outcome_tracking": outcomes.get("status") == "available",
        "historical_accuracy": historical.get("status") == "available",
    }

    all_healthy = all(components.values())
    healthy_count = sum(1 for v in components.values() if v)

    return {
        "status": "healthy"
        if all_healthy
        else "partial"
        if healthy_count > 0
        else "unavailable",
        "components": components,
        "healthy_count": healthy_count,
        "total_components": len(components),
        "description": (
            "All ML components operational"
            if all_healthy
            else f"{healthy_count}/{len(components)} components operational"
        ),
    }
