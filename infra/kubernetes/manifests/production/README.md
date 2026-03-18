# UATP Capsule Engine - Production Kubernetes Deployment

This directory contains production-ready Kubernetes manifests for deploying the UATP Capsule Engine to a production cluster.

##  Prerequisites

### Required Tools
- **kubectl** (v1.25+) - Kubernetes CLI
- **helm** (v3.0+) - Optional, for advanced deployments
- **docker** - For building images
- **Access to Kubernetes cluster** with appropriate permissions

### Required Cluster Components
- **Ingress Controller** (NGINX recommended)
- **cert-manager** (for automatic SSL/TLS certificates)
- **Metrics Server** (for HPA to function)
- **PostgreSQL Database** (RDS, Cloud SQL, or self-hosted)
- **Redis** (ElastiCache, Cloud Memorystore, or self-hosted)

### Recommended Cluster Specifications
- **Kubernetes Version**: 1.25+
- **Node Count**: 3+ (for HA)
- **Node Size**: 4 CPU, 8GB RAM minimum per node
- **Storage**: Persistent volumes for database backups

##  Quick Start

### 1. Build and Push Docker Image

```bash
# Build production Docker image
docker build -f Dockerfile.production -t uatp-capsule-engine:latest .

# Tag for your registry
docker tag uatp-capsule-engine:latest your-registry.com/uatp-capsule-engine:v1.0.1

# Push to registry
docker push your-registry.com/uatp-capsule-engine:v1.0.1
```

### 2. Configure Secrets

```bash
# Copy secrets template
cp secrets-template.yaml secrets.yaml

# Edit secrets.yaml and replace all CHANGE_ME values
# IMPORTANT: Never commit secrets.yaml to git!

# Apply secrets
kubectl apply -f secrets.yaml
```

**Required Secrets:**
- `database-url` - PostgreSQL connection string
- `signing-key` - UATP cryptographic signing key (64-char hex)
- `anthropic-api-key` - Optional, for AI features
- `openai-api-key` - Optional, for AI features

**Generate Signing Key:**
```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

### 3. Update Configuration

Edit `configmap.yaml` and update:
- `API_HOST` - Your domain (e.g., api.uatp.app)
- `FRONTEND_URL` - Your frontend URL
- `REDIS_URL` - Your Redis connection string

### 4. Update Ingress

Edit `ingress.yaml` and update:
- `spec.rules[0].host` - Your domain
- `spec.tls[0].hosts` - Your domain
- CORS allowed origins in annotations

### 5. Deploy

**Automated Deployment:**
```bash
chmod +x deploy.sh
./deploy.sh
```

**Manual Deployment:**
```bash
# Create namespace
kubectl apply -f namespace.yaml

# Apply ConfigMap
kubectl apply -f configmap.yaml

# Apply secrets (prepared in step 2)
kubectl apply -f secrets.yaml

# Deploy application
kubectl apply -f deployment.yaml
kubectl apply -f service.yaml

# Configure autoscaling
kubectl apply -f hpa.yaml

# Configure ingress
kubectl apply -f ingress.yaml

