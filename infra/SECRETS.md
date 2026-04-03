# Secrets Management Guide

This document outlines the security practices for managing secrets in the UATP Capsule Engine.

## Core Principles

1. **Never commit secrets to git** - All `.env` files and Kubernetes secrets are gitignored
2. **Use example files as templates** - Copy `.example` files and fill in real values locally
3. **Rotate secrets regularly** - Especially after team member offboarding
4. **Use secrets managers in production** - AWS Secrets Manager, HashiCorp Vault, etc.

## Local Development

### Quick Start

```bash
# 1. Copy example files
cp infra/docker/environments/dev.env.example infra/docker/environments/dev.env
cp .env.example .env

# 2. Generate secure keys
python -c "import secrets; print(secrets.token_urlsafe(32))"

# 3. Fill in your API keys and credentials in the copied files
```

### Required Secrets

| Secret | Where to Get |
|--------|--------------|
| `DATABASE_PASSWORD` | Generate locally or use Docker Compose default |
| `JWT_SECRET` | Generate with `secrets.token_urlsafe(32)` |
| `OPENAI_API_KEY` | https://platform.openai.com/api-keys |
| `ANTHROPIC_API_KEY` | https://console.anthropic.com/ |
| `STRIPE_*` | https://dashboard.stripe.com/test/apikeys |

## Kubernetes Deployment

### Development/Staging

```bash
# Option 1: Create secret from file
kubectl create secret generic uatp-secrets \
  --from-env-file=infra/docker/environments/dev.env \
  -n uatp-dev

# Option 2: Create from literal values
kubectl create secret generic uatp-secrets \
  --from-literal=DATABASE_URL='postgresql://...' \
  --from-literal=JWT_SECRET='...' \
  -n uatp-dev
```

### Production (Recommended Approaches)

#### 1. External Secrets Operator (Recommended)

```yaml
apiVersion: external-secrets.io/v1beta1
kind: ExternalSecret
metadata:
  name: uatp-secrets
spec:
  refreshInterval: 1h
  secretStoreRef:
    name: aws-secrets-manager
    kind: SecretStore
  target:
    name: uatp-secrets
  data:
    - secretKey: DATABASE_URL
      remoteRef:
        key: uatp/production/database
        property: url
```

#### 2. Sealed Secrets (Bitnami)

```bash
# Install kubeseal
brew install kubeseal

# Encrypt secrets
kubeseal --format yaml < secret.yaml > sealed-secret.yaml

# Apply sealed secret (safe to commit)
kubectl apply -f sealed-secret.yaml
```

#### 3. HashiCorp Vault

```bash
# Store secrets
vault kv put secret/uatp/prod DATABASE_URL="postgresql://..."

# Use Vault Agent Injector in pods
```

## UATP Cryptographic Keys

UATP signing keys require special handling:

```bash
# Keys are stored encrypted in .uatp_keys/
# Encryption password should be stored in your secrets manager

# For development, keys are auto-generated on first run
python -m src.security.uatp_crypto_v7 --generate-keys

# For production, generate offline and store securely:
# - Private keys: secrets manager only
# - Public keys: can be distributed
```

## Security Checklist

- [ ] All `.env` files are gitignored
- [ ] No hardcoded credentials in source code
- [ ] Secrets rotated after team changes
- [ ] Production uses external secrets manager
- [ ] Backup encryption keys stored separately from backups
- [ ] API keys have minimum required permissions
- [ ] Webhook secrets are unique per environment

## Incident Response

If secrets are accidentally committed:

1. **Immediately rotate** all exposed credentials
2. **Revoke** any API keys that were exposed
3. **Remove from git history**:
   ```bash
   git filter-branch --force --index-filter \
     "git rm --cached --ignore-unmatch path/to/secret" \
     --prune-empty --tag-name-filter cat -- --all
   ```
4. **Force push** (coordinate with team)
5. **Document** the incident

## Questions?

Contact the security team or open an issue.
