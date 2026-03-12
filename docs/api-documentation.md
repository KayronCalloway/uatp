# UATP Capsule Engine API Documentation

## Overview

The UATP (Unified Agent Trust Protocol) Capsule Engine provides a RESTful API for managing cryptographically signed capsules that track AI agent reasoning and decisions. This API enables secure, verifiable, and auditable AI operations.

## Base URL

```
http://localhost:9090
```

## Authentication

All API endpoints require authentication via API key in the request header:

```
X-API-Key: your-api-key-here
```

### API Key Permissions

- **read**: Access to GET endpoints (retrieve capsules, stats, verification)
- **write**: Access to POST endpoints (create capsules)

## Rate Limiting

The API implements rate limiting per endpoint:
- **GET endpoints**: 150 requests per minute
- **POST endpoints**: 100 requests per minute
- **Bulk operations**: 30 requests per minute

## Endpoints

### Capsules

#### GET /capsules

List all capsules with pagination and optional compression.

**Query Parameters:**
- `page` (int, default: 1): Page number
- `per_page` (int, default: 50): Items per page
- `compress` (bool, default: false): Enable response compression

**Response:**
```json
{
  "capsules": [
    {
      "capsule_id": "550e8400-e29b-41d4-a716-446655440000",
      "agent_id": "agent_123",
      "capsule_type": "reasoning_trace",
      "timestamp": "2024-01-15T10:30:00Z",
      "input": "Analyze market trends",
      "output": "Market analysis complete",
      "reasoning": "[{\"step_type\": \"observation\", \"content\": \"...\"}]",
      "model_version": "gpt-4",
      "parent_capsule": null,
      "hash_": "abc123...",
      "signature": "def456..."
    }
  ]
}
```

#### GET /capsules/{capsule_id}

Retrieve a specific capsule by ID.

**Query Parameters:**
- `include_raw` (bool, default: false): Include raw capsule data

**Response:**
```json
{
  "capsule_id": "550e8400-e29b-41d4-a716-446655440000",
  "agent_id": "agent_123",
  "capsule_type": "reasoning_trace",
  "timestamp": "2024-01-15T10:30:00Z",
  "input": "Analyze market trends",
  "output": "Market analysis complete",
  "reasoning": "[{\"step_type\": \"observation\", \"content\": \"...\"}]",
  "model_version": "gpt-4",
  "parent_capsule": null,
  "hash_": "abc123...",
  "signature": "def456...",
  "raw_data": {
    "original_json": "...",
    "capsule_model": "Capsule"
  }
}
```

#### GET /capsules/{capsule_id}/descendants

Get all descendants of a specific capsule.

**Response:**
```json
{
  "capsule_id": "550e8400-e29b-41d4-a716-446655440000",
  "descendants": [
    {
      "capsule_id": "child-capsule-id",
      "agent_id": "agent_123",
      "parent_capsule": "550e8400-e29b-41d4-a716-446655440000",
      "..."
    }
  ]
}
```

#### POST /capsules

Create a new capsule.

**Request Body:**
```json
{
  "capsule_type": "reasoning_trace",
  "input_data": "Analyze market trends",
  "output": "Market analysis complete",
  "reasoning": "[{\"step_type\": \"observation\", \"content\": \"...\"}]",
  "model_version": "gpt-4",
  "parent_capsule": null,
  "metadata": {
    "source": "api",
    "priority": "high"
  }
}
```

**Response:**
```json
{
  "capsule_id": "550e8400-e29b-41d4-a716-446655440000",
  "agent_id": "agent_123",
  "capsule_type": "reasoning_trace",
  "timestamp": "2024-01-15T10:30:00Z",
  "input": "Analyze market trends",
  "output": "Market analysis complete",
  "reasoning": "[{\"step_type\": \"observation\", \"content\": \"...\"}]",
  "model_version": "gpt-4",
  "parent_capsule": null,
  "hash_": "abc123...",
  "signature": "def456...",
  "metadata": {
    "source": "api",
    "priority": "high"
  }
}
```

