# UATP OpenTelemetry Operations Runbook

## Quick Reference

### Emergency Contacts
- **On-Call Engineer**: +1-XXX-XXX-XXXX
- **Platform Team**: platform-team@uatp.ai
- **Escalation Manager**: escalation@uatp.ai

### Critical Services Status Page
- **Status Dashboard**: https://status.uatp.ai
- **Grafana**: https://grafana.uatp.local
- **Jaeger**: https://jaeger.uatp.local

## Alert Response Procedures

### P0 - Critical Service Down

#### Alert: UATPServiceDown
**Trigger**: `up{service_name="uatp-capsule-engine"} == 0`

**Immediate Actions (< 2 minutes):**
1. Check service status:
   ```bash
   kubectl get pods -n uatp-prod -l app=uatp-api
   ```

2. Check recent deployments:
   ```bash
   kubectl rollout history deployment/uatp-api -n uatp-prod
   ```

3. If recent deployment, consider immediate rollback:
   ```bash
   kubectl rollout undo deployment/uatp-api -n uatp-prod
   ```

**Investigation Steps:**
1. Check pod logs:
   ```bash
   kubectl logs -l app=uatp-api -n uatp-prod --tail=100
   ```

2. Check events:
   ```bash
   kubectl get events -n uatp-prod --sort-by=.metadata.creationTimestamp
   ```

3. Check resource constraints:
   ```bash
   kubectl describe pods -l app=uatp-api -n uatp-prod
   ```

**Resolution:**
- If OOMKilled: Increase memory limits
- If CrashLoopBackOff: Check application logs for startup errors
- If ImagePullError: Verify image availability

#### Alert: UATPCriticalErrorRate
**Trigger**: `(rate(uatp_http_errors_total[5m]) / rate(uatp_http_requests_total[5m])) * 100 > 15`

**Immediate Actions:**
1. Check error distribution:
   ```bash
   # Port forward to access metrics
   kubectl port-forward svc/uatp-api-service 9090:9090 -n uatp-prod
   # Query: rate(uatp_http_errors_total[5m]) by (status_code, endpoint)
   ```

2. Check trace errors in Jaeger:
   - Navigate to Jaeger UI
   - Filter by service: `uatp-capsule-engine`
   - Look for error traces (red indicators)

3. Examine recent changes:
   ```bash
   kubectl rollout history deployment/uatp-api -n uatp-prod
   ```

**Investigation:**
- Correlate errors with specific endpoints
- Check database connectivity
- Verify external service dependencies
- Review recent configuration changes

### P1 - Performance Degradation

#### Alert: UATPCriticalLatency
**Trigger**: `histogram_quantile(0.95, rate(uatp_http_request_duration_seconds_bucket[5m])) > 2.0`

**Immediate Actions:**
1. Check current load:
   ```bash
   kubectl top pods -n uatp-prod
   ```

2. Check HPA status:
   ```bash
   kubectl get hpa -n uatp-prod
   ```

3. Scale if needed:
   ```bash
   kubectl scale deployment uatp-api --replicas=10 -n uatp-prod
   ```

**Investigation:**
1. Identify slow endpoints:
   ```bash
   # Check Grafana dashboard: "UATP OpenTelemetry Overview"
   # Look at request duration by endpoint
   ```

2. Examine slow traces:
   - Use Jaeger to find traces > 2s
   - Identify bottleneck services/operations

3. Check resource utilization:
   ```bash
   kubectl top nodes
   kubectl describe nodes
   ```

#### Alert: UATPDatabaseConnectionPoolExhaustion
**Trigger**: `uatp_database_connections_active > 80`

**Immediate Actions:**
1. Check database status:
   ```bash
   kubectl get pods -l app=postgresql -n uatp-prod
   ```

2. Check connection pool settings:
   ```bash
   kubectl get configmap uatp-config -n uatp-prod -o yaml | grep -i pool
   ```

3. Restart application pods if necessary:
   ```bash
   kubectl rollout restart deployment/uatp-api -n uatp-prod
   ```

**Investigation:**
- Review database slow query logs
- Check for connection leaks in application
- Monitor database performance metrics

## Observability Component Issues

### OpenTelemetry Collector Problems

#### Alert: UATPOtelCollectorDown
**Immediate Actions:**
1. Check collector status:
   ```bash
   kubectl get pods -l app.kubernetes.io/name=uatp-otel-collector -n uatp-prod
   ```

2. Check collector logs:
   ```bash
   kubectl logs -l app.kubernetes.io/name=uatp-otel-collector -n uatp-prod
   ```

3. Restart if needed:
   ```bash
   kubectl rollout restart deployment/uatp-otel-collector -n uatp-prod
   ```

#### High Memory Usage in Collector
**Symptoms**: OOMKilled collector pods

