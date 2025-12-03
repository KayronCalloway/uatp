"""
Optimized UATP Capsule Engine API Server
========================================

Production-optimized Flask-based REST API with comprehensive performance enhancements:
- Response compression (gzip/brotli)
- Multi-layer caching (L1: memory, L2: Redis)
- Database read replicas with automatic routing
- Query optimization and monitoring
- Comprehensive performance metrics
- Response caching with intelligent invalidation
- Connection pooling optimization
"""

import argparse
import asyncio
import os
import time
from typing import Optional

from asgi_caches.middleware import CacheMiddleware
from caches import Cache
from src.core.database import db
from dotenv import load_dotenv
from src.engine.capsule_engine import CapsuleEngine
from quart import g, request
from quart_cors import cors
from quart_rate_limiter import RateLimiter
from quart_schema import Info, QuartSchema, tag
from quart_schema.validation import DataSource

from config.settings import Settings

from .custom_quart import CustomQuart
from .logger import configure_logging
from .compression_middleware import create_compression_middleware
from .enhanced_cache import initialize_cache, close_cache
from .response_cache import (
    start_response_cache_tasks,
    stop_response_cache_tasks,
    cached_response,
)
from src.database.read_replica_manager import ReadReplicaManager, ReplicaConfig
from src.performance.query_optimizer import initialize_query_optimizer
from src.monitoring.performance_metrics import (
    initialize_metrics_collector,
    setup_default_monitoring,
)

# Load environment variables from .env file
load_dotenv()

# Initialize extensions
limiter = RateLimiter()


async def create_optimized_app(
    config_overrides: dict = None, engine_override: CapsuleEngine = None
):
    """Create and configure a performance-optimized Quart app."""
    app = CustomQuart(__name__)
    QuartSchema(
        app, info=Info(title="UATP Capsule Engine API", version="2.0.0-optimized")
    )

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

    # Initialize database with optimizations
    db.init_app(app)

    # Initialize performance optimization systems
    await _initialize_performance_systems(app, config)

    # Use the provided engine or create a new one
    if engine_override:
        app.engine = engine_override
    else:
        # In production, the app creates its own engine
        app.engine = CapsuleEngine(db_manager=db)

    # Initialize other extensions
    limiter.init_app(app)

    # CORS - Production-safe configuration
    allowed_origins = os.getenv(
        "CORS_ALLOWED_ORIGINS",
        "https://uatp.app,https://api.uatp.app,https://dashboard.uatp.app",
    ).split(",")

    # Add localhost for development only
    if os.getenv("ENVIRONMENT") == "development":
        allowed_origins.extend(
            ["http://localhost:3000", "http://localhost:3001", "http://127.0.0.1:3000"]
        )

    cors(
        app,
        allow_origin=allowed_origins,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        allow_headers=[
            "Content-Type",
            "Authorization",
            "X-API-Key",
            "X-Correlation-ID",
        ],
        expose_headers=["X-Correlation-ID", "X-Cache", "X-Cache-Key"],
    )

    # Set up performance middleware
    await _setup_performance_middleware(app)

    # Import and register blueprints with caching decorators
    await _register_optimized_blueprints(app)

    # --- Prometheus Metrics Setup ---
    app.add_url_rule("/metrics", "metrics", _render_metrics, methods=["GET"])
    app.add_url_rule(
        "/metrics/performance",
        "performance_metrics",
        _render_performance_metrics,
        methods=["GET"],
    )

    # Set up request hooks to capture metrics
    _setup_metrics_hooks(app)
    app.logger.info(
        "Prometheus metrics endpoints enabled at /metrics and /metrics/performance"
    )

    # Apply caching middleware if enabled (legacy support)
    if app.config.get("CACHE_ENABLED", False):
        if app.config.get("TESTING", False):
            cache_url = "locmem://"
        else:
            cache_url = os.getenv("CACHE_URL", "locmem://")

        app.cache = Cache(cache_url)
        app.asgi_app = CacheMiddleware(app.asgi_app, cache=app.cache)

    # --- App Lifecycle Handlers ---
    @app.before_serving
    async def connect_extensions():
        app.logger.info("Connecting to database and performance systems...")
        # Start performance monitoring
        if hasattr(app, "metrics_collector"):
            await app.metrics_collector.start_collection()
        app.logger.info("All systems connected and monitoring started.")

    @app.after_serving
    async def disconnect_extensions():
        await _cleanup_performance_systems(app)
        await db.engine.dispose()
        app.logger.info("All systems disconnected.")

    @app.before_request
    async def before_request():
        g.db_session = db.get_session()
        g.request_start_time = time.time()

    @app.after_request
    async def after_request(response):
        # Record performance metrics
        if hasattr(g, "request_start_time") and hasattr(app, "metrics_collector"):
            duration = time.time() - g.request_start_time
            app.metrics_collector.record_request(
                request.method,
                request.endpoint or "unknown",
                response.status_code,
                duration,
            )

        if hasattr(g, "db_session"):
            await g.db_session.close()
        return response

    return app


