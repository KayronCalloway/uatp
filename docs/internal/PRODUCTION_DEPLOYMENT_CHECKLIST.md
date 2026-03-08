# UATP Capsule Engine - Production Deployment Checklist

This comprehensive checklist ensures all aspects of production deployment are properly configured and tested.

## 📅 Timeline: 2-4 Weeks

### Week 1: Infrastructure Setup
### Week 2: Application Deployment & Testing
### Week 3: Security Hardening & Performance Tuning
### Week 4: Monitoring, Documentation & Go-Live

---

## 🏗️ Phase 1: Infrastructure Preparation

### Kubernetes Cluster

- [ ] **Cluster provisioned** with minimum 3 nodes
  - [ ] 4 CPU, 8GB RAM per node minimum
  - [ ] Kubernetes version 1.25+
  - [ ] Node auto-scaling enabled

- [ ] **Storage classes configured**
  - [ ] Fast SSD storage for database
  - [ ] Standard storage for backups

- [ ] **Network configuration**
  - [ ] Private subnets for database/Redis
  - [ ] Public subnets for load balancer
  - [ ] Security groups/firewall rules configured

### Required Components

- [ ] **NGINX Ingress Controller** installed
  ```bash
  kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/main/deploy/static/provider/cloud/deploy.yaml
  ```

- [ ] **cert-manager** installed for SSL/TLS
  ```bash
  kubectl apply -f https://github.com/cert-manager/cert-manager/releases/download/v1.13.0/cert-manager.yaml
  ```

- [ ] **Metrics Server** installed for HPA
  ```bash
  kubectl apply -f https://github.com/kubernetes-sigs/metrics-server/releases/latest/download/components.yaml
  ```

- [ ] **ClusterIssuer** configured for Let's Encrypt
  ```yaml
  apiVersion: cert-manager.io/v1
  kind: ClusterIssuer
  metadata:
    name: letsencrypt-prod
  spec:
    acme:
      server: https://acme-v02.api.letsencrypt.org/directory
      email: your-email@example.com
      privateKeySecretRef:
        name: letsencrypt-prod
      solvers:
      - http01:
          ingress:
            class: nginx
  ```

### Database Setup

- [ ] **PostgreSQL provisioned**
  - [ ] Version 14+ recommended
  - [ ] Minimum 2 vCPU, 8GB RAM
  - [ ] 100GB SSD storage
  - [ ] Automated backups enabled (daily, 30-day retention)
  - [ ] Point-in-time recovery enabled

- [ ] **Database created**
  ```sql
  CREATE DATABASE uatp_production;
  CREATE USER uatp_user WITH ENCRYPTED PASSWORD 'strong_password';
  GRANT ALL PRIVILEGES ON DATABASE uatp_production TO uatp_user;
  ```

- [ ] **Connection string tested**
  ```
  postgresql+asyncpg://uatp_user:password@host:5432/uatp_production
  ```

- [ ] **Read replicas configured** (optional, for scaling)

### Redis Setup

- [ ] **Redis provisioned**
  - [ ] Version 6.2+ recommended
  - [ ] 2GB RAM minimum
  - [ ] Persistence enabled (RDB + AOF)
  - [ ] High availability mode (Redis Sentinel or Cluster)

- [ ] **Connection string tested**
  ```
  redis://username:password@host:6379/0
  ```

### DNS Configuration

- [ ] **Domain registered** (e.g., uatp.app)

- [ ] **DNS records created**
  - [ ] `A` record: `api.uatp.app` → Load Balancer IP
  - [ ] `CNAME` record: `www.uatp.app` → `uatp.app`
  - [ ] `TXT` record for domain verification (if needed)

- [ ] **DNS propagation verified**
  ```bash
  nslookup api.uatp.app
  dig api.uatp.app
  ```

---

## 🔐 Phase 2: Security Configuration

### Secrets Management

- [ ] **Signing key generated**
  ```bash
  python -c "import secrets; print(secrets.token_hex(32))"
  ```

- [ ] **API keys obtained**
  - [ ] Anthropic API key (if using Claude)
  - [ ] OpenAI API key (if using GPT)
  - [ ] Stripe API keys (if using billing)

- [ ] **Secrets file created**
  ```bash
  cp k8s/production/secrets-template.yaml k8s/production/secrets.yaml
  # Edit secrets.yaml with real values
  ```

- [ ] **Secrets applied to cluster**
  ```bash
  kubectl apply -f k8s/production/secrets.yaml
  ```

- [ ] **Secrets verified**
  ```bash
  kubectl get secret uatp-secrets -n uatp-production
  ```

- [ ] **secrets.yaml added to .gitignore** ✅ CRITICAL

### SSL/TLS Certificates

