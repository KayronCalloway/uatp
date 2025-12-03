# UATP Capsule Engine - Deployment and Operations Guide

## Overview

This guide provides comprehensive instructions for deploying and operating the UATP (Unified Agent Trust Protocol) Capsule Engine in production environments.

## Prerequisites

### System Requirements

- **Operating System**: Linux (Ubuntu 20.04+ recommended) or macOS
- **Docker**: Version 20.10+ with Docker Compose
- **Memory**: Minimum 4GB RAM, 8GB+ recommended
- **Storage**: Minimum 20GB free space for containers and data
- **Network**: Outbound internet access for Docker images and AI API calls

### Required Software

```bash
# Install Docker and Docker Compose
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER

# Install Docker Compose (if not included with Docker)
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
```

## Quick Start

### 1. Clone and Setup

```bash
# Clone the repository
git clone <repository-url>
cd uatp-capsule-engine

# Copy environment template
cp .env.example .env
```

### 2. Configure Environment

Edit `.env` file with your production values:

```env
# PostgreSQL Database Configuration
POSTGRES_USER=uatp_user
POSTGRES_PASSWORD=secure_password_here
POSTGRES_DB=uatp_production

# UATP Engine Settings
UATP_AGENT_ID=production_agent_001
UATP_SIGNING_KEY=your_64_char_hex_ed25519_key_here

# OpenAI API (optional, for AI features)
OPENAI_API_KEY=sk-your-openai-key-here

# API Keys for client access
UATP_API_KEYS={"prod-key-1": {"roles": ["read", "write"], "agent_id": "client_001", "description": "Production client key"}}

# Performance Tuning
UATP_DB_POOL_SIZE=10
UATP_DB_MAX_OVERFLOW=20
UATP_DB_POOL_RECYCLE=3600
```

### 3. Generate Signing Key

```bash
# Generate a new Ed25519 signing key
python3 -c "import secrets; print(secrets.token_hex(32))"
```

### 4. Deploy Services

```bash
# Start all services
docker-compose up -d

# Check service status
docker-compose ps

# View logs
docker-compose logs -f api
```

## Production Deployment

### Environment-Specific Configuration

#### Development
```env
ENVIRONMENT=development
UATP_API_PORT=9090
LOG_LEVEL=DEBUG
```

#### Staging
```env
ENVIRONMENT=staging
UATP_API_PORT=9090
LOG_LEVEL=INFO
```

#### Production
```env
ENVIRONMENT=production
UATP_API_PORT=9090
LOG_LEVEL=WARNING
```

### SSL/TLS Configuration

For production, use a reverse proxy with SSL termination:

#### Nginx Configuration

```nginx
upstream uatp_api {
    server localhost:9090;
}

server {
    listen 443 ssl http2;
    server_name api.yourdomain.com;

    ssl_certificate /path/to/ssl/cert.pem;
    ssl_certificate_key /path/to/ssl/private.key;

    location / {
        proxy_pass http://uatp_api;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # WebSocket support
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

### Load Balancing

For high availability, deploy multiple API instances:

```yaml
# docker-compose.prod.yml
version: '3.8'

services:
  api-1:
    build: .
    container_name: uatp_api_1
    env_file: .env
    depends_on: [db]

  api-2:
    build: .
    container_name: uatp_api_2
    env_file: .env
    depends_on: [db]

  nginx:
    image: nginx:alpine
    ports:
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
    depends_on: [api-1, api-2]
```

## Service Management

### Starting Services

```bash
# Start all services
docker-compose up -d

# Start specific service
docker-compose up -d api

# Scale API instances
docker-compose up -d --scale api=3
```

### Stopping Services

```bash
# Stop all services
docker-compose down

# Stop and remove volumes (WARNING: deletes data)
docker-compose down -v

# Stop specific service
docker-compose stop api
```

### Updating Services

```bash
# Pull latest images
docker-compose pull

# Rebuild and restart
docker-compose up -d --build