# Wait for deployment
kubectl rollout status deployment/uatp-api -n uatp-production
```

##  File Descriptions

### `namespace.yaml`
Creates the `uatp-production` namespace with resource quotas and limits.

**Features:**
- Isolated namespace for production workloads
- Resource quotas to prevent resource exhaustion
- Network policies for security

### `configmap.yaml`
Environment configuration for the application.

**Key Settings:**
- Environment (`ENVIRONMENT=production`)
- Database connection settings
- Cache configuration
- Feature flags
- Logging levels

### `secrets-template.yaml`
Template for creating secrets. **Copy this to `secrets.yaml` and populate with real values.**

**Contains:**
- Database credentials
- API keys (Anthropic, OpenAI)
- Signing keys
- Stripe keys (for billing)

### `deployment.yaml`
Main application deployment configuration.

**Features:**
- **3 replicas** for high availability
- **Rolling updates** with zero downtime
- **Resource limits** (500m-2000m CPU, 512Mi-2Gi RAM)
- **Health checks** (liveness & readiness probes)
- **Security context** (non-root user, read-only root filesystem)
- **Anti-affinity** rules for distributing pods across nodes

**Environment Variables:**
- Loaded from ConfigMap
- Secrets mounted as environment variables

### `service.yaml`
Kubernetes Service definitions.

**Services:**
1. **uatp-api** (ClusterIP) - Main service for Ingress
   - Port 80 → Container 8000 (HTTP)
   - Port 9090 → Container 9090 (Metrics)

2. **uatp-api-headless** (Headless) - For pod discovery
   - Port 8000 → Container 8000

### `hpa.yaml`
Horizontal Pod Autoscaler configuration.

**Scaling Rules:**
- **Min replicas**: 3
- **Max replicas**: 20
- **Target CPU**: 70%
- **Target Memory**: 80%

**Behavior:**
- **Scale up**: Aggressive (100% increase every 30s, max 4 pods)
- **Scale down**: Conservative (50% decrease every 60s, max 2 pods, 5min stabilization)

### `ingress.yaml`
NGINX Ingress configuration with SSL, CORS, and rate limiting.

**Features:**
- **Automatic SSL/TLS** via cert-manager and Let's Encrypt
- **Rate limiting** (100 RPS, 50 connections)
- **CORS** configuration
- **Security headers** (X-Frame-Options, CSP, etc.)
- **Timeouts** (60s connect, send, read)
- **Body size limit** (10MB)

### `deploy.sh`
Automated deployment script with validation and health checks.

**Functions:**
- Checks kubectl installation and cluster connectivity
- Creates namespace
- Applies ConfigMap
- Validates secrets exist
- Deploys application
- Configures HPA and Ingress
- Waits for deployment to be ready
- Shows deployment status and useful commands

##  Configuration

### Environment Variables (ConfigMap)

| Variable | Description | Default |
|----------|-------------|---------|
| `ENVIRONMENT` | Deployment environment | `production` |
| `LOG_LEVEL` | Logging verbosity | `INFO` |
| `API_HOST` | API domain | `api.uatp.app` |
| `DATABASE_POOL_SIZE` | Connection pool size | `20` |
| `DATABASE_MAX_OVERFLOW` | Max overflow connections | `40` |
| `REDIS_URL` | Redis connection string | `redis://redis:6379/0` |
| `ENABLE_CACHING` | Enable response caching | `true` |
| `ENABLE_METRICS` | Enable Prometheus metrics | `true` |
| `CORS_ORIGINS` | Allowed CORS origins | `https://uatp.app` |

### Resource Requirements

**Per Pod:**
- **CPU Request**: 500m (0.5 cores)
- **CPU Limit**: 2000m (2 cores)
- **Memory Request**: 512Mi
- **Memory Limit**: 2Gi

**Cluster Total (3 replicas):**
- **CPU**: 1.5 cores requested, 6 cores limit
- **Memory**: 1.5Gi requested, 6Gi limit

### Scaling Configuration

**Autoscaling Triggers:**
- CPU usage > 70% → Scale up
- Memory usage > 80% → Scale up
- CPU usage < 40% (for 5min) → Scale down
- Memory usage < 50% (for 5min) → Scale down

##  Security

### Pod Security

```yaml
securityContext:
  runAsNonRoot: true
  runAsUser: 1000
  fsGroup: 1000
  allowPrivilegeEscalation: false
  capabilities:
    drop: ["ALL"]
  readOnlyRootFilesystem: true
```

### Network Policies

- Pods can only communicate within namespace
- Ingress only accepts traffic from NGINX Ingress Controller
- Egress allowed to database and Redis

### Secrets Management