- [ ] **Certificate issued** by Let's Encrypt
- [ ] **Certificate stored** in Kubernetes secret
- [ ] **Certificate auto-renewal** verified

### Network Security

- [ ] **Network policies** applied
  - [ ] Restrict ingress to Ingress Controller only
  - [ ] Restrict egress to database, Redis, and internet (for AI APIs)

- [ ] **Pod security policies** enforced
  - [ ] Non-root user required
  - [ ] Privilege escalation disabled
  - [ ] Read-only root filesystem

- [ ] **RBAC configured**
  - [ ] Service accounts created
  - [ ] Minimal permissions granted

---

## 🚀 Phase 3: Application Deployment

### Docker Image Build

- [ ] **Production Dockerfile reviewed**
  ```bash
  cat Dockerfile.production
  ```

- [ ] **Image built**
  ```bash
  docker build -f Dockerfile.production -t uatp-capsule-engine:v1.0.0 .
  ```

- [ ] **Image tested locally**
  ```bash
  docker run -p 8000:8000 \
    -e DATABASE_URL="postgresql+asyncpg://..." \
    -e UATP_SIGNING_KEY="..." \
    uatp-capsule-engine:v1.0.0
  ```

- [ ] **Image pushed to registry**
  ```bash
  docker tag uatp-capsule-engine:v1.0.0 your-registry.com/uatp:v1.0.0
  docker push your-registry.com/uatp:v1.0.0
  ```

### ConfigMap Configuration

- [ ] **ConfigMap edited** with production values
  - [ ] `API_HOST` set to production domain
  - [ ] `ENVIRONMENT=production`
  - [ ] `LOG_LEVEL=INFO`
  - [ ] Redis URL configured
  - [ ] CORS origins configured

- [ ] **ConfigMap applied**
  ```bash
  kubectl apply -f k8s/production/configmap.yaml
  ```

### Deployment

- [ ] **Namespace created**
  ```bash
  kubectl apply -f k8s/production/namespace.yaml
  ```

- [ ] **Deployment manifests updated** with correct image
  ```yaml
  image: your-registry.com/uatp:v1.0.0
  ```

- [ ] **Deployment applied**
  ```bash
  kubectl apply -f k8s/production/deployment.yaml
  ```

- [ ] **Service applied**
  ```bash
  kubectl apply -f k8s/production/service.yaml
  ```

- [ ] **HPA applied**
  ```bash
  kubectl apply -f k8s/production/hpa.yaml
  ```

- [ ] **Ingress applied**
  ```bash
  kubectl apply -f k8s/production/ingress.yaml
  ```

- [ ] **Deployment status verified**
  ```bash
  kubectl rollout status deployment/uatp-api -n uatp-production
  kubectl get pods -n uatp-production
  ```

---

## ✅ Phase 4: Testing & Validation

### Health Checks

- [ ] **Health endpoint responding**
  ```bash
  curl https://api.uatp.app/health
  ```
  Expected: `{"status": "healthy", ...}`

- [ ] **Readiness endpoint responding**
  ```bash
  curl https://api.uatp.app/health/ready
  ```

### API Endpoints

- [ ] **Mobile API tested**
  ```bash
  curl https://api.uatp.app/api/v1/mobile/health
  ```

- [ ] **Capsule creation tested**
  ```bash
  curl -X POST https://api.uatp.app/api/v1/mobile/capture/single \
    -H "Content-Type: application/json" \
    -d '{"device_id": "test", "platform": "ios", "messages": [...]}'
  ```

- [ ] **WebAuthn endpoints tested**
  ```bash
  curl https://api.uatp.app/api/v1/webauthn/health
  ```

- [ ] **API documentation accessible**
  ```bash
  curl https://api.uatp.app/docs
  ```

### Database Connectivity

- [ ] **Database migrations ran successfully**
  ```bash
  kubectl logs -l app=uatp-api -n uatp-production | grep -i migration
  ```

- [ ] **Connection pooling working**
  ```bash
  kubectl logs -l app=uatp-api -n uatp-production | grep -i "database connected"
  ```

- [ ] **Queries executing successfully**

### Caching

- [ ] **Redis connected**
  ```bash
  kubectl logs -l app=uatp-api -n uatp-production | grep -i redis
  ```

- [ ] **Cache hits/misses monitored**

### SSL/TLS

- [ ] **HTTPS working**
  ```bash
  curl -I https://api.uatp.app/health
  ```
  Check for: `HTTP/2 200`

- [ ] **Certificate valid**
  ```bash
  openssl s_client -connect api.uatp.app:443 -servername api.uatp.app
  ```

- [ ] **SSL Labs test passed** (A+ rating)
  - Visit: https://www.ssllabs.com/ssltest/

