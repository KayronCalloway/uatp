import time
from datetime import datetime

from quart import Blueprint, current_app, jsonify
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from .dependencies import get_db, get_engine

health_bp = Blueprint("health", __name__)


@health_bp.route("/health", methods=["GET", "OPTIONS"])
async def health_check():
    """Basic health check endpoint that returns service status."""
    # Handle OPTIONS requests for CORS
    from quart import request

    if request.method == "OPTIONS":
        return "", 200

    try:
        # Check database connectivity
        db_status = "ok"
        try:
            from src.core.database import db

            async with db.get_session() as session:
                await session.execute(text("SELECT 1"))
        except Exception as e:
            db_status = f"error: {e}"

        engine_status = (
            "OK"
            if hasattr(current_app, "engine") and current_app.engine
            else "Not Initialized"
        )
        features = {
            "caching": current_app.config.get("CACHE_ENABLED", False),
            "rate_limiting": True,
        }

        overall_healthy = db_status == "ok" and engine_status == "OK"

        health_data = {
            "status": "healthy" if overall_healthy else "unhealthy",
            "version": current_app.config.get("VERSION", "1.0.0"),
            "engine": engine_status,
            "database": db_status,
            "features": features,
            "timestamp": datetime.utcnow().isoformat(),
        }

        return jsonify(health_data), 200 if overall_healthy else 503

    except Exception as e:
        return (
            jsonify(
                {
                    "status": "unhealthy",
                    "error": str(e),
                    "timestamp": datetime.utcnow().isoformat(),
                }
            ),
            503,
        )


@health_bp.route("/health/ready")
async def readiness_check():
    """Readiness check that verifies all dependencies are available."""
    checks = {}
    overall_healthy = True

    # Check database connectivity
    try:
        db_session = get_db()
        if hasattr(db_session, "execute"):
            # Async session
            result = await db_session.execute(text("SELECT 1"))
            result.fetchone()
        else:
            # Sync session fallback
            db_session.execute(text("SELECT 1"))

        checks["database"] = {"status": "healthy"}
    except Exception as e:
        checks["database"] = {"status": "unhealthy", "error": str(e)}
        overall_healthy = False

    # Check engine availability
    try:
        engine = get_engine()
        if engine:
            checks["engine"] = {"status": "healthy"}
        else:
            checks["engine"] = {"status": "unhealthy", "error": "Engine not available"}
            overall_healthy = False
    except Exception as e:
        checks["engine"] = {"status": "unhealthy", "error": str(e)}
        overall_healthy = False

    # Check cache if enabled
    if current_app.config.get("CACHE_ENABLED", False):
        try:
            if hasattr(current_app, "cache"):
                # Try to set and get a test value
                await current_app.cache.set("health_check", "test", expire=5)
                value = await current_app.cache.get("health_check")
                if value == "test":
                    checks["cache"] = {"status": "healthy"}
                else:
                    checks["cache"] = {
                        "status": "unhealthy",
                        "error": "Cache read/write failed",
                    }
                    overall_healthy = False
            else:
                checks["cache"] = {
                    "status": "unhealthy",
                    "error": "Cache not configured",
                }
                overall_healthy = False
        except Exception as e:
            checks["cache"] = {"status": "unhealthy", "error": str(e)}
            overall_healthy = False
    else:
        checks["cache"] = {"status": "disabled"}

    status_code = 200 if overall_healthy else 503

    return (
        jsonify(
            {
                "status": "ready" if overall_healthy else "not_ready",
                "checks": checks,
                "timestamp": datetime.utcnow().isoformat(),
            }
        ),
        status_code,
    )


@health_bp.route("/health/live")
async def liveness_check():
    """Liveness check that verifies the service is running."""
    try:
        return (
            jsonify(
                {
                    "status": "alive",
                    "timestamp": datetime.utcnow().isoformat(),
                    "uptime_seconds": time.time()
                    - getattr(current_app, "start_time", time.time()),
                }
            ),
            200,
        )
    except Exception as e:
        return (
            jsonify(
                {
                    "status": "dead",
                    "error": str(e),
                    "timestamp": datetime.utcnow().isoformat(),
                }
            ),
            503,
        )


