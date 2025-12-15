#!/usr/bin/env python3
"""
Capture Orchestrator
===================

Single entry point for all live capture operations across platforms.
Automatically detects platform and routes to appropriate hook.

Usage:
    from src.live_capture.capture_orchestrator import CaptureOrchestrator

    orchestrator = CaptureOrchestrator()
    capsule_id = await orchestrator.capture(
        platform="openai",
        user_input="Help me build an app",
        assistant_response="I'll help you build an app...",
        model="gpt-4"
    )
"""

import logging
from typing import Any, Dict, Optional

from src.live_capture.anthropic_hook import AnthropicLiveCapture
from src.live_capture.antigravity_hook import AntigravityLiveCapture
from src.live_capture.claude_code_hook import ClaudeCodeLiveCapture
from src.live_capture.cursor_hook import CursorLiveCapture
from src.live_capture.openai_hook import OpenAILiveCapture
from src.live_capture.windsurf_hook import WindsurfLiveCapture

logger = logging.getLogger(__name__)


class CaptureOrchestrator:
    """
    Orchestrates capture operations across all platforms.

    Provides a unified interface for capturing interactions from any platform,
    automatically routing to the appropriate hook implementation.
    """

    def __init__(self, user_id: str = "default_user"):
        """
        Initialize the capture orchestrator.

        Args:
            user_id: Default user ID for capture operations
        """
        self.user_id = user_id
        self._hooks: Dict[str, Any] = {}

        logger.info(f"🎭 Capture Orchestrator initialized for user: {user_id}")

    def _get_hook(self, platform: str, **kwargs) -> Any:
        """
        Get or create a hook instance for the specified platform.

        Args:
            platform: Platform identifier
            **kwargs: Platform-specific initialization parameters

        Returns:
            Hook instance for the platform

        Raises:
            ValueError: If platform is not supported
        """
        # Normalize platform name
        platform_lower = platform.lower().replace("-", "_").replace(" ", "_")

        # Check if hook already exists
        if platform_lower in self._hooks:
            return self._hooks[platform_lower]

        # Create new hook based on platform
        hook = None

        if platform_lower in ["openai", "openai_api", "gpt"]:
            hook = OpenAILiveCapture(
                user_id=kwargs.get("user_id", self.user_id),
                api_key=kwargs.get("api_key")
            )

        elif platform_lower in ["anthropic", "claude", "claude_api"]:
            hook = AnthropicLiveCapture(
                user_id=kwargs.get("user_id", self.user_id),
                api_key=kwargs.get("api_key")
            )

        elif platform_lower in ["cursor", "cursor_ide"]:
            hook = CursorLiveCapture(
                user_id=kwargs.get("user_id", self.user_id),
                workspace_path=kwargs.get("workspace_path")
            )

        elif platform_lower in ["windsurf", "windsurf_ide"]:
            hook = WindsurfLiveCapture(
                user_id=kwargs.get("user_id", self.user_id),
                workspace_path=kwargs.get("workspace_path")
            )

        elif platform_lower in ["antigravity", "gemini", "google_antigravity"]:
            hook = AntigravityLiveCapture(
                user_id=kwargs.get("user_id", self.user_id),
                session_id=kwargs.get("session_id"),
                model=kwargs.get("model", "gemini-2.5-pro")
            )

        elif platform_lower in ["claude_code", "claudecode"]:
            hook = ClaudeCodeLiveCapture(
                session_id=kwargs.get("session_id", "claude-code-session")
            )

        else:
            raise ValueError(
                f"Unsupported platform: {platform}. "
                f"Supported platforms: openai, anthropic, cursor, windsurf, antigravity, claude_code"
            )

        # Cache the hook
        self._hooks[platform_lower] = hook

        return hook

    async def capture(
        self,
        platform: str,
        user_input: str,
        assistant_response: str,
        model: str = None,
        interaction_type: str = "general",
        **platform_kwargs
    ) -> Optional[str]:
        """
        Capture an interaction from any platform.

        This is the main entry point for all capture operations. It automatically
        routes to the appropriate platform hook and returns the capsule ID.

        Args:
            platform: Platform identifier (openai, anthropic, cursor, etc.)
            user_input: User's message
            assistant_response: AI's response
            model: Model identifier (optional, platform-specific defaults used)
            interaction_type: Type of interaction
            **platform_kwargs: Platform-specific parameters

        Returns:
            Capsule ID if created, None if not significant

        Raises:
            ValueError: If platform is not supported

        Example:
            >>> orchestrator = CaptureOrchestrator()
            >>> capsule_id = await orchestrator.capture(
            ...     platform="openai",
            ...     user_input="Help me code",
            ...     assistant_response="I'll help you...",
            ...     model="gpt-4"
            ... )
        """
        try:
            # Get the appropriate hook
            hook = self._get_hook(platform, **platform_kwargs)

            # Use the hook's main capture method
            # Each hook has its own platform-specific capture method
            platform_lower = platform.lower().replace("-", "_").replace(" ", "_")

            if platform_lower in ["openai", "openai_api", "gpt"]:
                return await hook.capture_openai_interaction(
                    user_input=user_input,
                    assistant_response=assistant_response,
                    model=model or "gpt-4",
                    interaction_type=interaction_type,
                    **platform_kwargs
                )

            elif platform_lower in ["anthropic", "claude", "claude_api"]:
                return await hook.capture_anthropic_interaction(
                    user_input=user_input,
                    assistant_response=assistant_response,
                    model=model or "claude-3-sonnet-20240229",
                    interaction_type=interaction_type,
                    **platform_kwargs
                )

            elif platform_lower in ["cursor", "cursor_ide"]:
                return await hook.capture_cursor_interaction(
                    user_input=user_input,
                    assistant_response=assistant_response,
                    cursor_model=model or "claude-3.5-sonnet",
                    interaction_type=interaction_type,
                    **platform_kwargs
                )

            elif platform_lower in ["windsurf", "windsurf_ide"]:
                return await hook.capture_windsurf_interaction(
                    user_input=user_input,
                    assistant_response=assistant_response,
                    windsurf_model=model or "windsurf-ai",
                    interaction_type=interaction_type,
                    **platform_kwargs
                )

            elif platform_lower in ["antigravity", "gemini", "google_antigravity"]:
                return await hook.capture_antigravity_interaction(
                    user_input=user_input,
                    assistant_response=assistant_response,
                    interaction_type=interaction_type,
                    **platform_kwargs
                )

            elif platform_lower in ["claude_code", "claudecode"]:
                return await hook.capture_current_conversation(
                    user_message=user_input,
                    ai_response=assistant_response
                )

        except Exception as e:
            logger.error(f"❌ Capture failed for platform {platform}: {e}")
            return None

    def get_supported_platforms(self) -> list[str]:
        """
        Get list of supported platforms.

        Returns:
            List of supported platform identifiers
        """
        return [
            "openai",
            "anthropic",
            "cursor",
            "windsurf",
            "antigravity",
            "claude_code"
        ]

    def get_platform_info(self, platform: str) -> Dict[str, Any]:
        """
        Get information about a specific platform.

        Args:
            platform: Platform identifier

        Returns:
            Dictionary with platform information
        """
        platform_info = {
            "openai": {
                "name": "OpenAI",
                "emoji": "🤖",
                "models": ["gpt-4", "gpt-3.5-turbo"],
                "type": "api"
            },
            "anthropic": {
                "name": "Anthropic Claude",
                "emoji": "🧠",
                "models": ["claude-3-opus", "claude-3-sonnet", "claude-3-haiku"],
                "type": "api"
            },
            "cursor": {
                "name": "Cursor IDE",
                "emoji": "🎯",
                "models": ["claude-3.5-sonnet"],
                "type": "ide"
            },
            "windsurf": {
                "name": "Windsurf IDE",
                "emoji": "🌊",
                "models": ["windsurf-ai"],
                "type": "ide"
            },
            "antigravity": {
                "name": "Google Gemini (Antigravity)",
                "emoji": "✨",
                "models": ["gemini-2.5-pro", "gemini-pro"],
                "type": "api"
            },
            "claude_code": {
                "name": "Claude Code",
                "emoji": "🎯",
                "models": ["claude-sonnet-4"],
                "type": "cli"
            }
        }

        platform_lower = platform.lower().replace("-", "_").replace(" ", "_")

        # Map aliases to canonical names
        aliases = {
            "openai_api": "openai",
            "gpt": "openai",
            "claude": "anthropic",
            "claude_api": "anthropic",
            "cursor_ide": "cursor",
            "windsurf_ide": "windsurf",
            "gemini": "antigravity",
            "google_antigravity": "antigravity",
            "claudecode": "claude_code"
        }

        canonical = aliases.get(platform_lower, platform_lower)
        return platform_info.get(canonical, {})

    def get_active_hooks(self) -> Dict[str, Any]:
        """
        Get information about currently active hooks.

        Returns:
            Dictionary mapping platform names to hook instances
        """
        return {
            platform: {
                "platform": hook.platform,
                "user_id": hook.user_id,
                "session_id": hook.session_id
            }
            for platform, hook in self._hooks.items()
        }

    def clear_hooks(self):
        """Clear all cached hook instances."""
        self._hooks.clear()
        logger.info("🧹 Cleared all cached hooks")


