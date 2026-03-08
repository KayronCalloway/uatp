"""
UATP Canonical ASGI Application Entry Point
Production-ready FastAPI application with unified architecture
"""

import structlog

from .app_factory import create_app

# Configure logging for ASGI deployment
logger = structlog.get_logger(__name__)


def create_asgi_app():
    """Create production-ready ASGI application"""
    logger.info(" Initializing UATP ASGI application")

    # Use the canonical FastAPI factory
    app = create_app()

    # Add ASGI-specific production enhancements
    @app.middleware("http")
    async def asgi_production_middleware(request, call_next):
        """Production security headers for ASGI deployment"""
        response = await call_next(request)

        # Add security headers
        response.headers.update(
            {
                "X-Content-Type-Options": "nosniff",
                "X-Frame-Options": "DENY",
                "X-XSS-Protection": "1; mode=block",
                "Referrer-Policy": "strict-origin-when-cross-origin",
            }
        )

        return response

    logger.info("[OK] UATP ASGI application ready for deployment")
    return app


# Create the canonical application instance
app = create_asgi_app()

# Export for ASGI servers (gunicorn, uvicorn, etc.)
__all__ = ["app"]
