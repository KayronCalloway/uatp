#!/bin/bash
# Production Deployment Script for UATP Capsule Engine

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
NAMESPACE="uatp-production"
DEPLOYMENT="uatp-api"
IMAGE_TAG="${IMAGE_TAG:-latest}"
KUBECONFIG="${KUBECONFIG:-~/.kube/config}"

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}UATP Capsule Engine - Production Deployment${NC}"
echo -e "${GREEN}========================================${NC}\n"

# Function to check if kubectl is installed
check_kubectl() {
    if ! command -v kubectl &> /dev/null; then
        echo -e "${RED}❌ kubectl not found. Please install kubectl first.${NC}"
        exit 1
    fi
    echo -e "${GREEN}✅ kubectl found${NC}"
}

# Function to check cluster connectivity
check_cluster() {
    echo -e "\n${YELLOW}Checking cluster connectivity...${NC}"
    if ! kubectl cluster-info &> /dev/null; then
        echo -e "${RED}❌ Cannot connect to Kubernetes cluster${NC}"
        echo "Please check your kubeconfig: $KUBECONFIG"
        exit 1
    fi
    echo -e "${GREEN}✅ Connected to cluster${NC}"
    kubectl cluster-info | head -1
}

# Function to create namespace if it doesn't exist
create_namespace() {
    echo -e "\n${YELLOW}Creating namespace...${NC}"
    kubectl apply -f namespace.yaml
    echo -e "${GREEN}✅ Namespace ready${NC}"
}

# Function to apply configmap
apply_configmap() {
    echo -e "\n${YELLOW}Applying ConfigMap...${NC}"
    kubectl apply -f configmap.yaml
    echo -e "${GREEN}✅ ConfigMap applied${NC}"
}

# Function to check if secrets exist
check_secrets() {
    echo -e "\n${YELLOW}Checking secrets...${NC}"
    if ! kubectl get secret uatp-secrets -n $NAMESPACE &> /dev/null; then
        echo -e "${YELLOW}⚠️  Secrets not found${NC}"
        echo "Please create secrets from secrets-template.yaml"
        echo "Instructions:"
        echo "  1. Copy secrets-template.yaml to secrets.yaml"
        echo "  2. Replace all CHANGE_ME values"
        echo "  3. Run: kubectl apply -f secrets.yaml"
        echo ""
        read -p "Continue without secrets? (y/N) " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
    else
        echo -e "${GREEN}✅ Secrets found${NC}"
    fi
}

# Function to deploy application
deploy_application() {
    echo -e "\n${YELLOW}Deploying application...${NC}"
    kubectl apply -f deployment.yaml
    kubectl apply -f service.yaml
    echo -e "${GREEN}✅ Application deployed${NC}"
}

# Function to apply HPA
apply_hpa() {
    echo -e "\n${YELLOW}Applying Horizontal Pod Autoscaler...${NC}"
    kubectl apply -f hpa.yaml
    echo -e "${GREEN}✅ HPA configured${NC}"
}

# Function to apply ingress
apply_ingress() {
    echo -e "\n${YELLOW}Applying Ingress...${NC}"
    if kubectl apply -f ingress.yaml; then
        echo -e "${GREEN}✅ Ingress configured${NC}"
    else
        echo -e "${YELLOW}⚠️  Ingress configuration failed (may need cert-manager)${NC}"
    fi
}

# Function to wait for deployment
wait_for_deployment() {
    echo -e "\n${YELLOW}Waiting for deployment to be ready...${NC}"
    kubectl rollout status deployment/$DEPLOYMENT -n $NAMESPACE --timeout=5m
    echo -e "${GREEN}✅ Deployment ready${NC}"
}

# Function to show deployment status
show_status() {
    echo -e "\n${YELLOW}Deployment Status:${NC}"
    kubectl get pods -n $NAMESPACE -l app=uatp-api
    echo ""
    kubectl get svc -n $NAMESPACE
    echo ""
    kubectl get ingress -n $NAMESPACE
}

# Function to show deployment info
show_info() {
    echo -e "\n${GREEN}========================================${NC}"
    echo -e "${GREEN}Deployment Complete!${NC}"
    echo -e "${GREEN}========================================${NC}\n"

    echo "Namespace: $NAMESPACE"
    echo "Deployment: $DEPLOYMENT"
    echo ""

    echo "Useful commands:"
    echo "  - View logs:        kubectl logs -f -l app=uatp-api -n $NAMESPACE"
    echo "  - View pods:        kubectl get pods -n $NAMESPACE"
    echo "  - Describe pod:     kubectl describe pod <pod-name> -n $NAMESPACE"
    echo "  - Execute command:  kubectl exec -it <pod-name> -n $NAMESPACE -- /bin/bash"
    echo "  - View HPA:         kubectl get hpa -n $NAMESPACE"
    echo "  - Scale manually:   kubectl scale deployment $DEPLOYMENT --replicas=5 -n $NAMESPACE"
    echo ""

    # Get ingress URL if available
    INGRESS_HOST=$(kubectl get ingress uatp-api-ingress -n $NAMESPACE -o jsonpath='{.spec.rules[0].host}' 2>/dev/null || echo "Not configured")
    echo "API URL: https://$INGRESS_HOST"
}

# Main deployment flow
main() {
    check_kubectl
    check_cluster
    create_namespace
    apply_configmap
    check_secrets
    deploy_application
    apply_hpa
    apply_ingress
    wait_for_deployment
    show_status
    show_info
}

# Run main function
main
