# UATP Configuration Guide

This document outlines the required and optional environment variables for running the UATP Capsule Engine.

## Required Environment Variables

### Core Application

- **`UATP_SIGNING_KEY`** - 64-character hex string for cryptographic signing
  - Example: `6f4a423a4a4b4a4c4d4e4f505152535455565758595a5b5c5d5e5f6061626364`
  - Used for: Post-quantum cryptographic operations and capsule signing

### AI Platform Integration

- **`OPENAI_API_KEY`** - OpenAI API key for GPT models
  - Format: `sk-...` (standard OpenAI format)
  - Used for: Multi-modal AI processing and reasoning chains

- **`ANTHROPIC_API_KEY`** - Anthropic API key for Claude models
  - Format: `sk-ant-...` (standard Anthropic format)
  - Used for: Cross-platform AI attribution and reasoning

### Database Configuration

- **`DATABASE_URL`** - Database connection string
  - SQLite example: `sqlite:///uatp.db`
  - PostgreSQL example: `postgresql://user:password@localhost:5432/uatp_db`
  - Used for: Persistent storage of capsules, chains, and metadata

## Optional Environment Variables

### API Server Configuration

- **`API_HOST`** - Host interface to bind (default: `0.0.0.0`)
- **`API_PORT`** - Port to listen on (default: `8000`)
- **`ENVIRONMENT`** - Runtime environment (`development`, `production`, `testing`)
- **`LOG_LEVEL`** - Logging verbosity (`debug`, `info`, `warning`, `error`)

### Security & CORS

- **`ALLOWED_HOSTS`** - Comma-separated list of allowed hosts (default: `localhost,127.0.0.1`)
- **`CORS_ORIGINS`** - Allowed CORS origins for API access

### Cache & Performance

- **`REDIS_URL`** - Redis connection string for caching
  - Example: `redis://localhost:6379/0`
  - Used for: Session storage and performance caching

### Testing Environment

When running tests, these variables are automatically set:

```bash
UATP_SIGNING_KEY="6f4a423a4a4b4a4c4d4e4f505152535455565758595a5b5c5d5e5f6061626364"
UATP_API_KEYS='{"test_read_key": {"scopes": ["read"]}, "test_write_key": {"scopes": ["write"]}}'
DATABASE_URL="sqlite:///test.db"  # or PostgreSQL for CI
```

## Quick Setup for Development

Create a `.env` file in the project root:

```bash
# Core requirements
UATP_SIGNING_KEY=6f4a423a4a4b4a4c4d4e4f505152535455565758595a5b5c5d5e5f6061626364
OPENAI_API_KEY=sk-your-openai-key-here
ANTHROPIC_API_KEY=sk-ant-your-anthropic-key-here

# Database (SQLite for local development)
DATABASE_URL=sqlite:///uatp_dev.db

# Development settings
ENVIRONMENT=development
LOG_LEVEL=debug
API_PORT=8000
```

## Quick Setup for Testing

```bash
# Install dependencies
pip install -e ".[dev,test]"

# Set test environment variables
export UATP_SIGNING_KEY="6f4a423a4a4b4a4c4d4e4f505152535455565758595a5b5c5d5e5f6061626364"
export DATABASE_URL="sqlite:///test.db"

# Run tests
pytest tests/ -v
```

## Production Considerations

### Security
- Use a strong, randomly generated `UATP_SIGNING_KEY`
- Store API keys securely (environment variables, not in code)
- Use PostgreSQL for production databases
- Configure `ALLOWED_HOSTS` restrictively

### Performance
- Set up Redis for caching in production
- Use `ENVIRONMENT=production` to disable debug features
- Configure appropriate `LOG_LEVEL` (typically `info` or `warning`)

### Monitoring
- Enable telemetry and metrics collection
- Configure structured logging for observability
- Set up health check endpoints monitoring

## Troubleshooting

### Common Issues

1. **Missing UATP_SIGNING_KEY**: Tests will fail with cryptographic errors
2. **Invalid API Keys**: AI platform integrations will return 401/403 errors
3. **Database Connection**: Check `DATABASE_URL` format and permissions
4. **Port Conflicts**: Ensure `API_PORT` is available

### Validation Script

```python
#!/usr/bin/env python3
import os

def validate_config():
    required = ['UATP_SIGNING_KEY', 'DATABASE_URL']
    missing = [var for var in required if not os.getenv(var)]

    if missing:
        print(f"[ERROR] Missing required variables: {missing}")
        return False

    print("[OK] All required configuration present")
    return True

if __name__ == "__main__":
    validate_config()
```

For additional configuration options, see the [Developer Guide](developer_guide.md) and [Deployment Guide](deployment-guide.md).
