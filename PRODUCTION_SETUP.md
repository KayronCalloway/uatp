# UATP Production Setup Guide

Complete guide for deploying UATP to production with real AI integration, database, payment processors, and Kubernetes.

## 🚀 Quick Start

1. **Set up environment variables:**
   ```bash
   cp .env.example .env
   # Edit .env with your production credentials
   ```

2. **Deploy to Kubernetes:**
   ```bash
   ./deployment/scripts/deploy.sh
   ```

3. **Test the deployment:**
   ```bash
   ./deployment/scripts/test-production.sh --url https://api.uatp.example.com
   ```

## 📋 Prerequisites

### Required Tools
- Docker (20.10+)
- Kubernetes (1.24+)
- kubectl configured with cluster access
- Helm (3.8+) - optional but recommended

### Required Accounts & Credentials
- **AI Platforms:**
  - OpenAI API key
  - Anthropic API key
  - HuggingFace API key (optional)
  - Cohere API key (optional)

- **Payment Processors:**
  - Stripe account (live keys)
  - PayPal business account
  - Crypto wallet addresses (optional)

- **Infrastructure:**
  - PostgreSQL database
  - Redis instance
  - Domain name and SSL certificates
  - Cloud storage (AWS S3)
  - Email service (SendGrid)

## 🔧 Environment Configuration

### 1. Copy Environment Template
```bash
cp .env.example .env
```

### 2. Configure API Keys

#### AI Platform Keys
```bash
# OpenAI
OPENAI_API_KEY=sk-your-openai-api-key-here

# Anthropic
ANTHROPIC_API_KEY=sk-ant-your-anthropic-api-key-here

# HuggingFace (optional)
HUGGINGFACE_API_KEY=hf_your-huggingface-api-key-here

# Cohere (optional)
COHERE_API_KEY=your-cohere-api-key-here
```

#### Payment Processor Keys
```bash
# Stripe
STRIPE_SECRET_KEY=sk_live_your_stripe_secret_key
STRIPE_PUBLISHABLE_KEY=pk_live_your_stripe_publishable_key
STRIPE_WEBHOOK_SECRET=whsec_your_webhook_secret

# PayPal
PAYPAL_CLIENT_ID=your_paypal_client_id
PAYPAL_CLIENT_SECRET=your_paypal_client_secret
PAYPAL_MODE=live
```

#### Database Configuration
```bash
# PostgreSQL
DATABASE_URL=postgresql://uatp_user:your_password@localhost:5432/uatp_production
DATABASE_HOST=localhost
DATABASE_PORT=5432
DATABASE_NAME=uatp_production
DATABASE_USER=uatp_user
DATABASE_PASSWORD=your_secure_password

# Redis
REDIS_URL=redis://localhost:6379/0
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
```

#### Security Configuration
```bash
# Generate secure keys
SECRET_KEY=your-super-secret-key-for-jwt-tokens
JWT_SECRET=your-jwt-secret-key
ENCRYPTION_KEY=your-32-character-encryption-key
```

## 🗄️ Database Setup

### Option 1: Managed Database (Recommended)
Use managed PostgreSQL service:
- **AWS RDS**
- **Google Cloud SQL**
- **Azure Database for PostgreSQL**
- **DigitalOcean Managed Database**

### Option 2: Self-Hosted Database
```bash
# Create database
createdb uatp_production

# Create user
psql -c "CREATE USER uatp_user WITH PASSWORD 'your_secure_password';"
psql -c "GRANT ALL PRIVILEGES ON DATABASE uatp_production TO uatp_user;"

# Run migrations
python -m src.database.migrations create
```

### Database Migrations
```bash
# Check migration status
python -m src.database.migrations status

# Run migrations
python -m src.database.migrations migrate

# Reset database (development only)
python -m src.database.migrations reset
```

## 🚢 Kubernetes Deployment

### 1. Prepare Kubernetes Cluster

#### Create Namespace
```bash
kubectl apply -f deployment/kubernetes/namespace.yaml
```

