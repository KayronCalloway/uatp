"""
UATP Application Factory
Creates and configures the FastAPI application instance
"""

import os
import traceback
import uuid
from contextlib import asynccontextmanager
from typing import Any, Dict

import structlog
from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from prometheus_client import Histogram, generate_latest

from src.utils.timezone_utils import utc_now

from .auth.auth_middleware import setup_auth_middleware
from .auth.auth_routes import router as auth_router
from .core.database import db
from .database.connection import get_database_manager

# Import Redis-backed rate limiter (replaces in-memory slowapi)
from .middleware.rate_limiting import (
    RateLimitConfig,
    RateLimitMiddleware,
)

db_manager = get_database_manager()
from .database.migrations import run_migrations  # noqa: E402
from .integrations.ai_platform_framework import (  # noqa: E402
    setup_multi_platform_attribution,
)

# noqa: E402
from .security.csrf_protection import csrf_middleware  # noqa: E402
from .security.input_validation import (  # noqa: E402
    PAYMENT_REQUEST_SCHEMA,
    USER_REGISTRATION_SCHEMA,
    security_validator,
)
from .user_management.user_service import create_user_service  # noqa: E402


def configure_logging():
    """Configure structured logging"""
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.JSONRenderer(),
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )


def create_metrics():
    """Get Prometheus metrics from monitoring module to prevent duplicates."""
    from prometheus_client import REGISTRY, CollectorRegistry

    # Import metrics from monitoring module (which handles deduplication)
    from .middleware.monitoring import REQUEST_COUNT, REQUEST_DURATION

    # Create attribution metric if not exists (use try/except to avoid private API)
    try:
        attribution_metric = Histogram(
            "attribution_processing_duration_seconds",
            "Attribution processing time",
        )
    except ValueError:
        # Metric already exists, get it from collectors
        for collector in REGISTRY.collect():
            if (
                hasattr(collector, "_name")
                and collector._name == "attribution_processing_duration_seconds"
            ):
                attribution_metric = collector
                break
        else:
            # Fallback: create with a unique name
            attribution_metric = Histogram(
                "attribution_processing_duration_seconds_v2",
                "Attribution processing time",
            )

    return {
        "REQUEST_COUNT": REQUEST_COUNT,
        "REQUEST_DURATION": REQUEST_DURATION,
        "ATTRIBUTION_PROCESSING_TIME": attribution_metric,
    }


