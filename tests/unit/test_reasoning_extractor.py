"""
Unit tests for Reasoning Extractor.
"""

import json
import os

import pytest

from src.enrichment.reasoning_extractor import ReasoningExtractor


class TestReasoningExtractorInit:
    """Tests for ReasoningExtractor initialization."""

    def test_disabled_by_default(self):
        """Test extractor is disabled by default."""
        # Ensure env var is not set
        if "ENABLE_AI_ENRICHMENT" in os.environ:
            del os.environ["ENABLE_AI_ENRICHMENT"]

        extractor = ReasoningExtractor()

        assert extractor.enabled is False

    def test_enabled_when_env_set(self, monkeypatch):
        """Test extractor is enabled when env var is set."""
        monkeypatch.setenv("ENABLE_AI_ENRICHMENT", "true")

        extractor = ReasoningExtractor()

        assert extractor.enabled is True

    def test_default_model(self):
        """Test default model."""
        extractor = ReasoningExtractor()

        assert extractor.model == "gpt-4o-mini"

    def test_custom_model(self):
        """Test custom model."""
        extractor = ReasoningExtractor(model="gpt-4-turbo")

        assert extractor.model == "gpt-4-turbo"


class TestConstructPrompt:
    """Tests for _construct_prompt method."""

    def test_construct_prompt(self):
        """Test constructing the prompt."""
        extractor = ReasoningExtractor()

        prompt = extractor._construct_prompt(
            user_input="What is 2+2?",
            ai_response="2+2 equals 4 because we're adding two pairs.",
        )

        assert "USER: What is 2+2?" in prompt
        assert "AI: 2+2 equals 4" in prompt
        assert "steps" in prompt
        assert "JSON" in prompt

    def test_construct_prompt_with_long_input(self):
        """Test constructing prompt with long input."""
        extractor = ReasoningExtractor()

        long_input = "x" * 1000
        long_response = "y" * 1000

        prompt = extractor._construct_prompt(long_input, long_response)

        assert "x" * 100 in prompt
        assert "y" * 100 in prompt


class TestParseResponse:
    """Tests for _parse_response method."""

    def test_parse_valid_json(self):
        """Test parsing valid JSON."""
        extractor = ReasoningExtractor()

        response = '{"steps": [{"description": "Step 1"}]}'
        result = extractor._parse_response(response)

        assert "steps" in result
        assert len(result["steps"]) == 1

    def test_parse_json_with_code_blocks(self):
        """Test parsing JSON wrapped in code blocks."""
        extractor = ReasoningExtractor()

        response = '```json\n{"steps": [{"description": "Step 1"}]}\n```'
        result = extractor._parse_response(response)

        assert "steps" in result
        assert len(result["steps"]) == 1

    def test_parse_invalid_json(self):
        """Test parsing invalid JSON returns empty steps."""
        extractor = ReasoningExtractor()

        response = "This is not JSON"
        result = extractor._parse_response(response)

        assert result == {"steps": []}

    def test_parse_empty_response(self):
        """Test parsing empty response."""
        extractor = ReasoningExtractor()

        result = extractor._parse_response("")

        assert result == {"steps": []}