**Actions:**
1. Check current resource usage:
   ```bash
   kubectl top pods -l app.kubernetes.io/name=uatp-otel-collector -n uatp-prod
   ```

2. Scale collector:
   ```bash
   kubectl scale deployment uatp-otel-collector --replicas=3 -n uatp-prod
   ```

3. Adjust batch processor settings:
   ```yaml
   # Edit collector config to reduce batch size
   processors:
     batch:
       send_batch_size: 512  # Reduce from 1024
       timeout: 500ms        # Reduce from 1s
   ```

### Jaeger Issues

#### Jaeger UI Inaccessible
**Actions:**
1. Check Jaeger pods:
   ```bash
   kubectl get pods -n observability -l app=jaeger
   ```

2. Check ingress:
   ```bash
   kubectl get ingress -n observability
   ```

3. Port forward for direct access:
   ```bash
   kubectl port-forward svc/jaeger-query 16686:16686 -n observability
   ```

#### Missing Traces
**Investigation:**
1. Check trace volume:
   ```bash
   # In Prometheus: rate(traces_received_total[5m])
   ```

2. Verify collector-Jaeger connection:
   ```bash
   kubectl logs -l app.kubernetes.io/name=uatp-otel-collector -n uatp-prod | grep -i jaeger
   ```

3. Check sampling rate:
   ```bash
   kubectl get instrumentation uatp-auto-instrumentation -n uatp-prod -o yaml
   ```

## Business Logic Monitoring

### Capsule Operation Issues

#### Alert: UATPCapsuleCreationFailures
**Investigation:**
1. Check capsule creation error logs:
   ```bash
   kubectl logs -l app=uatp-api -n uatp-prod | grep -i "capsule.*error"
   ```

2. Review failed capsule traces:
   - Search Jaeger for `operation.type:capsule_create` with errors

3. Check database constraints:
   ```bash
   # Connect to database and check constraints
   kubectl exec -it postgresql-primary -n uatp-prod -- psql -U uatp -d uatp_prod
   ```

#### Alert: UATPAttributionTrackingFailures
**Investigation:**
1. Check attribution system logs:
   ```bash
   kubectl logs -l app=uatp-api -n uatp-prod | grep -i "attribution.*fail"
   ```

2. Verify attribution chain integrity:
   - Use custom dashboard to check chain completeness

3. Check external service dependencies:
   ```bash
   # Test API connectivity to attribution services
   kubectl run test-pod --image=curlimages/curl --rm -it -- \
     curl -I http://attribution-service/health
   ```

### Economic System Issues

#### Alert: UATPEconomicCalculationFailures
**High Priority - Financial Impact**

**Immediate Actions:**
1. Check economic calculation errors:
   ```bash
   kubectl logs -l app=uatp-api -n uatp-prod | grep -i "economic.*error"
   ```

2. Verify calculation service status:
   ```bash
   kubectl get pods -l component=economic-engine -n uatp-prod
   ```

3. Check for data integrity issues:
   ```bash
   # Review economic calculation traces in Jaeger
   # Look for failed economic operations
   ```

**Escalation**: Always escalate economic system failures to finance team

## Maintenance Procedures

### Planned Maintenance

#### Updating OpenTelemetry Collector
1. **Preparation:**
   ```bash
   # Backup current configuration
   kubectl get configmap otel-collector-config -n uatp-prod -o yaml > otel-config-backup.yaml
   
   # Check current version
   kubectl get pods -l app.kubernetes.io/name=uatp-otel-collector -n uatp-prod -o jsonpath='{.items[0].spec.containers[0].image}'
   ```

2. **Update:**
   ```bash
   # Update collector image
   kubectl set image deployment/uatp-otel-collector \
     otel-collector=otel/opentelemetry-collector-contrib:0.89.0 \
     -n uatp-prod
   
   # Monitor rollout
   kubectl rollout status deployment/uatp-otel-collector -n uatp-prod
   ```

3. **Validation:**
   ```bash
   # Check collector health
   kubectl get pods -l app.kubernetes.io/name=uatp-otel-collector -n uatp-prod
   
   # Verify data flow
   kubectl logs -l app.kubernetes.io/name=uatp-otel-collector -n uatp-prod --tail=50
   ```

#### Updating UATP Application
1. **Pre-deployment:**
   ```bash
   # Check current observability status
   curl http://uatp-api-service:8080/health/observability
   
   # Verify dashboards are functional
   # Check recent alert history
   ```

2. **Deployment:**
   ```bash
   # Deploy with monitoring
   kubectl apply -f uatp-deployment-otel.yaml
   kubectl rollout status deployment/uatp-api -n uatp-prod
   
   # Monitor metrics during rollout
   watch 'kubectl get pods -n uatp-prod -l app=uatp-api'
   ```

