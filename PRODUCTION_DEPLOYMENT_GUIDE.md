# UATP Production Deployment Guide

## Table of Contents
- [Overview](#overview)
- [Prerequisites](#prerequisites)
- [Environment Setup](#environment-setup)
- [Container Orchestration](#container-orchestration)
- [Load Balancing & High Availability](#load-balancing--high-availability)
- [Backup & Recovery](#backup--recovery)
- [Monitoring & Alerting](#monitoring--alerting)
- [Deployment Process](#deployment-process)
- [Testing & Validation](#testing--validation)
- [Operational Procedures](#operational-procedures)
- [Troubleshooting](#troubleshooting)

## Overview

This guide provides comprehensive instructions for deploying the UATP Capsule Engine system to production with enterprise-grade reliability, security, and scalability.

### Key Features Implemented:
- **Multi-environment support** (dev/staging/prod)
- **High-availability architecture** with load balancing
- **Automated backup and recovery** procedures
- **Comprehensive monitoring** and alerting
- **Production-grade security** configurations
- **Automated deployment** scripts
- **Health checks and testing** suites

## Prerequisites

### Required Tools
```bash
# Essential tools
docker (20.10+)
kubectl (1.24+)
helm (3.8+)
curl
openssl
awk

# Optional but recommended
yq (YAML processor)
jq (JSON processor)
aws-cli (for S3 backups)
```

### Infrastructure Requirements
- **Kubernetes cluster** (managed or self-hosted)
- **PostgreSQL database** (managed recommended)
- **Redis instance** (clustered for production)
- **SSL certificates** (Let's Encrypt or commercial)
- **Domain names** configured
- **Cloud storage** for backups (S3 compatible)

### Access Requirements
- Kubernetes cluster admin access
- Container registry push/pull access
- DNS management access
- SSL certificate management access

## Environment Setup

### 1. Environment Configuration Files

Three environment-specific configuration files have been created:

```bash
deployment/environments/
├── dev.env      # Development environment
├── staging.env  # Staging environment
└── prod.env     # Production environment
```

### 2. Configure Production Environment

Edit `deployment/environments/prod.env` with your production values:

```bash
# Copy example and customize
cp deployment/environments/prod.env deployment/environments/prod.env.local

# Edit with your values
vim deployment/environments/prod.env.local
```

### 3. Set Required Secrets

Ensure these critical secrets are set:
- `DATABASE_PASSWORD` - PostgreSQL password
- `SECRET_KEY` - Application secret key
- `JWT_SECRET` - JWT signing secret
- `ENCRYPTION_KEY` - Data encryption key
- `OPENAI_API_KEY` - OpenAI API key
- `ANTHROPIC_API_KEY` - Anthropic API key
- `STRIPE_SECRET_KEY` - Stripe payment key
- `REDIS_PASSWORD` - Redis authentication

## Container Orchestration

### 1. Enhanced Docker Configuration

**Production Dockerfile**: `deployment/docker/Dockerfile.production`
- Multi-stage build for optimization
- Security hardening (non-root user)
- Health checks built-in
- Minimal attack surface

**Docker Compose**: `deployment/docker/docker-compose.production.yml`
- Multi-replica application instances
- Load balancer (HAProxy)
- Database with read replica
- Redis clustering
- Monitoring stack (Prometheus/Grafana)
- Automated backups

### 2. Kubernetes Deployment

**Enhanced Features**:
- **Resource limits and requests** properly configured
- **Security contexts** enforced
- **Health checks** (liveness, readiness, startup)
- **Pod disruption budgets** for high availability
- **Horizontal Pod Autoscaling** based on CPU/memory
- **Anti-affinity rules** for pod distribution

**Key Files**:
```bash
k8s/environments/production/
├── namespace.yaml     # Namespace with resource quotas
├── deployment.yaml    # Application deployment
├── ingress.yaml       # Load balancing and SSL
└── monitoring.yaml    # Monitoring stack
```

## Load Balancing & High Availability

### 1. HAProxy Configuration

**Features**:
- SSL termination with modern ciphers
- Health checks for backend services
- Session persistence for WebSockets
- Rate limiting and security headers
- Statistics dashboard

**Configuration**: `deployment/docker/haproxy/haproxy.cfg`

### 2. Kubernetes Ingress

**Features**:
- NGINX Ingress Controller
- Automatic SSL with Let's Encrypt
- Security headers injection
- Rate limiting
- WebSocket support with session affinity

**Configuration**: `k8s/environments/production/ingress.yaml`

### 3. High Availability Setup

**Database**:
- Primary/replica PostgreSQL setup
- Read replica for read-heavy workloads
- Automated failover capabilities

**Application**:
- Minimum 3 replicas in production
- Pod anti-affinity across nodes
- Rolling updates with zero downtime
- Circuit breakers for external services

## Backup & Recovery

### 1. Automated Backup System

**Backup Service**: `deployment/docker/Dockerfile.backup`
- Dedicated container for backup operations
- Scheduled via cron or Kubernetes CronJob
- Multiple storage backends (local, S3)

**Backup Script**: `deployment/scripts/backup/automated-backup.sh`

**Features**:
- PostgreSQL full/incremental backups
- Redis data backup
- Application state backup
- Compression and encryption
- Integrity verification
- Cloud storage upload
- Retention policy enforcement
- Notification system

### 2. Recovery Procedures

**Database Recovery**:
```bash
# Restore from backup
kubectl exec -i postgres-pod -- psql -U postgres -d uatp_prod < backup.sql

# Point-in-time recovery
pg_basebackup -h postgres-primary -D /recovery -U replicator -W
```

**Application Recovery**:
```bash
# Rollback deployment
kubectl rollout undo deployment/uatp-api -n uatp-prod

# Restore from backup
kubectl apply -f backup-manifest.yaml
```

## Monitoring & Alerting

### 1. Prometheus Configuration

**Metrics Collection**:
- Application metrics (custom UATP metrics)
- Infrastructure metrics (node, container)
- Database metrics (PostgreSQL)
- Cache metrics (Redis)
- Load balancer metrics (HAProxy)

**Configuration**: `deployment/monitoring/prometheus/prometheus.yml`

### 2. Alert Rules

**Comprehensive Alerting**:
- Application health alerts
- Performance degradation alerts
- Security incident alerts
- Infrastructure failure alerts
- Business metric alerts

**Configuration**: `deployment/monitoring/prometheus/rules/uatp-alerts.yml`

### 3. Alertmanager Setup

**Multi-channel Notifications**:
- Email alerts for different teams
- Slack integration
- PagerDuty for critical alerts
- Alert grouping and inhibition

**Configuration**: `deployment/monitoring/alertmanager/alertmanager.yml`

### 4. Grafana Dashboards

**Dashboards Included**:
- System overview dashboard
- Application performance dashboard
- Business metrics dashboard
- Security monitoring dashboard

## Deployment Process

### 1. Automated Deployment

**Main Deployment Script**: `deployment/scripts/deploy-production.sh`

**Features**:
- Pre-deployment validation
- Environment-specific configuration
- Container building and pushing
- Database migrations
- Rolling deployment
- Health checks
- Rollback on failure

**Usage**:
```bash
# Standard production deployment
./deployment/scripts/deploy-production.sh

# Deploy specific version
./deployment/scripts/deploy-production.sh -v v1.2.0

# Dry run (preview changes)
./deployment/scripts/deploy-production.sh --dry-run

# Quick deployment (skip tests and build)
./deployment/scripts/deploy-production.sh --skip-tests --skip-build
```

### 2. Deployment Steps

1. **Prerequisites Check**
   - Tool availability
   - Kubernetes connectivity
   - Environment configuration

2. **Testing Phase**
   - Unit tests
   - Integration tests
   - Security tests

3. **Build Phase**
   - Container image building
   - Registry push
   - Version tagging

4. **Infrastructure Setup**
   - Namespace creation
   - Secrets management
   - Database deployment

5. **Application Deployment**
   - Database migrations
   - Application rollout
   - Health verification

6. **Post-deployment**
   - Monitoring setup
   - Smoke tests
   - Documentation update

## Testing & Validation

### 1. Production Test Suite

**Test Script**: `deployment/scripts/production-test.sh`

**Test Categories**:
- Connectivity tests
- SSL/TLS validation
- Health endpoint verification
- Security header checks
- Performance benchmarks
- API functionality tests

**Usage**:
```bash
# Full test suite
./deployment/scripts/production-test.sh

# Quick health checks only
./deployment/scripts/production-test.sh --quick

# Test specific environment
./deployment/scripts/production-test.sh -u https://staging.uatp.com

# Verbose output
./deployment/scripts/production-test.sh --verbose
```

### 2. Load Testing

**Load Testing Setup**:
```bash
# Install locust
pip install locust

# Run load test
locust -f performance/locustfile.py --host https://api.uatp.com
```

## Operational Procedures

### 1. Regular Maintenance

**Daily Tasks**:
- Monitor system health dashboards
- Review alert notifications
- Check backup completion
- Verify SSL certificate status

**Weekly Tasks**:
- Review performance metrics
- Update security patches
- Clean up old logs and backups
- Validate disaster recovery procedures

**Monthly Tasks**:
- Security audit
- Capacity planning review
- Dependency updates
- Documentation updates

### 2. Scaling Operations

**Horizontal Scaling**:
```bash
# Scale application replicas
kubectl scale deployment uatp-api --replicas=10 -n uatp-prod

# Update HPA settings
kubectl patch hpa uatp-api-hpa -n uatp-prod -p '{"spec":{"maxReplicas":20}}'
```

**Vertical Scaling**:
```bash
# Update resource limits
kubectl patch deployment uatp-api -n uatp-prod -p '{"spec":{"template":{"spec":{"containers":[{"name":"uatp-api","resources":{"limits":{"memory":"4Gi","cpu":"2000m"}}}]}}}}'
```

### 3. Security Operations

**Security Monitoring**:
- Monitor authentication failures
- Track suspicious activity patterns
- Review rate limiting effectiveness
- Validate SSL/TLS configurations

**Incident Response**:
1. Immediate containment
2. Evidence collection
3. Impact assessment
4. Communication plan
5. Recovery procedures
6. Post-incident review

## Troubleshooting

### 1. Common Issues

**Application Won't Start**:
```bash
# Check pod status
kubectl get pods -n uatp-prod

# View pod logs
kubectl logs -f deployment/uatp-api -n uatp-prod

# Check configuration
kubectl describe pod <pod-name> -n uatp-prod
```

**Database Connection Issues**:
```bash
# Test database connectivity
kubectl exec -it postgres-pod -- psql -U postgres -d uatp_prod -c "SELECT 1;"

# Check database logs
kubectl logs -f deployment/postgresql -n uatp-prod
```

**Performance Issues**:
```bash
# Check resource utilization
kubectl top pods -n uatp-prod

# Review metrics in Grafana
kubectl port-forward service/grafana 3000:3000 -n uatp-prod
```

### 2. Emergency Procedures

**Application Rollback**:
```bash
# Rollback to previous version
kubectl rollout undo deployment/uatp-api -n uatp-prod

# Check rollout status
kubectl rollout status deployment/uatp-api -n uatp-prod
```

**Database Recovery**:
```bash
# Restore from latest backup
kubectl exec -i postgres-pod -- pg_restore -U postgres -d uatp_prod /backups/latest-backup.sql
```

**Scale Down for Emergency**:
```bash
# Reduce traffic temporarily
kubectl patch hpa uatp-api-hpa -n uatp-prod -p '{"spec":{"maxReplicas":2}}'
```

## Monitoring URLs

After successful deployment, these URLs will be available:

- **Main Application**: https://api.uatp.com
- **Health Check**: https://api.uatp.com/health
- **Metrics**: https://api.uatp.com/metrics
- **Monitoring Dashboard**: https://monitoring.uatp.com
- **Load Balancer Stats**: https://api.uatp.com:8404/stats

## Security Considerations

### 1. Network Security
- All traffic encrypted (TLS 1.2+)
- Network policies implemented
- Rate limiting configured
- DDoS protection enabled

### 2. Application Security
- Security headers enforced
- Input validation implemented
- Authentication/authorization required
- Secrets properly managed

### 3. Infrastructure Security
- Container security contexts
- Pod security policies
- Resource quotas and limits
- Regular security updates

## Performance Optimization

### 1. Database Optimization
- Connection pooling configured
- Read replicas for read-heavy workloads
- Query optimization and indexing
- Regular VACUUM and ANALYZE

### 2. Application Optimization
- HTTP/2 enabled
- Compression configured
- Caching strategies implemented
- Circuit breakers for resilience

### 3. Infrastructure Optimization
- Pod resource limits tuned
- Node affinity configured
- Horizontal Pod Autoscaling
- Cluster autoscaling enabled

---

## Quick Start Commands

```bash
# 1. Deploy to production
./deployment/scripts/deploy-production.sh

# 2. Run health checks
./deployment/scripts/production-test.sh --quick

# 3. Monitor deployment
kubectl get pods -n uatp-prod -w

# 4. Check application logs
kubectl logs -f deployment/uatp-api -n uatp-prod

# 5. Access monitoring
kubectl port-forward service/grafana 3000:3000 -n uatp-prod
```

Your UATP Capsule Engine is now production-ready with enterprise-grade reliability, security, and observability!

## Support

For issues or questions:
1. Check the troubleshooting section above
2. Review application and infrastructure logs
3. Consult monitoring dashboards
4. Run the production test suite
5. Review recent deployment changes