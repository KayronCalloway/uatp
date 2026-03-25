# Architecture

## System Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                         Frontend (Next.js :3000)                │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │ Capsule List │  │ Trust Dash   │  │ Onboarding   │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Backend (FastAPI :8000)                    │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │ /capsules    │  │ /auth        │  │ /health      │          │
│  │ /chain       │  │ /trust       │  │ /live        │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
└─────────────────────────────────────────────────────────────────┘
                              │
              ┌───────────────┼───────────────┐
              ▼               ▼               ▼
        ┌──────────┐   ┌──────────┐   ┌──────────┐
        │ SQLite   │   │ Redis    │   │ RFC 3161 │
        │ (dev)    │   │ (CSRF)   │   │ TSA      │
        └──────────┘   └──────────┘   └──────────┘
```

## Directory Structure

```
src/
├── api/                 # FastAPI routers
├── auth/                # JWT auth (3 files - all used)
├── security/            # Crypto: Ed25519, ML-DSA-65, RFC 3161
├── crypto/              # SDK signing utilities
├── models/              # SQLAlchemy models
├── live_capture/        # Claude Code hook integration
└── core/                # Config, database

frontend/
├── src/app/             # Next.js pages
├── src/components/      # React components
├── src/contexts/        # Auth, Creator, Onboarding
├── src/lib/             # API client, utils, logger
└── src/hooks/           # Custom hooks

sdk/typescript/          # TypeScript SDK
```

## Key Flows

### Capsule Creation
```
Claude Code Hook → rich_hook_capture.py → live_capture/
    → Sign with Ed25519
    → Timestamp with RFC 3161
    → Store in SQLite
```

### Authentication
```
Frontend → /auth/login → JWT issued
    → Stored in sessionStorage
    → Sent as Bearer token
    → Backend validates claims
```

## Technical Debt

| Area | Issue | Status |
|------|-------|--------|
| `src/security/` vs `src/crypto/` | Overlapping key managers | Keep separate |
| `src/auth/` | 3 JWT files | All actively used |
| `archive/` | ~60K lines speculative code | Archived, not deleted |

## Security Architecture

- **Signing**: Ed25519 (fast) + ML-DSA-65 (post-quantum)
- **Timestamps**: RFC 3161 TSA
- **Auth**: JWT in sessionStorage (not localStorage)
- **CSRF**: Redis-backed tokens (skipped for Bearer auth endpoints)
- **Secrets**: gitleaks scanning + pre-commit hooks

## Database

- **Dev**: SQLite (`uatp_dev.db`)
- **Prod**: PostgreSQL (via `DATABASE_URL`)
- **Migrations**: Alembic
- **Model**: Single `CapsuleModel` (no polymorphism)
