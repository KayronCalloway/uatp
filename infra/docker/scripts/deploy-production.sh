#!/bin/bash

# UATP Production Deployment Script
# Comprehensive deployment automation for production environment

set -euo pipefail

# Script configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
DEPLOY_LOG="/tmp/uatp-deploy-$(date +%Y%m%d_%H%M%S).log"

# Default configuration
ENVIRONMENT="${ENVIRONMENT:-production}"
VERSION="${VERSION:-latest}"
REGISTRY="${REGISTRY:-ghcr.io/uatp}"
NAMESPACE="${NAMESPACE:-uatp-prod}"
SKIP_TESTS="${SKIP_TESTS:-false}"
SKIP_BUILD="${SKIP_BUILD:-false}"
SKIP_DB_MIGRATION="${SKIP_DB_MIGRATION:-false}"
DRY_RUN="${DRY_RUN:-false}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging function
log() {
    local level="$1"
    shift
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    local color=""

    case "$level" in
        "INFO")  color="$GREEN" ;;
        "WARN")  color="$YELLOW" ;;
        "ERROR") color="$RED" ;;
        "DEBUG") color="$BLUE" ;;
    esac

    echo -e "${color}[$timestamp] [$level] $*${NC}" | tee -a "$DEPLOY_LOG"
}

# Error handling
trap 'log ERROR "Deployment failed at line $LINENO. Check log: $DEPLOY_LOG"' ERR

# Usage information
usage() {
    cat << EOF
UATP Production Deployment Script

Usage: $0 [OPTIONS]

Options:
    -e, --environment ENV     Deployment environment (default: production)
    -v, --version VERSION     Application version to deploy (default: latest)
    -r, --registry REGISTRY   Container registry (default: ghcr.io/uatp)
    -n, --namespace NS        Kubernetes namespace (default: uatp-prod)
    --skip-tests             Skip running tests
    --skip-build             Skip building containers
    --skip-db-migration      Skip database migrations
    --dry-run                Show what would be deployed without executing
    -h, --help               Show this help message

Examples:
    $0                                          # Deploy latest to production
    $0 -v v1.2.0 -e production                # Deploy specific version
    $0 --dry-run                               # Preview deployment
    $0 --skip-build --skip-tests               # Quick deploy (use existing build)

EOF
}

# Parse command line arguments
parse_args() {
    while [[ $# -gt 0 ]]; do
        case $1 in
            -e|--environment)
                ENVIRONMENT="$2"
                shift 2
                ;;
            -v|--version)
                VERSION="$2"
                shift 2
                ;;
            -r|--registry)
                REGISTRY="$2"
                shift 2
                ;;
            -n|--namespace)
                NAMESPACE="$2"
                shift 2
                ;;
            --skip-tests)
                SKIP_TESTS="true"
                shift
                ;;
            --skip-build)
                SKIP_BUILD="true"
                shift
                ;;
            --skip-db-migration)
                SKIP_DB_MIGRATION="true"
                shift
                ;;
            --dry-run)
                DRY_RUN="true"
                shift
                ;;
            -h|--help)
                usage
                exit 0
                ;;
            *)
                log ERROR "Unknown option: $1"
                usage
                exit 1
                ;;
        esac
    done
}