def create_limiter():
    """Create rate limiter configuration for Redis-backed rate limiting."""
    return RateLimitConfig()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan management"""
    logger = structlog.get_logger(__name__)
    logger.info("Starting UATP application...")

    try:
        # Validate production secrets before initializing services
        from src.config.settings import validate_production_secrets

        validate_production_secrets()

        # Initialize SQLAlchemy database (needed for migrations)
        logger.info("Initializing SQLAlchemy database...")
        db.init_app(app)

        # Initialize asyncpg database manager (PostgreSQL - optional in development)
        logger.info("Initializing database connection...")
        try:
            await db_manager.connect()
            # Run migrations
            logger.info("Running database migrations...")
            await run_migrations()
        except Exception as e:
            logger.warning(f"PostgreSQL not available (using SQLite): {e}")

        # Load lineage graph from database
        try:
            from .services.capsule_lifecycle_service import capsule_lifecycle_service

            logger.info("Loading lineage graph from database...")
            async with db.get_session() as session:
                edge_count = await capsule_lifecycle_service.load_lineage_from_database(
                    session
                )
                logger.info(f"Loaded {edge_count} lineage edges into graph")
        except Exception as e:
            logger.warning(f"Failed to load lineage graph (non-critical): {e}")

        # Initialize services
        logger.info("Initializing services...")
        app.state.user_service = create_user_service()
        app.state.ai_orchestrator = setup_multi_platform_attribution(
            openai_key=os.getenv("OPENAI_API_KEY"),
            anthropic_key=os.getenv("ANTHROPIC_API_KEY"),
        )

        # Initialize live capture conversation monitor
        logger.info("Initializing live capture conversation monitor...")
        from .live_capture.conversation_monitor import get_monitor

        app.state.conversation_monitor = get_monitor(db_manager=db)

        # Start monitoring in background
        import asyncio

        app.state.monitor_task = asyncio.create_task(
            app.state.conversation_monitor.start_monitoring()
        )

        logger.info(
            f"Live capture enabled with significance threshold: {app.state.conversation_monitor.significance_threshold}"
        )

        logger.info("UATP application started successfully")

    except Exception as e:
        logger.error("Failed to start application", error=str(e))
        raise

    yield

    # Cleanup
    logger.info("Shutting down UATP application...")

    try:
        # Cleanup services
        if hasattr(app.state, "attribution_middleware"):
            await app.state.attribution_middleware.shutdown()

        logger.info("UATP application shut down successfully")

    except Exception as e:
        logger.error("Error during shutdown", error=str(e))


def setup_middleware(app: FastAPI, limiter: RateLimitConfig, metrics: Dict[str, Any]):
    """Setup application middleware"""
    logger = structlog.get_logger(__name__)

    # CORS - Production-safe configuration
    # Get allowed origins from environment or use secure defaults
    allowed_origins = os.getenv(
        "CORS_ALLOWED_ORIGINS",
        "https://uatp.app,https://api.uatp.app,https://dashboard.uatp.app",
    ).split(",")

    # Add localhost for development only (controlled by environment variable)
    if os.getenv("ENVIRONMENT") == "development":
        dev_origins = os.getenv(
            "DEV_ALLOWED_ORIGINS",
            "http://localhost:3000,http://localhost:3001,http://localhost:8080",
        ).split(",")
        allowed_origins.extend(dev_origins)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=allowed_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        allow_headers=[
            "Content-Type",
            "Authorization",
            "X-API-Key",
            "X-Correlation-ID",
        ],
        expose_headers=["X-Correlation-ID"],
    )

    # Trusted hosts - MUST be configured for production
    # Development default is localhost only; production MUST set ALLOWED_HOSTS
    default_hosts = "localhost,127.0.0.1"
    env_hosts = os.getenv("ALLOWED_HOSTS", "")
    if env_hosts:
        allowed_hosts = [h.strip() for h in env_hosts.split(",") if h.strip()]
    else:
        allowed_hosts = [h.strip() for h in default_hosts.split(",")]

    # Only warn if in production AND no ALLOWED_HOSTS was configured
    if os.getenv("ENVIRONMENT") == "production" and not env_hosts:
        logger.warning(
            "[SECURITY] ALLOWED_HOSTS not set in production! "
            "Set ALLOWED_HOSTS=uatp.app,api.uatp.app,dashboard.uatp.app"
        )
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=allowed_hosts)

    # Redis-backed rate limiting middleware
    # Uses sliding window algorithm with Redis for distributed rate limiting
    use_redis = os.getenv("RATE_LIMIT_USE_REDIS", "true").lower() == "true"
    if use_redis:
        logger.info(" Using Redis-backed rate limiter (production mode)")
        app.add_middleware(RateLimitMiddleware, config=limiter)
    else:
        logger.warning("[WARN] Using in-memory rate limiter (development mode only)")
        # Fallback: create in-memory limiter for development
        from .middleware.rate_limiting import InMemoryRateLimiter

        class InMemoryRateLimitMiddleware(RateLimitMiddleware):
            def __init__(self, app, config):
                super().__init__(app, config)
                self.limiter = InMemoryRateLimiter(config)

        app.add_middleware(InMemoryRateLimitMiddleware, config=limiter)

    app.state.rate_limit_config = limiter

    # Authentication and security middleware
    setup_auth_middleware(app)
    app.middleware("http")(csrf_middleware)

    # Metrics and correlation ID middleware
    @app.middleware("http")
    async def metrics_middleware(request: Request, call_next):
        """Collect HTTP metrics and add correlation IDs"""
        import time as time_module

        # Generate or extract correlation ID
        correlation_id = request.headers.get("X-Correlation-ID") or str(uuid.uuid4())

        # Add correlation ID to request state for access in route handlers
        request.state.correlation_id = correlation_id

        start_time = time_module.time()
        try:
            response = await call_next(request)

            # Record duration with labels
            duration = time_module.time() - start_time
            metrics["REQUEST_DURATION"].labels(
                method=request.method, endpoint=request.url.path
            ).observe(duration)

            # Add correlation ID to response headers
            response.headers["X-Correlation-ID"] = correlation_id

            metrics["REQUEST_COUNT"].labels(
                method=request.method,
                endpoint=request.url.path,
                status_code=response.status_code,
            ).inc()

            return response

        except Exception:
            duration = time_module.time() - start_time
            metrics["REQUEST_DURATION"].labels(
                method=request.method, endpoint=request.url.path
            ).observe(duration)
            metrics["REQUEST_COUNT"].labels(
                method=request.method, endpoint=request.url.path, status_code=500
            ).inc()
            raise


def setup_exception_handlers(app: FastAPI):
    """Setup exception handlers with structured error handling and correlation IDs"""
    logger = structlog.get_logger(__name__)

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        request: Request, exc: RequestValidationError
    ):
        """Handle validation errors with correlation ID"""
        correlation_id = str(uuid.uuid4())

        logger.warning(
            "Validation error",
            correlation_id=correlation_id,
            path=request.url.path,
            method=request.method,
            errors=exc.errors(),
            client_ip=request.client.host if request.client else "unknown",
        )

        return JSONResponse(
            status_code=422,
            content={
                "error": "Validation failed",
                "detail": "Request validation failed",
                "errors": exc.errors(),
                "correlation_id": correlation_id,
                "timestamp": utc_now().isoformat(),
            },
            headers={"X-Correlation-ID": correlation_id},
        )

    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException):
        """Handle HTTP exceptions with correlation ID"""
        correlation_id = str(uuid.uuid4())

        logger.info(
            "HTTP exception",
            correlation_id=correlation_id,
            path=request.url.path,
            method=request.method,
            status_code=exc.status_code,
            detail=exc.detail,
            client_ip=request.client.host if request.client else "unknown",
        )

        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": "HTTP error",
                "detail": exc.detail,
                "correlation_id": correlation_id,
                "timestamp": utc_now().isoformat(),
            },
            headers={"X-Correlation-ID": correlation_id},
        )

    @app.exception_handler(Exception)
    async def general_exception_handler(request: Request, exc: Exception):
        """Handle general exceptions with structured logging and correlation ID"""
        correlation_id = str(uuid.uuid4())

        # Log with full context for debugging
        logger.error(
            "Unhandled exception",
            correlation_id=correlation_id,
            path=request.url.path,
            method=request.method,
            error_type=type(exc).__name__,
            error_message=str(exc),
            stack_trace=traceback.format_exc(),
            client_ip=request.client.host if request.client else "unknown",
            user_agent=request.headers.get("user-agent", "unknown"),
        )

        # Return sanitized error response (don't expose internal details in production)
        is_production = os.getenv("ENVIRONMENT") == "production"

        response_content = {
            "error": "Internal server error",
            "detail": "An unexpected error occurred. Please try again later.",
            "correlation_id": correlation_id,
            "timestamp": utc_now().isoformat(),
        }

        # Add debug info in non-production environments
        if not is_production:
            response_content["debug"] = {
                "error_type": type(exc).__name__,
                "error_message": str(exc),
            }

        return JSONResponse(
            status_code=500,
            content=response_content,
            headers={"X-Correlation-ID": correlation_id},
        )


def setup_health_routes(app: FastAPI):
    """Setup health check routes"""
    logger = structlog.get_logger(__name__)

    @app.get("/health", tags=["Monitoring"])
    async def health_check():
        """Health check endpoint"""
        from datetime import datetime, timezone

        return {
            "status": "healthy",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    @app.get("/ready", tags=["Monitoring"])
    async def readiness_check():
        """Readiness check endpoint"""
        try:
            # Check Redis connection
            health = db_manager.health_check()
            if not health["database"]:
                raise HTTPException(status_code=503, detail="Database not ready")

            return {"status": "ready", "checks": health}

        except Exception as e:
            logger.error("Readiness check failed", error=str(e))
            raise HTTPException(status_code=503, detail="Service not ready") from e

    @app.get("/startup")
    async def startup_check():
        """Startup check endpoint"""
        from datetime import datetime, timezone

        return {
            "status": "started",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    @app.get("/health/activity", tags=["Monitoring"])
    async def recent_activity():
        """Get recent system activity feed for Mission Control dashboard"""
        try:
            from src.core.database import db

            activities = []

            # Get recent capsules from database
            async with db.session() as session:
                from sqlalchemy import text

                result = await session.execute(
                    text(
                        """
                        SELECT id, capsule_type, agent_id, created_at, payload
                        FROM capsules
                        ORDER BY created_at DESC
                        LIMIT 20
                    """
                    )
                )
                capsules = result.fetchall()

                for capsule in capsules:
                    activities.append(
                        {
                            "id": capsule[0],
                            "type": "capsule_created",
                            "title": "Capsule Created",
                            "description": f"{capsule[1]} by {capsule[2]}",
                            "status": "success",
                            "timestamp": capsule[3].isoformat()
                            if capsule[3]
                            else utc_now().isoformat(),
                            "metadata": {
                                "capsule_id": capsule[0],
                                "capsule_type": capsule[1],
                                "agent_id": capsule[2],
                            },
                        }
                    )

            return {"activities": activities}
        except Exception as e:
            logger.error("Error fetching activity", error=str(e))
            return {"activities": []}

    @app.get("/health/metrics", tags=["Monitoring"])
    async def system_health_metrics():
        """Get system health metrics for Mission Control dashboard"""
        try:
            import time

            from src.core.database import db

            metrics = []

            # Database health
            db_health = 95
            try:
                async with db.session() as session:
                    from sqlalchemy import text

                    start = time.time()
                    await session.execute(text("SELECT 1"))
                    response_time = (time.time() - start) * 1000

                    if response_time < 50:
                        db_health = 98
                    elif response_time < 100:
                        db_health = 92
                    else:
                        db_health = 85
            except Exception:
                db_health = 60

            metrics.append(
                {
                    "name": "database",
                    "label": "Database",
                    "value": db_health,
                    "status": "healthy" if db_health >= 90 else "degraded",
                }
            )

            # API health - based on successful response
            api_health = 100 if db_health >= 60 else 50
            metrics.append(
                {
                    "name": "api",
                    "label": "API",
                    "value": api_health,
                    "status": "healthy" if api_health >= 90 else "degraded",
                }
            )

            # Crypto/signature system health - verify key manager is accessible
            crypto_health = 100
            try:
                from src.security.secure_key_manager import SecureKeyManager

                key_manager = SecureKeyManager()
                if key_manager.get_signing_key():
                    crypto_health = 100
                else:
                    crypto_health = 50
            except Exception:
                crypto_health = 0

            metrics.append(
                {
                    "name": "crypto",
                    "label": "Cryptography",
                    "value": crypto_health,
                    "status": "healthy"
                    if crypto_health >= 90
                    else "degraded"
                    if crypto_health >= 50
                    else "unhealthy",
                }
            )

            return {"metrics": metrics}
        except Exception as e:
            logger.error("Error fetching health metrics", error=str(e))
            return {"metrics": []}

    @app.get("/metrics", tags=["Monitoring"])
    async def metrics():
        """Prometheus metrics endpoint"""
        return generate_latest()

    @app.get("/health/crypto", tags=["Monitoring"])
    async def crypto_status():
        """Get cryptographic subsystem status for dashboard"""
        try:
            from src.security.uatp_crypto_v7 import (
                ED25519_AVAILABLE,
                PQ_AVAILABLE,
                UATPCryptoV7,
            )

            # Initialize crypto to get status
            crypto = UATPCryptoV7(enable_pq=PQ_AVAILABLE)
            status = crypto.get_security_status()

            # Check for actual module implementations
            try:
                from src.security.rfc3161_timestamps import RFC3161Timestamper

                rfc3161_available = True
            except ImportError:
                rfc3161_available = False

            try:
                from src.security.key_rotation import KeyRotationManager

                key_rotation_available = True
            except ImportError:
                key_rotation_available = False

            try:
                from src.security.merkle_audit_log import MerkleAuditLog

                merkle_available = True
            except ImportError:
                merkle_available = False

            # Build feature list
            features = {
                "ed25519": {
                    "name": "Ed25519 Signatures",
                    "available": ED25519_AVAILABLE,
                    "status": "active" if ED25519_AVAILABLE else "unavailable",
                },
                "ml_dsa_65": {
                    "name": "ML-DSA-65 (Post-Quantum)",
                    "available": PQ_AVAILABLE,
                    "status": "active"
                    if status.get("pq_enabled")
                    else "available"
                    if PQ_AVAILABLE
                    else "unavailable",
                },
                "hybrid_signatures": {
                    "name": "Hybrid Signatures",
                    "available": status.get("hybrid_capable", False),
                    "status": "active"
                    if status.get("hybrid_capable")
                    else "unavailable",
                },
                "rfc3161_timestamps": {
                    "name": "RFC 3161 Timestamps",
                    "available": rfc3161_available,
                    "status": "active" if rfc3161_available else "unavailable",
                },
                "key_rotation": {
                    "name": "Key Rotation",
                    "available": key_rotation_available,
                    "status": "active" if key_rotation_available else "unavailable",
                },
                "merkle_audit_log": {
                    "name": "Merkle Audit Logs",
                    "available": merkle_available,
                    "status": "active" if merkle_available else "unavailable",
                },
                "key_encryption": {
                    "name": "Key Encryption (AES-256-GCM)",
                    "available": True,
                    "status": "active",
                },
            }

            # Count features
            total = len(features)
            active = sum(1 for f in features.values() if f["status"] == "active")

            return {
                "environment": status.get("environment", "development"),
                "algorithms": status.get("algorithms", {}),
                "features": features,
                "summary": {
                    "total_features": total,
                    "active_features": active,
                    "completion_percent": int(100 * active / total) if total > 0 else 0,
                },
                "recommendations": status.get("recommendations", []),
                "warnings": status.get("warnings", []),
            }
        except Exception as e:
            logger.error("Error fetching crypto status", error=str(e))
            return {
                "error": str(e),
                "features": {},
                "summary": {
                    "total_features": 0,
                    "active_features": 0,
                    "completion_percent": 0,
                },
            }


def setup_api_routes(app: FastAPI, rate_config: RateLimitConfig):
    """Setup API routes. Rate limiting is now handled by middleware."""
    logger = structlog.get_logger(__name__)

    @app.get("/")
    async def root():
        """Root endpoint"""
        return {
            "message": "UATP - Unified Agent Trust Protocol",
            "version": "0.3.0",
            "environment": os.getenv("ENVIRONMENT", "development"),
        }

    @app.get("/api/v1/status")
    async def api_status():
        """API status endpoint"""
        return {
            "api_version": "0.3.0",
            "status": "operational",
            "features": {
                "attribution_tracking": True,
                "payment_processing": True,
                "ai_integrations": True,
                "privacy_compliance": True,
            },
        }

    @app.post("/api/v1/users/register", tags=["Authentication"])
    async def register_user(request: Request, user_data: Dict[str, Any]):
        """Register a new user with validation"""
        try:
            # Validate input data
            validated_data = security_validator.validate_json_schema(
                user_data, USER_REGISTRATION_SCHEMA
            )

            user_service = app.state.user_service
            result = await user_service.register_user(**validated_data)

            if result["success"]:
                logger.info("User registered", user_id=result["user_id"])
                return {"success": True, "user_id": result["user_id"]}
            else:
                logger.warning("User registration failed", error=result["error"])
                raise HTTPException(status_code=400, detail=result["error"])

        except Exception as e:
            logger.error("User registration error", error=str(e))
            raise HTTPException(status_code=500, detail="Registration failed") from e

    @app.get("/api/v1/users/{user_id}", tags=["Authentication"])
    async def get_user(request: Request, user_id: str):
        """Get user profile"""
        try:
            user_service = app.state.user_service
            user = await user_service.get_user_profile(user_id)

            if user:
                return {
                    "user_id": user.user_id,
                    "username": user.username,
                    "email": user.email,
                    "total_earnings": float(user.total_earnings),
                    "total_attributions": user.total_attributions,
                }
            else:
                raise HTTPException(status_code=404, detail="User not found")

        except Exception as e:
            logger.error("Get user error", user_id=user_id, error=str(e))
            raise HTTPException(status_code=500, detail="Failed to get user") from e

    @app.post("/api/v1/attribution/track", tags=["Attribution"])
    async def track_attribution(request: Request, attribution_data: Dict[str, Any]):
        """Track attribution event"""
        try:
            # This would integrate with the attribution middleware
            logger.info("Attribution tracked", data=attribution_data)
            return {"success": True, "attribution_id": "attr_123"}

        except Exception as e:
            logger.error("Attribution tracking error", error=str(e))
            raise HTTPException(
                status_code=500, detail="Attribution tracking failed"
            ) from e

    @app.get("/api/v1/admin/stats", tags=["Monitoring"])
    async def admin_stats(request: Request):
        """Get admin statistics"""
        try:
            # This would be protected by authentication
            stats = {
                "total_users": 1000,
                "total_attributions": 50000,
                "total_payouts": 25000.00,
                "active_conversations": 150,
            }
            return stats

        except Exception as e:
            logger.error("Admin stats error", error=str(e))
            raise HTTPException(status_code=500, detail="Failed to get stats") from e


def setup_development_routes(app: FastAPI):
    """Setup development-only routes"""
    if os.getenv("ENVIRONMENT") == "development":

        @app.get("/debug/info")
        async def debug_info():
            """Debug information (development only)"""
            return {
                "environment": os.getenv("ENVIRONMENT"),
                "database_url": os.getenv("DATABASE_URL", "").replace(
                    os.getenv("DATABASE_PASSWORD", ""), "***"
                ),
                "redis_url": os.getenv("REDIS_URL"),
                "services": {
                    "user_service": hasattr(app.state, "user_service"),
                    "ai_orchestrator": hasattr(app.state, "ai_orchestrator"),
                },
            }


def create_app() -> FastAPI:
    """
    Application factory function.
    Creates and configures a FastAPI application instance.
    """
    # Configure logging
    configure_logging()

    # Create metrics
    metrics = create_metrics()

    # Create rate limiter
    limiter = create_limiter()

    # Create FastAPI app with comprehensive documentation
    app = FastAPI(
        title="UATP - Unified Agent Trust Protocol",
        description="""
        ## Advanced AI Attribution and Payment Platform

        The UATP Capsule Engine provides a comprehensive framework for:

        * **AI Attribution Tracking** - Real-time attribution across multiple AI platforms
        * **Economic Engine** - Fair Creator Dividend Engine (FCDE) for value distribution
        * **Governance System** - Decentralized decision-making and voting mechanisms
        * **Capsule Management** - Cryptographically sealed reasoning chains
        * **Security & Privacy** - Post-quantum cryptography and zero-knowledge proofs

        ### Quick Start

        1. Register as a stakeholder in the governance system
        2. Configure your AI platform integrations
        3. Start tracking attributions through the unified API
        4. Monitor economic value distribution via the dashboard

        ### Authentication

        All API endpoints require proper authentication. See the `/auth` endpoints for details.
        """,
        version="0.3.0",
        lifespan=lifespan,
        docs_url="/docs" if os.getenv("ENVIRONMENT") != "production" else None,
        redoc_url="/redoc" if os.getenv("ENVIRONMENT") != "production" else None,
        openapi_tags=[
            {
                "name": "Authentication",
                "description": "User authentication and authorization",
            },
            {
                "name": "Capsules",
                "description": "Capsule creation, management, and retrieval operations",
            },
            {
                "name": "Attribution",
                "description": "AI attribution tracking and economic value calculation",
            },
            {
                "name": "Registry",
                "description": "LLM provider and model registry management",
            },
            {
                "name": "Monitoring",
                "description": "Performance monitoring, health checks, and metrics",
            },
            {
                "name": "Security",
                "description": "Security validation, cryptographic operations",
            },
            {
                "name": "Cursor IDE Integration",
                "description": "Cursor IDE workflow capture and session management",
            },
        ],
        contact={
            "name": "UATP Development Team",
            "url": "https://github.com/KayronCalloway/uatp",
            "email": "Kayron@houseofcalloway.com",
        },
        license_info={
            "name": "MIT License",
            "url": "https://opensource.org/licenses/MIT",
        },
    )

    # Setup middleware
    setup_middleware(app, limiter, metrics)

    # Setup exception handlers
    setup_exception_handlers(app)

    # Include authentication routes
    app.include_router(auth_router)

    # Include real database-backed capsules router
    from .api.capsules_fastapi_router import router as capsules_router

    app.include_router(capsules_router)

    # Include live capture router for real-time monitoring
    from .api.live_capture_fastapi_router import router as live_capture_router

    app.include_router(live_capture_router)

    # Include trust management router
    from .api.trust_fastapi_router import router as trust_router

    app.include_router(trust_router)

    # Include platform router (converted from Quart)
    from .api.platform_fastapi_router import router as platform_router

    app.include_router(platform_router)

    # Include Cursor IDE integration router (converted from Quart)
    # NOTE: cursor_fastapi_router was never committed - using cursor_routes instead
    # from .api.cursor_fastapi_router import router as cursor_router
    # app.include_router(cursor_router)

    # Include training data export router
    from .api.export_router import router as export_router

    app.include_router(export_router)

    # Include RFC 3161 Timestamp router (zero-trust timestamping)
    from .api.timestamp_router import router as timestamp_router

    app.include_router(timestamp_router)

    # Include user encryption keys router
    from .api.user_keys_router import router as user_keys_router

    app.include_router(user_keys_router)

    # Include UATP 7.2 Model Registry router (Training Provenance)
    from .api.model_registry_router import router as model_registry_router

    app.include_router(model_registry_router)

    # Include UATP 7.2 Workflow Chain router (Agentic Workflows)
    from .api.workflow_chain_router import router as workflow_chain_router

    app.include_router(workflow_chain_router)

    # Include UATP 7.2 Hardware Attestation router
    from .api.attestation_router import router as attestation_router

    app.include_router(attestation_router)

    # Include UATP 7.2 Model Artifacts and Licenses router
    from .api.model_artifacts_router import router as model_artifacts_router

    app.include_router(model_artifacts_router)

    # Include UATP 7.4 Agent Execution Traces router
    from .api.agent_execution_router import router as agent_execution_router

    app.include_router(agent_execution_router)

    # Include Chain Sealing router
    from .api.chain_fastapi_router import router as chain_router

    app.include_router(chain_router)

    # Include Reasoning Analysis router
    from .api.reasoning_fastapi_router import router as reasoning_router

    app.include_router(reasoning_router)

    # Setup routes
    setup_health_routes(app)
    setup_api_routes(app, limiter)
    setup_development_routes(app)

    return app