### Load Testing

- [ ] **Load test performed**
  ```bash
  # Using Apache Bench
  ab -n 1000 -c 10 https://api.uatp.app/health

  # Using wrk
  wrk -t4 -c100 -d30s https://api.uatp.app/health
  ```

- [ ] **HPA scaling verified**
  ```bash
  kubectl get hpa -n uatp-production -w
  ```

- [ ] **Performance metrics acceptable**
  - [ ] p50 latency < 100ms
  - [ ] p95 latency < 500ms
  - [ ] p99 latency < 1000ms
  - [ ] Error rate < 0.1%

### Security Testing

- [ ] **Security headers present**
  ```bash
  curl -I https://api.uatp.app
  ```
  Check for:
  - `X-Frame-Options: DENY`
  - `X-Content-Type-Options: nosniff`
  - `X-XSS-Protection: 1; mode=block`

- [ ] **CORS configured correctly**
  ```bash
  curl -H "Origin: https://uatp.app" -I https://api.uatp.app/health
  ```

- [ ] **Rate limiting working**
  ```bash
  for i in {1..200}; do curl https://api.uatp.app/health; done
  ```
  Should see 429 errors after limit

- [ ] **Vulnerability scan passed**
  ```bash
  # Scan Docker image
  trivy image your-registry.com/uatp:v1.0.0
  ```

---

## 📊 Phase 5: Monitoring & Observability

### Prometheus Metrics

- [ ] **Metrics endpoint accessible**
  ```bash
  kubectl port-forward -n uatp-production svc/uatp-api 9090:9090
  curl http://localhost:9090/metrics
  ```

- [ ] **Key metrics present**
  - [ ] `http_requests_total`
  - [ ] `http_request_duration_seconds`
  - [ ] `capsule_creations_total`
  - [ ] `database_connections_active`
  - [ ] `cache_hits_total`

### Grafana Dashboards

- [ ] **Grafana installed** (if not already)
  ```bash
  helm install grafana grafana/grafana
  ```

- [ ] **Dashboards imported**
  - [ ] Application performance dashboard
  - [ ] Infrastructure dashboard
  - [ ] Business metrics dashboard

- [ ] **Data sources configured**
  - [ ] Prometheus
  - [ ] Loki (for logs)

### Alerting

- [ ] **Alert rules configured**
  - [ ] High error rate (> 1%)
  - [ ] High latency (p95 > 1s)
  - [ ] Pod crashes
  - [ ] Database connection failures
  - [ ] Certificate expiration (< 30 days)

- [ ] **Alert channels configured**
  - [ ] Email
  - [ ] Slack
  - [ ] PagerDuty

- [ ] **Test alerts sent**

### Logging

- [ ] **Log aggregation configured**
  - [ ] Loki, ELK, or CloudWatch

- [ ] **Log queries working**
  ```bash
  kubectl logs -f -l app=uatp-api -n uatp-production
  ```

- [ ] **Log retention configured** (30 days minimum)

### Distributed Tracing

- [ ] **Jaeger or Zipkin installed** (optional)
- [ ] **Traces captured and viewable**

---

## 🎯 Phase 6: Performance Optimization

### Database Optimization

- [ ] **Indexes created** for common queries
  ```sql
  CREATE INDEX idx_capsules_created_at ON capsules(created_at);
  CREATE INDEX idx_capsules_user_id ON capsules(user_id);
  ```

- [ ] **Connection pooling tuned**
  - [ ] `DATABASE_POOL_SIZE=20`
  - [ ] `DATABASE_MAX_OVERFLOW=40`

- [ ] **Query performance analyzed**
  ```sql
  EXPLAIN ANALYZE SELECT * FROM capsules WHERE user_id = '...';
  ```

- [ ] **Slow query logging enabled**

### Caching Strategy

- [ ] **Cache TTL configured**
  - [ ] Capsule list: 5 minutes
  - [ ] User stats: 10 minutes
  - [ ] Reference data: 1 hour

- [ ] **Cache invalidation working**

- [ ] **Cache hit rate > 80%**

### Resource Optimization

- [ ] **CPU/memory requests tuned** based on usage
- [ ] **Horizontal scaling thresholds adjusted**
- [ ] **Vertical scaling considered** for database

---

## 📚 Phase 7: Documentation

### Internal Documentation

- [ ] **Runbooks created**
  - [ ] Deployment procedure
  - [ ] Rollback procedure
  - [ ] Incident response
  - [ ] Database backup/restore

- [ ] **Architecture diagrams updated**

- [ ] **API documentation published**
  - [ ] Swagger/OpenAPI at `/docs`
  - [ ] Postman collection

