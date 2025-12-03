"""
OpenAPI Examples and Documentation Enhancements
Comprehensive examples for all API endpoints
"""

# User Registration Examples
USER_REGISTRATION_EXAMPLES = {
    "normal_user": {
        "summary": "Standard User Registration",
        "description": "Register a standard user with basic information",
        "value": {
            "username": "alice_creator",
            "email": "alice@example.com",
            "password": "SecurePassword123!",
            "full_name": "Alice Creator",
            "user_type": "creator",
            "metadata": {
                "preferred_attribution_method": "direct",
                "content_specialization": ["ai_training", "technical_writing"],
            },
        },
    },
    "platform_integration": {
        "summary": "Platform Integration User",
        "description": "Register a user representing an AI platform",
        "value": {
            "username": "openai_platform",
            "email": "integration@openai.com",
            "password": "PlatformKey789$",
            "full_name": "OpenAI Platform Integration",
            "user_type": "platform",
            "metadata": {
                "platform_type": "ai_provider",
                "supported_models": ["gpt-4", "gpt-3.5-turbo"],
                "api_version": "v1",
            },
        },
    },
}

# Attribution Tracking Examples
ATTRIBUTION_TRACKING_EXAMPLES = {
    "ai_conversation": {
        "summary": "AI Conversation Attribution",
        "description": "Track attribution for an AI conversation with multiple sources",
        "value": {
            "user_id": "user_alice_123",
            "conversation_id": "conv_20240712_456",
            "platform": "openai",
            "model": "gpt-4",
            "prompt": "Explain quantum computing principles",
            "completion": "Quantum computing uses quantum mechanics principles...",
            "estimated_cost": 0.0024,
            "prompt_sources": [
                "user_input",
                "technical_documentation",
                "research_papers",
            ],
            "training_data_sources": ["web_crawl", "academic_papers", "textbooks"],
            "metadata": {
                "conversation_turn": 1,
                "processing_time_ms": 1250,
                "token_count": {"prompt": 48, "completion": 150},
            },
        },
    },
    "multimodal_interaction": {
        "summary": "Multimodal AI Interaction",
        "description": "Track attribution for interactions involving text and images",
        "value": {
            "user_id": "user_bob_456",
            "conversation_id": "conv_20240712_789",
            "platform": "anthropic",
            "model": "claude-3-5-sonnet",
            "prompt": "Analyze this architectural image",
            "completion": "This image shows a modern building with...",
            "estimated_cost": 0.0156,
            "prompt_sources": ["user_input", "image_upload", "architectural_database"],
            "training_data_sources": [
                "image_datasets",
                "architectural_texts",
                "web_crawl",
            ],
            "metadata": {
                "modality": "text_and_image",
                "image_size": "1024x768",
                "analysis_type": "architectural",
            },
        },
    },
}

# Payment/Payout Examples
PAYOUT_REQUEST_EXAMPLES = {
    "creator_payout": {
        "summary": "Content Creator Payout",
        "description": "Request payout for accumulated attribution earnings",
        "value": {
            "user_id": "user_alice_123",
            "amount": 25.50,
            "currency": "USD",
            "payout_method": "bank_transfer",
            "description": "Monthly attribution earnings payout",
            "metadata": {
                "attribution_period": "2024-06",
                "total_attributions": 142,
                "average_attribution": 0.18,
                "payout_schedule": "monthly",
            },
        },
    },
    "instant_micropayment": {
        "summary": "Instant Micropayment",
        "description": "Small instant payout for immediate attribution",
        "value": {
            "user_id": "user_charlie_789",
            "amount": 0.85,
            "currency": "USD",
            "payout_method": "crypto_wallet",
            "description": "Instant micropayment for technical answer",
            "metadata": {
                "instant_payout": True,
                "crypto_address": "0x1234...abcd",
                "attribution_source": "technical_qa",
            },
        },
    },
}

# Governance Examples
GOVERNANCE_EXAMPLES = {
    "proposal_creation": {
        "summary": "Policy Change Proposal",
        "description": "Create a governance proposal for platform policy changes",
        "value": {
            "title": "Update Attribution Allocation Percentages",
            "description": "Proposal to adjust the standard attribution allocation from 60/25/15 to 65/20/15 (direct/commons/UBA) to better incentivize content creators.",
            "proposal_type": "policy_change",
            "proposer_id": "stakeholder_alice_123",
            "voting_duration_days": 7,
            "voting_method": "supermajority",
            "required_threshold": 0.67,
            "execution_data": {
                "parameter_name": "attribution_allocation_ratio",
                "new_value": [0.65, 0.20, 0.15],
                "effective_date": "2024-08-01",
            },
            "metadata": {
                "category": "economic_policy",
                "impact_assessment": "medium",
                "stakeholder_consultation": True,
            },
        },
    },
    "vote_casting": {
        "summary": "Cast Vote on Proposal",
        "description": "Cast a vote on an active governance proposal",
        "value": {
            "proposal_id": "prop_20240712_abc123",
            "voter_id": "stakeholder_bob_456",
            "vote_type": "for",
            "justification": "This change would better align incentives for content creators while maintaining fair commons allocation.",
            "metadata": {
                "voting_power": 1250.75,
                "stake_amount": 1000.0,
                "reputation_multiplier": 1.15,
                "participation_multiplier": 1.09,
            },
        },
    },
}