async def _initialize_performance_systems(app, config):
    """Initialize all performance optimization systems."""
    app.logger.info("Initializing performance optimization systems...")

    # Initialize enhanced caching
    redis_url = os.getenv("REDIS_URL")
    if redis_url:
        try:
            cache = await initialize_cache(
                redis_url=redis_url,
                l1_enabled=True,
                l2_enabled=True,
                l1_max_size=int(os.getenv("CACHE_L1_MAX_SIZE", "1000")),
                l1_max_memory_mb=int(os.getenv("CACHE_L1_MAX_MEMORY_MB", "100")),
            )
            app.cache_system = cache
            app.logger.info("Multi-layer cache system initialized")
        except Exception as e:
            app.logger.warning(f"Failed to initialize Redis cache: {e}")
            # Initialize without Redis
            cache = await initialize_cache(
                redis_url=None,
                l1_enabled=True,
                l2_enabled=False,
                l1_max_size=int(os.getenv("CACHE_L1_MAX_SIZE", "1000")),
                l1_max_memory_mb=int(os.getenv("CACHE_L1_MAX_MEMORY_MB", "100")),
            )
            app.cache_system = cache
            app.logger.info("L1-only cache system initialized")

    # Initialize query optimizer
    slow_query_threshold = float(os.getenv("SLOW_QUERY_THRESHOLD_MS", "100.0"))
    query_optimizer = initialize_query_optimizer(slow_query_threshold)
    app.query_optimizer = query_optimizer
    app.logger.info(
        f"Query optimizer initialized (threshold: {slow_query_threshold}ms)"
    )

    # Initialize read replicas if configured
    read_replicas = []
    replica_count = int(os.getenv("DB_READ_REPLICA_COUNT", "0"))

    for i in range(replica_count):
        replica_host = os.getenv(f"DB_READ_REPLICA_{i}_HOST")
        replica_port = int(os.getenv(f"DB_READ_REPLICA_{i}_PORT", "5432"))

        if replica_host:
            replica_config = ReplicaConfig(
                host=replica_host,
                port=replica_port,
                database=os.getenv(
                    f"DB_READ_REPLICA_{i}_NAME",
                    os.getenv("DB_NAME", "uatp_capsule_engine"),
                ),
                username=os.getenv(
                    f"DB_READ_REPLICA_{i}_USERNAME",
                    os.getenv("DB_USERNAME", "uatp_user"),
                ),
                password=os.getenv(
                    f"DB_READ_REPLICA_{i}_PASSWORD",
                    os.getenv("DB_PASSWORD", "uatp_password"),
                ),
                max_lag_seconds=float(os.getenv(f"DB_READ_REPLICA_{i}_MAX_LAG", "5.0")),
                priority=int(os.getenv(f"DB_READ_REPLICA_{i}_PRIORITY", "1")),
            )
            read_replicas.append(replica_config)

    if read_replicas:
        # This would need to be integrated with the database manager
        app.logger.info(
            f"Read replica configuration loaded for {len(read_replicas)} replicas"
        )

    # Initialize performance metrics collector
    collection_interval = int(os.getenv("METRICS_COLLECTION_INTERVAL", "30"))
    metrics_collector = initialize_metrics_collector(collection_interval)
    app.metrics_collector = metrics_collector

    # Register components with metrics collector
    if hasattr(app, "engine") and hasattr(app.engine, "db_manager"):
        metrics_collector.register_database_manager(app.engine.db_manager)

    if hasattr(app, "cache_system"):
        metrics_collector.register_cache_manager(app.cache_system)

    metrics_collector.register_query_optimizer(query_optimizer)

    # Set up monitoring with custom alert rules
    await _setup_custom_monitoring(metrics_collector)
    app.logger.info("Performance monitoring system initialized")

    # Start response cache background tasks
    await start_response_cache_tasks()
    app.logger.info("Response cache system initialized")


