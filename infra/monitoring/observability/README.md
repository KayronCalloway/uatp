# UATP OpenTelemetry Observability Stack

## Overview

This directory contains the complete OpenTelemetry observability implementation for the UATP Capsule Engine, providing comprehensive monitoring, distributed tracing, and structured logging capabilities for production deployment.

##  Quick Start

Deploy the complete observability stack:

```bash
# Make deployment script executable
chmod +x observability/deployment/deploy.sh

# Deploy everything
./observability/deployment/deploy.sh

# Check deployment status
./observability/deployment/deploy.sh status
```

##  Directory Structure

```
observability/
├── README.md                          # This file
├── otel-collector-config.yaml         # Main collector configuration
├── deployment/
│   └── deploy.sh                      # Automated deployment script
├── kubernetes/
│   ├── otel-operator.yaml             # OpenTelemetry Operator
│   ├── otel-collector.yaml            # Collector deployment
│   ├── auto-instrumentation.yaml     # Auto-instrumentation config
│   ├── jaeger-deployment.yaml        # Jaeger tracing backend
│   └── uatp-deployment-otel.yaml     # Updated UATP deployment
├── grafana/
│   └── dashboards/
│       ├── uatp-otel-overview.json   # Main overview dashboard
│       └── uatp-distributed-tracing.json # Tracing dashboard
├── alerting/
│   └── otel-alerting-rules.yaml      # Prometheus alerting rules
└── docs/
    ├── OPENTELEMETRY_MIGRATION_GUIDE.md # Complete migration guide
    ├── OPERATIONS_RUNBOOK.md           # Operations procedures
    └── ARCHITECTURE.md                 # Technical architecture
```

##  Architecture

### Components

1. **OpenTelemetry Collector**: Centralized telemetry hub
2. **Jaeger**: Distributed tracing backend
3. **Prometheus**: Metrics storage (compatible with existing setup)
4. **Grafana**: Visualization and dashboards
5. **Auto-Instrumentation**: Automatic code instrumentation

### Data Flow

```
UATP Services → OpenTelemetry SDK → Collector → Storage Backends → Visualization
```

##  Configuration

### Environment Variables

Key environment variables for OpenTelemetry:

```bash
# Service identification
OTEL_SERVICE_NAME=uatp-capsule-engine
OTEL_SERVICE_VERSION=7.0.0
OTEL_DEPLOYMENT_ENVIRONMENT=production

# Endpoints
OTEL_EXPORTER_OTLP_ENDPOINT=http://uatp-otel-collector:4317
OTEL_EXPORTER_OTLP_PROTOCOL=grpc

# Sampling
OTEL_TRACES_SAMPLER=parentbased_traceidratio
OTEL_TRACES_SAMPLER_ARG=0.1  # 10% sampling

# Propagation
OTEL_PROPAGATORS=tracecontext,baggage,b3,jaeger
```

### Collector Configuration

The collector processes telemetry through:

- **Receivers**: OTLP, Prometheus, Jaeger, Kubernetes
- **Processors**: Memory limiter, batch, resource, sampling
- **Exporters**: Prometheus, Jaeger, logging, cloud backends

##  Observability Features

### Distributed Tracing

- **Automatic instrumentation** for HTTP, database, cache operations
- **Custom business logic tracing** for capsule operations
- **Trace correlation** across services and requests
- **Performance analysis** with span timing and dependencies

### Metrics Collection

#### Application Metrics
- HTTP request rates, latency, errors
- Capsule operation metrics
- Attribution tracking metrics
- Economic calculation metrics
- Business KPIs (active capsules, trust scores)

#### Infrastructure Metrics
- Resource utilization (CPU, memory)
- Database connection pools
- Cache hit rates
- Kubernetes cluster metrics

### Structured Logging

- **JSON-formatted logs** with consistent structure
- **Trace correlation** with automatic trace ID injection
- **Business context** enrichment
- **Centralized log aggregation**

##  Monitoring & Alerting

### Critical Alerts

- **Service Down**: `UATPServiceDown`
- **High Error Rate**: `UATPCriticalErrorRate`
- **High Latency**: `UATPCriticalLatency`
- **Resource Exhaustion**: `UATPCriticalMemoryUsage`

### Business Logic Alerts

- **Capsule Creation Failures**: `UATPCapsuleCreationFailures`
- **Attribution Tracking Issues**: `UATPAttributionTrackingFailures`
- **Economic Calculation Errors**: `UATPEconomicCalculationFailures`

### Dashboards

1. **UATP OpenTelemetry Overview**: Main operational dashboard
2. **Distributed Tracing**: Trace analysis and service dependencies
3. **Business Metrics**: Capsule and attribution analytics

##  Security Considerations

- **PII Protection**: Automatic sanitization of sensitive data
- **Access Control**: RBAC for observability components
- **Secure Communication**: TLS for all telemetry data
- **Audit Logging**: Configuration change tracking

##  Performance Impact

### Resource Overhead

| Component | CPU Impact | Memory Impact |
|-----------|------------|---------------|
| OpenTelemetry SDK | ~2-5% | ~50-100MB |
| Auto-instrumentation | ~1-3% | ~20-50MB |
| Collector (per instance) | 500m CPU | 1GB Memory |

