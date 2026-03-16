# UATP Capsule Engine Deployment Guide

## Overview

This guide provides instructions for deploying the UATP Capsule Engine in various environments, from development to production. It covers infrastructure requirements, configuration, security best practices, and monitoring recommendations.

## Deployment Options

### Local Development Deployment

For local testing and development:

```bash
# Run API server
python -m api.server

# Run visualization dashboard
streamlit run tests/unified_capsule_visualization_dashboard.py
```

### Docker Deployment

A Dockerfile is provided for containerized deployment:

```bash
# Build the Docker image
docker build -t uatp-capsule-engine .

# Run the container
docker run -p 5000:5000 --env-file .env uatp-capsule-engine
```

### Production Deployment

For production environments, we recommend:

1. Using a production WSGI server like Gunicorn
2. Setting up proper reverse proxy with Nginx/Apache
3. Implementing horizontal scaling for API servers
4. Using a distributed caching system

Example production deployment with Gunicorn:

```bash
# Install Gunicorn
pip install gunicorn

# Run with Gunicorn
gunicorn --workers=4 --bind=0.0.0.0:5000 "api.server:app"
```

## Configuration

### Environment Variables

The application uses environment variables for configuration. Create a `.env` file or set these in your environment:

```
# Required settings
UATP_API_KEY=your-production-api-key
UATP_SIGNING_KEY=your-production-signing-key
UATP_STORAGE_PATH=/path/to/persistent/storage

# Security settings
UATP_AUTH_REQUIRED=true
UATP_RATE_LIMIT=100

# Performance settings
UATP_CACHE_SIZE=10000
UATP_CACHE_ENABLED=true
UATP_CHAIN_CACHE_TTL=60
UATP_VERIFICATION_CACHE_TTL=300
UATP_STATS_CACHE_TTL=120
UATP_FORKS_CACHE_TTL=300
UATP_GENERAL_CACHE_TTL=60

# Logging settings
UATP_LOG_LEVEL=INFO
UATP_LOG_FORMAT=json
```

### Configuring Cache Settings

Cache settings can be adjusted based on your deployment environment and usage patterns:

1. For development environments with limited resources:
   ```
   UATP_CACHE_SIZE=1000
   UATP_CHAIN_CACHE_TTL=30
   ```

2. For production environments with high traffic:
   ```
   UATP_CACHE_SIZE=10000
   UATP_CHAIN_CACHE_TTL=60
   ```

3. For multi-instance deployments:
   ```
   UATP_CACHE_SIZE=5000  # Lower per-instance cache size
   UATP_CHAIN_CACHE_TTL=30  # Lower TTL to prevent stale data
   ```

## Scaling Considerations

### Horizontal Scaling

The UATP Capsule Engine API can be horizontally scaled:

1. Deploy multiple API instances behind a load balancer
2. Use a shared filesystem or object storage for chain data
3. Implement a distributed cache like Redis for multi-instance deployments

### Vertical Scaling

Consider these vertical scaling options:

1. Increase cache size based on available memory
2. Adjust worker processes based on available CPU cores
3. Optimize TTL settings based on access patterns

## Security

### API Key Management

1. Generate strong API keys using a secure random generator
2. Implement key rotation policy (e.g., every 90 days)
3. Use separate keys for different environments and clients

### Network Security

1. Always use HTTPS in production environments
2. Implement proper firewall rules
3. Consider using a Web Application Firewall (WAF)

### Environment Isolation

1. Use separate environments for development, staging, and production
2. Implement least-privilege access controls
3. Segregate sensitive components from public-facing services

## Monitoring and Maintenance

### Health Checks

Implement and use the health check endpoint:

```
GET /health
```

This returns system status and key metrics.

### Metrics and Logging

1. Monitor key performance metrics:
   - API response times
   - Cache hit/miss rates
   - Chain loading times
   - Memory usage

2. Log important events:
   - API authentication failures
   - Cache invalidations
   - Chain modifications
   - System errors

3. Use structured logging for easier analysis

### Backup Strategy

1. Implement regular backups of chain data
2. Store backups in a separate, secure location
3. Test restoration procedures periodically

## Troubleshooting Production Issues

### Common Production Issues

1. **High Memory Usage**
   - Check cache size configuration
   - Monitor for memory leaks
   - Consider reducing worker count or increasing server resources

2. **Slow API Response**
   - Check cache hit rates
   - Verify chain loading performance
   - Analyze database or storage performance

3. **Authentication Failures**
   - Verify API key configuration
   - Check key permissions and expiration
   - Review logs for suspicious access patterns

### Diagnostic Tools

1. Use the cache statistics endpoint:
   ```
   GET /admin/cache_stats
   ```

2. Enable debug logging temporarily:
   ```
   UATP_LOG_LEVEL=DEBUG
   ```

3. Use performance monitoring tools:
   - New Relic
   - Datadog
   - Prometheus/Grafana

## Deployment Checklist

Before deploying to production:

- [ ] Set all required environment variables
- [ ] Configure appropriate cache sizes and TTLs
- [ ] Set up monitoring and logging
- [ ] Test health check endpoints
- [ ] Verify API key authentication
- [ ] Configure backup strategy
- [ ] Set up alerting for critical metrics
- [ ] Document deployment-specific configurations
- [ ] Perform security review
