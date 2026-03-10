#!/usr/bin/env python3
"""
Unit Tests for BaseHook
=======================

Tests the base hook functionality that all platform hooks inherit.
"""

from typing import Any, Dict
from unittest.mock import patch

import pytest

from src.live_capture.base_hook import BaseHook, SimplePlatformHook


class TestHook(BaseHook):
    """Test implementation of BaseHook for testing."""

    def __init__(self, user_id: str = "test_user", session_id: str = None):
        self.custom_field = "test_value"
        super().__init__(
            platform="test_platform", user_id=user_id, session_id=session_id
        )

    def get_platform_emoji(self) -> str:
        return ""

    def get_platform_specific_metadata(self, **kwargs) -> Dict[str, Any]:
        return {
            "test_version": "1.0",
            "custom_field": self.custom_field,
            "test_param": kwargs.get("test_param"),
        }


class TestBaseHookInitialization:
    """Test BaseHook initialization."""

    def test_basic_initialization(self):
        """Test basic hook initialization."""
        hook = TestHook(user_id="test_user")

        assert hook.platform == "test_platform"
        assert hook.user_id == "test_user"
        assert hook.session_id.startswith("test_platform_session_")

    def test_custom_session_id(self):
        """Test initialization with custom session ID."""
        hook = TestHook(user_id="test_user", session_id="custom_session_123")

        assert hook.session_id == "custom_session_123"

    def test_platform_emoji(self):
        """Test platform emoji is correctly set."""
        hook = TestHook()

        assert hook.get_platform_emoji() == ""

    def test_platform_specific_metadata(self):
        """Test platform-specific metadata generation."""
        hook = TestHook()

        metadata = hook.get_platform_specific_metadata(test_param="test_value")

        assert metadata["test_version"] == "1.0"
        assert metadata["custom_field"] == "test_value"
        assert metadata["test_param"] == "test_value"


class TestBaseHookCapture:
    """Test BaseHook capture functionality."""

    @pytest.mark.asyncio
    async def test_successful_capture(self):
        """Test successful capture interaction."""
        hook = TestHook()

        with patch(
            "src.live_capture.base_hook.capture_live_interaction"
        ) as mock_capture:
            mock_capture.return_value = "cap_test_123"

            capsule_id = await hook.capture_interaction(
                user_input="Test user input",
                assistant_response="Test AI response",
                model="test-model",
                test_param="test_value",
            )

            # Verify capture was called correctly
            assert mock_capture.called
            call_args = mock_capture.call_args

            # Check arguments
            assert call_args.kwargs["user_message"] == "Test user input"
            assert call_args.kwargs["ai_response"] == "Test AI response"
            assert call_args.kwargs["model"] == "test-model"
            assert call_args.kwargs["platform"] == "test_platform"

            # Check metadata
            metadata = call_args.kwargs["metadata"]
            assert metadata["interaction_type"] == "general"
            assert metadata["model"] == "test-model"
            assert metadata["platform"] == "test_platform"
            assert metadata["test_version"] == "1.0"
            assert metadata["test_param"] == "test_value"

            # Verify return value
            assert capsule_id == "cap_test_123"

    @pytest.mark.asyncio
    async def test_capture_with_custom_interaction_type(self):
        """Test capture with custom interaction type."""
        hook = TestHook()

        with patch(
            "src.live_capture.base_hook.capture_live_interaction"
        ) as mock_capture:
            mock_capture.return_value = "cap_test_456"

            await hook.capture_interaction(
                user_input="Test",
                assistant_response="Response",
                model="test-model",
                interaction_type="code_generation",
            )

            metadata = mock_capture.call_args.kwargs["metadata"]
            assert metadata["interaction_type"] == "code_generation"

    @pytest.mark.asyncio
    async def test_capture_failure_returns_none(self):
        """Test that capture returns None on failure."""
        hook = TestHook()

        with patch(
            "src.live_capture.base_hook.capture_live_interaction"
        ) as mock_capture:
            mock_capture.side_effect = Exception("Test error")

            capsule_id = await hook.capture_interaction(
                user_input="Test", assistant_response="Response", model="test-model"
            )

            assert capsule_id is None

    @pytest.mark.asyncio
    async def test_capture_returns_none_when_not_significant(self):
        """Test that capture returns None when interaction is not significant."""
        hook = TestHook()

        with patch(
            "src.live_capture.base_hook.capture_live_interaction"
        ) as mock_capture:
            mock_capture.return_value = None

            capsule_id = await hook.capture_interaction(
                user_input="Short", assistant_response="OK", model="test-model"
            )

            assert capsule_id is None


class TestBaseHookSessionManagement:
    """Test session management functionality."""

    def test_session_stats(self):
        """Test get_session_stats method."""
        hook = TestHook(user_id="stats_user", session_id="stats_session_123")

        stats = hook.get_session_stats()

        assert stats["platform"] == "test_platform"
        assert stats["user_id"] == "stats_user"
        assert stats["session_id"] == "stats_session_123"