#### POST /capsules/bulk

Create multiple capsules in a single request.

**Request Body:**
```json
{
  "capsules": [
    {
      "capsule_type": "reasoning_trace",
      "input_data": "Task 1",
      "output": "Result 1",
      "reasoning": "...",
      "model_version": "gpt-4"
    },
    {
      "capsule_type": "decision",
      "input_data": "Task 2",
      "output": "Result 2",
      "reasoning": "...",
      "model_version": "gpt-4"
    }
  ]
}
```

**Response:**
```json
{
  "successful_capsules": [
    {
      "capsule_id": "...",
      "..."
    }
  ],
  "failed_capsules": [
    {
      "index": 1,
      "error": "Validation failed",
      "data": {
        "capsule_type": "decision",
        "..."
      }
    }
  ]
}
```

### Search

#### GET /capsules/search

Full-text search across capsule content. Uses FTS5 for SQLite and ts_vector for PostgreSQL.

**Query Parameters:**
- `q` (string, required): Search query (min 2 characters)
- `page` (int, default: 1): Page number
- `per_page` (int, default: 10, max: 100): Results per page
- `type` (string, optional): Filter by capsule type

**Response:**
```json
{
  "query": "loan decision",
  "total_count": 42,
  "results": [
    {
      "capsule_id": "caps_2026_03_10_183645",
      "capsule_type": "reasoning_trace",
      "timestamp": "2026-03-10T18:36:45Z",
      "snippet": "Credit score 720 (excellent)...",
      "relevance_score": 0.92,
      "payload_preview": {
        "platform": "claude-code",
        "topics": ["Finance", "Risk Assessment"]
      }
    }
  ],
  "page": 1,
  "per_page": 10,
  "has_more": true,
  "total_pages": 5
}
```

#### GET /capsules/context

Verified Context Retrieval - search with cryptographic verification status. Designed for trusted RAG (Retrieval-Augmented Generation) applications where LLMs should only use verified context.

**Query Parameters:**
- `q` (string, required): Search query (min 2 characters)
- `page` (int, default: 1): Page number
- `per_page` (int, default: 10, max: 50): Results per page
- `verified_only` (bool, default: false): Only return capsules with valid signatures
- `type` (string, optional): Filter by capsule type
- `min_confidence` (float, optional): Minimum confidence score (0.0-1.0)

**Response:**
```json
{
  "query": "loan decision",
  "total_count": 15,
  "verified_count": 12,
  "results": [
    {
      "capsule_id": "caps_2026_03_10_183645",
      "capsule_type": "reasoning_trace",
      "timestamp": "2026-03-10T18:36:45Z",
      "snippet": "Credit score 720 (excellent)...",
      "relevance_score": 0.92,
      "verification": {
        "signature_valid": true,
        "signature_present": true,
        "timestamp_valid": true,
        "timestamp_present": true,
        "verification_method": "Ed25519Signature2020",
        "fully_verified": true,
        "error": null
      },
      "reasoning_summary": "Approved based on credit score and DTI ratio",
      "confidence": 0.95,
      "metadata": {
        "platform": "claude-code",
        "topics": ["Finance", "Risk Assessment"]
      }
    }
  ],
  "page": 1,
  "per_page": 10,
  "verified_only": false,
  "trust_summary": {
    "total_results": 10,
    "fully_verified": 8,
    "signature_only": 2,
    "unverified": 0
  }
}
```

**Use Cases:**
- **Trusted RAG**: Only feed verified capsules to LLMs as context
- **Audit queries**: Find decisions with specific verification status
- **Quality filtering**: Combine with `min_confidence` for high-quality context

### Verification

#### GET /capsules/{capsule_id}/verify

Verify the cryptographic signature of a capsule.

**Response:**
```json
{
  "capsule_id": "550e8400-e29b-41d4-a716-446655440000",
  "verified": true,
  "verification_method": "Ed25519Signature2020",
  "verification_error": null,
  "signature_present": true,
  "signature_metadata": {
    "signature": "abc123...",
    "signer": "local_engine",
    "verify_key": "def456..."
  },
  "message": "Capsule signature VERIFIED",
  "status": "sealed",
  "timestamp": "2024-01-15T10:30:00Z"
}
```

