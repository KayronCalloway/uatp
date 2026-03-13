# UATP Capsule Engine - Claude Code Context

## Quick Reference

### Common Issues & Solutions

#### 1. Stats count doesn't match database
```bash
# Check for NULL IDs (causes COUNT to be wrong)
sqlite3 uatp_dev.db "SELECT COUNT(*) FROM capsules WHERE id IS NULL"

# Fix NULL IDs
sqlite3 uatp_dev.db "UPDATE capsules SET id = (SELECT COALESCE(MAX(id), 0) + 1 FROM capsules) + rowid WHERE id IS NULL"
```
See: `docs/incidents/2026-01-13_ORM_POLYMORPHISM_INCIDENT.md`

#### 2. Frontend shows "Verification Data Not Available"
```bash
cd frontend && rm -rf .next && npm run build
# Then restart dev server
```

#### 3. ORM queries return None instead of objects
- **Root cause:** Polymorphism misconfiguration (subclasses with `polymorphic_identity` but base without `polymorphic_on`)
- **Solution:** All 26 subclasses were removed on 2026-01-13
- **Test:** `pytest tests/integration/test_capsule_orm.py -v`

### Architecture Notes

#### Module Structure (Known Technical Debt)

**Core Crypto (canonical imports):**
```python
from src.security.uatp_crypto_v7 import UATPCryptoV7  # Ed25519 + ML-DSA-65
from src.security.rfc3161_timestamps import RFC3161Timestamper  # Timestamping
from src.crypto.local_signer import LocalSigner  # SDK local signing
```

**Known Overlaps (DO NOT consolidate without careful migration):**
- `src/security/` and `src/crypto/` both have key managers
- `src/auth/` has 3 JWT files (jwt_manager.py, jwt_handler.py, jwt_auth.py) - all actively used by different parts
- Archived: `src/verifier/`, `src/verification/` → `archive/src/`

**Archived Speculative Code (~60K lines):**
- `archive/src/ai_rights/` - AI rights concepts
- `archive/src/governance/` - Governance frameworks
- `archive/src/economic/` - Economic models
- `archive/src/compliance/` - Compliance frameworks

#### Database
- SQLite in dev: `uatp_dev.db`
- Config: `src/core/config.py` reads `DATABASE_URL` from `.env`
- Models: `src/models/capsule.py` - uses single `CapsuleModel` (no polymorphism)

#### Capsule Capture
- Hook: `.claude/hooks/auto_capture.sh`
- Capture script: `rich_hook_capture.py` -> `src/live_capture/claude_code_capture.py`
- Signing: Ed25519 signatures + RFC 3161 timestamps
- Signal detection: `src/live_capture/signal_detector.py` - detects implicit feedback (corrections, acceptance, refinement, abandonment)

#### API
- FastAPI backend on port 8000
- Capsules router: `src/api/capsules_fastapi_router.py`
- Verify endpoint: `/capsules/{id}/verify`

#### Frontend
- Next.js on port 3000
- API client: `frontend/src/lib/api-client.ts`
- Capsule detail: `frontend/src/components/capsules/capsule-detail.tsx`

### Debugging Commands

```bash
# Check backend status
curl -s "http://localhost:8000/capsules/stats" | python3 -m json.tool

# Check recent capsules with signatures
sqlite3 uatp_dev.db "SELECT capsule_id, json_extract(verification, '$.signature') IS NOT NULL as has_sig FROM capsules ORDER BY timestamp DESC LIMIT 5"

# Test verify endpoint
curl -s "http://localhost:8000/capsules/{CAPSULE_ID}/verify" | python3 -m json.tool

# Run ORM tests
pytest tests/integration/test_capsule_orm.py -v

# Check frontend logs
tail -50 frontend/frontend.log
```

### Recent Incidents

| Date | Issue | Resolution |
|------|-------|------------|
| 2026-01-13 | ORM returning None | Removed 26 polymorphism subclasses |
| 2026-01-13 | Stats count 93 vs 120 | Fixed 27 NULL IDs in database |
| 2026-01-13 | Verification not showing | Rebuilt frontend (webpack cache) |

Full details: `docs/incidents/2026-01-13_ORM_POLYMORPHISM_INCIDENT.md`
