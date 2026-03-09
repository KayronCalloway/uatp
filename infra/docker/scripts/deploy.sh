#!/bin/bash

# UATP Production Deployment Script
# This script handles the complete deployment of UATP to production

set -e

# Configuration
NAMESPACE="uatp-production"
DOCKER_REGISTRY="your-registry.com/uatp"
APP_VERSION="${APP_VERSION:-latest}"
ENVIRONMENT="${ENVIRONMENT:-production}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

warn() {
    echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] WARNING:${NC} $1"
}

error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] ERROR:${NC} $1"
    exit 1
}

# Check prerequisites
check_prerequisites() {
    log "Checking prerequisites..."

    # Check if kubectl is installed
    if ! command -v kubectl &> /dev/null; then
        error "kubectl is not installed"
    fi

    # Check if docker is installed
    if ! command -v docker &> /dev/null; then
        error "docker is not installed"
    fi

    # Check if helm is installed
    if ! command -v helm &> /dev/null; then
        warn "helm is not installed, some features may not work"
    fi

    # Check kubectl connection
    if ! kubectl cluster-info &> /dev/null; then
        error "kubectl cannot connect to cluster"
    fi

    log "Prerequisites check passed"
}

# Build Docker image
build_image() {
    log "Building Docker image..."

    cd "$(dirname "$0")/../.."

    # Build the image
    docker build -t "${DOCKER_REGISTRY}:${APP_VERSION}" -f deployment/docker/Dockerfile .

    # Tag as latest
    docker tag "${DOCKER_REGISTRY}:${APP_VERSION}" "${DOCKER_REGISTRY}:latest"

    log "Docker image built successfully"
}

# Push Docker image
push_image() {
    log "Pushing Docker image to registry..."

    # Push versioned image
    docker push "${DOCKER_REGISTRY}:${APP_VERSION}"

    # Push latest
    docker push "${DOCKER_REGISTRY}:latest"

    log "Docker image pushed successfully"
}

# Create namespace
create_namespace() {
    log "Creating namespace..."

    if kubectl get namespace $NAMESPACE &> /dev/null; then
        log "Namespace $NAMESPACE already exists"
    else
        kubectl apply -f deployment/kubernetes/namespace.yaml
        log "Namespace $NAMESPACE created"
    fi
}

# Deploy secrets and config
deploy_config() {
    log "Deploying configuration..."

    # Check if .env file exists
    if [ ! -f ".env" ]; then
        warn "No .env file found, using .env.example"
        cp .env.example .env
    fi

    # Apply ConfigMap and Secrets
    kubectl apply -f deployment/kubernetes/configmap.yaml

    log "Configuration deployed"
}

# Deploy database
deploy_database() {
    log "Deploying PostgreSQL database..."

    # Apply PostgreSQL deployment
    kubectl apply -f deployment/kubernetes/postgresql.yaml

    # Wait for PostgreSQL to be ready
    kubectl wait --for=condition=ready pod -l app=postgresql -n $NAMESPACE --timeout=300s

    log "PostgreSQL deployed and ready"
}

# Deploy Redis
deploy_redis() {
    log "Deploying Redis cache..."

    # Apply Redis deployment
    kubectl apply -f deployment/kubernetes/redis.yaml

    # Wait for Redis to be ready
    kubectl wait --for=condition=ready pod -l app=redis -n $NAMESPACE --timeout=300s

    log "Redis deployed and ready"
}

# Deploy application
deploy_app() {
    log "Deploying UATP application..."

    # Update image in deployment
    sed -i.bak "s|image: uatp/app:latest|image: ${DOCKER_REGISTRY}:${APP_VERSION}|g" deployment/kubernetes/uatp-app.yaml

    # Apply application deployment
    kubectl apply -f deployment/kubernetes/uatp-app.yaml

    # Wait for deployment to be ready
    kubectl wait --for=condition=available deployment/uatp-app -n $NAMESPACE --timeout=600s

    # Restore original file
    mv deployment/kubernetes/uatp-app.yaml.bak deployment/kubernetes/uatp-app.yaml

    log "UATP application deployed and ready"
}