- [ ] **Operations guide written**
  - [ ] Common tasks
  - [ ] Troubleshooting guide
  - [ ] Performance tuning

### External Documentation

- [ ] **User guides published**
- [ ] **API reference published**
- [ ] **Integration guides published**
  - [ ] iOS integration
  - [ ] Web integration

---

## 🚨 Phase 8: Disaster Recovery

### Backup Strategy

- [ ] **Database backups automated**
  - [ ] Daily full backups
  - [ ] 30-day retention
  - [ ] Stored in separate region

- [ ] **Backup restoration tested**
  ```bash
  # Restore to test environment
  pg_restore -d uatp_test < backup.sql
  ```

- [ ] **Redis backups configured** (if persistence required)

### High Availability

- [ ] **Multi-AZ deployment** verified
  - [ ] Pods distributed across availability zones
  - [ ] Database in multi-AZ mode

- [ ] **Failover tested**
  - [ ] Simulate node failure
  - [ ] Verify pods reschedule
  - [ ] Verify no downtime

### Incident Response

- [ ] **Incident response plan documented**
  - [ ] Contact list
  - [ ] Escalation procedures
  - [ ] Communication templates

- [ ] **On-call rotation established**

---

## 🎉 Phase 9: Go-Live

### Pre-Launch Checklist

- [ ] **All above phases completed** ✅
- [ ] **Stakeholders notified** of launch date
- [ ] **Support team trained**
- [ ] **Monitoring dashboards open** on launch day
- [ ] **On-call engineers ready**

### Launch Day

- [ ] **DNS cutover performed**
  - [ ] Update DNS records to production
  - [ ] Wait for propagation (15-60 minutes)

- [ ] **Traffic monitoring**
  - [ ] Watch metrics dashboards
  - [ ] Monitor error rates
  - [ ] Check logs for issues

- [ ] **Smoke tests passed**
  - [ ] Health checks passing
  - [ ] API calls succeeding
  - [ ] Authentication working
  - [ ] Capsule creation working

### Post-Launch (First 24 Hours)

- [ ] **Monitor continuously** for first 24 hours
- [ ] **Check metrics** every hour
  - [ ] Request rate
  - [ ] Error rate
  - [ ] Latency
  - [ ] CPU/memory usage

- [ ] **Verify autoscaling** working under load

- [ ] **Check cost estimates** vs actual usage

---

## 📊 Post-Launch Monitoring (First Week)

### Daily Tasks

- [ ] **Review metrics** (every morning)
- [ ] **Check logs** for errors
- [ ] **Verify backups** ran successfully
- [ ] **Monitor costs**
- [ ] **Review alerts** (if any triggered)

### Weekly Tasks

- [ ] **Performance review**
  - [ ] Latency trends
  - [ ] Throughput trends
  - [ ] Error rates

- [ ] **Capacity planning**
  - [ ] Current usage vs capacity
  - [ ] Growth projections
  - [ ] Scaling recommendations

- [ ] **Security review**
  - [ ] Check for vulnerabilities
  - [ ] Review access logs
  - [ ] Update dependencies

---

## 🔄 Ongoing Maintenance

### Monthly Tasks

- [ ] **Dependency updates**
  ```bash
  pip list --outdated
  ```

- [ ] **Security patches** applied

- [ ] **Database maintenance**
  - [ ] Vacuum and analyze
  - [ ] Index optimization
  - [ ] Query performance review

- [ ] **Cost optimization review**

- [ ] **Documentation updates**

### Quarterly Tasks

- [ ] **Disaster recovery drill**
- [ ] **Load testing** to verify capacity
- [ ] **Architecture review**
- [ ] **Security audit**

---

## ✅ Sign-Off

### Required Approvals

- [ ] **Engineering Lead** - Technical implementation complete
- [ ] **DevOps Lead** - Infrastructure and deployment verified
- [ ] **Security Lead** - Security requirements met
- [ ] **Product Lead** - Functionality meets requirements
- [ ] **Executive Sponsor** - Ready for production launch

### Deployment Authorization

**Date:** _______________

**Approved By:**

- Engineering: _______________
- DevOps: _______________
- Security: _______________
- Product: _______________
- Executive: _______________

---

## 📞 Emergency Contacts

| Role | Name | Email | Phone |
|------|------|-------|-------|
| Engineering Lead | | | |
| DevOps Lead | | | |
| Database Admin | | | |
| Security Lead | | | |
| On-Call Engineer | | | |

---

## 📝 Notes

**Deployment Date:** _______________

**Version Deployed:** _______________

**Issues Encountered:**
-

**Lessons Learned:**
-

**Follow-Up Actions:**
-

---

**Document Version:** 1.0
**Last Updated:** 2025-01-06
**Owner:** UATP Engineering Team