# Check prerequisites
check_prerequisites() {
    log INFO "Checking deployment prerequisites..."

    local missing_tools=()
    local required_tools=("kubectl" "docker" "helm" "yq")

    for tool in "${required_tools[@]}"; do
        if ! command -v "$tool" &> /dev/null; then
            missing_tools+=("$tool")
        fi
    done

    if [ ${#missing_tools[@]} -gt 0 ]; then
        log ERROR "Missing required tools: ${missing_tools[*]}"
        log INFO "Please install missing tools and try again"
        exit 1
    fi

    # Check Kubernetes connection
    if ! kubectl cluster-info &> /dev/null; then
        log ERROR "Cannot connect to Kubernetes cluster"
        log INFO "Please configure kubectl and try again"
        exit 1
    fi

    # Check Docker daemon
    if ! docker info &> /dev/null; then
        log ERROR "Docker daemon is not running"
        exit 1
    fi

    # Check environment files
    local env_file="$PROJECT_ROOT/deployment/environments/${ENVIRONMENT}.env"
    if [ ! -f "$env_file" ]; then
        log ERROR "Environment file not found: $env_file"
        exit 1
    fi

    log INFO "Prerequisites check passed"
}

# Load environment configuration
load_environment() {
    log INFO "Loading environment configuration for: $ENVIRONMENT"

    local env_file="$PROJECT_ROOT/deployment/environments/${ENVIRONMENT}.env"

    # Source environment file
    set -a  # automatically export all variables
    source "$env_file"
    set +a

    # Validate required environment variables
    local required_vars=(
        "DATABASE_PASSWORD"
        "SECRET_KEY"
        "JWT_SECRET"
        "OPENAI_API_KEY"
    )

    local missing_vars=()
    for var in "${required_vars[@]}"; do
        if [ -z "${!var:-}" ]; then
            missing_vars+=("$var")
        fi
    done

    if [ ${#missing_vars[@]} -gt 0 ]; then
        log ERROR "Missing required environment variables: ${missing_vars[*]}"
        exit 1
    fi

    log INFO "Environment configuration loaded successfully"
}

# Run tests
run_tests() {
    if [ "$SKIP_TESTS" = "true" ]; then
        log INFO "Skipping tests (--skip-tests specified)"
        return 0
    fi

    log INFO "Running test suite..."
    cd "$PROJECT_ROOT"

    # Install test dependencies
    pip install -r requirements-dev.in

    # Run unit tests
    pytest tests/ -v --tb=short --cov=src --cov-report=term-missing

    # Run integration tests
    pytest tests/integration/ -v --tb=short

    # Run security tests
    python run_security_tests.py

    log INFO "All tests passed successfully"
}

# Build container images
build_images() {
    if [ "$SKIP_BUILD" = "true" ]; then
        log INFO "Skipping build (--skip-build specified)"
        return 0
    fi

    log INFO "Building container images..."
    cd "$PROJECT_ROOT"

    local image_tag="${REGISTRY}/uatp-capsule-engine:${VERSION}"
    local backup_image_tag="${REGISTRY}/uatp-backup-service:${VERSION}"

    # Build main application image
    log INFO "Building main application image: $image_tag"
    docker build \
        -f deployment/docker/Dockerfile.production \
        -t "$image_tag" \
        --build-arg BUILD_DATE="$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
        --build-arg VERSION="$VERSION" \
        --build-arg GIT_COMMIT="$(git rev-parse HEAD)" \
        .

    # Build backup service image
    log INFO "Building backup service image: $backup_image_tag"
    docker build \
        -f deployment/docker/Dockerfile.backup \
        -t "$backup_image_tag" \
        --build-arg VERSION="$VERSION" \
        .

    if [ "$DRY_RUN" = "false" ]; then
        # Push images to registry
        log INFO "Pushing images to registry..."
        docker push "$image_tag"
        docker push "$backup_image_tag"
    else
        log INFO "[DRY RUN] Would push images: $image_tag, $backup_image_tag"
    fi

    log INFO "Container images built and pushed successfully"
}

# Create Kubernetes namespace and secrets
setup_kubernetes() {
    log INFO "Setting up Kubernetes resources..."

    # Create namespace
    if [ "$DRY_RUN" = "false" ]; then
        kubectl apply -f "$PROJECT_ROOT/k8s/environments/${ENVIRONMENT}/namespace.yaml"
    else
        log INFO "[DRY RUN] Would create namespace: $NAMESPACE"
    fi

    # Create secrets
    log INFO "Creating Kubernetes secrets..."

    local secret_file="/tmp/uatp-secrets.yaml"
    cat > "$secret_file" << EOF
apiVersion: v1
kind: Secret
metadata:
  name: uatp-secrets
  namespace: $NAMESPACE
type: Opaque
stringData:
  DATABASE_PASSWORD: "$DATABASE_PASSWORD"
  SECRET_KEY: "$SECRET_KEY"
  JWT_SECRET: "$JWT_SECRET"
  ENCRYPTION_KEY: "$ENCRYPTION_KEY"
  OPENAI_API_KEY: "$OPENAI_API_KEY"
  ANTHROPIC_API_KEY: "$ANTHROPIC_API_KEY"
  STRIPE_SECRET_KEY: "$STRIPE_SECRET_KEY"
  STRIPE_WEBHOOK_SECRET: "$STRIPE_WEBHOOK_SECRET"
  PAYPAL_CLIENT_SECRET: "$PAYPAL_CLIENT_SECRET"
  REDIS_PASSWORD: "$REDIS_PASSWORD"
EOF

    if [ "$DRY_RUN" = "false" ]; then
        kubectl apply -f "$secret_file"
        rm "$secret_file"
    else
        log INFO "[DRY RUN] Would create secrets in namespace: $NAMESPACE"
        rm "$secret_file"
    fi

    log INFO "Kubernetes setup completed"
}

# Deploy database
deploy_database() {
    log INFO "Deploying PostgreSQL database..."

    if [ "$DRY_RUN" = "false" ]; then
        kubectl apply -f "$PROJECT_ROOT/k8s/environments/${ENVIRONMENT}/postgresql.yaml"

        # Wait for database to be ready
        log INFO "Waiting for database to be ready..."
        kubectl wait --for=condition=ready pod -l app=postgresql -n "$NAMESPACE" --timeout=300s
    else
        log INFO "[DRY RUN] Would deploy PostgreSQL database"
    fi

    log INFO "Database deployment completed"
}

# Run database migrations
run_migrations() {
    if [ "$SKIP_DB_MIGRATION" = "true" ]; then
        log INFO "Skipping database migrations (--skip-db-migration specified)"
        return 0
    fi

    log INFO "Running database migrations..."

    if [ "$DRY_RUN" = "false" ]; then
        # Run migrations using a temporary pod
        kubectl run migration-job \
            --image="${REGISTRY}/uatp-capsule-engine:${VERSION}" \
            --rm -i --restart=Never \
            --namespace="$NAMESPACE" \
            --env="DATABASE_URL=$DATABASE_URL" \
            -- python -m alembic upgrade head
    else
        log INFO "[DRY RUN] Would run database migrations"
    fi

    log INFO "Database migrations completed"
}

# Deploy application
deploy_application() {
    log INFO "Deploying UATP application..."

    # Update deployment with new image
    local deployment_file="$PROJECT_ROOT/k8s/environments/${ENVIRONMENT}/deployment.yaml"
    local temp_deployment="/tmp/deployment-${ENVIRONMENT}.yaml"

    # Replace image tag in deployment
    sed "s|image: uatp-capsule-engine:.*|image: ${REGISTRY}/uatp-capsule-engine:${VERSION}|g" \
        "$deployment_file" > "$temp_deployment"

    if [ "$DRY_RUN" = "false" ]; then
        kubectl apply -f "$temp_deployment"

        # Wait for rollout to complete
        log INFO "Waiting for deployment rollout..."
        kubectl rollout status deployment/uatp-api -n "$NAMESPACE" --timeout=600s

        # Verify deployment
        local ready_replicas=$(kubectl get deployment uatp-api -n "$NAMESPACE" -o jsonpath='{.status.readyReplicas}')
        local desired_replicas=$(kubectl get deployment uatp-api -n "$NAMESPACE" -o jsonpath='{.spec.replicas}')

        if [ "$ready_replicas" = "$desired_replicas" ]; then
            log INFO "Application deployed successfully ($ready_replicas/$desired_replicas replicas ready)"
        else
            log ERROR "Application deployment failed ($ready_replicas/$desired_replicas replicas ready)"
            exit 1
        fi
    else
        log INFO "[DRY RUN] Would deploy application with image: ${REGISTRY}/uatp-capsule-engine:${VERSION}"
    fi

    rm -f "$temp_deployment"
    log INFO "Application deployment completed"
}

# Deploy monitoring stack
deploy_monitoring() {
    log INFO "Deploying monitoring stack..."

    if [ "$DRY_RUN" = "false" ]; then
        # Deploy Prometheus
        kubectl apply -f "$PROJECT_ROOT/k8s/environments/${ENVIRONMENT}/monitoring.yaml"

        # Wait for monitoring components
        log INFO "Waiting for monitoring components to be ready..."
        kubectl wait --for=condition=ready pod -l app=prometheus -n "$NAMESPACE" --timeout=300s
        kubectl wait --for=condition=ready pod -l app=grafana -n "$NAMESPACE" --timeout=300s
    else
        log INFO "[DRY RUN] Would deploy monitoring stack"
    fi

    log INFO "Monitoring deployment completed"
}

# Setup ingress and load balancing
setup_ingress() {
    log INFO "Setting up ingress and load balancing..."

    if [ "$DRY_RUN" = "false" ]; then
        kubectl apply -f "$PROJECT_ROOT/k8s/environments/${ENVIRONMENT}/ingress.yaml"

        # Wait for ingress to get external IP
        log INFO "Waiting for ingress to be ready..."
        sleep 30  # Give time for ingress controller to process

        local external_ip=$(kubectl get ingress uatp-ingress -n "$NAMESPACE" -o jsonpath='{.status.loadBalancer.ingress[0].ip}')
        if [ -n "$external_ip" ]; then
            log INFO "Ingress external IP: $external_ip"
        else
            log WARN "External IP not yet assigned to ingress"
        fi
    else
        log INFO "[DRY RUN] Would setup ingress and load balancing"
    fi

    log INFO "Ingress setup completed"
}

# Health checks
run_health_checks() {
    log INFO "Running health checks..."

    if [ "$DRY_RUN" = "true" ]; then
        log INFO "[DRY RUN] Would run health checks"
        return 0
    fi

    # Internal health checks
    local health_url="http://uatp-api-service.$NAMESPACE.svc.cluster.local:80/health"

    # Use a temporary pod to check internal health
    kubectl run health-check \
        --image=curlimages/curl:latest \
        --rm -i --restart=Never \
        --namespace="$NAMESPACE" \
        -- curl -f "$health_url" || {
        log ERROR "Internal health check failed"
        exit 1
    }

    log INFO "Health checks passed"
}

# Smoke tests
run_smoke_tests() {
    log INFO "Running smoke tests..."

    if [ "$DRY_RUN" = "true" ]; then
        log INFO "[DRY RUN] Would run smoke tests"
        return 0
    fi

    # Run basic API tests
    local test_script="$PROJECT_ROOT/deployment/scripts/test-production.sh"
    if [ -f "$test_script" ]; then
        "$test_script" --env "$ENVIRONMENT" --quick
    else
        log WARN "Smoke test script not found, skipping"
    fi

    log INFO "Smoke tests completed"
}

# Cleanup function
cleanup() {
    log INFO "Cleaning up temporary files..."
    rm -f /tmp/uatp-secrets.yaml
    rm -f /tmp/deployment-*.yaml
}

# Main deployment function
main() {
    log INFO "Starting UATP production deployment..."
    log INFO "Environment: $ENVIRONMENT"
    log INFO "Version: $VERSION"
    log INFO "Registry: $REGISTRY"
    log INFO "Namespace: $NAMESPACE"
    log INFO "Dry Run: $DRY_RUN"

    local start_time=$(date +%s)

    # Execute deployment steps
    check_prerequisites
    load_environment
    run_tests
    build_images
    setup_kubernetes
    deploy_database
    run_migrations
    deploy_application
    deploy_monitoring
    setup_ingress
    run_health_checks
    run_smoke_tests

    local end_time=$(date +%s)
    local duration=$((end_time - start_time))

    log INFO "Deployment completed successfully in ${duration}s"
    log INFO "Application should be available at: https://api.uatp.com"
    log INFO "Monitoring available at: https://monitoring.uatp.com"
    log INFO "Deployment log saved to: $DEPLOY_LOG"

    cleanup
}

# Trap cleanup on exit
trap cleanup EXIT

# Parse arguments and run main function
parse_args "$@"
main