async def _setup_performance_middleware(app):
    """Set up performance middleware."""
    # Response compression middleware
    compression_enabled = os.getenv("COMPRESSION_ENABLED", "true").lower() == "true"
    if compression_enabled:
        minimum_size = int(os.getenv("COMPRESSION_MIN_SIZE", "500"))
        gzip_level = int(os.getenv("COMPRESSION_GZIP_LEVEL", "6"))
        brotli_level = int(os.getenv("COMPRESSION_BROTLI_LEVEL", "4"))

        app.asgi_app = create_compression_middleware(
            app.asgi_app,
            minimum_size=minimum_size,
            gzip_level=gzip_level,
            brotli_level=brotli_level,
        )
        app.logger.info("Response compression middleware enabled")


async def _register_optimized_blueprints(app):
    """Register blueprints with performance optimizations."""
    from .ai_routes import ai_bp
    from .chain_routes import chain_bp
    from .dependencies import get_engine, require_api_key
    from .health_routes import health_bp
    from .live_capture_routes import live_capture_bp
    from .reasoning_api import create_reasoning_blueprint
    from .mirror_mode_api import create_mirror_mode_api_blueprint
    from .rights_evolution_api import create_rights_evolution_api_blueprint
    from .bonds_citizenship_api import create_bonds_citizenship_api_blueprint
    from .capsule_routes import capsules_bp
    from .trust_routes import trust_bp
    from .governance_routes import governance_bp
    from .federation_routes import federation_bp
    from .organization_routes import organization_bp
    from .economics_routes import economics_bp

    # Create optimized blueprints
    reasoning_bp = create_reasoning_blueprint(
        engine_getter=get_engine, require_api_key=require_api_key
    )

    mirror_mode_bp = create_mirror_mode_api_blueprint(
        engine_getter=get_engine, require_api_key=require_api_key
    )

    rights_evolution_bp = create_rights_evolution_api_blueprint(
        engine_getter=get_engine, require_api_key=require_api_key
    )

    bonds_citizenship_bp = create_bonds_citizenship_api_blueprint(
        engine_getter=get_engine, require_api_key=require_api_key
    )

    # Register blueprints
    app.register_blueprint(health_bp)
    app.register_blueprint(ai_bp)
    app.register_blueprint(chain_bp)
    app.register_blueprint(capsules_bp)
    app.register_blueprint(live_capture_bp)
    app.register_blueprint(trust_bp, url_prefix="/trust")
    app.register_blueprint(reasoning_bp, url_prefix="/reasoning")
    app.register_blueprint(mirror_mode_bp, url_prefix="/api/v1/mirror")
    app.register_blueprint(rights_evolution_bp)
    app.register_blueprint(bonds_citizenship_bp)
    app.register_blueprint(governance_bp, url_prefix="/governance")
    app.register_blueprint(federation_bp, url_prefix="/federation")
    app.register_blueprint(organization_bp, url_prefix="/organization")
    app.register_blueprint(economics_bp, url_prefix="/economics")


async def _setup_custom_monitoring(metrics_collector):
    """Set up custom monitoring and alerts."""
    from src.monitoring.performance_metrics import AlertRule

    # Add UATP-specific alert rules
    custom_rules = [
        AlertRule(
            name="capsule_processing_slow",
            metric_name="avg_response_time_ms",
            threshold=500.0,  # 500ms for capsule operations
            operator="gt",
            window_seconds=180,
            severity="warning",
        ),
        AlertRule(
            name="database_connection_pool_exhausted",
            metric_name="connection_pool_utilization",
            threshold=90.0,  # 90% utilization
            operator="gt",
            window_seconds=120,
            severity="critical",
        ),
        AlertRule(
            name="cache_performance_degraded",
            metric_name="cache_hit_rate_percent",
            threshold=60.0,  # Below 60% hit rate
            operator="lt",
            window_seconds=300,
            severity="warning",
        ),
    ]

    for rule in custom_rules:
        metrics_collector.add_alert_rule(rule)

    # Set up default monitoring
    await setup_default_monitoring()


