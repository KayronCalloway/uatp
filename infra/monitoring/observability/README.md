# UATP OpenTelemetry Observability Stack

Status: experimental infrastructure support, not a production guarantee.

This directory contains OpenTelemetry collector, dashboard, alerting, and deployment materials for local/staging observability experiments around the UATP Capsule Engine. Treat it as an operations scaffold. It does not certify production readiness, compliance, uptime, trace coverage, or business KPI quality.

For current project status, see ../../../STATUS.md.

---

## What is here

```text
observability/
├── README.md
├── otel-collector-config.yaml
├── deployment/
│   └── deploy.sh
├── kubernetes/
│   ├── otel-operator.yaml
│   ├── otel-collector.yaml
│   ├── auto-instrumentation.yaml
│   ├── jaeger-deployment.yaml
│   └── uatp-deployment-otel.yaml
├── grafana/
│   └── dashboards/
│       ├── uatp-otel-overview.json
│       └── uatp-distributed-tracing.json
├── alerting/
│   └── otel-alerting-rules.yaml
└── docs/
    ├── OPENTELEMETRY_MIGRATION_GUIDE.md
    └── OPERATIONS_RUNBOOK.md
```

---

## Local/staging quick start

From `infra/monitoring`:

```bash
chmod +x observability/deployment/deploy.sh
./observability/deployment/deploy.sh
./observability/deployment/deploy.sh status
```

Review the scripts and manifests before pointing them at shared infrastructure.

---

## Core components

- OpenTelemetry Collector for telemetry routing
- Jaeger for traces
- Prometheus-compatible metrics export
- Grafana dashboards
- Kubernetes manifests for experimental deployment
- Alert rules for service and latency/error signals

---

## Configuration example

```bash
OTEL_SERVICE_NAME=uatp-capsule-engine
OTEL_SERVICE_VERSION=1.1.0
OTEL_DEPLOYMENT_ENVIRONMENT=staging
OTEL_EXPORTER_OTLP_ENDPOINT=http://uatp-otel-collector:4317
OTEL_EXPORTER_OTLP_PROTOCOL=grpc
OTEL_TRACES_SAMPLER=parentbased_traceidratio
OTEL_TRACES_SAMPLER_ARG=0.1
OTEL_PROPAGATORS=tracecontext,baggage,b3,jaeger
```

Use environment-specific values in real deployments. Do not treat this README as a production configuration source.

---

## Boundaries

This observability stack can help inspect runtime behavior. It does not replace UATP receipt verification.

Use signed receipt bundles when the question is:

- did this agent action happen;
- did this event chain change;
- did this artifact hash still match;
- did a trusted signer policy accept the signer;
- did trusted timestamp validation pass with explicit TSA anchors.

Use OpenTelemetry when the question is operational:

- how long did a request take;
- where did a service fail;
- what is the error rate;
- which component is noisy.

Telemetry is useful, but it is not independent proof by itself.

---

## Related docs

- OPENTELEMETRY_MIGRATION_GUIDE.md
- OPERATIONS_RUNBOOK.md
- ../../../TRUST_MODEL.md
- ../../../docs/architecture/agent-receipt-verification.md
