"""
UATP Universal Filter System
============================

This module provides the universal filter system that determines what AI interactions
should be encapsulated into attribution capsules.

Key Components:
- UniversalFilter: Core filtering logic
- IntegrationLayer: Platform integration
- FilterConfig: Configuration management
- FilterResult: Filter decision results

Usage:
    from filters import process_ai_interaction
    
    result = await process_ai_interaction(
        messages=conversation_messages,
        user_id="user123",
        platform="openai"
    )
    
    if result.should_encapsulate:
        print("Creating capsule...")
"""

from .universal_filter import (
    UniversalFilter,
    FilterConfig,
    FilterResult,
    FilterDecision,
    get_universal_filter,
    filter_interaction,
    should_encapsulate,
)

from .integration_layer import (
    IntegrationLayer,
    AIInteraction,
    get_integration_layer,
    process_ai_interaction,
    process_openai_interaction,
    process_claude_interaction,
    process_claude_code_interaction,
    auto_capture,
)

from .capsule_creator import (
    FilterCapsuleCreator,
    get_capsule_creator,
    create_capsule_from_filter,
)

__all__ = [
    # Core filter components
    "UniversalFilter",
    "FilterConfig",
    "FilterResult",
    "FilterDecision",
    "get_universal_filter",
    "filter_interaction",
    "should_encapsulate",
    # Integration layer
    "IntegrationLayer",
    "AIInteraction",
    "get_integration_layer",
    "process_ai_interaction",
    "process_openai_interaction",
    "process_claude_interaction",
    "process_claude_code_interaction",
    "auto_capture",
    # Capsule creation
    "FilterCapsuleCreator",
    "get_capsule_creator",
    "create_capsule_from_filter",
]