3. **Post-deployment:**
   ```bash
   # Verify observability features
   kubectl logs -l app=uatp-api -n uatp-prod --tail=10 | grep -i "observability.*initialized"
   
   # Check trace generation
   # Verify new metrics are being emitted
   ```

### Configuration Changes

#### Updating Collector Configuration
```bash
# Edit configuration
kubectl edit configmap otel-collector-config -n uatp-prod

# Restart collector to apply changes
kubectl rollout restart deployment/uatp-otel-collector -n uatp-prod

# Verify configuration is valid
kubectl logs -l app.kubernetes.io/name=uatp-otel-collector -n uatp-prod | grep -i "config.*loaded"
```

#### Updating Sampling Rates
```bash
# Update instrumentation configuration
kubectl edit instrumentation uatp-auto-instrumentation -n uatp-prod

# Restart application pods to apply new instrumentation
kubectl rollout restart deployment/uatp-api -n uatp-prod
```

## Performance Tuning

### Optimizing Collector Performance

#### Memory Optimization
```yaml
processors:
  memory_limiter:
    limit_mib: 1800    # Adjust based on available memory
    spike_limit_mib: 400
  
  batch:
    timeout: 1s
    send_batch_size: 1024      # Tune based on throughput
    send_batch_max_size: 2048
```

#### CPU Optimization
```yaml
service:
  telemetry:
    metrics:
      level: basic  # Reduce from detailed for lower CPU usage
```

### Optimizing Application Performance

#### Sampling Configuration
```yaml
# For high-traffic production
sampler:
  type: parentbased_traceidratio
  argument: "0.01"  # 1% sampling for very high traffic

# For specific operations
sampler:
  type: jaeger_remote
  jaeger_remote:
    endpoint: http://jaeger-agent:5778/sampling
```

#### Resource Tuning
```yaml
resources:
  requests:
    cpu: 500m
    memory: 1Gi
  limits:
    cpu: 2000m
    memory: 2Gi
```

## Capacity Planning

### Monitoring Growth
Track these metrics for capacity planning:

1. **Request Volume**: `rate(uatp_http_requests_total[1h])`
2. **Trace Volume**: `rate(traces_received_total[1h])`
3. **Resource Usage**: CPU/Memory trends over time
4. **Storage Growth**: Jaeger storage usage

### Scaling Guidelines

#### Horizontal Scaling Triggers
- CPU usage > 70% for 10 minutes
- Memory usage > 80% for 5 minutes
- Request queue depth > 100

#### Vertical Scaling Triggers
- Consistent CPU usage > 80%
- Memory usage approaching limits
- GC pressure indicators

## Security Considerations

### Sensitive Data Handling
- Ensure no PII in traces
- Sanitize log messages
- Use secure communication (TLS)

### Access Control
- Restrict Jaeger UI access
- Monitor configuration changes
- Audit observability access

## Disaster Recovery

### Backup Procedures
```bash
# Backup collector configuration
kubectl get configmap otel-collector-config -n uatp-prod -o yaml > collector-config-backup.yaml

# Backup instrumentation settings
kubectl get instrumentation -n uatp-prod -o yaml > instrumentation-backup.yaml

# Backup Grafana dashboards
kubectl get configmap -l grafana_dashboard=1 -n uatp-prod -o yaml > grafana-dashboards-backup.yaml
```

### Recovery Procedures
```bash
# Restore from backup
kubectl apply -f collector-config-backup.yaml
kubectl apply -f instrumentation-backup.yaml
kubectl apply -f grafana-dashboards-backup.yaml

# Restart affected components
kubectl rollout restart deployment/uatp-otel-collector -n uatp-prod
kubectl rollout restart deployment/uatp-api -n uatp-prod
```

---

## Appendix: Useful Queries

### Prometheus Queries
```promql
# Error rate by endpoint
rate(uatp_http_errors_total[5m]) / rate(uatp_http_requests_total[5m]) * 100

# 95th percentile latency
histogram_quantile(0.95, rate(uatp_http_request_duration_seconds_bucket[5m]))

# Active capsule count trend
uatp_active_capsules

# Database connection utilization
uatp_database_connections_active / uatp_database_connections_max * 100
```

### Jaeger Queries
```
# Find slow operations
operation:"uatp.capsule.create" duration:>5s

# Find error traces
error=true service="uatp-capsule-engine"

# Find traces for specific user
tags:"user_id:12345"

# Find attribution traces
operation:"uatp.capsule.attribution_track"
```

### LogQL Queries (if using Loki)
```logql
{service_name="uatp-capsule-engine"} |= "ERROR"

{service_name="uatp-capsule-engine"} | json | operation_type="capsule_operation"

{service_name="uatp-capsule-engine"} | json | level="ERROR" | line_format "{{.timestamp}} {{.message}}"
```