class TestSimplePlatformHook:
    """Test SimplePlatformHook implementation."""

    def test_simple_hook_initialization(self):
        """Test SimplePlatformHook basic initialization."""
        hook = SimplePlatformHook(
            platform="simple_test", user_id="simple_user", emoji=""
        )

        assert hook.platform == "simple_test"
        assert hook.user_id == "simple_user"
        assert hook.get_platform_emoji() == ""

    def test_simple_hook_with_metadata_provider(self):
        """Test SimplePlatformHook with custom metadata provider."""

        def metadata_provider(**kwargs):
            return {"custom_field": "custom_value", "param": kwargs.get("param")}

        hook = SimplePlatformHook(
            platform="simple_test",
            user_id="simple_user",
            emoji="",
            metadata_provider=metadata_provider,
        )

        metadata = hook.get_platform_specific_metadata(param="test_param")

        assert metadata["custom_field"] == "custom_value"
        assert metadata["param"] == "test_param"

    def test_simple_hook_default_metadata(self):
        """Test SimplePlatformHook with default metadata provider."""
        hook = SimplePlatformHook(platform="simple_test", user_id="simple_user")

        metadata = hook.get_platform_specific_metadata()

        assert metadata == {}

    @pytest.mark.asyncio
    async def test_simple_hook_capture(self):
        """Test SimplePlatformHook can capture interactions."""
        hook = SimplePlatformHook(
            platform="simple_test", user_id="simple_user", emoji=""
        )

        with patch(
            "src.live_capture.base_hook.capture_live_interaction"
        ) as mock_capture:
            mock_capture.return_value = "cap_simple_123"

            capsule_id = await hook.capture_interaction(
                user_input="Test input",
                assistant_response="Test response",
                model="simple-model",
            )

            assert capsule_id == "cap_simple_123"
            assert mock_capture.called


class TestBaseHookLogging:
    """Test logging functionality."""

    def test_initialization_logging(self, caplog):
        """Test that initialization logs correctly."""
        with caplog.at_level("INFO"):
            hook = TestHook(user_id="log_user", session_id="log_session")

        # Check for initialization log messages
        assert any(
            "Test_platform Live Capture initialized" in record.message
            for record in caplog.records
        )
        assert any("User ID: log_user" in record.message for record in caplog.records)
        assert any(
            "Session ID: log_session" in record.message for record in caplog.records
        )

    @pytest.mark.asyncio
    async def test_success_logging(self, caplog):
        """Test that successful capture logs correctly."""
        hook = TestHook()

        with patch(
            "src.live_capture.base_hook.capture_live_interaction"
        ) as mock_capture:
            mock_capture.return_value = "cap_log_123"

            with caplog.at_level("INFO"):
                await hook.capture_interaction(
                    user_input="Test", assistant_response="Response", model="test-model"
                )

            # Check for success log messages
            assert any(
                "interaction encapsulated: cap_log_123" in record.message
                for record in caplog.records
            )
            assert any(
                "Model: test-model" in record.message for record in caplog.records
            )

    @pytest.mark.asyncio
    async def test_failure_logging(self, caplog):
        """Test that failed capture logs correctly."""
        hook = TestHook()

        with patch(
            "src.live_capture.base_hook.capture_live_interaction"
        ) as mock_capture:
            mock_capture.side_effect = Exception("Test error")

            with caplog.at_level("ERROR"):
                await hook.capture_interaction(
                    user_input="Test", assistant_response="Response", model="test-model"
                )

            # Check for error log message
            assert any(
                "interaction capture failed" in record.message
                for record in caplog.records
            )


class TestBaseHookExtensibility:
    """Test extensibility hooks."""

    class CustomLoggingHook(BaseHook):
        """Hook with custom logging."""

        def __init__(self):
            self.init_logged = False
            self.success_logged = False
            super().__init__(platform="custom", user_id="custom_user")

        def get_platform_emoji(self) -> str:
            return ""

        def get_platform_specific_metadata(self, **kwargs) -> Dict[str, Any]:
            return {"custom": "metadata"}

        def _log_platform_specific_init(self) -> None:
            self.init_logged = True

        def _log_platform_specific_success(self, capsule_id: str, **kwargs) -> None:
            self.success_logged = True

    def test_custom_init_logging(self):
        """Test that custom init logging is called."""
        hook = self.CustomLoggingHook()

        assert hook.init_logged is True

    @pytest.mark.asyncio
    async def test_custom_success_logging(self):
        """Test that custom success logging is called."""
        hook = self.CustomLoggingHook()

        with patch(
            "src.live_capture.base_hook.capture_live_interaction"
        ) as mock_capture:
            mock_capture.return_value = "cap_custom_123"

            await hook.capture_interaction(
                user_input="Test", assistant_response="Response", model="custom-model"
            )

            assert hook.success_logged is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
