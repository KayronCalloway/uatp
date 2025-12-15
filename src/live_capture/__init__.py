"""
Live Capture Module
==================

Real-time capsule generation for live AI interactions.

This module provides the infrastructure to capture AI conversations
as they happen and automatically create attribution capsules.

Components:
- RealTimeCapsuleGenerator: Core real-time capture system
- ClaudeCodeLiveCapture: Claude Code specific integration
- API hooks for external platform integration

Usage:
    from live_capture import get_real_time_generator, capture_live_interaction

    generator = get_real_time_generator()
    capsule_id = await capture_live_interaction(
        session_id="my-session",
        user_message="How do I implement a binary tree?",
        ai_response="Here's a binary tree implementation...",
        platform="claude_code"
    )
"""

from .antigravity_hook import (
    AntigravityLiveCapture,
    capture_antigravity_interaction,
    get_antigravity_capture,
)
from .claude_code_hook import ClaudeCodeLiveCapture
from .real_time_capsule_generator import (
    LiveInteraction,
    RealTimeCapsuleGenerator,
    capture_live_interaction,
    get_real_time_generator,
)

__all__ = [
    "RealTimeCapsuleGenerator",
    "LiveInteraction",
    "ClaudeCodeLiveCapture",
    "AntigravityLiveCapture",
    "get_real_time_generator",
    "capture_live_interaction",
    "get_antigravity_capture",
    "capture_antigravity_interaction",
]
