"""
UATP Capsule Engine API Server

A Flask-based REST API for accessing and interacting with the UATP Capsule Engine.
This allows external systems and agents to submit, verify, and query capsules.
Enhanced with authentication, rate limiting, chain sealing, and compression support.
"""

import argparse
import os

from asgi_caches.middleware import CacheMiddleware
from caches import Cache
from dotenv import load_dotenv
from quart import g, jsonify
from quart_rate_limiter import RateLimiter
from quart_schema import Info, QuartSchema
from quart_schema.validation import DataSource

from src.config.settings import Settings
from src.core.database import db
from src.engine.capsule_engine import CapsuleEngine

from .custom_quart import CustomQuart
from .logger import configure_logging

# Load environment variables from .env file
load_dotenv()

# Initialize extensions
limiter = RateLimiter()


def create_app(config_overrides: dict = None, engine_override: CapsuleEngine = None):
    """Create and configure a new Quart app."""
    app = CustomQuart(__name__)
    QuartSchema(app, info=Info(title="UATP Capsule Engine API", version="1.0.0"))

    # Load configuration
    config = Settings()
    app.config.from_object(config)
    if config_overrides:
        app.config.update(config_overrides)

    # Set default Flask config values that Quart might expect
    app.config.setdefault("QUART_SCHEMA_CONVERT_CASING", False)
    app.config.setdefault(
        "QUART_SCHEMA_CONVERSION_PREFERENCE",
        (DataSource.JSON, DataSource.FORM, DataSource.FORM_MULTIPART),
    )

    # Initialize logging
    configure_logging(app.name)
    app.logger.info(f"Log level set to {app.config.get('LOG_LEVEL', 'INFO')}")

    # Configure API Keys for authentication
    app.config["API_KEYS"] = {
        "test-api-key": {
            "permissions": ["read", "write"],
            "agent_id": "claude-code-integration",
            "description": "Test key for development and integration",
        },
        "uatp-admin-key": {
            "permissions": ["read", "write", "admin"],
            "agent_id": "uatp-system-admin",
            "description": "Administrative access key",
        },
        "claude-key": {
            "permissions": ["read", "write"],
            "agent_id": "claude-sonnet-4",
            "description": "Claude Code session key",
        },
    }
    app.logger.info(
        f"✅ API Keys configured: {len(app.config['API_KEYS'])} keys registered"
    )

    # Initialize database
    db.init_app(app)

    # Import all models to ensure they're registered with SQLAlchemy
    from src.models.capsule import CapsuleModel  # noqa
    from src.models.payment import PayoutMethodModel, TransactionModel  # noqa
    from src.models.user import UserModel  # noqa
    from src.models.outcome import (  # noqa
        CapsuleOutcomeModel,
        ConfidenceCalibrationModel,
        ReasoningPatternModel,
    )

    try:
        from src.insurance.models import (
            AILiabilityEventLog,
            InsuranceClaim,
            InsurancePolicy,
        )
    except ImportError:
        pass  # Insurance models may not exist yet

    # Use the provided engine or create a new one. This is key for testing.
    if engine_override:
        app.engine = engine_override
    else:
        # In production, the app creates its own engine.
        # Pass the db manager, not a session, since the engine is long-lived.
        app.engine = CapsuleEngine(db_manager=db)

    # Initialize other extensions
    limiter.init_app(app)

    # CORS is now handled manually in before_request and after_request hooks
    # to provide better control and avoid middleware conflicts
    # See the create_session() and close_session() functions below

    # Initialize security middleware
    from .security_middleware import SecurityMiddleware

    security_middleware = SecurityMiddleware(app)
    app.security_middleware = security_middleware  # Store reference for access

    # Security initialization is handled in connect_extensions (@app.before_serving)
    # to avoid double initialization and race conditions.

    # Import and register blueprints
    from .ai_routes import ai_bp
    from .bonds_citizenship_api import create_bonds_citizenship_api_blueprint
    from .capsule_routes import capsules_bp
    from .chain_routes import chain_bp
    from .dependencies import get_engine, require_api_key
    from .economics_routes import economics_bp
    from .federation_routes import federation_bp
    from .governance_routes import governance_bp
    from .health_routes import health_bp
    from .insurance_routes import insurance_bp
    from .live_capture_routes import live_capture_bp
    from .metrics import render_metrics, setup_metrics_hooks
    from .mirror_mode_api import create_mirror_mode_api_blueprint
    from .mobile_routes import mobile_bp
    from .monitoring_routes import monitoring_bp
    from .organization_routes import organization_bp
    from .outcome_routes_quart import outcome_bp
    from .platform_routes import create_platform_blueprint
    from .reasoning_api import create_reasoning_blueprint
    from .rights_evolution_api import create_rights_evolution_api_blueprint
    from .security_dashboard import create_security_dashboard_blueprint
    from .security_routes import create_security_blueprint
    from .spatial_routes import init_spatial_providers, spatial_bp
    from .trust_routes import trust_bp
    from .user_routes import create_user_blueprint
    from .webauthn_routes import webauthn_bp

    reasoning_bp = create_reasoning_blueprint(
        engine_getter=get_engine, require_api_key=require_api_key
    )

    # Initialize spatial AI providers
    init_spatial_providers()
    app.logger.info("✅ Spatial AI providers initialized")

    # Try to import and create onboarding blueprint with error handling
    onboarding_bp = None
    try:
        from ..onboarding.web_interface import create_onboarding_blueprint

        onboarding_bp = create_onboarding_blueprint()
        app.logger.info("✅ Onboarding blueprint created successfully")
    except Exception as e:
        app.logger.error(f"❌ Failed to create onboarding blueprint: {e}")
        import traceback

        app.logger.error(traceback.format_exc())

    user_bp = create_user_blueprint()
    platform_bp = create_platform_blueprint()
    security_bp = create_security_blueprint()
    security_dashboard_bp = create_security_dashboard_blueprint()

    mirror_mode_bp = create_mirror_mode_api_blueprint(
        engine_getter=get_engine, require_api_key=require_api_key
    )

    rights_evolution_bp = create_rights_evolution_api_blueprint(
        engine_getter=get_engine, require_api_key=require_api_key
    )

    bonds_citizenship_bp = create_bonds_citizenship_api_blueprint(
        engine_getter=get_engine, require_api_key=require_api_key
    )

    app.register_blueprint(health_bp)
    app.register_blueprint(ai_bp)
    app.register_blueprint(chain_bp)
    app.register_blueprint(capsules_bp)
    app.register_blueprint(live_capture_bp)
    app.register_blueprint(mobile_bp, url_prefix="/api/v1/mobile")
    app.register_blueprint(webauthn_bp, url_prefix="/api/v1/webauthn")
    app.register_blueprint(insurance_bp, url_prefix="/api/v1/insurance")
    app.register_blueprint(trust_bp, url_prefix="/trust")
    app.register_blueprint(reasoning_bp, url_prefix="/reasoning")
    app.register_blueprint(mirror_mode_bp, url_prefix="/api/v1/mirror")
    app.register_blueprint(rights_evolution_bp)
    app.register_blueprint(bonds_citizenship_bp)
    app.register_blueprint(governance_bp, url_prefix="/governance")
    app.register_blueprint(federation_bp, url_prefix="/federation")
    app.register_blueprint(organization_bp, url_prefix="/organization")
    app.register_blueprint(economics_bp, url_prefix="/economics")
    app.register_blueprint(monitoring_bp)  # Performance and security monitoring
    app.logger.info("✅ Monitoring routes registered at /api/v1/monitoring")
    app.register_blueprint(outcome_bp)  # Outcome tracking and learning
    app.logger.info("✅ Outcome tracking routes registered at /outcomes")

    # Register onboarding blueprint with error handling
    if onboarding_bp is not None:
        try:
            app.register_blueprint(onboarding_bp)
            app.logger.info("✅ Onboarding blueprint registered")
        except Exception as e:
            app.logger.error(f"❌ Failed to register onboarding blueprint: {e}")
    else:
        app.logger.warning(
            "⚠️ Onboarding blueprint was not created, skipping registration"
        )

    app.register_blueprint(user_bp)
    app.register_blueprint(platform_bp)
    app.register_blueprint(security_bp, url_prefix="/api/v1")
    app.register_blueprint(security_dashboard_bp, url_prefix="/api/v1")
    app.register_blueprint(spatial_bp)  # Spatial AI integration
    app.logger.info("✅ Spatial AI routes registered at /api/spatial")

    # --- Prometheus Metrics Setup ---
    # Add the /metrics endpoint for Prometheus scraping
    app.add_url_rule("/metrics", "metrics", render_metrics, methods=["GET"])
    # Set up request hooks to capture metrics
    setup_metrics_hooks(app)
    app.logger.info("Prometheus metrics endpoint enabled at /metrics")

    # --- Security Statistics Endpoint ---
    @app.route("/security-stats", methods=["GET"])
    @require_api_key(["read"])
    async def security_statistics():
        """Get comprehensive security middleware statistics."""
        try:
            if hasattr(app, "security_middleware"):
                stats = app.security_middleware.get_security_statistics()
                return jsonify(stats)
            else:
                return jsonify({"error": "Security middleware not initialized"}), 503
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    app.logger.info("Security statistics endpoint enabled at /security-stats")

    # Apply caching middleware if enabled
    if app.config.get("CACHE_ENABLED", False):
        # For testing with locmem, the URL scheme is simple.
        # For other backends, a full URL would be constructed from config.
        if app.config.get("TESTING", False):
            cache_url = "locmem://"
        else:
            cache_url = os.getenv("CACHE_URL", "locmem://")

        app.cache = Cache(cache_url)
        app.asgi_app = CacheMiddleware(app.asgi_app, cache=app.cache)

    # --- App Lifecycle Handlers ---
    @app.before_serving
    async def connect_extensions():
        app.logger.info("Connecting to database...")
        app.logger.info("Database connection established.")

        # Initialize security systems
        app.logger.info("Initializing unified security systems...")
        try:
            from ..security.security_manager import (
                SecurityConfiguration,
                SecurityLevel,
                initialize_security_manager,
            )

            # Create security configuration
            security_config = SecurityConfiguration(
                security_level=SecurityLevel.HIGH,
                quantum_resistant_required=True,
                real_time_monitoring=True,
                enable_zero_knowledge=True,
                enable_market_protection=True,
                enable_consent_verification=True,
                enable_attribution_proofs=True,
                enable_reasoning_verification=True,
                enable_side_channel_protection=True,
                enable_multi_entity_detection=True,
            )

            # Initialize global security manager
            security_success = await initialize_security_manager(security_config)
            if security_success:
                app.logger.info("✅ Unified security systems initialized successfully")
            else:
                app.logger.warning("⚠️  Security systems partially initialized")

        except Exception as e:
            app.logger.error(f"❌ Failed to initialize security systems: {e}")
            import traceback

            traceback.print_exc()

        # Start live conversation monitor background tasks
        app.logger.info("Starting live conversation monitor...")
        try:
            import asyncio

            from ..live_capture.conversation_monitor import get_monitor

            # Get the monitor instance (same one used by API routes)
            monitor = get_monitor(
                db_manager=getattr(app.engine, "db_manager", None)
                if hasattr(app, "engine")
                else None
            )

            # Start background monitoring tasks
            app.monitor_tasks = [
                asyncio.create_task(monitor.monitor_conversations()),
                asyncio.create_task(monitor.process_capsule_queue()),
                asyncio.create_task(monitor.cleanup_expired_conversations()),
            ]

            app.logger.info("✅ Live conversation monitor started successfully")

        except Exception as e:
            app.logger.error(f"❌ Failed to start live conversation monitor: {e}")
            import traceback

            traceback.print_exc()

    @app.after_serving
    async def disconnect_extensions():
        # Stop live conversation monitor tasks
        if hasattr(app, "monitor_tasks"):
            app.logger.info("Stopping live conversation monitor...")
            for task in app.monitor_tasks:
                if not task.done():
                    task.cancel()
            app.logger.info("✅ Live conversation monitor stopped")

        # Shutdown security systems
        try:
            from ..security.security_manager import get_security_manager

            security_manager = get_security_manager()
            if security_manager:
                await security_manager.shutdown()
                app.logger.info("✅ Security systems shutdown completed")
        except Exception as e:
            app.logger.error(f"❌ Error during security system shutdown: {e}")

        await db.engine.dispose()
        app.logger.info("Database engine disposed.")

    @app.before_request
    async def create_session():
        # Handle OPTIONS requests immediately
        from quart import request

        if request.method == "OPTIONS":
            from quart import make_response

            response = await make_response("", 200)
            origin = request.headers.get("Origin")

            # Determine allowed origins
            allowed_origins = os.getenv(
                "CORS_ALLOWED_ORIGINS",
                "https://uatp.app,https://api.uatp.app,https://dashboard.uatp.app",
            ).split(",")

            # Add localhost for development
            if os.getenv("ENVIRONMENT") == "development":
                allowed_origins.extend(
                    [
                        "http://localhost:3000",
                        "http://localhost:3001",
                        "http://127.0.0.1:3000",
                        "http://127.0.0.1:3001",
                    ]
                )

            # Set CORS headers if origin is allowed
            if origin in allowed_origins:
                response.headers["Access-Control-Allow-Origin"] = origin
                response.headers["Access-Control-Allow-Methods"] = (
                    "GET, POST, PUT, DELETE, OPTIONS"
                )
                response.headers["Access-Control-Allow-Headers"] = (
                    "Content-Type, Authorization, X-API-Key, X-Correlation-ID"
                )
                response.headers["Access-Control-Allow-Credentials"] = "true"
                response.headers["Access-Control-Max-Age"] = "3600"

            return response

        g.db_session = db.get_session()

    @app.after_request
    async def close_session(response):
        # Add CORS headers to all responses
        from quart import request

        origin = request.headers.get("Origin")

        # Determine allowed origins
        allowed_origins = os.getenv(
            "CORS_ALLOWED_ORIGINS",
            "https://uatp.app,https://api.uatp.app,https://dashboard.uatp.app",
        ).split(",")

        # Add localhost for development
        if os.getenv("ENVIRONMENT") == "development":
            allowed_origins.extend(
                [
                    "http://localhost:3000",
                    "http://localhost:3001",
                    "http://127.0.0.1:3000",
                    "http://127.0.0.1:3001",
                ]
            )

        # Set CORS headers if origin is allowed
        if origin in allowed_origins:
            response.headers["Access-Control-Allow-Origin"] = origin
            response.headers["Access-Control-Allow-Credentials"] = "true"
            response.headers["Access-Control-Expose-Headers"] = "X-Correlation-ID"

        if hasattr(g, "db_session"):
            await g.db_session.close()
        return response

    return app


# Create default app instance for external imports
app = create_app()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="UATP Capsule Engine API Server")
    parser.add_argument("--host", default="127.0.0.1", help="Host to bind to")
    parser.add_argument(
        "--port",
        type=int,
        default=os.getenv("UATP_API_PORT", 9090),
        help="Port to listen on",
    )
    parser.add_argument("--debug", action="store_true", help="Enable debug mode")
    args = parser.parse_args()

    app = create_app()
    app.run(host=args.host, port=args.port, debug=args.debug)
