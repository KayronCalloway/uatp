# UATP Capsule Engine - Production Quick Start

**5-Minute Guide to Deploying UATP to Production**

This is a condensed version for experienced DevOps engineers. For complete details, see:
- `k8s/production/README.md` - Full deployment guide
- `PRODUCTION_DEPLOYMENT_CHECKLIST.md` - Complete checklist

---

## Prerequisites [OK]

- Kubernetes cluster (1.25+, 3+ nodes)
- kubectl configured
- Docker registry access
- PostgreSQL database
- Redis instance
- Domain name configured

---

##  Deploy in 5 Steps

### 1️⃣ Build & Push Image

```bash
# Build
docker build -f Dockerfile.production -t uatp:v1.0.0 .

# Tag & Push
docker tag uatp:v1.0.0 your-registry.com/uatp:v1.0.0
docker push your-registry.com/uatp:v1.0.0
```

### 2️⃣ Configure Secrets

```bash
cd k8s/production

# Copy template
cp secrets-template.yaml secrets.yaml

# Generate signing key
python -c "import secrets; print(secrets.token_hex(32))"

# Edit secrets.yaml with:
# - database-url: postgresql+asyncpg://user:pass@host:5432/db
# - signing-key: <generated-key>
# - anthropic-api-key: sk-ant-api03-...
# - openai-api-key: sk-...

# Apply
kubectl apply -f secrets.yaml
```

### 3️⃣ Configure Environment

```bash
# Edit configmap.yaml
# Update: API_HOST, FRONTEND_URL, REDIS_URL

# Edit ingress.yaml
# Update: spec.rules[0].host to your domain

# Apply
kubectl apply -f configmap.yaml
```

### 4️⃣ Deploy

```bash
# Automated deployment
chmod +x deploy.sh
./deploy.sh

# OR Manual deployment
kubectl apply -f namespace.yaml
kubectl apply -f configmap.yaml
kubectl apply -f secrets.yaml
kubectl apply -f deployment.yaml
kubectl apply -f service.yaml
kubectl apply -f hpa.yaml
kubectl apply -f ingress.yaml
```

### 5️⃣ Verify

```bash
# Check pods
kubectl get pods -n uatp-production

# Check health
curl https://your-domain.com/health

# Watch logs
kubectl logs -f -l app=uatp-api -n uatp-production
```

---

##  Key Metrics

**Default Configuration:**
- **Replicas:** 3 (min) → 20 (max)
- **CPU:** 500m-2000m per pod
- **Memory:** 512Mi-2Gi per pod
- **Autoscaling:** 70% CPU, 80% memory
- **Health checks:** Every 10s

---

##  Common Operations

### Scale Manually
```bash
kubectl scale deployment uatp-api --replicas=10 -n uatp-production
```

### Update Image
```bash
kubectl set image deployment/uatp-api \
  uatp-api=your-registry.com/uatp:v1.0.1 \
  -n uatp-production
```

### Rollback
```bash
kubectl rollout undo deployment/uatp-api -n uatp-production
```

### View Logs
```bash
kubectl logs -f -l app=uatp-api -n uatp-production
```

### Shell into Pod
```bash
kubectl exec -it <pod-name> -n uatp-production -- /bin/bash
```

---

##  Quick Troubleshooting

### Pods Not Starting
```bash
kubectl describe pod <pod-name> -n uatp-production
kubectl logs <pod-name> -n uatp-production
```

### Database Connection Issues
```bash
# Test from pod
kubectl exec -it <pod-name> -n uatp-production -- \
  curl localhost:8000/health
```

### SSL Issues
```bash
kubectl get certificate -n uatp-production
kubectl describe certificate uatp-api-tls -n uatp-production
```

### HPA Not Working
```bash
kubectl get hpa -n uatp-production
kubectl describe hpa uatp-api-hpa -n uatp-production
kubectl top pods -n uatp-production
```

---

##  Pre-Deployment Checklist

- [ ] Docker image built and pushed
- [ ] Secrets configured and applied
- [ ] ConfigMap updated with production values
- [ ] Ingress configured with correct domain
- [ ] DNS pointing to cluster
- [ ] Database accessible
- [ ] Redis accessible
- [ ] cert-manager installed
- [ ] Metrics Server installed

---

##  Security Essentials

1. **Never commit secrets.yaml** - Add to .gitignore
2. **Use strong signing key** - 64-character hex
3. **Enable HTTPS only** - Force SSL redirect
4. **Rotate secrets regularly** - Every 90 days
5. **Enable rate limiting** - Configured in Ingress
6. **Use non-root containers** - Already configured
7. **Network policies** - Restrict pod communication

---

##  Monitoring Endpoints

| Endpoint | Purpose |
|----------|---------|
| `/health` | Basic health check |
| `/health/ready` | Readiness probe |
| `/metrics` (port 9090) | Prometheus metrics |
| `/docs` | API documentation |

---

## 🆘 Emergency Contacts

**Critical Issues:**
1. Check logs: `kubectl logs -f -l app=uatp-api -n uatp-production`
2. Check health: `curl https://your-domain.com/health`
3. Rollback if needed: `kubectl rollout undo deployment/uatp-api -n uatp-production`

**Support:**
- GitHub Issues: [github.com/KayronCalloway/capsule-engine/issues](https://github.com/KayronCalloway/capsule-engine/issues)
- Email: Kayron@houseofcalloway.com

---

##  Additional Resources

- **Full Deployment Guide:** `k8s/production/README.md`
- **Complete Checklist:** `PRODUCTION_DEPLOYMENT_CHECKLIST.md`
- **System Manual:** `MASTER_SYSTEM_GUIDE.md`
- **API Docs:** `docs/api-documentation.md`

---

**Last Updated:** 2025-01-06
**Version:** 1.0.0
