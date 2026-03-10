"""
Tests for multi-modal adapter functionality.

These tests validate the multi-modal adapter interfaces and implementations
for the UATP Capsule Engine.
"""

import base64
import os
from unittest.mock import MagicMock, patch

import pytest

from src.integrations.multimodal_adapters import (
    ContentType,
    MediaContent,
    MediaFormat,
    MockMultiModalAdapter,
    MultiModalReasoningStep,
)


@pytest.fixture
def mock_adapter():
    """Create a mock multi-modal adapter for testing."""
    return MockMultiModalAdapter()


@pytest.fixture
def test_image():
    """Create a test image for use in tests."""
    # Simple 1x1 red pixel PNG
    image_data = b"iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg=="

    return MediaContent(
        content_type=ContentType.IMAGE,
        format=MediaFormat.PNG,
        data=image_data,
        metadata={"test": True, "filesize": len(image_data)},
    )


@pytest.fixture
def test_audio():
    """Create a test audio snippet for use in tests."""
    # Mock audio data (not actual audio, just for testing)
    audio_data = b"TESTAUDIODATA"

    return MediaContent(
        content_type=ContentType.AUDIO,
        format=MediaFormat.MP3,
        data=audio_data,
        metadata={"test": True, "duration": 3.5},
    )


@pytest.fixture
def test_video():
    """Create a test video snippet for use in tests."""
    # Mock video data (not actual video, just for testing)
    video_data = b"TESTVIDEODATA"

    return MediaContent(
        content_type=ContentType.VIDEO,
        format=MediaFormat.MP4,
        data=video_data,
        metadata={"test": True, "duration": 5.0},
    )


class TestMediaContent:
    """Test the MediaContent class functionality."""

    def test_creation(self, test_image):
        """Test creating a MediaContent object."""
        assert test_image.content_type == ContentType.IMAGE
        assert test_image.format == MediaFormat.PNG
        assert isinstance(test_image.data, bytes)
        assert test_image.metadata.get("test") is True

    def test_to_base64(self, test_image):
        """Test converting media content to base64."""
        b64 = test_image.to_base64()
        assert isinstance(b64, str)
        # Verify we can decode it back
        decoded = base64.b64decode(b64)
        assert decoded == test_image.data

    def test_content_hash(self, test_image, test_audio):
        """Test generating content hash."""
        # Same content should have same hash
        image1 = test_image
        image2 = MediaContent(
            content_type=ContentType.IMAGE,
            format=MediaFormat.PNG,
            data=test_image.data,
            metadata={
                "different": "metadata"
            },  # Different metadata shouldn't affect hash
        )

        assert image1.content_hash == image2.content_hash

        # Different content should have different hash
        assert image1.content_hash != test_audio.content_hash

    def test_media_reference(self, test_image):
        """Test creating a media reference."""
        ref = test_image.create_reference()
        assert ref.content_type == test_image.content_type
        assert ref.format == test_image.format
        assert ref.content_hash == test_image.content_hash
        # Reference metadata should include original metadata plus content_hash
        assert "content_hash" in ref.metadata
        for key, value in test_image.metadata.items():
            assert ref.metadata[key] == value
        assert ref.data is None  # Reference should not contain data


class TestMultiModalReasoningStep:
    """Test the MultiModalReasoningStep class functionality."""

    def test_creation(self):
        """Test creating a reasoning step."""
        step = MultiModalReasoningStep(
            step_id=1,
            operation="test_operation",
            reasoning="This is a test",
            confidence=0.9,
        )

        assert step.step_id == 1
        assert step.operation == "test_operation"
        assert step.reasoning == "This is a test"
        assert step.confidence == 0.9
        assert step.parent_step_id is None
        assert step.input_media == []
        assert step.output_media == []

    def test_add_media(self, test_image, test_audio):
        """Test adding media to reasoning steps."""
        step = MultiModalReasoningStep(
            step_id=1,
            operation="media_test",
            reasoning="Testing media addition",
            confidence=0.85,
        )

        # Add input media
        step.add_input_media(test_image)
        assert len(step.input_media) == 1
        assert step.input_media[0].content_type == ContentType.IMAGE

        # Add output media
        step.add_output_media(test_audio)
        assert len(step.output_media) == 1
        assert step.output_media[0].content_type == ContentType.AUDIO

    def test_to_dict(self, test_image):
        """Test converting reasoning step to dictionary."""
        step = MultiModalReasoningStep(
            step_id=1,
            operation="dict_test",
            reasoning="Testing dictionary conversion",
            confidence=0.95,
            parent_step_id=None,
        )

        step.add_input_media(test_image)

        step_dict = step.to_dict()

        assert step_dict["step_id"] == 1
        assert step_dict["operation"] == "dict_test"
        assert step_dict["reasoning"] == "Testing dictionary conversion"
        assert step_dict["confidence"] == 0.95
        assert "input_media" in step_dict
        assert len(step_dict["input_media"]) == 1
        assert step_dict["input_media"][0]["content_type"] == "image"

    def test_chaining(self):
        """Test chaining reasoning steps."""
        step1 = MultiModalReasoningStep(
            step_id=1,
            operation="first_step",
            reasoning="First operation",
            confidence=0.8,
        )

        step2 = MultiModalReasoningStep(
            step_id=2,
            operation="second_step",
            reasoning="Second operation",
            confidence=0.85,
            parent_step_id=1,  # Reference to step1
        )

        step3 = MultiModalReasoningStep(
            step_id=3,
            operation="third_step",
            reasoning="Third operation",
            confidence=0.9,
            parent_step_id=[1, 2],  # Multiple parents
        )

        assert step2.parent_step_id == 1
        assert isinstance(step3.parent_step_id, list)
        assert 1 in step3.parent_step_id
        assert 2 in step3.parent_step_id


