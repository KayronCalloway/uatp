# UATP Capsule Engine - Monitoring & Observability Setup Guide

Complete guide for setting up production monitoring with Prometheus, Grafana, and Alertmanager.

---

## 📊 Overview

**Monitoring Stack:**
- **Prometheus** - Metrics collection and storage
- **Grafana** - Visualization and dashboards
- **Alertmanager** - Alert routing and notifications
- **Loki** (optional) - Log aggregation
- **Jaeger** (optional) - Distributed tracing

**Metrics Exposed:**
- HTTP request rate, latency, errors
- Capsule creation metrics
- Database connection pool stats
- Cache hit/miss rates
- WebAuthn activity
- Mobile API usage
- Kubernetes pod metrics

---

## 🚀 Quick Setup

### 1. Install Monitoring Stack

```bash
# Add Prometheus Community Helm charts
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo update

# Install kube-prometheus-stack (includes Prometheus, Grafana, Alertmanager)
helm install prometheus prometheus-community/kube-prometheus-stack \
  --namespace monitoring \
  --create-namespace \
  --values config/prometheus/values.yaml
```

### 2. Configure Prometheus

```bash
# Apply custom alert rules
kubectl create configmap prometheus-alert-rules \
  --from-file=config/prometheus/alert-rules.yml \
  -n monitoring

# Update Prometheus to load custom rules
kubectl edit prometheus prometheus-kube-prometheus-prometheus -n monitoring
```

Add under `spec`:
```yaml
spec:
  ruleSelector:
    matchLabels:
      prometheus: kube-prometheus
```

### 3. Configure Alertmanager

```bash
# Create secret with notification credentials
kubectl create secret generic alertmanager-secrets \
  --from-literal=slack-webhook-url='https://hooks.slack.com/services/YOUR/WEBHOOK/URL' \
  --from-literal=pagerduty-service-key='YOUR_PAGERDUTY_KEY' \
  --from-literal=smtp-password='YOUR_SMTP_PASSWORD' \
  -n monitoring

# Apply Alertmanager config
kubectl create configmap alertmanager-config \
  --from-file=config/prometheus/alertmanager-config.yml \
  -n monitoring
```

### 4. Import Grafana Dashboards

```bash
# Port-forward to Grafana
kubectl port-forward -n monitoring svc/prometheus-grafana 3000:80

# Open browser: http://localhost:3000
# Default credentials: admin / prom-operator

# Import dashboards:
# 1. Go to Dashboards → Import
# 2. Upload JSON files from grafana/dashboards/
#    - api-dashboard.json
#    - infrastructure-dashboard.json
#    - business-metrics-dashboard.json
```

### 5. Verify Setup

```bash
# Check Prometheus targets
kubectl port-forward -n monitoring svc/prometheus-kube-prometheus-prometheus 9090:9090
# Open: http://localhost:9090/targets

# Check Alertmanager
kubectl port-forward -n monitoring svc/prometheus-kube-prometheus-alertmanager 9093:9093
# Open: http://localhost:9093
```

---

## 📁 File Structure

```
config/prometheus/
├── alert-rules.yml          # Prometheus alert definitions
├── alertmanager-config.yml  # Alertmanager routing config
└── values.yaml              # Helm chart values

grafana/dashboards/
├── api-dashboard.json              # API performance metrics
├── infrastructure-dashboard.json   # K8s & system metrics
└── business-metrics-dashboard.json # Business KPIs
```

---

## 📈 Dashboards

### 1. API Performance Dashboard

**Metrics:**
- Request rate by endpoint and method
- P50, P95, P99 latency
- Error rate (4xx, 5xx)
- Response size distribution

**Panels:**
- API Request Rate (time series)
- P95 Request Latency (time series)
- API Error Rate (time series)

**Use Cases:**
- Monitor API health
- Detect performance degradation
- Identify problematic endpoints

### 2. Infrastructure Dashboard