# Update specific service
docker-compose up -d --build api
```

## Monitoring and Observability

### Accessing Monitoring Stack

- **Grafana Dashboard**: http://localhost:3000
  - Username: `admin`
  - Password: `admin`
- **Prometheus Metrics**: http://localhost:9091
- **API Health**: http://localhost:9090/health (if implemented)

### Key Metrics to Monitor

#### Application Metrics
- Request rate and latency
- Error rates by endpoint
- Database connection pool utilization
- Cache hit/miss ratios
- Active sessions

#### System Metrics
- CPU and memory usage
- Disk space and I/O
- Network throughput
- Container health status

#### Database Metrics
- Connection count
- Query performance
- Database size and growth
- Lock contention

### Alerting

Configure alerts for:
- High error rates (>5% over 5 minutes)
- Response time degradation (>2s P95)
- Database connection pool exhaustion
- Disk space usage (>80%)
- Container restarts

## Backup and Recovery

### Database Backups

The system includes automated daily backups:

```bash
# Manual backup
docker-compose exec backup /scripts/backup.sh

# Restore from backup
docker-compose exec db psql -U $POSTGRES_USER -d $POSTGRES_DB < /backups/backup_file.sql
```

### Backup Configuration

```yaml
# docker-compose.yml backup service
backup:
  image: postgres:15-alpine
  container_name: uatp_backup
  restart: unless-stopped
  volumes:
    - ./scripts:/scripts
    - backups:/backups
  environment:
    - POSTGRES_HOST=db
  depends_on: [db]
  command: sh -c "echo '0 0 * * * /scripts/backup.sh' | crontab - && crond -f"
```

### Recovery Procedures

#### Database Recovery
1. Stop the API service: `docker-compose stop api`
2. Restore database from backup
3. Restart services: `docker-compose up -d`

#### Full System Recovery
1. Clone repository to new server
2. Restore `.env` file and configuration
3. Restore database from backup
4. Deploy services: `docker-compose up -d`

## Security

### Security Checklist

- [ ] Use strong, unique passwords for all services
- [ ] Enable SSL/TLS for all external communications
- [ ] Regularly rotate API keys and signing keys
- [ ] Keep Docker images updated
- [ ] Monitor access logs for suspicious activity
- [ ] Use non-root users in containers
- [ ] Enable firewall rules to restrict access
- [ ] Implement rate limiting at network level

### API Key Management

```bash
# Generate new API key
python3 -c "import secrets; print(secrets.token_urlsafe(32))"

# Update API keys in environment
# Edit .env file and restart services
docker-compose restart api
```

### Network Security

```bash
# Firewall configuration (Ubuntu/Debian)
sudo ufw allow 443/tcp  # HTTPS
sudo ufw allow 22/tcp   # SSH
sudo ufw enable

# Block direct access to internal ports
sudo ufw deny 9090/tcp  # API port
sudo ufw deny 5432/tcp  # PostgreSQL port
```

## Performance Optimization

### Database Optimization

```sql
-- PostgreSQL performance tuning
ALTER SYSTEM SET shared_preload_libraries = 'pg_stat_statements';
ALTER SYSTEM SET max_connections = 100;
ALTER SYSTEM SET shared_buffers = '256MB';
ALTER SYSTEM SET effective_cache_size = '1GB';
ALTER SYSTEM SET maintenance_work_mem = '64MB';
ALTER SYSTEM SET checkpoint_completion_target = 0.9;
ALTER SYSTEM SET wal_buffers = '16MB';
```

### Application Performance

```env
# Connection pooling
UATP_DB_POOL_SIZE=10
UATP_DB_MAX_OVERFLOW=20
UATP_DB_POOL_RECYCLE=3600

# Caching
CACHE_ENABLED=true
CACHE_TTL=300

# Rate limiting
CREATE_CAPSULE_RATE_LIMIT="100 per minute"
```

### Resource Allocation

```yaml
# docker-compose.yml with resource limits
services:
  api:
    deploy:
      resources:
        limits:
          cpus: '2.0'
          memory: 2G
        reservations:
          cpus: '1.0'
          memory: 1G
