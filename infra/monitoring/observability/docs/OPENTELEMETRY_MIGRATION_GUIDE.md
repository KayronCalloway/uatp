# OpenTelemetry Migration Guide for UATP Production

## Overview

This guide provides comprehensive instructions for migrating from the legacy Prometheus-based monitoring to modern OpenTelemetry observability for the UATP Capsule Engine production environment.

## Table of Contents

1. [Pre-Migration Checklist](#pre-migration-checklist)
2. [Architecture Overview](#architecture-overview)
3. [Deployment Instructions](#deployment-instructions)
4. [Configuration Management](#configuration-management)
5. [Monitoring and Alerting](#monitoring-and-alerting)
6. [Troubleshooting](#troubleshooting)
7. [Rollback Procedures](#rollback-procedures)

## Pre-Migration Checklist

### Infrastructure Requirements

- [ ] Kubernetes cluster v1.20+ with sufficient resources
- [ ] OpenTelemetry Operator v0.88.0+ installed
- [ ] Helm v3.0+ for package management
- [ ] kubectl access with cluster-admin privileges
- [ ] Persistent storage for trace and metric data

### Resource Allocation

| Component | CPU | Memory | Storage |
|-----------|-----|--------|---------|
| OpenTelemetry Collector | 1000m | 2Gi | - |
| Jaeger All-in-One | 200m | 512Mi | 10Gi |
| Updated UATP API | 2000m | 2Gi | 4Gi |

### Network Requirements

- [ ] Ingress controller configured
- [ ] DNS resolution for observability endpoints
- [ ] Firewall rules for OTLP (4317/4318), Jaeger (16686), Prometheus (8889)

## Architecture Overview

### Components

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   UATP API      │    │ OpenTelemetry   │    │   Backends      │
│   (Instrumented)│───▶│   Collector     │───▶│ - Prometheus    │
│                 │    │                 │    │ - Jaeger        │
└─────────────────┘    └─────────────────┘    │ - Grafana       │
                                              └─────────────────┘
```

### Data Flow

1. **Application Layer**: UATP services emit telemetry via OpenTelemetry SDK
2. **Collection Layer**: OpenTelemetry Collector receives, processes, and exports data
3. **Storage Layer**: Prometheus (metrics), Jaeger (traces), Elasticsearch (logs)
4. **Visualization Layer**: Grafana dashboards and Jaeger UI

## Deployment Instructions

### Step 1: Deploy OpenTelemetry Operator

```bash
# Apply the OpenTelemetry Operator
kubectl apply -f observability/kubernetes/otel-operator.yaml

# Verify operator is running
kubectl get pods -n opentelemetry-operator-system
```

### Step 2: Deploy OpenTelemetry Collector

```bash
# Create observability namespace
kubectl create namespace observability

# Deploy the collector
kubectl apply -f observability/kubernetes/otel-collector.yaml

# Verify collector is running
kubectl get pods -n uatp-prod -l app=uatp-otel-collector
```

### Step 3: Deploy Jaeger

```bash
# Deploy Jaeger for distributed tracing
kubectl apply -f observability/kubernetes/jaeger-deployment.yaml

# Verify Jaeger is running
kubectl get pods -n observability -l app=jaeger
```

### Step 4: Configure Auto-Instrumentation

```bash
# Apply auto-instrumentation configuration
kubectl apply -f observability/kubernetes/auto-instrumentation.yaml

# Verify instrumentation resource
kubectl get instrumentation -n uatp-prod
```

### Step 5: Update UATP Deployment

```bash
# Deploy updated UATP API with OpenTelemetry
kubectl apply -f observability/kubernetes/uatp-deployment-otel.yaml

# Monitor rollout
kubectl rollout status deployment/uatp-api -n uatp-prod
```

### Step 6: Update Monitoring Stack

```bash
# Update Grafana dashboards
kubectl create configmap grafana-otel-dashboards \
  --from-file=observability/grafana/dashboards/ \
  -n uatp-prod

# Apply new alerting rules
kubectl apply -f observability/alerting/otel-alerting-rules.yaml
```

## Configuration Management

### Environment Variables

Key environment variables for OpenTelemetry configuration:

```yaml
env:
  # OpenTelemetry Core
  - name: OTEL_SERVICE_NAME
    value: "uatp-capsule-engine"
  - name: OTEL_SERVICE_VERSION
    value: "7.0.0"
  - name: OTEL_DEPLOYMENT_ENVIRONMENT
    value: "production"

  # Exporters
  - name: OTEL_EXPORTER_OTLP_ENDPOINT
    value: "http://uatp-otel-collector:4317"
  - name: OTEL_EXPORTER_OTLP_PROTOCOL
    value: "grpc"

  # Sampling
  - name: OTEL_TRACES_SAMPLER
    value: "parentbased_traceidratio"
  - name: OTEL_TRACES_SAMPLER_ARG
    value: "0.1"  # 10% sampling

  # Propagation
  - name: OTEL_PROPAGATORS
    value: "tracecontext,baggage,b3,jaeger"
```

### Collector Configuration

The OpenTelemetry Collector configuration includes:

- **Receivers**: OTLP, Prometheus, Jaeger, Kubernetes
- **Processors**: Memory limiter, batch, resource attribution, sampling
- **Exporters**: Prometheus, Jaeger, logging, cloud backends

### Resource Limits

```yaml
resources:
  requests:
    cpu: 500m
    memory: 1Gi
  limits:
    cpu: 1000m
    memory: 2Gi
```

## Monitoring and Alerting

### Key Metrics to Monitor

#### Application Metrics
- `uatp_http_requests_total` - HTTP request count
- `uatp_http_request_duration_seconds` - Request latency
- `uatp_capsule_operations_total` - Capsule operation count
- `uatp_attribution_tracks_total` - Attribution tracking
- `uatp_active_capsules` - Active capsule count

#### Infrastructure Metrics
- `uatp_memory_usage_bytes` - Memory usage
- `uatp_database_connections_active` - DB connections
- `up{service_name="uatp-capsule-engine"}` - Service health

#### Tracing Metrics
- `traces_received_total` - Trace volume
- `spans_received_total` - Span count
- `traces_dropped_total` - Dropped traces

### Critical Alerts

1. **Service Down**: `up{service_name="uatp-capsule-engine"} == 0`
2. **High Latency**: `histogram_quantile(0.95, rate(uatp_http_request_duration_seconds_bucket[5m])) > 0.5`
3. **High Error Rate**: `rate(uatp_http_errors_total[5m]) / rate(uatp_http_requests_total[5m]) > 0.05`
4. **Memory Usage**: `uatp_memory_usage_bytes > 1.5e9`

### Dashboard Access

- **Grafana**: `https://grafana.uatp.local`
- **Jaeger**: `https://jaeger.uatp.local`
- **Prometheus**: `https://prometheus.uatp.local`

## Troubleshooting

### Common Issues

#### 1. Collector Not Receiving Data

**Symptoms**: No metrics/traces in backends
**Diagnosis**:
```bash
# Check collector logs
kubectl logs -l app.kubernetes.io/name=uatp-otel-collector -n uatp-prod

# Check collector metrics
kubectl port-forward svc/uatp-otel-collector 8888:8888 -n uatp-prod
curl http://localhost:8888/metrics
```

**Solutions**:
- Verify OTLP endpoint configuration
- Check network connectivity
- Validate collector configuration

#### 2. High Memory Usage

**Symptoms**: OOMKilled pods, high memory alerts
**Diagnosis**:
```bash
# Check resource usage
kubectl top pods -n uatp-prod

# Check collector memory usage
kubectl exec -it deployment/uatp-otel-collector -n uatp-prod -- \
  curl http://localhost:8888/metrics | grep memory
```

**Solutions**:
- Increase batch processor limits
- Adjust sampling rates
- Scale collector horizontally

#### 3. Missing Traces

**Symptoms**: Incomplete trace data in Jaeger
**Diagnosis**:
```bash
# Check sampling configuration
kubectl get instrumentation uatp-auto-instrumentation -n uatp-prod -o yaml

# Verify propagation headers
kubectl logs -l app=uatp-api -n uatp-prod | grep -i trace
```

**Solutions**:
- Increase sampling rate
- Check propagation configuration
- Verify trace context passing

#### 4. Dashboard Display Issues

**Symptoms**: Empty or incorrect dashboard data
**Diagnosis**:
```bash
# Test Prometheus queries
kubectl port-forward svc/prometheus-server 9090:9090 -n uatp-prod
# Navigate to http://localhost:9090 and test queries
```

**Solutions**:
- Update dashboard queries for new metric names
- Verify data source configuration
- Check metric label consistency

### Debug Commands

```bash
# Check all observability components
kubectl get pods -n uatp-prod -l component=observability
kubectl get pods -n observability

# View collector configuration
kubectl get opentelemetrycollector uatp-otel-collector -n uatp-prod -o yaml

# Check instrumentation
kubectl describe instrumentation uatp-auto-instrumentation -n uatp-prod

# Monitor live metrics
kubectl port-forward svc/uatp-otel-collector 8889:8889 -n uatp-prod
curl http://localhost:8889/metrics | grep uatp_

# View trace data
kubectl port-forward svc/jaeger-query 16686:16686 -n observability
# Navigate to http://localhost:16686
```

## Rollback Procedures

### Emergency Rollback

If critical issues occur, follow this rollback procedure:

#### 1. Revert to Previous Deployment

```bash
# Rollback UATP API deployment
kubectl rollout undo deployment/uatp-api -n uatp-prod

# Verify rollback
kubectl rollout status deployment/uatp-api -n uatp-prod
```

#### 2. Disable Auto-Instrumentation

```bash
# Remove instrumentation annotation
kubectl patch deployment uatp-api -n uatp-prod -p '{"spec":{"template":{"metadata":{"annotations":{"instrumentation.opentelemetry.io/inject-python":null}}}}}'
```

#### 3. Restore Legacy Monitoring

```bash
# Re-enable Prometheus scraping
kubectl apply -f k8s/monitoring.yaml

# Restore original Grafana dashboards
kubectl apply -f grafana/dashboards/
```

### Gradual Rollback

For non-critical issues, consider a gradual approach:

1. **Reduce Sampling Rate**: Lower trace sampling to reduce load
2. **Scale Resources**: Increase collector resources temporarily
3. **Selective Instrumentation**: Disable specific instrumentation components

## Migration Validation

### Post-Migration Checklist

- [ ] All services showing as healthy in dashboards
- [ ] Traces visible in Jaeger UI
- [ ] Metrics flowing to Prometheus
- [ ] Alerts firing correctly
- [ ] No increase in application errors
- [ ] Performance impact within acceptable limits

### Performance Validation

```bash
# Run performance tests
kubectl run perf-test --image=loadimpact/k6 --rm -it -- \
  run -u 100 -d 5m https://api.uatp.local/health

# Monitor during test
kubectl top pods -n uatp-prod
```

### Data Validation

```bash
# Verify metric continuity
# Compare pre/post migration metrics in Grafana

# Verify trace completeness
# Check trace completion rates in Jaeger

# Verify log correlation
# Ensure logs contain trace IDs
kubectl logs -l app=uatp-api -n uatp-prod | grep trace_id
```

## Support and Escalation

### Internal Contacts

- **Platform Team**: platform-team@uatp.ai
- **DevOps Team**: devops@uatp.ai
- **On-Call Engineer**: +1-XXX-XXX-XXXX

### External Resources

- **OpenTelemetry Documentation**: https://opentelemetry.io/docs/
- **Kubernetes Documentation**: https://kubernetes.io/docs/
- **Prometheus Documentation**: https://prometheus.io/docs/

### Monitoring During Migration

Monitor these metrics closely during and after migration:

1. **Application Performance**: Response times, error rates
2. **Resource Usage**: CPU, memory, network
3. **Data Completeness**: Metric/trace/log volume
4. **System Stability**: Pod restarts, OOM events

### Migration Timeline

- **Week 1**: Deploy OpenTelemetry infrastructure
- **Week 2**: Enable instrumentation with low sampling
- **Week 3**: Increase sampling, validate data quality
- **Week 4**: Full cutover, monitor for 1 week
- **Week 5**: Remove legacy monitoring if stable

---

## Appendix

### Useful Commands Reference

```bash
# Scale collector
kubectl scale deployment uatp-otel-collector --replicas=3 -n uatp-prod

# Update collector config
kubectl patch configmap otel-collector-config -n uatp-prod --patch-file config-patch.yaml

# Force pod recreation (after config changes)
kubectl rollout restart deployment/uatp-otel-collector -n uatp-prod

# Export traces for analysis
kubectl exec -it deployment/jaeger -n observability -- \
  curl "http://localhost:16686/api/traces?service=uatp-capsule-engine"

# View real-time metrics
watch kubectl get --raw /apis/metrics.k8s.io/v1beta1/namespaces/uatp-prod/pods
```

This migration guide ensures a smooth transition to OpenTelemetry while maintaining production stability and observability coverage.