@health_bp.route("/health/detailed")
async def detailed_health_check():
    """Detailed health check with comprehensive system status."""
    start_time = time.time()
    checks = {}
    overall_healthy = True

    # Database detailed check
    try:
        db_start = time.time()
        from src.core.database import db

        async with db.get_session() as session:
            # Check database connectivity and basic query
            result = await session.execute(text("SELECT version()"))
            db_version = result.fetchone()[0] if result.fetchone() else "Unknown"

            # Check if capsule table exists
            result = await session.execute(
                text(
                    """
                SELECT COUNT(*) FROM information_schema.tables
                WHERE table_name = 'capsules'
            """
                )
            )
            table_exists = result.fetchone()[0] > 0

            # Get capsule count if table exists
            capsule_count = 0
            if table_exists:
                result = await session.execute(text("SELECT COUNT(*) FROM capsules"))
                capsule_count = result.fetchone()[0]

        db_time = (time.time() - db_start) * 1000

        checks["database"] = {
            "status": "healthy",
            "response_time_ms": round(db_time, 2),
            "version": db_version,
            "capsule_count": capsule_count,
            "tables_exist": table_exists,
        }
    except SQLAlchemyError as e:
        checks["database"] = {
            "status": "unhealthy",
            "error": f"Database error: {str(e)}",
            "type": "database_error",
        }
        overall_healthy = False
    except Exception as e:
        checks["database"] = {
            "status": "unhealthy",
            "error": str(e),
            "type": "general_error",
        }
        overall_healthy = False

    # Engine detailed check
    try:
        engine = get_engine()
        if engine:
            checks["engine"] = {
                "status": "healthy",
                "agent_id": getattr(engine, "agent_id", "not_set"),
                "has_signing_key": hasattr(engine, "signing_key")
                and engine.signing_key is not None,
            }
        else:
            checks["engine"] = {"status": "unhealthy", "error": "Engine not available"}
            overall_healthy = False
    except Exception as e:
        checks["engine"] = {"status": "unhealthy", "error": str(e)}
        overall_healthy = False

    # Cache detailed check
    if current_app.config.get("CACHE_ENABLED", False):
        try:
            cache_start = time.time()
            if hasattr(current_app, "cache"):
                test_key = f"health_check_{int(time.time())}"
                await current_app.cache.set(test_key, "test_value", expire=5)
                value = await current_app.cache.get(test_key)
                await current_app.cache.delete(test_key)

                cache_time = (time.time() - cache_start) * 1000

                checks["cache"] = {
                    "status": "healthy",
                    "response_time_ms": round(cache_time, 2),
                    "read_write_test": value == "test_value",
                }
            else:
                checks["cache"] = {
                    "status": "unhealthy",
                    "error": "Cache not configured",
                }
                overall_healthy = False
        except Exception as e:
            checks["cache"] = {"status": "unhealthy", "error": str(e)}
            overall_healthy = False
    else:
        checks["cache"] = {"status": "disabled"}

    # System information
    system_info = {
        "python_version": current_app.config.get("PYTHON_VERSION", "unknown"),
        "environment": current_app.config.get("ENVIRONMENT", "unknown"),
        "debug_mode": current_app.debug,
        "testing_mode": current_app.config.get("TESTING", False),
    }

    total_time = (time.time() - start_time) * 1000
    status_code = 200 if overall_healthy else 503

    return (
        jsonify(
            {
                "status": "healthy" if overall_healthy else "unhealthy",
                "checks": checks,
                "system": system_info,
                "timestamp": datetime.utcnow().isoformat(),
                "check_duration_ms": round(total_time, 2),
            }
        ),
        status_code,
    )
