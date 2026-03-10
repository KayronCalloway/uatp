#!/usr/bin/env python3
"""
Unit Tests for CaptureOrchestrator
==================================

Tests the unified capture interface for all platforms.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.live_capture.capture_orchestrator import (
    CaptureOrchestrator,
    capture,
    get_orchestrator,
)


class TestCaptureOrchestratorInitialization:
    """Test orchestrator initialization."""

    def test_basic_initialization(self):
        """Test basic orchestrator initialization."""
        orchestrator = CaptureOrchestrator(user_id="test_user")

        assert orchestrator.user_id == "test_user"
        assert orchestrator._hooks == {}

    def test_default_user_id(self):
        """Test initialization with default user ID."""
        orchestrator = CaptureOrchestrator()

        assert orchestrator.user_id == "default_user"


class TestPlatformRouting:
    """Test platform routing functionality."""

    @pytest.mark.asyncio
    async def test_openai_routing(self):
        """Test routing to OpenAI hook."""
        orchestrator = CaptureOrchestrator()

        with patch.object(orchestrator, "_get_hook") as mock_get_hook:
            mock_hook = MagicMock()
            mock_hook.capture_openai_interaction = AsyncMock(
                return_value="cap_openai_123"
            )
            mock_get_hook.return_value = mock_hook

            result = await orchestrator.capture(
                platform="openai",
                user_input="Test",
                assistant_response="Response",
                model="gpt-4",
            )

            assert result == "cap_openai_123"
            assert mock_hook.capture_openai_interaction.called

    @pytest.mark.asyncio
    async def test_anthropic_routing(self):
        """Test routing to Anthropic hook."""
        orchestrator = CaptureOrchestrator()

        with patch.object(orchestrator, "_get_hook") as mock_get_hook:
            mock_hook = MagicMock()
            mock_hook.capture_anthropic_interaction = AsyncMock(
                return_value="cap_anthropic_123"
            )
            mock_get_hook.return_value = mock_hook

            result = await orchestrator.capture(
                platform="anthropic",
                user_input="Test",
                assistant_response="Response",
                model="claude-3-sonnet",
            )

            assert result == "cap_anthropic_123"
            assert mock_hook.capture_anthropic_interaction.called

    @pytest.mark.asyncio
    async def test_cursor_routing(self):
        """Test routing to Cursor hook."""
        orchestrator = CaptureOrchestrator()

        with patch.object(orchestrator, "_get_hook") as mock_get_hook:
            mock_hook = MagicMock()
            mock_hook.capture_cursor_interaction = AsyncMock(
                return_value="cap_cursor_123"
            )
            mock_get_hook.return_value = mock_hook

            result = await orchestrator.capture(
                platform="cursor", user_input="Test", assistant_response="Response"
            )

            assert result == "cap_cursor_123"
            assert mock_hook.capture_cursor_interaction.called

    @pytest.mark.asyncio
    async def test_windsurf_routing(self):
        """Test routing to Windsurf hook."""
        orchestrator = CaptureOrchestrator()

        with patch.object(orchestrator, "_get_hook") as mock_get_hook:
            mock_hook = MagicMock()
            mock_hook.capture_windsurf_interaction = AsyncMock(
                return_value="cap_windsurf_123"
            )
            mock_get_hook.return_value = mock_hook

            result = await orchestrator.capture(
                platform="windsurf", user_input="Test", assistant_response="Response"
            )

            assert result == "cap_windsurf_123"
            assert mock_hook.capture_windsurf_interaction.called

    @pytest.mark.asyncio
    async def test_antigravity_routing(self):
        """Test routing to Antigravity hook."""
        orchestrator = CaptureOrchestrator()

        with patch.object(orchestrator, "_get_hook") as mock_get_hook:
            mock_hook = MagicMock()
            mock_hook.capture_antigravity_interaction = AsyncMock(
                return_value="cap_antigravity_123"
            )
            mock_get_hook.return_value = mock_hook

            result = await orchestrator.capture(
                platform="antigravity", user_input="Test", assistant_response="Response"
            )

            assert result == "cap_antigravity_123"
            assert mock_hook.capture_antigravity_interaction.called

    @pytest.mark.asyncio
    async def test_claude_code_routing(self):
        """Test routing to Claude Code hook."""
        orchestrator = CaptureOrchestrator()

        with patch.object(orchestrator, "_get_hook") as mock_get_hook:
            mock_hook = MagicMock()
            mock_hook.capture_current_conversation = AsyncMock(
                return_value="cap_claude_code_123"
            )
            mock_get_hook.return_value = mock_hook

            result = await orchestrator.capture(
                platform="claude_code", user_input="Test", assistant_response="Response"
            )

            assert result == "cap_claude_code_123"
            assert mock_hook.capture_current_conversation.called


class TestPlatformAliases:
    """Test platform alias resolution."""

    @pytest.mark.asyncio
    async def test_gpt_alias(self):
        """Test 'gpt' alias routes to openai."""
        orchestrator = CaptureOrchestrator()

        with patch.object(orchestrator, "_get_hook") as mock_get_hook:
            mock_hook = MagicMock()
            mock_hook.capture_openai_interaction = AsyncMock(return_value="cap_123")
            mock_get_hook.return_value = mock_hook

            await orchestrator.capture(
                platform="gpt", user_input="Test", assistant_response="Response"
            )

            assert mock_hook.capture_openai_interaction.called

    @pytest.mark.asyncio
    async def test_claude_alias(self):
        """Test 'claude' alias routes to anthropic."""
        orchestrator = CaptureOrchestrator()

        with patch.object(orchestrator, "_get_hook") as mock_get_hook:
            mock_hook = MagicMock()
            mock_hook.capture_anthropic_interaction = AsyncMock(return_value="cap_123")
            mock_get_hook.return_value = mock_hook

            await orchestrator.capture(
                platform="claude", user_input="Test", assistant_response="Response"
            )

            assert mock_hook.capture_anthropic_interaction.called

    @pytest.mark.asyncio
    async def test_gemini_alias(self):
        """Test 'gemini' alias routes to antigravity."""
        orchestrator = CaptureOrchestrator()

        with patch.object(orchestrator, "_get_hook") as mock_get_hook:
            mock_hook = MagicMock()
            mock_hook.capture_antigravity_interaction = AsyncMock(
                return_value="cap_123"
            )
            mock_get_hook.return_value = mock_hook

            await orchestrator.capture(
                platform="gemini", user_input="Test", assistant_response="Response"
            )

            assert mock_hook.capture_antigravity_interaction.called

    @pytest.mark.asyncio
    async def test_case_insensitive_platform(self):
        """Test that platform names are case-insensitive."""
        orchestrator = CaptureOrchestrator()

        with patch.object(orchestrator, "_get_hook") as mock_get_hook:
            mock_hook = MagicMock()
            mock_hook.capture_openai_interaction = AsyncMock(return_value="cap_123")
            mock_get_hook.return_value = mock_hook

            await orchestrator.capture(
                platform="OpenAI", user_input="Test", assistant_response="Response"
            )

            assert mock_hook.capture_openai_interaction.called


class TestHookCaching:
    """Test hook caching functionality."""

    def test_hook_is_cached(self):
        """Test that hooks are cached after creation."""
        orchestrator = CaptureOrchestrator()

        with patch(
            "src.live_capture.capture_orchestrator.OpenAILiveCapture"
        ) as MockHook:
            mock_instance = MagicMock()
            MockHook.return_value = mock_instance

            # Get hook twice
            hook1 = orchestrator._get_hook("openai")
            hook2 = orchestrator._get_hook("openai")

            # Should be same instance
            assert hook1 is hook2
            # Constructor called only once
            assert MockHook.call_count == 1

    def test_different_platforms_different_hooks(self):
        """Test that different platforms get different hooks."""
        orchestrator = CaptureOrchestrator()

        with patch(
            "src.live_capture.capture_orchestrator.OpenAILiveCapture"
        ) as MockOpenAI, patch(
            "src.live_capture.capture_orchestrator.AnthropicLiveCapture"
        ) as MockAnthropic:
            mock_openai = MagicMock()
            mock_anthropic = MagicMock()
            MockOpenAI.return_value = mock_openai
            MockAnthropic.return_value = mock_anthropic

            hook1 = orchestrator._get_hook("openai")
            hook2 = orchestrator._get_hook("anthropic")

            assert hook1 is not hook2
            assert MockOpenAI.called
            assert MockAnthropic.called

    def test_clear_hooks(self):
        """Test clearing hook cache."""
        orchestrator = CaptureOrchestrator()

        with patch(
            "src.live_capture.capture_orchestrator.OpenAILiveCapture"
        ) as MockHook:
            mock_instance = MagicMock()
            MockHook.return_value = mock_instance

            # Create hook
            orchestrator._get_hook("openai")
            assert len(orchestrator._hooks) == 1

            # Clear cache
            orchestrator.clear_hooks()
            assert len(orchestrator._hooks) == 0


class TestPlatformDiscovery:
    """Test platform discovery functionality."""

    def test_get_supported_platforms(self):
        """Test getting list of supported platforms."""
        orchestrator = CaptureOrchestrator()

        platforms = orchestrator.get_supported_platforms()

        assert "openai" in platforms
        assert "anthropic" in platforms
        assert "cursor" in platforms
        assert "windsurf" in platforms
        assert "antigravity" in platforms
        assert "claude_code" in platforms
        assert len(platforms) == 6

    def test_get_platform_info_openai(self):
        """Test getting OpenAI platform info."""
        orchestrator = CaptureOrchestrator()

        info = orchestrator.get_platform_info("openai")

        assert info["name"] == "OpenAI"
        assert info["emoji"] == ""
        assert "gpt-4" in info["models"]
        assert info["type"] == "api"

    def test_get_platform_info_anthropic(self):
        """Test getting Anthropic platform info."""
        orchestrator = CaptureOrchestrator()

        info = orchestrator.get_platform_info("anthropic")

        assert info["name"] == "Anthropic Claude"
        assert info["emoji"] == ""
        assert "claude-3-sonnet" in info["models"]
        assert info["type"] == "api"

    def test_get_platform_info_with_alias(self):
        """Test getting platform info using alias."""
        orchestrator = CaptureOrchestrator()

        info = orchestrator.get_platform_info("gpt")

        # Should resolve to openai
        assert info["name"] == "OpenAI"

    def test_get_active_hooks(self):
        """Test getting active hooks info."""
        orchestrator = CaptureOrchestrator()

        with patch(
            "src.live_capture.capture_orchestrator.OpenAILiveCapture"
        ) as MockHook:
            mock_instance = MagicMock()
            mock_instance.platform = "openai"
            mock_instance.user_id = "test_user"
            mock_instance.session_id = "session_123"
            MockHook.return_value = mock_instance

            # Create a hook
            orchestrator._get_hook("openai")

            # Get active hooks
            active = orchestrator.get_active_hooks()

            assert "openai" in active
            assert active["openai"]["platform"] == "openai"
            assert active["openai"]["user_id"] == "test_user"
            assert active["openai"]["session_id"] == "session_123"


class TestErrorHandling:
    """Test error handling."""

    def test_invalid_platform_raises_error(self):
        """Test that invalid platform raises ValueError."""
        orchestrator = CaptureOrchestrator()

        with pytest.raises(ValueError) as exc_info:
            orchestrator._get_hook("invalid_platform")

        assert "Unsupported platform" in str(exc_info.value)
        assert "invalid_platform" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_capture_error_returns_none(self):
        """Test that capture errors return None."""
        orchestrator = CaptureOrchestrator()

        with patch.object(orchestrator, "_get_hook") as mock_get_hook:
            mock_hook = MagicMock()
            mock_hook.capture_openai_interaction = AsyncMock(
                side_effect=Exception("Test error")
            )
            mock_get_hook.return_value = mock_hook

            result = await orchestrator.capture(
                platform="openai", user_input="Test", assistant_response="Response"
            )

            assert result is None


class TestGlobalOrchestrator:
    """Test global orchestrator functionality."""

    def test_get_orchestrator_creates_instance(self):
        """Test that get_orchestrator creates instance."""
        # Clear global instance
        import src.live_capture.capture_orchestrator as module

        module._orchestrator = None

        orchestrator = get_orchestrator(user_id="global_user")

        assert orchestrator is not None
        assert orchestrator.user_id == "global_user"

    def test_get_orchestrator_reuses_instance(self):
        """Test that get_orchestrator reuses same instance."""
        import src.live_capture.capture_orchestrator as module

        module._orchestrator = None

        orchestrator1 = get_orchestrator(user_id="global_user")
        orchestrator2 = get_orchestrator(user_id="different_user")

        # Should be same instance (user_id only set on first call)
        assert orchestrator1 is orchestrator2

    @pytest.mark.asyncio
    async def test_convenience_function(self):
        """Test global convenience function."""
        import src.live_capture.capture_orchestrator as module

        module._orchestrator = None

        with patch.object(
            CaptureOrchestrator, "capture", new_callable=AsyncMock
        ) as mock_capture:
            mock_capture.return_value = "cap_convenience_123"

            result = await capture(
                platform="openai",
                user_input="Test",
                assistant_response="Response",
                user_id="convenience_user",
            )

            assert result == "cap_convenience_123"
            assert mock_capture.called


class TestIntegration:
    """Integration tests."""

    @pytest.mark.asyncio
    async def test_end_to_end_capture(self):
        """Test end-to-end capture flow."""
        orchestrator = CaptureOrchestrator(user_id="integration_user")

        # Mock the actual hook's capture method
        with patch(
            "src.live_capture.capture_orchestrator.OpenAILiveCapture"
        ) as MockHook:
            mock_instance = MagicMock()
            mock_instance.capture_openai_interaction = AsyncMock(
                return_value="cap_integration_123"
            )
            MockHook.return_value = mock_instance

            # Perform capture
            result = await orchestrator.capture(
                platform="openai",
                user_input="Write a Python function",
                assistant_response="Here's a Python function...",
                model="gpt-4",
                interaction_type="code_generation",
            )

            # Verify result
            assert result == "cap_integration_123"

            # Verify hook was called with correct parameters
            call_args = mock_instance.capture_openai_interaction.call_args
            assert call_args.kwargs["user_input"] == "Write a Python function"
            assert (
                call_args.kwargs["assistant_response"] == "Here's a Python function..."
            )
            assert call_args.kwargs["model"] == "gpt-4"
            assert call_args.kwargs["interaction_type"] == "code_generation"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