@pytest.mark.asyncio
class TestMockMultiModalAdapter:
    """Test the MockMultiModalAdapter implementation."""

    async def test_list_models(self, mock_adapter):
        """Test listing available models."""
        models = await mock_adapter.list_models()
        assert isinstance(models, list)
        assert "vision-model" in models
        assert "audio-model" in models
        assert "video-model" in models

    def test_supported_content_types(self, mock_adapter):
        """Test getting supported content types."""
        content_types = mock_adapter.get_supported_content_types()
        assert ContentType.TEXT in content_types
        assert ContentType.IMAGE in content_types
        assert ContentType.AUDIO in content_types
        assert ContentType.VIDEO in content_types

    async def test_generate(self, mock_adapter):
        """Test text generation."""
        result = await mock_adapter.generate(
            model="test-model", prompt="This is a test prompt", temperature=0.7
        )

        assert "mock response" in result.content.lower()
        assert result.model == "test-model"
        assert result.provider == "mock_multimodal"
        assert isinstance(result.total_tokens, int)
        assert isinstance(result.cost, float)
        # LLMOutput doesn't have metadata field

    async def test_process_image(self, mock_adapter, test_image):
        """Test image processing."""
        result = await mock_adapter.process_image(
            model="vision-model", image=test_image, prompt="Describe this image"
        )

        assert "mock image description" in result.content.lower()
        assert "regarding your question" in result.content.lower()
        assert result.model == "vision-model"
        assert result.provider == "mock_multimodal"
        assert len(result.reasoning_steps) == 1
        assert result.reasoning_steps[0].operation == "image_analysis"
        assert result.input_media[0].content_hash == test_image.content_hash

    async def test_process_audio(self, mock_adapter, test_audio):
        """Test audio processing."""
        result = await mock_adapter.process_audio(
            model="audio-model", audio=test_audio, prompt="Transcribe this audio"
        )

        assert "mock audio transcription" in result.content.lower()
        assert result.model == "audio-model"
        assert result.provider == "mock_multimodal"
        assert len(result.reasoning_steps) == 1
        assert result.reasoning_steps[0].operation == "audio_transcription"
        assert result.input_media[0].content_hash == test_audio.content_hash

    async def test_process_video(self, mock_adapter, test_video):
        """Test video processing."""
        result = await mock_adapter.process_video(
            model="video-model", video=test_video, prompt="Analyze this video"
        )

        assert "mock video analysis" in result.content.lower()
        assert result.model == "video-model"
        assert result.provider == "mock_multimodal"
        assert len(result.reasoning_steps) == 1
        assert result.reasoning_steps[0].operation == "video_analysis"
        assert result.input_media[0].content_hash == test_video.content_hash

    async def test_generate_image(self, mock_adapter):
        """Test image generation."""
        result = await mock_adapter.generate_image(
            model="image-gen-model", prompt="A beautiful sunset over mountains"
        )

        assert "image generated successfully" in result.content.lower()
        assert result.model == "image-gen-model"
        assert result.provider == "mock_multimodal"
        assert len(result.reasoning_steps) == 1
        assert result.reasoning_steps[0].operation == "image_generation"
        assert len(result.media_outputs) == 1
        assert result.media_outputs[0].content_type == ContentType.IMAGE
        assert result.media_outputs[0].metadata.get("generated") is True

    async def test_multi_modal_generate(self, mock_adapter, test_image, test_audio):
        """Test multi-modal content generation."""
        inputs = [test_image, test_audio]

        result = await mock_adapter.multi_modal_generate(
            model="vision-model", inputs=inputs, prompt="Process these inputs together"
        )

        assert "multi-modal response" in result.content.lower()
        assert (
            "image, audio" in result.content.lower()
            or "audio, image" in result.content.lower()
        )
        assert result.model == "vision-model"
        assert result.provider == "mock_multimodal"

        # Should have steps for each input plus a synthesis step
        assert len(result.reasoning_steps) == len(inputs) + 1

        # Verify the final step has parent steps
        final_step = result.reasoning_steps[-1]
        assert final_step.operation == "multi_modal_synthesis"
        assert isinstance(final_step.parent_step_id, list)
        assert len(final_step.parent_step_id) == len(inputs)


# Add more test cases if needed for OpenAI adapter, but using mocks to avoid API calls
@pytest.mark.asyncio
class TestOpenAIMultiModalAdapter:
    """Test the OpenAIMultiModalAdapter implementation."""

    @pytest.mark.skipif(
        "OPENAI_API_KEY" not in os.environ, reason="OpenAI API key not available"
    )
    async def test_list_models_mock(self):
        """Test listing available models using a mock."""
        with patch(
            "src.integrations.openai_multimodal_adapter.OpenAIMultiModalAdapter"
        ) as mock_class:
            # Setup mock
            mock_instance = MagicMock()
            # Make the mock async

            async def mock_list_models():
                return ["gpt-4-vision-preview", "dall-e-3", "gpt-4"]

            mock_instance.list_models = mock_list_models
            mock_class.return_value = mock_instance

            # Import here to use the mock
            from src.integrations.openai_multimodal_adapter import (
                OpenAIMultiModalAdapter,
            )

            adapter = OpenAIMultiModalAdapter()
            models = await adapter.list_models()

            assert isinstance(models, list)
            assert "gpt-4-vision-preview" in models
            assert "dall-e-3" in models