**Recommendations:**
1. Use external secrets manager:
   - **AWS**: AWS Secrets Manager
   - **Azure**: Azure Key Vault
   - **GCP**: Google Secret Manager
   - **HashiCorp Vault**

2. Enable secret encryption at rest in etcd
3. Use RBAC to restrict secret access
4. Rotate secrets regularly

##  Monitoring

### Health Checks

**Liveness Probe:**
- Endpoint: `/health`
- Initial delay: 30s
- Period: 10s
- Timeout: 5s
- Failure threshold: 3

**Readiness Probe:**
- Endpoint: `/health/ready`
- Initial delay: 10s
- Period: 5s
- Timeout: 3s
- Failure threshold: 3

### Metrics

**Prometheus metrics available at:**
- `http://<pod-ip>:9090/metrics`

**Key Metrics:**
- HTTP request rate, latency, errors
- Capsule creation rate
- Database connection pool stats
- Cache hit/miss rates
- Queue depth

### Logs

**View logs:**
```bash
# All pods
kubectl logs -f -l app=uatp-api -n uatp-production

# Specific pod
kubectl logs -f <pod-name> -n uatp-production

# Previous instance (if crashed)
kubectl logs --previous <pod-name> -n uatp-production
```

##  Deployment Workflow

### Standard Deployment

```bash
# 1. Build new image
docker build -f Dockerfile.production -t uatp:v1.0.1 .

# 2. Push to registry
docker push your-registry.com/uatp:v1.0.1

# 3. Update deployment
kubectl set image deployment/uatp-api \
  uatp-api=your-registry.com/uatp:v1.0.1 \
  -n uatp-production

# 4. Monitor rollout
kubectl rollout status deployment/uatp-api -n uatp-production
```

### Rollback

```bash
# Rollback to previous version
kubectl rollout undo deployment/uatp-api -n uatp-production

# Rollback to specific revision
kubectl rollout undo deployment/uatp-api --to-revision=3 -n uatp-production

# View rollout history
kubectl rollout history deployment/uatp-api -n uatp-production
```

### Zero-Downtime Updates

The deployment is configured for rolling updates:
- `maxSurge: 1` - One extra pod during update
- `maxUnavailable: 0` - No pods taken down until new ones are ready
- Readiness probes ensure traffic only goes to healthy pods

##  Troubleshooting

### Pods Not Starting

```bash
# Check pod status
kubectl get pods -n uatp-production

# Describe pod for events
kubectl describe pod <pod-name> -n uatp-production

# Check logs
kubectl logs <pod-name> -n uatp-production
```

**Common Issues:**
- **ImagePullBackOff**: Check image exists and registry credentials
- **CrashLoopBackOff**: Check logs for application errors
- **Pending**: Check node resources and scheduling constraints

### Database Connection Issues

```bash
# Test database connectivity from pod
kubectl exec -it <pod-name> -n uatp-production -- \
  python3 -c "
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
async def test():
    engine = create_async_engine('$DATABASE_URL')
    async with engine.begin() as conn:
        result = await conn.execute('SELECT 1')
        print('Database connected!')
    await engine.dispose()
asyncio.run(test())
"
```

### HPA Not Scaling

```bash
# Check HPA status
kubectl get hpa -n uatp-production

# Describe HPA
kubectl describe hpa uatp-api-hpa -n uatp-production

# Check metrics server
kubectl top nodes
kubectl top pods -n uatp-production
```

**Common Issues:**
- Metrics Server not installed or not working
- Resource requests not defined (HPA requires them)
- Current utilization below scaling threshold

### SSL/TLS Issues

```bash
# Check cert-manager
kubectl get certificate -n uatp-production
kubectl describe certificate uatp-api-tls -n uatp-production

# Check certificate secrets
kubectl get secret uatp-api-tls -n uatp-production

# Check ingress
kubectl describe ingress uatp-api-ingress -n uatp-production
```

##  Useful Commands

### Cluster Management