# Deploy monitoring
deploy_monitoring() {
    log "Deploying monitoring stack..."

    # Apply monitoring configuration
    kubectl apply -f deployment/kubernetes/monitoring.yaml

    log "Monitoring stack deployed"
}

# Run database migrations
run_migrations() {
    log "Running database migrations..."

    # Get a pod name
    POD_NAME=$(kubectl get pods -n $NAMESPACE -l app=uatp-app -o jsonpath='{.items[0].metadata.name}')

    # Run migrations
    kubectl exec -n $NAMESPACE $POD_NAME -- python -m src.database.migrations migrate

    log "Database migrations completed"
}

# Health check
health_check() {
    log "Performing health check..."

    # Get service endpoint
    SERVICE_IP=$(kubectl get service uatp-app-service -n $NAMESPACE -o jsonpath='{.spec.clusterIP}')

    # Port forward for health check
    kubectl port-forward -n $NAMESPACE service/uatp-app-service 8080:8000 &
    PF_PID=$!

    # Wait for port forward
    sleep 5

    # Health check
    if curl -f http://localhost:8080/health &> /dev/null; then
        log "Health check passed"
    else
        error "Health check failed"
    fi

    # Clean up port forward
    kill $PF_PID
}

# Show deployment status
show_status() {
    log "Deployment status:"

    echo ""
    echo "Namespace: $NAMESPACE"
    kubectl get all -n $NAMESPACE

    echo ""
    echo "Pod logs (last 10 lines):"
    kubectl logs -n $NAMESPACE deployment/uatp-app --tail=10

    echo ""
    echo "Service endpoints:"
    kubectl get endpoints -n $NAMESPACE
}

# Cleanup function
cleanup() {
    log "Cleaning up..."

    # Kill any background processes
    jobs -p | xargs -r kill

    log "Cleanup completed"
}

# Main deployment function
main() {
    log "Starting UATP production deployment..."

    # Set up cleanup trap
    trap cleanup EXIT

    # Parse command line arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            --skip-build)
                SKIP_BUILD=true
                shift
                ;;
            --skip-push)
                SKIP_PUSH=true
                shift
                ;;
            --skip-db)
                SKIP_DB=true
                shift
                ;;
            --version)
                APP_VERSION="$2"
                shift 2
                ;;
            --registry)
                DOCKER_REGISTRY="$2"
                shift 2
                ;;
            --namespace)
                NAMESPACE="$2"
                shift 2
                ;;
            --help)
                echo "Usage: $0 [OPTIONS]"
                echo "Options:"
                echo "  --skip-build    Skip Docker image build"
                echo "  --skip-push     Skip Docker image push"
                echo "  --skip-db       Skip database deployment"
                echo "  --version       Set app version (default: latest)"
                echo "  --registry      Set Docker registry URL"
                echo "  --namespace     Set Kubernetes namespace"
                echo "  --help          Show this help message"
                exit 0
                ;;
            *)
                error "Unknown option: $1"
                ;;
        esac
    done

    # Check prerequisites
    check_prerequisites

    # Build and push image
    if [ "$SKIP_BUILD" != true ]; then
        build_image
    fi

    if [ "$SKIP_PUSH" != true ]; then
        push_image
    fi

    # Deploy infrastructure
    create_namespace
    deploy_config

    if [ "$SKIP_DB" != true ]; then
        deploy_database
        deploy_redis
    fi

    # Deploy application
    deploy_app
    run_migrations
    deploy_monitoring

    # Final checks
    health_check
    show_status

    log " UATP production deployment completed successfully!"
    log "Application is running at: https://api.uatp.example.com"
    log "Monitoring dashboard: http://localhost:3000 (port-forward required)"
}

# Run main function
main "$@"