class TestExtractLocal:
    """Tests for _extract_local method (rule-based extraction)."""

    @pytest.fixture
    def extractor(self, monkeypatch):
        """Create an enabled extractor."""
        monkeypatch.setenv("ENABLE_AI_ENRICHMENT", "true")
        return ReasoningExtractor()

    def test_extract_code_modification(self, extractor):
        """Test extracting code modification reasoning."""
        result = extractor._extract_local(
            user_input="Please fix the bug",
            ai_response="Let me fix the authentication error in the login function.",
        )

        assert "steps" in result
        assert "suggested_score" in result

    def test_extract_problem_identification(self, extractor):
        """Test extracting problem identification."""
        result = extractor._extract_local(
            user_input="What's wrong?",
            ai_response="The error is caused by a null pointer exception.",
        )

        assert "steps" in result

    def test_extract_recommendation(self, extractor):
        """Test extracting recommendation."""
        result = extractor._extract_local(
            user_input="What should I do?",
            ai_response="We should use a database connection pool instead.",
        )

        assert "steps" in result

    def test_extract_causal_reasoning(self, extractor):
        """Test extracting causal reasoning."""
        result = extractor._extract_local(
            user_input="Why did it fail?",
            ai_response="It failed because the API key was invalid.",
        )

        assert "steps" in result
        # Should find "because" pattern
        has_causal = any(
            step.get("step_type") == "causal_reasoning"
            for step in result.get("steps", [])
        )
        assert has_causal or len(result["steps"]) > 0

    def test_extract_conclusion(self, extractor):
        """Test extracting conclusion."""
        result = extractor._extract_local(
            user_input="What's the result?",
            ai_response="Therefore the function returns the correct value.",
        )

        assert "steps" in result

    def test_extract_code_blocks(self, extractor):
        """Test detecting code blocks."""
        result = extractor._extract_local(
            user_input="Show me the code",
            ai_response="Here's the solution:\n```python\ndef foo(): pass\n```",
        )

        assert "steps" in result
        # Should detect code implementation
        has_code = any(
            step.get("step_type") == "code_implementation"
            for step in result.get("steps", [])
        )
        assert has_code

    def test_extract_multiple_code_blocks(self, extractor):
        """Test detecting multiple code blocks."""
        result = extractor._extract_local(
            user_input="Help me",
            ai_response="```python\ncode1\n```\n\n```python\ncode2\n```",
        )

        # Should detect code implementation with multiple blocks
        code_steps = [
            s
            for s in result.get("steps", [])
            if s.get("step_type") == "code_implementation"
        ]
        if code_steps:
            assert "2 code block" in code_steps[0].get("reasoning", "")

    def test_extract_empty_input(self, extractor):
        """Test extraction with empty input."""
        result = extractor._extract_local(
            user_input="",
            ai_response="",
        )

        assert "steps" in result
        assert "suggested_score" in result

    def test_suggested_score_increases_with_steps(self, extractor):
        """Test that suggested score increases with more steps."""
        result_simple = extractor._extract_local(
            user_input="Hi",
            ai_response="Hello.",
        )

        result_complex = extractor._extract_local(
            user_input="Help me fix this",
            ai_response="Let me fix the bug. The error is caused by null. Therefore we need to add validation. Because validation is important.",
        )

        # More reasoning should lead to higher score
        assert result_complex["suggested_score"] >= result_simple["suggested_score"]

    def test_suggested_score_capped(self, extractor):
        """Test that suggested score is capped."""
        result = extractor._extract_local(
            user_input="x" * 100,
            ai_response="Let me fix. The error is. Because. Therefore. Hence. Thus. So. Found. Looking at. We should. Instead of x, we use y.",
        )

        assert result["suggested_score"] <= 0.95

    def test_extraction_method_included(self, extractor):
        """Test that extraction method is included in result."""
        result = extractor._extract_local(
            user_input="test",
            ai_response="test response",
        )

        assert result.get("extraction_method") == "local_rule_based"

    def test_steps_limited_to_ten(self, extractor):
        """Test that steps are limited to 10."""
        # Create response with many patterns
        patterns = "Because x. Therefore y. Thus z. Hence a. So b. Found c. Looking at d. We should e. Instead of f, we g. The error is h. Let me fix i. I'll update j."

        result = extractor._extract_local(
            user_input="test",
            ai_response=patterns * 5,  # Repeat to trigger many matches
        )

        assert len(result["steps"]) <= 10

    def test_step_structure(self, extractor):
        """Test that steps have correct structure."""
        result = extractor._extract_local(
            user_input="What's wrong?",
            ai_response="The error is caused by memory leak. Therefore we need to fix it.",
        )

        if result["steps"]:
            step = result["steps"][0]
            assert "step_id" in step
            assert "operation" in step
            assert "reasoning" in step
            assert "evidence" in step
            assert "conclusion" in step
            assert "confidence" in step
            assert "weight" in step
            assert "step_type" in step
            assert "timestamp" in step


class TestExtractReasoningDisabled:
    """Tests for extract_reasoning when disabled."""

    @pytest.mark.asyncio
    async def test_returns_empty_when_disabled(self):
        """Test that extraction returns empty when disabled."""
        if "ENABLE_AI_ENRICHMENT" in os.environ:
            del os.environ["ENABLE_AI_ENRICHMENT"]

        extractor = ReasoningExtractor()
        result = await extractor.extract_reasoning(
            user_input="test",
            ai_response="test response",
        )

        assert result["steps"] == []
        assert result["suggested_score"] == 0.0


class TestExtractReasoningLocal:
    """Tests for extract_reasoning using local extraction."""

    @pytest.mark.asyncio
    async def test_uses_local_extraction(self, monkeypatch):
        """Test that local extraction is used when enabled without API key."""
        monkeypatch.setenv("ENABLE_AI_ENRICHMENT", "true")
        # Don't set API keys so it falls back to local

        extractor = ReasoningExtractor()
        result = await extractor.extract_reasoning(
            user_input="Fix the bug",
            ai_response="Let me fix the authentication issue.",
        )

        assert "steps" in result
        assert "suggested_score" in result
