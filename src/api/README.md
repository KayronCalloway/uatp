# UATP Capsule Engine API

FastAPI-based REST API for UATP capsule operations.

## Quick Start

```bash
# Run the server
python run.py
# Server runs on http://localhost:8000

# Or with uvicorn directly
uvicorn src.main:app --reload --port 8000
```

## Key Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Health check |
| `/capsules` | GET | List capsules (paginated) |
| `/capsules/{id}` | GET | Get capsule by ID |
| `/capsules/{id}/verify` | GET | Verify capsule signature |
| `/capsules/store` | POST | Store pre-signed capsule |
| `/capsules/stats` | GET | Capsule statistics |
| `/timestamp` | POST | Get RFC 3161 timestamp for hash |

## Response Formats

### GET /capsules/{id}
```json
{
  "capsule": {
    "capsule_id": "...",
    "type": "reasoning_trace",
    "status": "sealed",
    "timestamp": "2026-03-14T12:00:00Z",
    "payload": {...},
    "verification": {...}
  },
  "verification": {...}
}
```

### GET /capsules/{id}/verify
```json
{
  "verified": true,
  "signature_valid": true,
  "hash_valid": true,
  "timestamp_valid": true,
  "details": {...}
}
```

## Authentication

- Public endpoints: `/health`, `/capsules/{id}/verify`, `/timestamp`
- Authenticated endpoints: `/capsules/store`, outcome recording
- Admin endpoints: `/capsules/admin/*`

Set `JWT_SECRET` environment variable for production.

## API Documentation

Interactive docs available at:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