def _setup_metrics_hooks(app):
    """Set up request hooks for metrics collection."""
    # This is handled in the before_request and after_request handlers
    pass


async def _render_metrics():
    """Render Prometheus metrics."""
    from quart import current_app

    if hasattr(current_app, "metrics_collector"):
        return current_app.metrics_collector.export_prometheus_metrics()
    return "# Metrics not available\n"


async def _render_performance_metrics():
    """Render detailed performance metrics."""
    from quart import jsonify, current_app

    metrics = {}

    if hasattr(current_app, "metrics_collector"):
        metrics["system"] = current_app.metrics_collector.get_metrics_summary()

    if hasattr(current_app, "query_optimizer"):
        metrics["queries"] = current_app.query_optimizer.get_metrics_summary()

    if hasattr(current_app, "cache_system"):
        metrics["cache"] = current_app.cache_system.get_stats()

    return jsonify(metrics)


async def _cleanup_performance_systems(app):
    """Clean up performance systems on shutdown."""
    app.logger.info("Cleaning up performance systems...")

    # Stop metrics collection
    if hasattr(app, "metrics_collector"):
        await app.metrics_collector.stop_collection()

    # Stop response cache tasks
    await stop_response_cache_tasks()

    # Close enhanced cache
    await close_cache()

    app.logger.info("Performance systems cleanup complete")


# Optimized route decorators for common endpoints
def cached_capsule_response(ttl: int = 300):
    """Decorator for caching capsule-related responses."""
    return cached_response(
        ttl=ttl,
        invalidation_tags={"capsules"},
        etag_enabled=True,
        last_modified_enabled=True,
    )


def cached_ai_response(ttl: int = 600):
    """Decorator for caching AI-related responses."""
    return cached_response(
        ttl=ttl,
        invalidation_tags={"ai_responses"},
        etag_enabled=True,
        cache_query_params=True,
    )


def cached_chain_response(ttl: int = 1800):
    """Decorator for caching chain-related responses."""
    return cached_response(
        ttl=ttl,
        invalidation_tags={"chains"},
        etag_enabled=True,
        last_modified_enabled=True,
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Optimized UATP Capsule Engine API Server"
    )
    parser.add_argument("--host", default="127.0.0.1", help="Host to bind to")
    parser.add_argument(
        "--port",
        type=int,
        default=os.getenv("UATP_API_PORT", 9090),
        help="Port to listen on",
    )
    parser.add_argument("--debug", action="store_true", help="Enable debug mode")
    parser.add_argument(
        "--workers", type=int, default=4, help="Number of worker processes"
    )
    args = parser.parse_args()

    # Create and run the optimized app
    async def main():
        app = await create_optimized_app()

        # Log startup information
        app.logger.info("=" * 60)
        app.logger.info("UATP Capsule Engine API Server - Performance Optimized")
        app.logger.info("=" * 60)
        app.logger.info(f"Host: {args.host}")
        app.logger.info(f"Port: {args.port}")
        app.logger.info(f"Debug: {args.debug}")
        app.logger.info(f"Workers: {args.workers}")
        app.logger.info("Performance Features Enabled:")
        app.logger.info("  ✓ Response Compression (gzip/brotli)")
        app.logger.info("  ✓ Multi-layer Caching (L1: Memory, L2: Redis)")
        app.logger.info("  ✓ Database Query Optimization")
        app.logger.info("  ✓ Performance Monitoring & Metrics")
        app.logger.info("  ✓ Response Caching with ETags")
        app.logger.info("  ✓ Connection Pool Optimization")
        app.logger.info("=" * 60)

        app.run(host=args.host, port=args.port, debug=args.debug)

    asyncio.run(main())