### Optimization

- **Sampling**: Configurable trace sampling (default 10%)
- **Batching**: Efficient telemetry batching
- **Filtering**: Noise reduction processors
- **Caching**: Intelligent resource caching

##  Production Deployment

### Prerequisites

- Kubernetes v1.20+
- OpenTelemetry Operator v0.88.0+
- Sufficient cluster resources
- Network connectivity for telemetry endpoints

### Deployment Steps

1. **Deploy Infrastructure**:
   ```bash
   ./observability/deployment/deploy.sh
   ```

2. **Validate Deployment**:
   ```bash
   ./observability/deployment/deploy.sh validate
   ```

3. **Configure External Integrations**:
   - Populate API keys in secrets
   - Configure ingress for external access
   - Set up alerting notification channels

4. **Monitor and Tune**:
   - Adjust sampling rates based on traffic
   - Scale collectors as needed
   - Optimize resource allocations

##  Documentation

- **[Migration Guide](docs/OPENTELEMETRY_MIGRATION_GUIDE.md)**: Complete migration instructions
- **[Operations Runbook](docs/OPERATIONS_RUNBOOK.md)**: Day-to-day operations procedures
- **[Architecture Guide](docs/ARCHITECTURE.md)**: Technical architecture details

##  Development Integration

### Using OpenTelemetry in Code

```python
from src.observability.integration import uatp_observability, observe_capsule_operation

# Initialize observability
uatp_observability.initialize()

# Use decorators for automatic instrumentation
@observe_capsule_operation("create")
async def create_capsule(capsule_data):
    # Your business logic here
    pass

# Manual instrumentation
with uatp_observability.trace_operation("custom_operation"):
    # Critical business logic
    pass
```

### Custom Metrics

```python
from src.observability.metrics import uatp_metrics

# Record business metrics
uatp_metrics.record_capsule_operation("create", "consent", success=True, duration=0.5)
uatp_metrics.record_trust_score(0.85, "user")
```

### Structured Logging

```python
from src.observability.logging import get_logger

logger = get_logger(__name__)
logger.info("Capsule created", extra={
    "capsule_id": "caps_123",
    "operation_type": "create",
    "user_id": "user_456"
})
```

##  Troubleshooting

### Common Issues

1. **Missing Traces**: Check sampling configuration and trace propagation
2. **High Memory Usage**: Adjust batch processor settings
3. **Collector Failures**: Verify configuration and network connectivity
4. **Dashboard Issues**: Update queries for new metric names

### Debug Commands

```bash
# Check collector status
kubectl logs -l app.kubernetes.io/name=uatp-otel-collector -n uatp-prod

# Test connectivity
kubectl port-forward svc/uatp-otel-collector 4317:4317 -n uatp-prod

# Verify instrumentation
kubectl get instrumentation -n uatp-prod -o yaml
```

##  Migration from Legacy Monitoring

The implementation provides backward compatibility during migration:

1. **Legacy Prometheus metrics** continue to work
2. **Gradual migration** with side-by-side operation
3. **Rollback procedures** for safety
4. **Data continuity** preservation

##  Scaling Considerations

### Horizontal Scaling

- **Collector scaling**: Multiple collector instances with load balancing
- **Backend scaling**: Separate backends for different data types
- **Regional deployment**: Multi-region observability

### Vertical Scaling

- **Resource allocation**: Tune CPU/memory based on throughput
- **Storage optimization**: Efficient data retention policies
- **Network optimization**: Compression and batching

##  Integration Capabilities

### Cloud Backends

- **Datadog**: Native OTLP export
- **New Relic**: Direct integration
- **Grafana Cloud**: Seamless connection
- **AWS X-Ray**: Trace export
- **Google Cloud Trace**: Native support

### Existing Tools

- **Prometheus**: Backward compatible metrics
- **Grafana**: Enhanced dashboards
- **AlertManager**: Integrated alerting
- **ELK Stack**: Log forwarding

##  Maintenance

### Regular Tasks

- **Update components** to latest versions
- **Review sampling rates** based on traffic patterns
- **Clean up old traces** according to retention policies
- **Monitor resource usage** and scale as needed

### Health Checks

- **Component health**: All observability services running
- **Data flow validation**: Telemetry reaching all backends
- **Performance monitoring**: Impact on application performance
- **Alert validation**: Ensure alerts fire correctly

##  Training Resources

- **OpenTelemetry Documentation**: https://opentelemetry.io/docs/
- **UATP Observability Training**: Internal training materials
- **Best Practices Guide**: Production observability patterns
- **Troubleshooting Guides**: Common issue resolution

---

##  Success Metrics

Post-deployment success indicators:

- [OK] **100% trace coverage** for critical business operations
- [OK] **<2% performance overhead** from observability
- [OK] **<5 minutes MTTR improvement** for production issues
- [OK] **Comprehensive business metrics** for attribution and economics
- [OK] **Automated alerting** for all critical scenarios

This OpenTelemetry implementation provides world-class observability for the UATP Capsule Engine, enabling proactive monitoring, rapid troubleshooting, and data-driven optimization of the production environment.
