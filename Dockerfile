# Multi-stage Docker build for UATP Capsule Engine
# Production-ready containerization with security best practices

# Stage 1: Build dependencies
FROM python:3.11-slim as builder

# Install build dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    gcc \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .

# Create virtual environment and install dependencies
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Upgrade pip and install dependencies
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Stage 2: Runtime image
FROM python:3.11-slim as runtime

# Set labels for image metadata
LABEL maintainer="UATP Team" \
      version="1.0.1" \
      description="UATP Capsule Engine - AI Rights and Financial Operations Platform"

# Install runtime dependencies and security updates
RUN apt-get update && apt-get install -y \
    libpq5 \
    ca-certificates \
    curl \
    dumb-init \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean \
    && apt-get autoremove -y

# Create non-root user with specific UID/GID for security
RUN groupadd -r uatp -g 1000 && \
    useradd -r -u 1000 -g uatp -m -d /home/uatp -s /bin/bash uatp

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Set working directory
WORKDIR /app

# Copy application code with proper ownership
COPY --chown=uatp:uatp src/ ./src/
COPY --chown=uatp:uatp *.py ./
COPY --chown=uatp:uatp *.toml ./
COPY --chown=uatp:uatp *.ini ./

# Create necessary directories with proper permissions
RUN mkdir -p /app/logs /app/data /tmp/uatp && \
    chown -R uatp:uatp /app /tmp/uatp && \
    chmod 755 /app && \
    chmod 750 /app/logs /app/data

# Set environment variables
ENV PYTHONPATH=/app/src \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONHASHSEED=random \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Switch to non-root user
USER uatp

# Expose ports (FastAPI main on 8000, metrics on 9090)
# Note: Health endpoints are served on the main port (8000), not a separate port
EXPOSE 8000 9090

# Health check with proper timeout and retries
# IMPORTANT: Health endpoint is on the main application port (8000)
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
  CMD curl -f http://localhost:8000/health || exit 1

# Use dumb-init to handle signals properly
ENTRYPOINT ["dumb-init", "--"]

# Default command with production settings
# Use gunicorn with uvicorn workers for production multi-worker deployment
# - gunicorn manages worker processes and handles restarts
# - uvicorn.workers.UvicornWorker provides async ASGI support
# - Workers scaled based on CPU cores: typically 2-4 workers per core
CMD ["gunicorn", "src.main:app", "--bind", "0.0.0.0:8000", "--workers", "4", "--worker-class", "uvicorn.workers.UvicornWorker", "--access-logfile", "-", "--error-logfile", "-", "--capture-output"]