# Registry Management Examples
REGISTRY_EXAMPLES = {
    "provider_registration": {
        "summary": "Register AI Provider",
        "description": "Register a new AI provider in the LLM registry",
        "value": {
            "provider_name": "anthropic",
            "api_key": "sk-ant-api-key-here",
            "base_url": "https://api.anthropic.com",
            "supported_capabilities": [
                "chat",
                "reasoning_trace",
                "multimodal",
                "function_calling",
            ],
            "models": [
                {
                    "model_name": "claude-3-5-sonnet",
                    "max_tokens": 200000,
                    "cost_per_1k_tokens": 0.015,
                    "capabilities": ["chat", "reasoning_trace", "multimodal"],
                },
                {
                    "model_name": "claude-3-haiku",
                    "max_tokens": 200000,
                    "cost_per_1k_tokens": 0.0005,
                    "capabilities": ["chat", "reasoning_trace"],
                },
            ],
            "metadata": {
                "tier": "enterprise",
                "rate_limits": {
                    "requests_per_minute": 1000,
                    "tokens_per_minute": 500000,
                },
            },
        },
    },
    "model_query": {
        "summary": "Query Available Models",
        "description": "Query models by capabilities and availability",
        "value": {
            "capabilities": ["chat", "reasoning_trace"],
            "max_cost_per_1k": 0.02,
            "min_max_tokens": 50000,
            "providers": ["openai", "anthropic"],
            "status": "active",
        },
    },
}

# Monitoring Examples
MONITORING_EXAMPLES = {
    "performance_dashboard": {
        "summary": "Performance Dashboard Data",
        "description": "Get comprehensive performance metrics and system status",
        "value": {
            "time_range": "24h",
            "include_alerts": True,
            "include_metrics": ["cpu", "memory", "database", "cache"],
            "detail_level": "full",
        },
    },
    "alert_configuration": {
        "summary": "Configure Performance Alerts",
        "description": "Set up custom performance alert thresholds",
        "value": {
            "metric_name": "response_time",
            "warning_threshold": 1.5,
            "critical_threshold": 3.0,
            "notification_channels": ["email", "slack"],
            "alert_frequency": "immediate",
            "metadata": {
                "business_impact": "high",
                "escalation_policy": "on_call_engineer",
            },
        },
    },
}

# Security Examples
SECURITY_EXAMPLES = {
    "capsule_verification": {
        "summary": "Verify Capsule Integrity",
        "description": "Verify the cryptographic integrity of a capsule",
        "value": {
            "capsule_id": "caps_2024_07_12_abc123def456",
            "verification_type": "full",
            "include_merkle_proof": True,
            "include_signature_chain": True,
            "metadata": {
                "verification_timestamp": "2024-07-12T10:30:00Z",
                "verifier_id": "security_system_v1",
            },
        },
    },
    "cryptographic_operation": {
        "summary": "Post-Quantum Cryptographic Operation",
        "description": "Perform post-quantum cryptographic signing or verification",
        "value": {
            "operation": "sign",
            "algorithm": "dilithium3",
            "data": "Important message to be signed",
            "key_id": "pq_key_2024_001",
            "metadata": {"use_case": "capsule_sealing", "compliance_level": "high"},
        },
    },
}

# Error Response Examples
ERROR_EXAMPLES = {
    "validation_error": {
        "summary": "Validation Error",
        "description": "Request failed validation",
        "value": {
            "detail": "Validation error",
            "errors": [
                {
                    "field": "email",
                    "message": "Invalid email format",
                    "type": "value_error.email",
                },
                {
                    "field": "amount",
                    "message": "Amount must be positive",
                    "type": "value_error.number.not_gt",
                },
            ],
            "error_code": "VALIDATION_FAILED",
            "timestamp": "2024-07-12T10:30:00Z",
        },
    },
    "authentication_error": {
        "summary": "Authentication Error",
        "description": "Authentication failed",
        "value": {
            "detail": "Authentication failed",
            "error_code": "AUTH_FAILED",
            "message": "Invalid API key or expired token",
            "timestamp": "2024-07-12T10:30:00Z",
        },
    },
    "rate_limit_error": {
        "summary": "Rate Limit Exceeded",
        "description": "Too many requests",
        "value": {
            "detail": "Rate limit exceeded",
            "error_code": "RATE_LIMIT_EXCEEDED",
            "retry_after": 60,
            "limit": "100/minute",
            "timestamp": "2024-07-12T10:30:00Z",
        },
    },
}

# Combined examples dictionary for easy access
API_EXAMPLES = {
    "user_registration": USER_REGISTRATION_EXAMPLES,
    "attribution_tracking": ATTRIBUTION_TRACKING_EXAMPLES,
    "payout_requests": PAYOUT_REQUEST_EXAMPLES,
    "governance": GOVERNANCE_EXAMPLES,
    "registry": REGISTRY_EXAMPLES,
    "monitoring": MONITORING_EXAMPLES,
    "security": SECURITY_EXAMPLES,
    "errors": ERROR_EXAMPLES,
}

# Response model examples
RESPONSE_EXAMPLES = {
    "success_response": {
        "summary": "Successful Operation",
        "value": {
            "success": True,
            "message": "Operation completed successfully",
            "data": {},
            "timestamp": "2024-07-12T10:30:00Z",
        },
    },
    "paginated_response": {
        "summary": "Paginated Results",
        "value": {
            "success": True,
            "data": [],
            "pagination": {
                "page": 1,
                "per_page": 20,
                "total_items": 150,
                "total_pages": 8,
                "has_next": True,
                "has_prev": False,
            },
            "timestamp": "2024-07-12T10:30:00Z",
        },
    },
}