### Statistics

#### GET /capsules/stats

Get statistics about the capsule chain.

**Response:**
```json
{
  "total_capsules": 1250,
  "types": {
    "reasoning_trace": 800,
    "decision": 300,
    "observation": 150
  },
  "unique_agents": 5
}
```

### AI Integration

#### POST /reasoning/generate

Generate a reasoning capsule using AI.

**Request Body:**
```json
{
  "prompt": "Explain the theory of relativity",
  "model": "gpt-4",
  "agent_id": "agent_123",
  "capsule_type": "reasoning_trace"
}
```

**Response:**
```json
{
  "capsule_id": "550e8400-e29b-41d4-a716-446655440000",
  "agent_id": "agent_123",
  "capsule_type": "reasoning_trace",
  "timestamp": "2024-01-15T10:30:00Z",
  "input": "Explain the theory of relativity",
  "output": "Einstein's theory of relativity...",
  "reasoning": "[{\"step_type\": \"observation\", \"content\": \"...\"}]",
  "model_version": "gpt-4",
  "hash_": "abc123...",
  "signature": "def456..."
}
```

## Error Responses

All endpoints return consistent error responses:

```json
{
  "error": "Error message",
  "details": "Additional error details (optional)"
}
```

### HTTP Status Codes

- **200**: Success
- **201**: Created
- **400**: Bad Request
- **401**: Unauthorized (missing or invalid API key)
- **403**: Forbidden (insufficient permissions)
- **404**: Not Found
- **429**: Rate Limited
- **500**: Internal Server Error

## Data Models

### Capsule

```json
{
  "capsule_id": "string (UUID)",
  "agent_id": "string",
  "capsule_type": "string",
  "timestamp": "string (ISO 8601)",
  "input": "string",
  "output": "string",
  "reasoning": "string (JSON)",
  "model_version": "string",
  "parent_capsule": "string (UUID, optional)",
  "hash_": "string (SHA-256 hex)",
  "signature": "string (Ed25519 hex)",
  "metadata": "object (optional)"
}
```

### Reasoning Step

```json
{
  "step_type": "observation|thought|action|conclusion",
  "content": "string",
  "timestamp": "string (ISO 8601, optional)",
  "metadata": "object (optional)"
}
```

## Caching

The API implements intelligent caching:

- **Response caching**: GET endpoints cache responses for 60-300 seconds
- **AI response caching**: Generated AI responses are cached to avoid duplicate API calls
- **Cache headers**: Responses include appropriate `Cache-Control` headers

## Security

### Cryptographic Signatures

All capsules are signed using Ed25519 cryptography:
- **Signing**: Each capsule is signed with the agent's private key
- **Verification**: Signatures can be verified using the `/capsules/verify/{id}` endpoint
- **Hash integrity**: SHA-256 hashes ensure data integrity

### API Security

- **API Key Authentication**: All endpoints require valid API keys
- **Rate Limiting**: Prevents abuse with per-endpoint limits
- **Input Validation**: All inputs are validated using Pydantic schemas
- **HTTPS**: Use HTTPS in production for encrypted communication

## Performance

### Optimization Features

- **Connection pooling**: Database connections are pooled for efficiency
- **Async processing**: All operations are asynchronous
- **Pagination**: Large result sets are paginated
- **Compression**: Optional response compression for large payloads

### Performance Tuning

Configure these environment variables for optimal performance:

```env
UATP_DB_POOL_SIZE=5
UATP_DB_MAX_OVERFLOW=10
UATP_DB_POOL_RECYCLE=3600
```

## Monitoring

### Metrics

The API exposes Prometheus metrics at `/metrics` (if enabled):

- Request count and duration
- Database connection pool stats
- Cache hit/miss ratios
- Error rates

### Health Checks

- **Database**: Connection health monitoring
- **Cache**: Redis/memory cache status
- **External APIs**: OpenAI API connectivity