#### Update Secrets
Edit `deployment/kubernetes/configmap.yaml` with your credentials:
```yaml
# Update the secrets section with your actual values
stringData:
  DATABASE_PASSWORD: "your_actual_password"
  OPENAI_API_KEY: "sk-your-actual-openai-key"
  STRIPE_SECRET_KEY: "sk_live_your_actual_stripe_key"
  # ... etc
```

### 2. Deploy Infrastructure

#### Deploy PostgreSQL
```bash
kubectl apply -f deployment/kubernetes/postgresql.yaml
```

#### Deploy Redis
```bash
kubectl apply -f deployment/kubernetes/redis.yaml
```

#### Deploy Application
```bash
kubectl apply -f deployment/kubernetes/uatp-app.yaml
```

#### Deploy Monitoring
```bash
kubectl apply -f deployment/kubernetes/monitoring.yaml
```

### 3. Configure Ingress

#### Install NGINX Ingress Controller
```bash
helm repo add ingress-nginx https://kubernetes.github.io/ingress-nginx
helm install ingress-nginx ingress-nginx/ingress-nginx
```

#### Configure SSL with cert-manager
```bash
# Install cert-manager
kubectl apply -f https://github.com/cert-manager/cert-manager/releases/download/v1.13.0/cert-manager.yaml

# Create ClusterIssuer
kubectl apply -f - <<EOF
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
EOF
```

### 4. Full Deployment Script

Use the automated deployment script:
```bash
# Deploy everything
./deployment/scripts/deploy.sh

# Deploy with custom settings
./deployment/scripts/deploy.sh --version v1.0.0 --registry your-registry.com/uatp

# Skip certain steps
./deployment/scripts/deploy.sh --skip-build --skip-db
```

## 🐳 Docker Deployment (Alternative)

### 1. Using Docker Compose
```bash
# Set environment variables
export DATABASE_PASSWORD=your_secure_password
export OPENAI_API_KEY=sk-your-openai-key
export STRIPE_SECRET_KEY=sk_live_your_stripe_key
# ... set all required variables

# Deploy
cd deployment/docker
docker-compose up -d
```

### 2. Single Container Deployment
```bash
# Build image
docker build -t uatp:latest -f deployment/docker/Dockerfile .

# Run container
docker run -d \
  --name uatp-app \
  -p 8000:8000 \
  --env-file .env \
  uatp:latest
```

## 🔍 Testing Production Deployment

### 1. Health Checks
```bash
# Basic health check
curl https://api.uatp.example.com/health

# Readiness check
curl https://api.uatp.example.com/ready

# Metrics
curl https://api.uatp.example.com/metrics
```

### 2. Full Test Suite
```bash
# Test everything
./deployment/scripts/test-production.sh --url https://api.uatp.example.com

# Test specific components
./deployment/scripts/test-production.sh --url https://api.uatp.example.com --env production
```

### 3. Load Testing
```bash
# Install locust
pip install locust

# Run load test
locust -f tests/load_test.py --host https://api.uatp.example.com
```

## 🔧 Live AI Integration Testing

### 1. Set API Keys
```bash
export OPENAI_API_KEY="sk-your-actual-openai-key"
export ANTHROPIC_API_KEY="sk-ant-your-actual-anthropic-key"
```

### 2. Test AI Attribution
```bash
# Run the complete integration demo
python complete_app_integration_demo.py

# Test specific AI platforms
python -c "
import asyncio
from src.integrations.openai_attribution import OpenAIAttributionClient
from src.integrations.anthropic_client import AnthropicAttributionClient

async def test_ai():
    # Test OpenAI
    openai_client = OpenAIAttributionClient()
    result = await openai_client.get_completion_with_attribution(
        prompt='Test prompt',
        attribution_context={'user_id': 'test_user'}
    )
    print('OpenAI:', result)

    # Test Anthropic
    anthropic_client = AnthropicAttributionClient()
    result = await anthropic_client.get_completion_with_attribution(
        prompt='Test prompt',
        attribution_context={'user_id': 'test_user'}
    )
    print('Anthropic:', result)

asyncio.run(test_ai())
"
```