**Metrics:**
- Running pods count
- CPU usage per pod
- Memory usage per pod
- Network I/O
- Pod replica status
- Database connection pool
- Cache hit rate

**Panels:**
- Pod status (stat)
- Average CPU/Memory usage (stat)
- CPU usage by pod (time series)
- Memory usage by pod (time series)
- Network I/O (time series)
- Database connections (time series)
- Cache performance (time series)

**Use Cases:**
- Monitor infrastructure health
- Detect resource constraints
- Plan capacity upgrades

### 3. Business Metrics Dashboard

**Metrics:**
- Total capsules created
- Capsule creation rate
- Active users (24h)
- Capsule failure rate
- Capsule creation by platform
- Capsule creation by type
- WebAuthn activity
- Mobile API usage
- Top users by capsule count
- Hourly usage patterns

**Panels:**
- Total capsules (stat)
- Creation rate (stat)
- Active users (stat)
- Failure rate (stat)
- Platform breakdown (time series)
- Type breakdown (time series)
- WebAuthn activity (time series)
- Mobile endpoint usage (time series)
- Top users (table)
- Hourly patterns (bar chart)

**Use Cases:**
- Track business KPIs
- Identify usage trends
- Monitor user engagement
- Detect anomalies in user behavior

---

## 🚨 Alert Rules

### Application Health Alerts

| Alert | Threshold | Severity | Notification |
|-------|-----------|----------|--------------|
| HighErrorRate | > 1% for 5m | Critical | PagerDuty + Slack |
| HighLatency | P95 > 1s for 10m | Warning | Slack |
| ServiceDown | Down for 1m | Critical | PagerDuty + Slack + Email |
| HighMemoryUsage | > 90% for 5m | Warning | Slack |
| HighCPUUsage | > 90% for 10m | Warning | Slack |

### Database Alerts

| Alert | Threshold | Severity | Notification |
|-------|-----------|----------|--------------|
| DatabaseConnectionPoolExhausted | Active >= 18 for 5m | Critical | PagerDuty + Slack |
| DatabaseHighLatency | P95 > 0.5s for 10m | Warning | Slack |
| DatabaseDown | Down for 1m | Critical | PagerDuty + Email |

### Cache Alerts

| Alert | Threshold | Severity | Notification |
|-------|-----------|----------|--------------|
| LowCacheHitRate | < 70% for 15m | Warning | Slack |
| RedisDown | Down for 1m | Critical | PagerDuty + Slack |

### Kubernetes Alerts

| Alert | Threshold | Severity | Notification |
|-------|-----------|----------|--------------|
| PodCrashLooping | Restarts > 0 for 5m | Critical | PagerDuty + Slack |
| PodNotReady | Not running for 5m | Warning | Slack |
| DeploymentReplicasMismatch | Mismatch for 10m | Warning | Slack |
| HPAMaxedOut | At max replicas for 15m | Warning | Slack + Email |

### Business Alerts

| Alert | Threshold | Severity | Notification |
|-------|-----------|----------|--------------|
| CapsuleCreationDropped | > 50% drop for 10m | Warning | Slack + Email |
| HighCapsuleVerificationFailureRate | > 5% for 10m | Critical | PagerDuty + Slack |
| NoRecentCapsuleCreation | 0 for 15m | Warning | Slack |

### Security Alerts

| Alert | Threshold | Severity | Notification |
|-------|-----------|----------|--------------|
| CertificateExpiringSoon | < 30 days | Warning | Slack + Email |
| CertificateExpired | Expired | Critical | PagerDuty + Slack + Email |
| HighWebAuthnFailureRate | > 10% for 10m | Warning | Slack |

---

## 🔔 Notification Channels

### Slack

**Channels:**
- `#uatp-critical-alerts` - Critical alerts (PagerDuty incidents)
- `#uatp-warnings` - Warning-level alerts
- `#uatp-business-metrics` - Business metric alerts
- `#uatp-database` - Database-specific alerts
- `#uatp-security` - Security and authentication alerts

