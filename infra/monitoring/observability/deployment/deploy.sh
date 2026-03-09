#!/bin/bash

# UATP OpenTelemetry Deployment Script
# Deploys the complete OpenTelemetry observability stack for UATP

set -euo pipefail

# Configuration
NAMESPACE_PROD="uatp-prod"
NAMESPACE_OBSERVABILITY="observability"
NAMESPACE_OPERATOR="opentelemetry-operator-system"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check prerequisites
check_prerequisites() {
    log_info "Checking prerequisites..."

    # Check kubectl
    if ! command -v kubectl &> /dev/null; then
        log_error "kubectl is not installed or not in PATH"
        exit 1
    fi

    # Check cluster connectivity
    if ! kubectl cluster-info &> /dev/null; then
        log_error "Cannot connect to Kubernetes cluster"
        exit 1
    fi

    # Check if running as the right user
    current_context=$(kubectl config current-context)
    log_info "Current kubectl context: $current_context"

    # Verify cluster-admin permissions
    if ! kubectl auth can-i create clusterroles &> /dev/null; then
        log_error "Insufficient permissions. cluster-admin role required."
        exit 1
    fi

    log_success "Prerequisites check passed"
}

# Create namespaces
create_namespaces() {
    log_info "Creating namespaces..."

    # Create namespaces if they don't exist
    kubectl create namespace $NAMESPACE_PROD --dry-run=client -o yaml | kubectl apply -f -
    kubectl create namespace $NAMESPACE_OBSERVABILITY --dry-run=client -o yaml | kubectl apply -f -
    kubectl create namespace $NAMESPACE_OPERATOR --dry-run=client -o yaml | kubectl apply -f -

    # Label namespaces
    kubectl label namespace $NAMESPACE_PROD observability=enabled --overwrite
    kubectl label namespace $NAMESPACE_OBSERVABILITY observability=core --overwrite

    log_success "Namespaces created and labeled"
}

# Deploy OpenTelemetry Operator
deploy_operator() {
    log_info "Deploying OpenTelemetry Operator..."

    # Apply operator resources
    kubectl apply -f observability/kubernetes/otel-operator.yaml

    # Wait for operator to be ready
    log_info "Waiting for operator to be ready..."
    kubectl wait --for=condition=ready pod -l app.kubernetes.io/name=opentelemetry-operator -n $NAMESPACE_OPERATOR --timeout=300s

    log_success "OpenTelemetry Operator deployed successfully"
}

# Deploy Jaeger
deploy_jaeger() {
    log_info "Deploying Jaeger..."

    kubectl apply -f observability/kubernetes/jaeger-deployment.yaml

    # Wait for Jaeger to be ready
    log_info "Waiting for Jaeger to be ready..."
    kubectl wait --for=condition=ready pod -l app=jaeger -n $NAMESPACE_OBSERVABILITY --timeout=300s

    # Get Jaeger URL
    jaeger_url=$(kubectl get ingress jaeger-ingress -n $NAMESPACE_OBSERVABILITY -o jsonpath='{.spec.rules[0].host}' 2>/dev/null || echo "Not configured")
    log_success "Jaeger deployed successfully. UI available at: http://$jaeger_url"
}

# Deploy OpenTelemetry Collector
deploy_collector() {
    log_info "Deploying OpenTelemetry Collector..."

    # Create observability secrets if they don't exist
    create_observability_secrets

    kubectl apply -f observability/kubernetes/otel-collector.yaml

    # Wait for collector to be ready
    log_info "Waiting for collector to be ready..."
    kubectl wait --for=condition=ready pod -l app.kubernetes.io/name=uatp-otel-collector -n $NAMESPACE_PROD --timeout=300s

    log_success "OpenTelemetry Collector deployed successfully"
}

# Create observability secrets
create_observability_secrets() {
    log_info "Creating observability secrets..."

    # Check if secret already exists
    if kubectl get secret observability-secrets -n $NAMESPACE_PROD &> /dev/null; then
        log_warning "Observability secrets already exist, skipping creation"
        return
    fi

    # Create empty secret (values should be populated by operations team)
    kubectl create secret generic observability-secrets -n $NAMESPACE_PROD \
        --from-literal=datadog-api-key="" \
        --from-literal=newrelic-license-key="" \
        --from-literal=grafana-cloud-token="" \
        --from-literal=honeycomb-api-key=""

    log_success "Observability secrets created (empty - populate as needed)"
}