```bash
# Get all resources
kubectl get all -n uatp-production

# Check resource usage
kubectl top pods -n uatp-production
kubectl top nodes

# Get events
kubectl get events -n uatp-production --sort-by='.lastTimestamp'

# Describe deployment
kubectl describe deployment uatp-api -n uatp-production
```

### Pod Management

```bash
# Shell into pod
kubectl exec -it <pod-name> -n uatp-production -- /bin/bash

# Port forward to pod (for debugging)
kubectl port-forward <pod-name> 8000:8000 -n uatp-production

# Copy files from pod
kubectl cp uatp-production/<pod-name>:/app/logs/app.log ./app.log

# Restart deployment (all pods)
kubectl rollout restart deployment/uatp-api -n uatp-production
```

### Scaling

```bash
# Manual scaling
kubectl scale deployment uatp-api --replicas=5 -n uatp-production

# Disable HPA (for manual scaling)
kubectl delete hpa uatp-api-hpa -n uatp-production

# Re-enable HPA
kubectl apply -f hpa.yaml
```

### Secrets and ConfigMaps

```bash
# View ConfigMap
kubectl get configmap uatp-config -n uatp-production -o yaml

# Edit ConfigMap
kubectl edit configmap uatp-config -n uatp-production

# View secret (base64 encoded)
kubectl get secret uatp-secrets -n uatp-production -o yaml

# Decode secret
kubectl get secret uatp-secrets -n uatp-production -o jsonpath='{.data.database-url}' | base64 -d
```

##  Performance Tuning

### Database Optimization

**Connection Pooling:**
```yaml
DATABASE_POOL_SIZE: "20"
DATABASE_MAX_OVERFLOW: "40"
DATABASE_POOL_RECYCLE: "3600"
DATABASE_POOL_PRE_PING: "true"
```

**Read Replicas:**
- Configure in `database_optimization.py`
- Route read queries to replicas
- Write queries to primary

### Caching

**Redis Configuration:**
```yaml
REDIS_URL: "redis://redis:6379/0"
ENABLE_CACHING: "true"
CACHE_TTL: "300"
```

**Cache Strategy:**
- Cache GET endpoints (capsule lists, stats)
- Cache-Control headers for client-side caching
- CDN for static assets

### Resource Limits

**Increase for high load:**
```yaml
resources:
  requests:
    cpu: "1000m"      # 1 core
    memory: "1Gi"
  limits:
    cpu: "4000m"      # 4 cores
    memory: "4Gi"
```

##  Multi-Region Deployment

For global deployments, consider:

1. **Deploy to multiple regions** (US, EU, Asia)
2. **Use geo-DNS** (Route53, Cloudflare) for routing
3. **Database replication** across regions
4. **Shared Redis** or per-region caches
5. **CDN** for static assets (CloudFront, Cloudflare)

##  Pre-Deployment Checklist

- [ ] Docker image built and pushed to registry
- [ ] Secrets created and applied
- [ ] ConfigMap updated with correct values
- [ ] Ingress configured with correct domain
- [ ] DNS records pointing to cluster
- [ ] cert-manager installed and configured
- [ ] Metrics Server installed
- [ ] Database accessible from cluster
- [ ] Redis accessible from cluster
- [ ] Resource quotas appropriate for cluster
- [ ] Network policies tested
- [ ] Monitoring and alerting configured

## 🆘 Support

**Documentation:**
- Main docs: `docs/deployment-guide.md`
- API docs: `docs/api-documentation.md`
- System guide: `MASTER_SYSTEM_GUIDE.md`

**Troubleshooting:**
- Check logs: `kubectl logs -f -l app=uatp-api -n uatp-production`
- Check health: `curl https://api.uatp.app/health`
- Check metrics: `curl https://api.uatp.app:9090/metrics`

**Contact:**
- GitHub Issues: [github.com/KayronCalloway/capsule-engine/issues](https://github.com/KayronCalloway/capsule-engine/issues)
- Email: Kayron@houseofcalloway.com