# Global orchestrator instance
_orchestrator: Optional[CaptureOrchestrator] = None


def get_orchestrator(user_id: str = "default_user") -> CaptureOrchestrator:
    """
    Get the global capture orchestrator instance.

    Args:
        user_id: User ID for capture operations

    Returns:
        Global CaptureOrchestrator instance
    """
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = CaptureOrchestrator(user_id)
    return _orchestrator


async def capture(
    platform: str,
    user_input: str,
    assistant_response: str,
    model: str = None,
    interaction_type: str = "general",
    user_id: str = "default_user",
    **platform_kwargs
) -> Optional[str]:
    """
    Convenience function for capturing interactions.

    This is a simplified API that uses the global orchestrator instance.

    Args:
        platform: Platform identifier
        user_input: User's message
        assistant_response: AI's response
        model: Model identifier (optional)
        interaction_type: Type of interaction
        user_id: User identifier
        **platform_kwargs: Platform-specific parameters

    Returns:
        Capsule ID if created, None if not significant

    Example:
        >>> from src.live_capture.capture_orchestrator import capture
        >>> capsule_id = await capture(
        ...     platform="openai",
        ...     user_input="Help me code",
        ...     assistant_response="I'll help you..."
        ... )
    """
    orchestrator = get_orchestrator(user_id)
    return await orchestrator.capture(
        platform=platform,
        user_input=user_input,
        assistant_response=assistant_response,
        model=model,
        interaction_type=interaction_type,
        **platform_kwargs
    )