# Deploy auto-instrumentation
deploy_instrumentation() {
    log_info "Deploying auto-instrumentation configuration..."

    kubectl apply -f observability/kubernetes/auto-instrumentation.yaml

    # Verify instrumentation resource
    kubectl get instrumentation uatp-auto-instrumentation -n $NAMESPACE_PROD

    log_success "Auto-instrumentation configuration deployed"
}

# Update UATP deployment
update_uatp_deployment() {
    log_info "Updating UATP deployment with OpenTelemetry..."

    # Backup current deployment
    kubectl get deployment uatp-api -n $NAMESPACE_PROD -o yaml > uatp-api-backup-$(date +%Y%m%d-%H%M%S).yaml
    log_info "Current deployment backed up"

    # Apply new deployment
    kubectl apply -f observability/kubernetes/uatp-deployment-otel.yaml

    # Wait for rollout to complete
    log_info "Waiting for UATP deployment rollout..."
    kubectl rollout status deployment/uatp-api -n $NAMESPACE_PROD --timeout=600s

    log_success "UATP deployment updated successfully"
}

# Update monitoring stack
update_monitoring() {
    log_info "Updating monitoring stack..."

    # Update Grafana dashboards
    if kubectl get configmap grafana-config -n $NAMESPACE_PROD &> /dev/null; then
        # Create dashboard configmaps
        kubectl create configmap grafana-otel-dashboards \
            --from-file=observability/grafana/dashboards/ \
            -n $NAMESPACE_PROD \
            --dry-run=client -o yaml | kubectl apply -f -

        # Label for Grafana discovery
        kubectl label configmap grafana-otel-dashboards grafana_dashboard=1 -n $NAMESPACE_PROD --overwrite

        log_success "Grafana dashboards updated"
    else
        log_warning "Grafana not found, skipping dashboard update"
    fi

    # Apply alerting rules
    if kubectl get prometheus -n $NAMESPACE_PROD &> /dev/null; then
        kubectl apply -f observability/alerting/otel-alerting-rules.yaml
        log_success "Alerting rules updated"
    else
        log_warning "Prometheus not found, skipping alerting rules"
    fi
}

# Validate deployment
validate_deployment() {
    log_info "Validating deployment..."

    # Check all pods are running
    log_info "Checking pod status..."

    # Check operator
    if ! kubectl get pods -n $NAMESPACE_OPERATOR -l app.kubernetes.io/name=opentelemetry-operator | grep -q Running; then
        log_error "OpenTelemetry Operator not running"
        return 1
    fi

    # Check Jaeger
    if ! kubectl get pods -n $NAMESPACE_OBSERVABILITY -l app=jaeger | grep -q Running; then
        log_error "Jaeger not running"
        return 1
    fi

    # Check collector
    if ! kubectl get pods -n $NAMESPACE_PROD -l app.kubernetes.io/name=uatp-otel-collector | grep -q Running; then
        log_error "OpenTelemetry Collector not running"
        return 1
    fi

    # Check UATP API
    if ! kubectl get pods -n $NAMESPACE_PROD -l app=uatp-api | grep -q Running; then
        log_error "UATP API not running"
        return 1
    fi

    # Check services
    log_info "Checking service endpoints..."

    # Test collector OTLP endpoint
    if kubectl run test-otel-connectivity --image=curlimages/curl --rm -it --restart=Never -- \
        curl -f http://uatp-otel-collector:4318/v1/traces --max-time 5 &> /dev/null; then
        log_success "Collector OTLP endpoint accessible"
    else
        log_warning "Collector OTLP endpoint not accessible (may be normal if no traces yet)"
    fi

    # Test Jaeger UI
    if kubectl run test-jaeger-connectivity --image=curlimages/curl --rm -it --restart=Never -- \
        curl -f http://jaeger-query.observability:16686 --max-time 5 &> /dev/null; then
        log_success "Jaeger UI accessible"
    else
        log_warning "Jaeger UI not accessible"
    fi

    # Check UATP API health with observability
    log_info "Checking UATP API observability health..."
    if kubectl exec deployment/uatp-api -n $NAMESPACE_PROD -- \
        curl -f http://localhost:8080/health/observability --max-time 5 &> /dev/null; then
        log_success "UATP API observability features healthy"
    else
        log_warning "UATP API observability health check failed"
    fi

    log_success "Deployment validation completed"
}