## Examples

### Python Client Example

```python
import requests
import json

# Configuration
API_BASE = "http://localhost:9090"
API_KEY = "your-api-key"
HEADERS = {"X-API-Key": API_KEY}

# Create a capsule
capsule_data = {
    "capsule_type": "reasoning_trace",
    "input_data": "What is 2+2?",
    "output": "4",
    "reasoning": json.dumps([
        {"step_type": "observation", "content": "I need to add 2+2"},
        {"step_type": "thought", "content": "2+2 equals 4"},
        {"step_type": "conclusion", "content": "The answer is 4"}
    ]),
    "model_version": "gpt-4"
}

response = requests.post(
    f"{API_BASE}/capsules",
    headers=HEADERS,
    json=capsule_data
)

if response.status_code == 201:
    capsule = response.json()
    print(f"Created capsule: {capsule['capsule_id']}")

    # Verify the capsule
    verify_response = requests.get(
        f"{API_BASE}/capsules/verify/{capsule['capsule_id']}",
        headers=HEADERS
    )

    if verify_response.status_code == 200:
        verification = verify_response.json()
        print(f"Verification: {verification['verified']}")
else:
    print(f"Error: {response.status_code} - {response.text}")
```

### cURL Examples

```bash
# Create a capsule
curl -X POST "http://localhost:9090/capsules" \
  -H "X-API-Key: your-api-key" \
  -H "Content-Type: application/json" \
  -d '{
    "capsule_type": "reasoning_trace",
    "input_data": "What is the capital of France?",
    "output": "Paris",
    "reasoning": "[{\"step_type\": \"observation\", \"content\": \"I need to identify the capital of France\"}]",
    "model_version": "gpt-4"
  }'

# Get capsule stats
curl -X GET "http://localhost:9090/capsules/stats" \
  -H "X-API-Key: your-api-key"

# List capsules with pagination
curl -X GET "http://localhost:9090/capsules?page=1&per_page=10" \
  -H "X-API-Key: your-api-key"
```

## Health Check Endpoints

The API provides comprehensive health check endpoints for monitoring:

### GET /health

Basic health check that returns service status.

**Response:**
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "engine": "OK",
  "database": "ok",
  "features": {
    "caching": true,
    "rate_limiting": true
  },
  "timestamp": "2024-01-15T10:30:00Z"
}
```

### GET /health/ready

Kubernetes-style readiness check that verifies all dependencies.

**Response:**
```json
{
  "status": "ready",
  "checks": {
    "database": {"status": "healthy"},
    "engine": {"status": "healthy"},
    "cache": {"status": "healthy"}
  },
  "timestamp": "2024-01-15T10:30:00Z"
}
```

### GET /health/live

Kubernetes-style liveness check that verifies the service is running.

**Response:**
```json
{
  "status": "alive",
  "timestamp": "2024-01-15T10:30:00Z",
  "uptime_seconds": 3600
}
```

### GET /health/detailed

Comprehensive health check with detailed system information.

**Response:**
```json
{
  "status": "healthy",
  "checks": {
    "database": {
      "status": "healthy",
      "response_time_ms": 15.2,
      "version": "PostgreSQL 15.0",
      "capsule_count": 1250,
      "tables_exist": true
    },
    "engine": {
      "status": "healthy",
      "agent_id": "agent_123",
      "has_signing_key": true
    },
    "cache": {
      "status": "healthy",
      "response_time_ms": 2.1,
      "read_write_test": true
    }
  },
  "system": {
    "python_version": "3.12.0",
    "environment": "production",
    "debug_mode": false,
    "testing_mode": false
  },
  "timestamp": "2024-01-15T10:30:00Z",
  "check_duration_ms": 25.3
}
```

## Support

For technical support and questions:
- Review the deployment guide: `docs/deployment-guide.md`
- Check logs: `docker-compose logs api`
- Monitor metrics: Grafana dashboard at `http://localhost:3000`
- Health checks: `curl http://localhost:9090/health`