**Configuration:**
1. Create Slack app and incoming webhook
2. Set webhook URL in alertmanager secret:
   ```bash
   kubectl create secret generic alertmanager-secrets \
     --from-literal=slack-webhook-url='https://hooks.slack.com/services/...' \
     -n monitoring
   ```

### PagerDuty

**Integration Keys:**
- **Critical Incidents** - `PAGERDUTY_SERVICE_KEY`
- **Database Incidents** - `PAGERDUTY_DATABASE_KEY`
- **Security Incidents** - `PAGERDUTY_SECURITY_KEY`

**Configuration:**
1. Create PagerDuty services
2. Get integration keys
3. Add to alertmanager secret:
   ```bash
   kubectl create secret generic alertmanager-secrets \
     --from-literal=pagerduty-service-key='YOUR_KEY' \
     -n monitoring
   ```

### Email

**Recipients:**
- **Critical** - `oncall@uatp.app`, `engineering-leads@uatp.app`
- **Warning** - `ops@uatp.app`
- **Business** - `business-team@uatp.app`, `product@uatp.app`
- **Database** - `dba@uatp.app`
- **Security** - `security@uatp.app`, `ciso@uatp.app`

**SMTP Configuration:**
```bash
kubectl create secret generic alertmanager-secrets \
  --from-literal=smtp-password='YOUR_SMTP_PASSWORD' \
  -n monitoring
```

---

## 🔍 Querying Metrics

### Useful PromQL Queries

**Request rate:**
```promql
sum(rate(uatp_requests_total[5m])) by (endpoint, method)
```

**Error rate:**
```promql
sum(rate(uatp_requests_failed_total[5m])) / sum(rate(uatp_requests_total[5m]))
```

**P95 latency:**
```promql
histogram_quantile(0.95, sum(rate(uatp_request_latency_seconds_bucket[5m])) by (le, endpoint))
```

**Capsule creation rate:**
```promql
sum(rate(uatp_capsules_created_total[5m])) by (platform)
```

**Database connection pool usage:**
```promql
uatp_database_connections_active / (uatp_database_connections_active + uatp_database_connections_idle)
```

**Cache hit rate:**
```promql
sum(rate(uatp_cache_hits_total[5m])) / (sum(rate(uatp_cache_hits_total[5m])) + sum(rate(uatp_cache_misses_total[5m])))
```

---

## 🧪 Testing Alerts

### Trigger Test Alerts

**High error rate:**
```bash
# Generate 500 errors
for i in {1..500}; do
  curl https://api.uatp.app/nonexistent-endpoint
done
```

**High latency:**
```bash
# Stress test endpoint
ab -n 10000 -c 100 https://api.uatp.app/api/v1/capsules
```

**Service down:**
```bash
# Scale deployment to 0
kubectl scale deployment uatp-api --replicas=0 -n uatp-production

# Wait 2 minutes for alert

# Scale back up
kubectl scale deployment uatp-api --replicas=3 -n uatp-production
```

**Memory pressure:**
```bash
# Reduce memory limits temporarily
kubectl set resources deployment uatp-api --limits=memory=128Mi -n uatp-production
```

---

## 📊 Metrics Reference

### Application Metrics

| Metric | Type | Description |
|--------|------|-------------|
| `uatp_requests_total` | Counter | Total HTTP requests |
| `uatp_requests_failed_total` | Counter | Failed HTTP requests (5xx) |
| `uatp_request_latency_seconds` | Histogram | Request latency |
| `uatp_capsules_created_total` | Counter | Total capsules created |
| `uatp_capsules_total` | Gauge | Current total capsules |
| `uatp_capsule_verification_failed_total` | Counter | Failed capsule verifications |
| `uatp_webauthn_registrations_total` | Counter | WebAuthn registrations |
| `uatp_webauthn_authentications_total` | Counter | WebAuthn authentications |
| `uatp_webauthn_authentication_failed_total` | Counter | Failed WebAuthn auths |
| `uatp_mobile_api_requests_total` | Counter | Mobile API requests |
| `uatp_mobile_sync_requests_total` | Counter | Mobile sync requests |
| `uatp_mobile_sync_failed_total` | Counter | Failed mobile syncs |
| `uatp_mobile_offline_queue_size` | Gauge | Mobile offline queue size |