```

## Troubleshooting

### Common Issues

#### Service Won't Start
```bash
# Check logs
docker-compose logs api

# Check environment variables
docker-compose exec api env | grep UATP

# Verify database connection
docker-compose exec api python -c "
import asyncio
import asyncpg
asyncio.run(asyncpg.connect('postgresql://user:pass@db/db'))
"
```

#### Database Connection Issues
```bash
# Check database status
docker-compose exec db pg_isready

# Check connection from API
docker-compose exec api nc -zv db 5432

# Reset database
docker-compose down db
docker volume rm uatp-capsule-engine_postgres_data
docker-compose up -d db
```

#### High Memory Usage
```bash
# Check container memory usage
docker stats

# Adjust memory limits
docker-compose down
# Edit docker-compose.yml resource limits
docker-compose up -d
```

#### API Performance Issues
```bash
# Check API response times
curl -w "@curl-format.txt" -o /dev/null -s http://localhost:9090/capsules/stats

# Monitor database queries
docker-compose exec db psql -U $POSTGRES_USER -d $POSTGRES_DB -c "
SELECT query, calls, total_time, mean_time
FROM pg_stat_statements
ORDER BY mean_time DESC LIMIT 10;
"
```

### Log Analysis

```bash
# View all logs
docker-compose logs

# Follow API logs
docker-compose logs -f api

# Search for errors
docker-compose logs api | grep ERROR

# Export logs for analysis
docker-compose logs --no-color api > api.log
```

### Health Checks

```bash
# API health check
curl -f http://localhost:9090/capsules/stats

# Database health check
docker-compose exec db pg_isready -U $POSTGRES_USER

# Container health status
docker-compose ps
```

## Maintenance

### Regular Maintenance Tasks

#### Daily
- Monitor service health and performance
- Check backup completion
- Review error logs

#### Weekly
- Update Docker images
- Analyze performance metrics
- Review security logs

#### Monthly
- Rotate API keys
- Update system packages
- Review and optimize database performance
- Test disaster recovery procedures

### Maintenance Commands

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Clean Docker resources
docker system prune -a
docker volume prune

# Optimize database
docker-compose exec db vacuumdb -U $POSTGRES_USER -d $POSTGRES_DB --analyze

# Backup configuration
tar -czf uatp-config-backup.tar.gz .env docker-compose.yml scripts/
```

## Scaling

### Horizontal Scaling

```yaml
# docker-compose.scale.yml
version: '3.8'

services:
  api:
    build: .
    deploy:
      replicas: 3
    ports:
      - "9090-9092:9090"

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
    depends_on:
      - api
```

### Vertical Scaling

```yaml
# Increase resources
services:
  api:
    deploy:
      resources:
        limits:
          cpus: '4.0'
          memory: 4G

  db:
    deploy:
      resources:
        limits:
          cpus: '2.0'
          memory: 4G
```

### Database Scaling

For high load, consider:
- Read replicas for read-heavy workloads
- Connection pooling (PgBouncer)
- Database sharding for write-heavy workloads

## Support and Resources

### Getting Help

1. **Documentation**: Review this guide and `docs/api-documentation.md`
2. **Logs**: Check application and container logs
3. **Monitoring**: Use Grafana dashboards for insights
4. **Community**: Check project repository for issues and discussions

### Useful Commands Reference

```bash
# Essential Docker Compose commands
docker-compose up -d              # Start services
docker-compose down               # Stop services
docker-compose ps                 # Service status
docker-compose logs -f <service>  # Follow logs
docker-compose exec <service> sh  # Access container
docker-compose restart <service>  # Restart service
docker-compose pull               # Update images
docker-compose build              # Rebuild images

# Database management
docker-compose exec db psql -U $POSTGRES_USER -d $POSTGRES_DB
docker-compose exec backup /scripts/backup.sh

# Monitoring
docker stats                      # Resource usage
docker-compose top                # Process list
curl localhost:9090/capsules/stats # API health
```

This deployment guide provides a comprehensive foundation for operating the UATP Capsule Engine in production environments. Adjust configurations based on your specific requirements and infrastructure.
