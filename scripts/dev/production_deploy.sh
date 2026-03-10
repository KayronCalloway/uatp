#!/bin/bash
"""
UATP Production Deployment Script
Runs the FastAPI application with Gunicorn + UvicornWorker for production
"""

# Set production environment
export ENVIRONMENT=production

# Get configuration from environment with production defaults
PORT=${API_PORT:-8000}
HOST=${API_HOST:-0.0.0.0}
WORKERS=${WORKERS:-4}
LOG_LEVEL=${LOG_LEVEL:-info}

# Gunicorn configuration for production
exec gunicorn src.main:app \
    --worker-class uvicorn.workers.UvicornWorker \
    --bind ${HOST}:${PORT} \
    --workers ${WORKERS} \
    --worker-connections 1000 \
    --max-requests 1000 \
    --max-requests-jitter 100 \
    --timeout 30 \
    --keepalive 2 \
    --log-level ${LOG_LEVEL} \
    --access-logfile - \
    --error-logfile - \
    --capture-output \
    --enable-stdio-inheritance \
    --preload
