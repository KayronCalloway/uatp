#!/usr/bin/env python3
"""
OpenAPI Specification for UATP Capsule API
==========================================

This module provides the OpenAPI/Swagger specification for the UATP Capsule API.
"""

from quart import jsonify
from quart_schema import QuartSchema, validate_json, validate_querystring
from dataclasses import dataclass
from typing import List, Optional, Dict, Any
from datetime import datetime

# OpenAPI specification
openapi_spec = {
    "openapi": "3.0.0",
    "info": {
        "title": "UATP Capsule API",
        "version": "1.0.0",
        "description": "REST API for Universal Attribution and Transparency Protocol (UATP) capsule management",
        "contact": {
            "name": "UATP Team",
            "url": "https://github.com/uatp/capsule-engine",
        },
    },
    "servers": [{"url": "http://localhost:8000", "description": "Development server"}],
    "components": {
        "schemas": {
            "Capsule": {
                "type": "object",
                "properties": {
                    "capsule_id": {
                        "type": "string",
                        "description": "Unique capsule identifier",
                    },
                    "type": {
                        "type": "string",
                        "description": "Capsule type (e.g., reasoning_trace)",
                    },
                    "timestamp": {
                        "type": "string",
                        "format": "date-time",
                        "description": "Capsule creation timestamp",
                    },
                    "platform": {
                        "type": "string",
                        "description": "AI platform (e.g., claude_code, windsurf)",
                    },
                    "significance_score": {
                        "type": "number",
                        "description": "Significance score (0.0-10.0)",
                    },
                    "user_id": {"type": "string", "description": "User identifier"},
                    "conversation_id": {
                        "type": "string",
                        "description": "Conversation identifier",
                    },
                    "payload": {
                        "type": "object",
                        "description": "Capsule payload data",
                    },
                    "metadata": {
                        "type": "object",
                        "description": "Additional metadata",
                    },
                },
            },
            "CapsuleList": {
                "type": "object",
                "properties": {
                    "capsules": {
                        "type": "array",
                        "items": {"$ref": "#/components/schemas/Capsule"},
                    },
                    "pagination": {"$ref": "#/components/schemas/Pagination"},
                },
            },
            "Pagination": {
                "type": "object",
                "properties": {
                    "page": {"type": "integer"},
                    "limit": {"type": "integer"},
                    "total_count": {"type": "integer"},
                    "total_pages": {"type": "integer"},
                    "has_next": {"type": "boolean"},
                    "has_previous": {"type": "boolean"},
                },
            },
            "SearchRequest": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Search query text"},
                    "filters": {
                        "type": "object",
                        "properties": {
                            "platforms": {"type": "array", "items": {"type": "string"}},
                            "significance_range": {
                                "type": "object",
                                "properties": {
                                    "min": {"type": "number"},
                                    "max": {"type": "number"},
                                },
                            },
                            "date_range": {
                                "type": "object",
                                "properties": {
                                    "start": {"type": "string", "format": "date-time"},
                                    "end": {"type": "string", "format": "date-time"},
                                },
                            },
                            "user_ids": {"type": "array", "items": {"type": "string"}},
                            "capsule_types": {
                                "type": "array",
                                "items": {"type": "string"},
                            },
                        },
                    },
                    "sort_by": {
                        "type": "string",
                        "enum": ["timestamp", "significance", "platform", "user_id"],
                    },
                    "sort_order": {"type": "string", "enum": ["asc", "desc"]},
                    "page": {"type": "integer"},
                    "limit": {"type": "integer"},
                },
            },
            "HealthCheck": {
                "type": "object",
                "properties": {
                    "status": {"type": "string", "enum": ["healthy", "unhealthy"]},
                    "timestamp": {"type": "string", "format": "date-time"},
                    "database": {
                        "type": "object",
                        "properties": {
                            "connected": {"type": "boolean"},
                            "recent_activity": {"type": "boolean"},
                        },
                    },
                    "api": {
                        "type": "object",
                        "properties": {
                            "version": {"type": "string"},
                            "uptime": {"type": "string"},
                        },
                    },
                },
            },
            "Error": {
                "type": "object",
                "properties": {
                    "error": {"type": "string", "description": "Error message"}
                },
            },
        }
    },
    "paths": {
        "/api/capsules": {
            "get": {
                "summary": "Get capsules with pagination and filtering",
                "parameters": [
                    {
                        "name": "page",
                        "in": "query",
                        "schema": {"type": "integer", "default": 1},
                        "description": "Page number",
                    },
                    {
                        "name": "limit",
                        "in": "query",
                        "schema": {"type": "integer", "default": 20, "maximum": 100},
                        "description": "Number of items per page",
                    },
                    {
                        "name": "platform",
                        "in": "query",
                        "schema": {"type": "string"},
                        "description": "Filter by platform",
                    },
                    {
                        "name": "user_id",
                        "in": "query",
                        "schema": {"type": "string"},
                        "description": "Filter by user ID",
                    },
                    {
                        "name": "min_significance",
                        "in": "query",
                        "schema": {"type": "number"},
                        "description": "Minimum significance score",
                    },
                    {
                        "name": "max_significance",
                        "in": "query",
                        "schema": {"type": "number"},
                        "description": "Maximum significance score",
                    },
                    {
                        "name": "start_date",
                        "in": "query",
                        "schema": {"type": "string", "format": "date-time"},
                        "description": "Start date filter",
                    },
                    {
                        "name": "end_date",
                        "in": "query",
                        "schema": {"type": "string", "format": "date-time"},
                        "description": "End date filter",
                    },
                    {
                        "name": "search",
                        "in": "query",
                        "schema": {"type": "string"},
                        "description": "Search in capsule content",
                    },
                ],
                "responses": {
                    "200": {
                        "description": "Successful response",
                        "content": {
                            "application/json": {
                                "schema": {"$ref": "#/components/schemas/CapsuleList"}
                            }
                        },
                    },
                    "500": {
                        "description": "Internal server error",
                        "content": {
                            "application/json": {
                                "schema": {"$ref": "#/components/schemas/Error"}
                            }
                        },
                    },
                },
            }
        },
        "/api/capsules/{capsule_id}": {
            "get": {
                "summary": "Get a specific capsule by ID",
                "parameters": [
                    {
                        "name": "capsule_id",
                        "in": "path",
                        "required": True,
                        "schema": {"type": "string"},
                        "description": "Capsule identifier",
                    }
                ],
                "responses": {
                    "200": {
                        "description": "Successful response",
                        "content": {
                            "application/json": {
                                "schema": {"$ref": "#/components/schemas/Capsule"}
                            }
                        },
                    },
                    "404": {
                        "description": "Capsule not found",
                        "content": {
                            "application/json": {
                                "schema": {"$ref": "#/components/schemas/Error"}
                            }
                        },
                    },
                    "500": {
                        "description": "Internal server error",
                        "content": {
                            "application/json": {
                                "schema": {"$ref": "#/components/schemas/Error"}
                            }
                        },
                    },
                },
            }
        },
        "/api/capsules/search": {
            "post": {
                "summary": "Advanced capsule search with complex filters",
                "requestBody": {
                    "required": True,
                    "content": {
                        "application/json": {
                            "schema": {"$ref": "#/components/schemas/SearchRequest"}
                        }
                    },
                },
                "responses": {
                    "200": {
                        "description": "Successful response",
                        "content": {
                            "application/json": {
                                "schema": {"$ref": "#/components/schemas/CapsuleList"}
                            }
                        },
                    },
                    "500": {
                        "description": "Internal server error",
                        "content": {
                            "application/json": {
                                "schema": {"$ref": "#/components/schemas/Error"}
                            }
                        },
                    },
                },
            }
        },
        "/api/capsules/stats": {
            "get": {
                "summary": "Get capsule statistics and analytics",
                "responses": {
                    "200": {
                        "description": "Successful response",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "basic_stats": {"type": "object"},
                                        "analytics": {"type": "object"},
                                    },
                                }
                            }
                        },
                    },
                    "500": {
                        "description": "Internal server error",
                        "content": {
                            "application/json": {
                                "schema": {"$ref": "#/components/schemas/Error"}
                            }
                        },
                    },
                },
            }
        },
        "/api/capsules/recent": {
            "get": {
                "summary": "Get recent capsules",
                "parameters": [
                    {
                        "name": "limit",
                        "in": "query",
                        "schema": {"type": "integer", "default": 10, "maximum": 50},
                        "description": "Number of recent capsules to return",
                    }
                ],
                "responses": {
                    "200": {
                        "description": "Successful response",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "capsules": {
                                            "type": "array",
                                            "items": {
                                                "$ref": "#/components/schemas/Capsule"
                                            },
                                        },
                                        "count": {"type": "integer"},
                                    },
                                }
                            }
                        },
                    },
                    "500": {
                        "description": "Internal server error",
                        "content": {
                            "application/json": {
                                "schema": {"$ref": "#/components/schemas/Error"}
                            }
                        },
                    },
                },
            }
        },
        "/api/health": {
            "get": {
                "summary": "Health check endpoint",
                "responses": {
                    "200": {
                        "description": "Service is healthy",
                        "content": {
                            "application/json": {
                                "schema": {"$ref": "#/components/schemas/HealthCheck"}
                            }
                        },
                    },
                    "503": {
                        "description": "Service is unhealthy",
                        "content": {
                            "application/json": {
                                "schema": {"$ref": "#/components/schemas/HealthCheck"}
                            }
                        },
                    },
                },
            }
        },
    },
}


def get_openapi_spec():
    """Return the OpenAPI specification."""
    return openapi_spec


# Data classes for request/response validation
@dataclass
class CapsuleResponse:
    capsule_id: str
    type: str
    timestamp: datetime
    platform: str
    significance_score: float
    user_id: str
    conversation_id: str
    payload: Dict[str, Any]
    metadata: Dict[str, Any]


@dataclass
class SearchRequest:
    query: Optional[str] = None
    filters: Optional[Dict[str, Any]] = None
    sort_by: str = "timestamp"
    sort_order: str = "desc"
    page: int = 1
    limit: int = 20
