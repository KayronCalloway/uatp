# UATP Capsule Engine Reasoning API Documentation

This document provides comprehensive documentation for the Reasoning Analysis API endpoints in the UATP Capsule Engine. These endpoints enable external systems to validate, analyze, and compare reasoning traces programmatically.

## Base URL

```
http://localhost:5006/reasoning
```

## Authentication

All API endpoints require authentication using an API key header:

```
X-API-Key: your_api_key
```

API keys have associated roles (`read`, `write`, `admin`) that determine access permissions.

## Rate Limiting

Endpoints are rate-limited to prevent abuse. Current limit: 1 request per 5 seconds.

## Endpoints

### 1. Validate Reasoning

**Endpoint:** `/reasoning/validate`
**Method:** POST
**Description:** Validates reasoning traces for structural and logical integrity.

#### Request Body

```json
{
  "capsule_id": "string",  // Optional: ID of the capsule containing the reasoning trace
  "reasoning_trace": []    // Optional: Direct reasoning trace data (either as structured data or string list)
}
```

Note: You must provide either `capsule_id` or `reasoning_trace`.

#### Response

```json
{
  "capsule_id": "string",  // Only included if capsule_id was provided
  "validation_result": {
    "is_valid": true,
    "issues": [
      {
        "message": "string",
        "severity": "warning|error"
      }
    ],
    "score": 75.5,
    "suggestions": ["string"]
  }
}
```

### 2. Analyze Reasoning

**Endpoint:** `/reasoning/analyze`
**Method:** POST
**Description:** Analyzes reasoning traces for patterns, quality metrics, and insights.

#### Request Body

```json
{
  "capsule_id": "string",  // Optional: ID of the capsule containing the reasoning trace
  "reasoning_trace": []    // Optional: Direct reasoning trace data (either as structured data or string list)
}
```

Note: You must provide either `capsule_id` or `reasoning_trace`.

#### Response

```json
{
  "analysis": {
    "average_confidence": 0.85,
    "step_count": 6,
    "has_conclusion": true,
    "type_distribution": {
      "observation": 0.33,
      "inference": 0.17,
      "evidence": 0.17,
      "reflection": 0.17,
      "conclusion": 0.16
    },
    "patterns": ["observation_inference_conclusion", "reflective"],
    "flow": {
      "confidence_trend": "stable",
      "flow_quality": "good",
      "early_step_placement": "good",
      "late_step_placement": "good"
    }
  }
}
```

### 3. Compare Reasoning Traces

**Endpoint:** `/reasoning/compare`
**Method:** POST
**Description:** Compares two reasoning traces for similarities and differences.

#### Request Body

```json
{
  "capsule_id1": "string",      // Optional: ID of the first capsule
  "capsule_id2": "string",      // Optional: ID of the second capsule
  "reasoning_trace1": [],       // Optional: First reasoning trace data
  "reasoning_trace2": []        // Optional: Second reasoning trace data
}
```

Note: You must provide either capsule IDs or reasoning traces for both traces to be compared.

#### Response

```json
{
  "comparison": {
    "step_count_diff": -2,
    "confidence_diff": 0.15,
    "type_distribution_diffs": {
      "observation": 0.05,
      "inference": -0.1,
      "evidence": 0.0,
      "reflection": -0.1,
      "conclusion": 0.15
    },
    "common_patterns": ["observation_based"],
    "unique_patterns": {
      "trace1": ["reflective", "observation_inference_conclusion"],
      "trace2": []
    }
  }
}
```

### 4. Analyze Batch Reasoning

**Endpoint:** `/reasoning/analyze-batch`
**Method:** POST
**Description:** Analyzes multiple reasoning traces for aggregate metrics and trends.

#### Request Body

```json
{
  "capsule_ids": ["string"],    // Optional: List of capsule IDs
  "reasoning_traces": []        // Optional: List of reasoning trace data
}
```

Note: You must provide either capsule IDs or reasoning traces or both.

#### Response

```json
{
  "batch_size": 3,
  "analysis": {
    "trace_count": 3,
    "step_statistics": {
      "min": 2,
      "max": 8,
      "mean": 5.3,
      "median": 6.0
    },
    "confidence_statistics": {
      "min": 0.6,
      "mean": 0.82,
      "max": 0.95
    },
    "common_patterns": [
      {
        "pattern": "observation_inference_conclusion",
        "frequency": 0.67
      },
      {
        "pattern": "reflective",
        "frequency": 0.33
      }
    ],
    "aggregate_type_distribution": {
      "observation": 0.35,
      "inference": 0.2,
      "evidence": 0.15,
      "reflection": 0.15,
      "conclusion": 0.15
    }
  }
}
```

## Reasoning Trace Format

Reasoning traces can be provided in two formats:

### 1. String List Format

```json
[
  "I observe that the input contains a potential security vulnerability.",
  "Based on the code structure, this could lead to an SQL injection attack.",
  "Therefore, I recommend implementing parameterized queries."
]
```

### 2. Structured Format

```json
{
  "steps": [
    {
      "content": "I observe that the input contains a potential security vulnerability.",
      "step_type": "OBSERVATION",
      "confidence": 0.95,
      "timestamp": "2025-07-03T14:00:00Z",
      "metadata": {}
    },
    {
      "content": "Based on the code structure, this could lead to an SQL injection attack.",
      "step_type": "INFERENCE",
      "confidence": 0.85,
      "metadata": {}
    },
    {
      "content": "Therefore, I recommend implementing parameterized queries.",
      "step_type": "CONCLUSION",
      "confidence": 1.0,
      "metadata": {}
    }
  ]
}
```

## Error Handling

All endpoints return appropriate HTTP status codes:
- 200: Success
- 400: Bad Request (missing or invalid parameters)
- 401: Unauthorized (invalid API key)
- 404: Not Found (capsule not found)
- 429: Too Many Requests (rate limit exceeded)
- 500: Internal Server Error

## Examples

### Example 1: Validate a capsule's reasoning

```python
import requests
import json

headers = {"X-API-Key": "your_api_key"}
data = {"capsule_id": "851fa3b4-1423-4251-b7b0-d9afdf480e7d"}

response = requests.post(
    "http://localhost:5006/reasoning/validate",
    headers=headers,
    json=data
)

print(json.dumps(response.json(), indent=2))
```

### Example 2: Compare two reasoning traces

```python
import requests
import json

headers = {"X-API-Key": "your_api_key"}
data = {
    "reasoning_trace1": [
        "I observe the user is requesting access to sensitive data.",
        "The user's authorization level is insufficient.",
        "According to security protocols, access must be denied.",
        "I will deny access and recommend proper authorization channels.",
        "Access denied due to insufficient permissions."
    ],
    "reasoning_trace2": [
        "User requesting sensitive data access.",
        "Permissions sufficient, granting access."
    ]
}

response = requests.post(
    "http://localhost:5006/reasoning/compare",
    headers=headers,
    json=data
)

print(json.dumps(response.json(), indent=2))
```

## Best Practices

1. **Cache Results**: Consider caching validation and analysis results for frequently accessed capsules.
2. **Rate Limit Consideration**: Implement backoff strategies when encountering rate limiting.
3. **Batch Processing**: Use `/reasoning/analyze-batch` for processing multiple traces efficiently.
4. **Error Handling**: Always check for and handle HTTP error codes appropriately.
5. **Provide Context**: When comparing traces, consider including metadata about the purpose of each trace for better context.