### Database Metrics

| Metric | Type | Description |
|--------|------|-------------|
| `uatp_database_connections_active` | Gauge | Active DB connections |
| `uatp_database_connections_idle` | Gauge | Idle DB connections |
| `uatp_database_query_duration_seconds` | Histogram | Query execution time |

### Cache Metrics

| Metric | Type | Description |
|--------|------|-------------|
| `uatp_cache_hits_total` | Counter | Cache hits |
| `uatp_cache_misses_total` | Counter | Cache misses |

---

## 🔧 Advanced Configuration

### Custom Metrics

**Add custom metric in Python:**
```python
from prometheus_client import Counter, Histogram

# Counter
insurance_claims_total = Counter(
    'uatp_insurance_claims_total',
    'Total insurance claims filed',
    ['claim_type', 'status']
)

insurance_claims_total.labels(claim_type='ai_failure', status='approved').inc()

# Histogram
risk_assessment_duration = Histogram(
    'uatp_risk_assessment_duration_seconds',
    'Risk assessment processing time',
    buckets=[0.1, 0.5, 1.0, 2.0, 5.0]
)

with risk_assessment_duration.time():
    perform_risk_assessment()
```

### Log Aggregation with Loki

```bash
# Install Loki
helm install loki grafana/loki-stack \
  --namespace monitoring \
  --set grafana.enabled=false \
  --set promtail.enabled=true

# Configure Grafana data source
# Add Loki: http://loki:3100
```

### Distributed Tracing with Jaeger

```bash
# Install Jaeger operator
kubectl create namespace observability
kubectl apply -f https://github.com/jaegertracing/jaeger-operator/releases/latest/download/jaeger-operator.yaml -n observability

# Deploy Jaeger instance
kubectl apply -f config/jaeger/jaeger-instance.yaml
```

---

## 📚 Resources

**Prometheus:**
- [Prometheus Query Basics](https://prometheus.io/docs/prometheus/latest/querying/basics/)
- [PromQL Examples](https://prometheus.io/docs/prometheus/latest/querying/examples/)

**Grafana:**
- [Dashboard Best Practices](https://grafana.com/docs/grafana/latest/dashboards/build-dashboards/best-practices/)
- [Panel Types](https://grafana.com/docs/grafana/latest/panels-visualizations/)

**Alertmanager:**
- [Alerting Rules](https://prometheus.io/docs/prometheus/latest/configuration/alerting_rules/)
- [Notification Templates](https://prometheus.io/docs/alerting/latest/notifications/)

---

## 🆘 Troubleshooting

### Prometheus not scraping targets

```bash
# Check service monitor
kubectl get servicemonitor -n uatp-production

# Check Prometheus config
kubectl get prometheus prometheus-kube-prometheus-prometheus -n monitoring -o yaml

# View Prometheus logs
kubectl logs -n monitoring -l app=prometheus
```

### Alerts not firing

```bash
# Check alert rules loaded
kubectl get prometheusrules -n monitoring

# Verify Alertmanager config
kubectl get secret alertmanager-prometheus-kube-prometheus-alertmanager -n monitoring -o yaml
```

### Grafana can't connect to Prometheus

```bash
# Check data source configuration
# Grafana → Configuration → Data Sources
# URL should be: http://prometheus-kube-prometheus-prometheus:9090
```

---

**Last Updated:** 2025-01-06
**Version:** 1.0.0
**Owner:** UATP DevOps Team
