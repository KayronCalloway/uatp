# UATP Capsule Engine API

This document provides comprehensive documentation for the UATP Capsule Engine API, a secure and efficient interface for interacting with UATP capsule chains.

## Overview

The API provides a robust set of endpoints for retrieving and managing capsules, with a strong focus on security, performance, and legal admissibility. Key features include:

- **Role-Based Authentication**: Secure access control using API keys with assigned roles.
- **Configurable Rate Limiting**: Protects the API from abuse and ensures fair usage.
- **Efficient Compression**: Reduces payload size for faster data transfer.
- **Cryptographic Chain Sealing**: Provides a mechanism for creating legally admissible snapshots of the chain.
- **Detailed Statistics**: Offers insights into chain composition and activity.

## Setup and Configuration

### Prerequisites
- Python 3.9+
- All dependencies listed in `requirements.txt`

### Installation
```bash
pip install -r requirements.txt
```

### Environment Variables
Configuration is managed via environment variables. See `.env.example` for a template.

- `UATP_API_PORT`: Port for the API server (default: `5006`).
- `UATP_API_KEYS`: JSON string defining API keys and their associated roles. See the Authentication section for details.
- `UATP_TEST_API_KEY`: A dedicated API key for running the automated test suite.
- `UATP_CHAIN_PATH`: Filesystem path to the capsule chain data (`capsule_chain.jsonl`).
- `FLASK_DEBUG`: Set to `true` to enable Flask's debug mode.

### Running the Server
```bash
# Run with default settings
python -m api.server

# Run on a custom port
UATP_API_PORT=8000 python -m api.server
```

## Security Features

### Authentication
The API uses a role-based access control (RBAC) system managed by API keys. Keys are defined in the `UATP_API_KEYS` environment variable.

**Format**:
A JSON object where keys are the API keys and values are a list of assigned roles.
```json
{
  "your-super-secret-key": ["read", "write"],
  "another-read-only-key": ["read"]
}
```

**Roles**:
- `read`: Grants access to `GET` endpoints (`/capsules`, `/capsules/stats`, `/health`).
- `write`: Grants access to `POST` endpoints (`/chain/seal`).
- `admin`: Reserved for future administrative tasks.

Requests must include the `X-API-Key` header with a valid key.

### Rate Limiting
Rate limits are applied per endpoint to prevent abuse. The limits are defined directly in the `server.py` code and can be customized.

- `/capsules`: 5 requests per minute
- `/capsules/stats`: 10 requests per minute
- `/chain/seal`: 5 requests per minute
- `/chain/verify-seal`: 10 requests per minute

Exceeding a rate limit will result in a `429 Too Many Requests` error.

## Performance

### Compression
The `/capsules` endpoint supports optional response compression to reduce payload size.

To receive a compressed response, include the `compress=true` query parameter:
```bash
curl -H "X-API-Key: <your_key>" "http://localhost:5006/capsules?compress=true"
```
The response body will be a Base64-encoded, zlib-compressed JSON string of the capsule list.

## API Endpoints

### `GET /health`
Returns the operational status of the API server.

- **Permissions**: None
- **Response**:
  ```json
  {
    "status": "healthy",
    "version": "2.0.0",
    "engine": "UATP Capsule Engine"
  }
  ```

### `GET /capsules`
Retrieves a list of all capsules in the chain.

- **Permissions**: `read`
- **Query Parameters**:
  - `compress` (optional, boolean): If `true`, returns a compressed response.
- **Success Response (200)**:
  - If `compress=false`: A JSON array of capsule objects.
  - If `compress=true`: A JSON object `{"data": "<base64_encoded_zlib_string>"}`.

### `GET /capsules/stats`
Returns statistical information about the capsule chain.

- **Permissions**: `read`
- **Success Response (200)**: A JSON object with chain statistics.
  ```json
  {
    "total_capsules": 5,
    "capsule_types": {
      "Refusal": 1,
      "Introspective": 2,
      "Joint": 2
    },
    "agent_ids": ["test-agent"],
    "first_capsule_timestamp": "...",
    "last_capsule_timestamp": "..."
  }
  ```

### `POST /chain/seal`
Creates a cryptographic seal of the current state of the capsule chain.

- **Permissions**: `write`
- **Success Response (200)**: A JSON object containing the seal details.
  ```json
  {
    "chain_hash": "...",
    "signature": "...",
    "signed_at": "..."
  }
  ```

### `GET /chain/verify-seal`
Verifies the most recent chain seal against the current chain data.

- **Permissions**: `read`
- **Success Response (200)**: A JSON object indicating the verification status.
  ```json
  {
    "verified": true,
    "message": "Chain seal is valid."
  }
  ```

## Testing

A comprehensive test suite is provided to validate all API functionality.

**To run the tests**:
```bash
python -m api.test_enhanced_api --port 5006
```
The test script will automatically start the API server, run all tests, and then shut down the server.
