#!/usr/bin/env python3
"""
Base Hook for Live Capture Integrations
========================================

Abstract base class for all platform-specific capture hooks.
Eliminates code duplication across OpenAI, Cursor, Windsurf, Anthropic, etc.

This module provides common functionality for:
- Session management
- Metadata enhancement
- Interaction capture
- Error handling and logging

Platform-specific hooks only need to implement:
- Platform-specific metadata
- Platform-specific initialization parameters
"""

import logging
import time
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

from src.live_capture.real_time_capsule_generator import capture_live_interaction

logger = logging.getLogger(__name__)


class BaseHook(ABC):
    """
    Abstract base class for platform capture hooks.

    Provides common functionality:
    - Session ID generation
    - Standardized capture flow
    - Error handling
    - Logging

    Subclasses must implement:
    - get_platform_specific_metadata(): Platform-specific metadata dict
    - get_platform_emoji(): Emoji for logging (e.g., "🤖" for OpenAI)
    """

    def __init__(
        self,
        platform: str,
        user_id: str,
        session_id: Optional[str] = None,
    ):
        """
        Initialize base hook.

        Args:
            platform: Platform name (e.g., "openai", "cursor", "anthropic")
            user_id: User identifier
            session_id: Optional custom session ID (auto-generated if not provided)
        """
        self.platform = platform
        self.user_id = user_id
        self.session_id = session_id or f"{platform}_session_{int(time.time())}"

        # Log initialization
        emoji = self.get_platform_emoji()
        logger.info(f"{emoji} {platform.title()} Live Capture initialized")
        logger.info(f"   User ID: {user_id}")
        logger.info(f"   Session ID: {self.session_id}")

        # Allow subclasses to add custom initialization logging
        self._log_platform_specific_init()

    @abstractmethod
    def get_platform_specific_metadata(self, **kwargs) -> Dict[str, Any]:
        """
        Get platform-specific metadata.

        Subclasses must implement this to provide platform-specific
        metadata fields (e.g., API version, workspace path, etc.).

        Args:
            **kwargs: Platform-specific parameters

        Returns:
            Dict of platform-specific metadata
        """
        pass

    @abstractmethod
    def get_platform_emoji(self) -> str:
        """
        Get platform emoji for logging.

        Returns:
            Emoji string (e.g., "🤖" for OpenAI, "🎯" for Cursor)
        """
        pass

    def _log_platform_specific_init(self) -> None:
        """
        Optional: Log platform-specific initialization info.

        Subclasses can override to add custom logging.
        Default implementation does nothing.
        """
        pass

    async def capture_interaction(
        self,
        user_input: str,
        assistant_response: str,
        model: str,
        interaction_type: str = "general",
        **platform_kwargs,
    ) -> Optional[str]:
        """
        Capture an interaction and create capsule if significant.

        This is the main capture method used by all platforms.
        Common logic handled here, platform-specific metadata from subclass.

        Args:
            user_input: User's message
            assistant_response: AI's response
            model: Model used (e.g., "gpt-4", "claude-3.5-sonnet")
            interaction_type: Type of interaction
            **platform_kwargs: Platform-specific parameters

        Returns:
            Capsule ID if created, None if not significant
        """
        try:
            # Get platform-specific metadata from subclass
            platform_metadata = self.get_platform_specific_metadata(**platform_kwargs)

            # Build complete metadata
            metadata = {
                "interaction_type": interaction_type,
                "model": model,
                "platform": self.platform,
                **platform_metadata,
                **platform_kwargs,  # Include any additional kwargs
            }

            # Capture the interaction using real-time capsule generator
            capsule_id = await capture_live_interaction(
                session_id=self.session_id,
                user_message=user_input,
                ai_response=assistant_response,
                user_id=self.user_id,
                platform=self.platform,
                model=model,
                metadata=metadata,
            )

            # Log success
            if capsule_id:
                emoji = self.get_platform_emoji()
                logger.info(f"{emoji} {self.platform.title()} interaction encapsulated: {capsule_id}")
                logger.info(f"   Model: {model}")
                logger.info(f"   Type: {interaction_type}")

                # Allow subclass to add custom success logging
                self._log_platform_specific_success(capsule_id, **platform_kwargs)

            return capsule_id

        except Exception as e:
            logger.error(f"❌ {self.platform.title()} interaction capture failed: {e}")
            return None

    def _log_platform_specific_success(self, capsule_id: str, **kwargs) -> None:
        """
        Optional: Log platform-specific success info.

        Subclasses can override to add custom logging after successful capture.
        Default implementation does nothing.

        Args:
            capsule_id: ID of created capsule
            **kwargs: Platform-specific parameters
        """
        pass

    def get_session_stats(self) -> Dict[str, Any]:
        """
        Get statistics for the current session.

        Returns:
            Dict with session information
        """
        return {
            "platform": self.platform,
            "user_id": self.user_id,
            "session_id": self.session_id,
        }


class SimplePlatformHook(BaseHook):
    """
    Simple implementation of BaseHook for quick platform integration.

    Use this for simple platforms that don't need custom behavior.
    Just provide platform name, emoji, and optional metadata.

    Example:
        hook = SimplePlatformHook(
            platform="my_platform",
            user_id="user123",
            emoji="🚀",
            metadata_provider=lambda **kwargs: {"custom_field": kwargs.get("field")}
        )
    """

    def __init__(
        self,
        platform: str,
        user_id: str,
        emoji: str = "📝",
        metadata_provider: Optional[callable] = None,
        **kwargs,
    ):
        self.emoji = emoji
        self.metadata_provider = metadata_provider or (lambda **kw: {})
        super().__init__(platform, user_id, **kwargs)

    def get_platform_emoji(self) -> str:
        return self.emoji

    def get_platform_specific_metadata(self, **kwargs) -> Dict[str, Any]:
        return self.metadata_provider(**kwargs)