# Show deployment status
show_status() {
    log_info "Deployment Status Summary:"
    echo ""

    echo "=== Namespaces ==="
    kubectl get namespaces | grep -E "(uatp-prod|observability|opentelemetry-operator-system)"
    echo ""

    echo "=== OpenTelemetry Operator ==="
    kubectl get pods -n $NAMESPACE_OPERATOR -l app.kubernetes.io/name=opentelemetry-operator
    echo ""

    echo "=== Jaeger ==="
    kubectl get pods -n $NAMESPACE_OBSERVABILITY -l app=jaeger
    echo ""

    echo "=== OpenTelemetry Collector ==="
    kubectl get pods -n $NAMESPACE_PROD -l app.kubernetes.io/name=uatp-otel-collector
    echo ""

    echo "=== UATP API ==="
    kubectl get pods -n $NAMESPACE_PROD -l app=uatp-api
    echo ""

    echo "=== Services ==="
    kubectl get svc -n $NAMESPACE_PROD | grep -E "(otel|uatp)"
    kubectl get svc -n $NAMESPACE_OBSERVABILITY | grep jaeger
    echo ""

    echo "=== Instrumentation ==="
    kubectl get instrumentation -n $NAMESPACE_PROD
    echo ""

    # Show access URLs
    echo "=== Access URLs ==="
    jaeger_url=$(kubectl get ingress jaeger-ingress -n $NAMESPACE_OBSERVABILITY -o jsonpath='{.spec.rules[0].host}' 2>/dev/null || echo "Not configured")
    echo "Jaeger UI: http://$jaeger_url"

    prometheus_url=$(kubectl get ingress prometheus-ingress -n $NAMESPACE_PROD -o jsonpath='{.spec.rules[0].host}' 2>/dev/null || echo "Not configured")
    echo "Prometheus: http://$prometheus_url"

    grafana_url=$(kubectl get ingress grafana-ingress -n $NAMESPACE_PROD -o jsonpath='{.spec.rules[0].host}' 2>/dev/null || echo "Not configured")
    echo "Grafana: http://$grafana_url"
}

# Cleanup function for failed deployments
cleanup() {
    log_warning "Cleaning up failed deployment..."

    # Remove OpenTelemetry resources
    kubectl delete -f observability/kubernetes/otel-collector.yaml --ignore-not-found=true
    kubectl delete -f observability/kubernetes/auto-instrumentation.yaml --ignore-not-found=true
    kubectl delete -f observability/kubernetes/jaeger-deployment.yaml --ignore-not-found=true
    kubectl delete -f observability/kubernetes/otel-operator.yaml --ignore-not-found=true

    log_success "Cleanup completed"
}

# Main deployment function
main() {
    log_info "Starting UATP OpenTelemetry deployment..."

    # Set trap for cleanup on failure
    trap cleanup ERR

    # Run deployment steps
    check_prerequisites
    create_namespaces
    deploy_operator
    deploy_jaeger
    deploy_collector
    deploy_instrumentation
    update_uatp_deployment
    update_monitoring

    # Validate deployment
    if validate_deployment; then
        log_success "UATP OpenTelemetry deployment completed successfully!"
        show_status
    else
        log_error "Deployment validation failed. Check the logs above."
        exit 1
    fi

    # Show next steps
    echo ""
    log_info "Next Steps:"
    echo "1. Populate observability secrets with actual API keys:"
    echo "   kubectl edit secret observability-secrets -n $NAMESPACE_PROD"
    echo ""
    echo "2. Configure ingress for external access to observability tools"
    echo ""
    echo "3. Set up alerting notification channels in Grafana/AlertManager"
    echo ""
    echo "4. Review and adjust sampling rates based on traffic volume"
    echo ""
    echo "5. Monitor resource usage and scale as needed"
    echo ""
    log_success "Deployment guide available at: observability/docs/OPENTELEMETRY_MIGRATION_GUIDE.md"
}

# Parse command line arguments
case "${1:-deploy}" in
    "deploy")
        main
        ;;
    "validate")
        validate_deployment
        show_status
        ;;
    "status")
        show_status
        ;;
    "cleanup")
        cleanup
        ;;
    "help"|"-h"|"--help")
        echo "Usage: $0 [deploy|validate|status|cleanup|help]"
        echo ""
        echo "Commands:"
        echo "  deploy    - Deploy the complete OpenTelemetry stack (default)"
        echo "  validate  - Validate existing deployment"
        echo "  status    - Show deployment status"
        echo "  cleanup   - Remove OpenTelemetry resources"
        echo "  help      - Show this help message"
        ;;
    *)
        log_error "Unknown command: $1"
        echo "Use '$0 help' for usage information"
        exit 1
        ;;
esac