## 🎯 Domain and SSL Setup

### 1. Domain Configuration
```bash
# Point your domain to the Kubernetes cluster
# Example DNS records:
# api.uatp.example.com -> <your-k8s-loadbalancer-ip>
# uatp.example.com -> <your-k8s-loadbalancer-ip>
```

### 2. SSL Certificate
```bash
# Update ingress with your domain
kubectl edit ingress uatp-ingress -n uatp-production

# cert-manager will automatically provision SSL certificates
```

## 💳 Payment Processor Setup

### 1. Stripe Configuration
```bash
# Test Stripe integration
curl -X POST https://api.uatp.example.com/api/v1/payments/payout \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "test_user",
    "amount": 25.00,
    "payout_method": "stripe"
  }'
```

### 2. PayPal Configuration
```bash
# Test PayPal integration
curl -X POST https://api.uatp.example.com/api/v1/payments/payout \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "test_user",
    "amount": 25.00,
    "payout_method": "paypal"
  }'
```

## 📊 Monitoring and Observability

### 1. Prometheus Metrics
```bash
# Check metrics
curl https://api.uatp.example.com/metrics
```

### 2. Grafana Dashboard
```bash
# Port forward to Grafana
kubectl port-forward service/grafana 3000:3000 -n uatp-production

# Access dashboard at http://localhost:3000
# Default credentials: admin/admin
```

### 3. Logs
```bash
# View application logs
kubectl logs -f deployment/uatp-app -n uatp-production

# View database logs
kubectl logs -f deployment/postgresql -n uatp-production
```

## 🚨 Troubleshooting

### Common Issues

#### Database Connection Failed
```bash
# Check database status
kubectl get pods -n uatp-production -l app=postgresql

# Check database logs
kubectl logs -f deployment/postgresql -n uatp-production

# Test connection
kubectl exec -it deployment/postgresql -n uatp-production -- psql -U uatp_user -d uatp_production
```

#### AI API Errors
```bash
# Check API key configuration
kubectl get secret uatp-secrets -n uatp-production -o yaml

# Test API keys
python -c "
import openai
openai.api_key = 'your-key'
print(openai.models.list())
"
```

#### Payment Processing Issues
```bash
# Check payment service logs
kubectl logs -f deployment/uatp-app -n uatp-production | grep payment

# Test payment endpoints
curl -X POST https://api.uatp.example.com/api/v1/payments/payout \
  -H "Content-Type: application/json" \
  -d '{"user_id": "test", "amount": 10.00}'
```

### Getting Help

1. **Check logs**: Always start with application and database logs
2. **Health endpoints**: Use `/health`, `/ready`, `/metrics` for diagnostics
3. **Test scripts**: Run the test script to identify issues
4. **Documentation**: Refer to component-specific documentation

## 🔄 Backup and Recovery

### Database Backup
```bash
# Create backup
kubectl exec deployment/postgresql -n uatp-production -- pg_dump -U uatp_user uatp_production > backup.sql

# Restore backup
kubectl exec -i deployment/postgresql -n uatp-production -- psql -U uatp_user uatp_production < backup.sql
```

### Application State
```bash
# Export configurations
kubectl get all -n uatp-production -o yaml > uatp-backup.yaml

# Restore configurations
kubectl apply -f uatp-backup.yaml
```

## 🎉 Success Checklist

- [ ] Environment variables configured
- [ ] Database deployed and migrated
- [ ] Redis deployed and accessible
- [ ] Application deployed and healthy
- [ ] SSL certificates provisioned
- [ ] AI integration tested with real API keys
- [ ] Payment processors configured
- [ ] Monitoring and alerting set up
- [ ] Domain pointing to application
- [ ] Load testing completed
- [ ] Backup procedures tested

## 📞 Support

For production deployment support:
- Check the troubleshooting section
- Review logs and metrics
- Run the test script for diagnostics
- Refer to component documentation

---

🚀 **UATP is now ready for production!**

Your AI attribution and payment platform is live and ready to handle real user traffic, process payments, and track AI attributions at scale.
