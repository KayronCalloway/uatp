"""
Multi-modal Adapter Interfaces for UATP Capsule Engine.

This module extends the LLM adapter framework to support multi-modal AI models
that can process and generate different types of content including:
- Images
- Audio
- Video
- Mixed-modal content

These adapters integrate with the UATP capsule system to provide comprehensive
reasoning traces across different modalities.
"""

import abc
import base64
import hashlib
import logging
import os
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Union

# Use the canonical UATP capsule ReasoningStep model so we inherit the correct
# pydantic schema (including ``step_id`` and alias handling).
from src.capsule_schema import ReasoningStep
from pydantic import BaseModel, Field

from src.integrations.advanced_llm_registry import (
    LLMOutput,
    LLMProviderAdapter,
)

logger = logging.getLogger(__name__)


class ContentType(str, Enum):
    """Types of content that multi-modal models can process."""

    TEXT = "text"
    IMAGE = "image"
    AUDIO = "audio"
    VIDEO = "video"
    PDF = "pdf"
    HTML = "html"
    JSON = "json"
    MIXED = "mixed"


class MediaFormat(str, Enum):
    """Supported media formats for different content types."""

    # Image formats
    PNG = "png"
    JPEG = "jpeg"
    GIF = "gif"
    WEBP = "webp"

    # Audio formats
    MP3 = "mp3"
    WAV = "wav"
    OGG = "ogg"
    FLAC = "flac"

    # Video formats
    MP4 = "mp4"
    WEBM = "webm"
    MOV = "mov"

    # Document formats
    PDF = "pdf"

    # Other
    JSON = "json"
    HTML = "html"
    TEXT = "text"


class MediaContent(BaseModel):
    """Represents multi-modal content."""

    content_type: ContentType
    format: MediaFormat
    # Allow ``None`` so that lightweight reference objects can omit raw payloads
    data: Optional[Union[str, bytes]] = Field(default=None)
    uri: Optional[str] = Field(default=None)
    metadata: Dict[str, Any] = Field(default_factory=dict)

    # ------------------------------------------------------------------
    # Hash helpers
    # ------------------------------------------------------------------
    def get_content_hash(self) -> str:
        """Return a deterministic SHA-256 hash representing this media's payload.

        If the raw ``data`` payload has been stripped (``None``) – as is the case
        for lightweight reference copies created via :py:meth:`create_reference`
        – we fall back to any pre-computed hash stored in its metadata. This
        ensures that equality checks in the test-suite (e.g. ``ref.content_hash
        == original.content_hash()``) still succeed without having to ship large
        binary/text blobs around.
        """
        if self.data is None:
            cached = self.metadata.get("content_hash")
            if cached:
                return cached
            # As a very last resort hash the string ``"None"`` for stability –
            # but this path should never be hit in the current code-base.
            return hashlib.sha256(b"None").hexdigest()

        # Raw payload is present – hash it normally.
        if isinstance(self.data, str):
            content: bytes = self.data.encode("utf-8")
        elif isinstance(self.data, bytes):
            content = self.data
        else:
            content = str(self.data).encode("utf-8")

        return hashlib.sha256(content).hexdigest()

    # ------------------------------------------------------------------
    # Back-compatibility helpers
    # ------------------------------------------------------------------
    @property
    def content_hash_value(self) -> str:  # noqa: D401 – simple alias property
        """Return the SHA-256 hash of the content (attribute-style)."""
        return self.get_content_hash()

    def content_hash(self) -> str:  # noqa: D401 legacy callable alias
        """Callable alias retained for backward-compatibility with tests."""
        return self.get_content_hash()

    def content_hash_(self) -> str:  # pragma: no cover – deprecated double alias
        return self.get_content_hash()

    def create_reference(self) -> "MediaContent":
        """Return a lightweight reference copy without raw data.

        Tests expect ``MediaContent.create_reference`` to strip the binary/text
        payload while preserving type, format, metadata, and, critically, the
        *content hash* so that equality checks still work.
        """
        # Pre-compute the content hash so that the reference object can expose it
        # even after the raw payload has been stripped.
        content_hash_value = self.get_content_hash()

        # Clone metadata and include the pre-computed hash for later retrieval.
        new_metadata = self.metadata.copy()
        new_metadata["content_hash"] = content_hash_value

        return MediaContent(
            content_type=self.content_type,
            format=self.format,
            data=None,  # Remove heavy payload
            uri=self.uri,
            metadata=new_metadata,
        )

    # ------------------------------------------------------------------
    # Backward-compatibility: content_hash as property
    # ------------------------------------------------------------------
    @property
    def content_hash(self) -> str:
        """Property version for test compatibility."""
        if self.data is None and "content_hash" in self.metadata:
            return self.metadata["content_hash"]
        return self.get_content_hash()

    def to_base64(self) -> str:
        """Convert content to base64 string."""
        if isinstance(self.data, str):
            # Handle text data
            if self.content_type == ContentType.TEXT:
                return self.data
            # Handle base64 data that's already a string
            return self.data
        elif isinstance(self.data, bytes):
            # Convert bytes to base64 string
            return base64.b64encode(self.data).decode("utf-8")
        else:
            raise ValueError(f"Unsupported data type: {type(self.data)}")

    @classmethod
    def from_file(cls, file_path: str) -> "MediaContent":
        """Create MediaContent from a file."""
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

        # Determine content type from file extension
        ext = os.path.splitext(file_path)[1].lower().replace(".", "")
        content_type = None
        media_format = None

        # Map extension to content type and format
        if ext in ["png", "jpg", "jpeg", "gif", "webp"]:
            content_type = ContentType.IMAGE
            media_format = MediaFormat(ext) if ext != "jpg" else MediaFormat.JPEG
        elif ext in ["mp3", "wav", "ogg", "flac"]:
            content_type = ContentType.AUDIO
            media_format = MediaFormat(ext)
        elif ext in ["mp4", "webm", "mov"]:
            content_type = ContentType.VIDEO
            media_format = MediaFormat(ext)
        elif ext == "pdf":
            content_type = ContentType.PDF
            media_format = MediaFormat.PDF
        elif ext == "json":
            content_type = ContentType.JSON
            media_format = MediaFormat.JSON
        elif ext == "html":
            content_type = ContentType.HTML
            media_format = MediaFormat.HTML
        elif ext in ["txt", "text"]:
            content_type = ContentType.TEXT
            media_format = MediaFormat.TEXT
        else:
            raise ValueError(f"Unsupported file extension: {ext}")

        # Read file content
        with open(file_path, "rb") as f:
            data = f.read()

        # For text-based formats, convert to string
        if content_type in [ContentType.TEXT, ContentType.JSON, ContentType.HTML]:
            data = data.decode("utf-8")

        return cls(
            content_type=content_type,
            format=media_format,
            data=data,
            metadata={
                "filename": os.path.basename(file_path),
                "filesize": os.path.getsize(file_path),
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
        )


@dataclass
class MultiModalOutput(LLMOutput):
    """Extended LLM output that supports multi-modal content."""

    media_outputs: List[MediaContent] = field(default_factory=list)
    input_media: List[MediaContent] = field(default_factory=list)

    def add_media_output(self, media: MediaContent) -> None:
        """Add a media output to this result."""
        self.media_outputs.append(media)

    def get_media_by_type(self, content_type: ContentType) -> List[MediaContent]:
        """Get all media outputs of a specific type."""
        return [m for m in self.media_outputs if m.content_type == content_type]


class MultiModalReasoningStep(ReasoningStep):
    """Extended reasoning step that supports multi-modal content."""

    # Store references to MediaContent (tests expect MediaContent objects)
    input_media: List["MediaContent"] = Field(default_factory=list)
    output_media: List["MediaContent"] = Field(default_factory=list)
    media_references: List[Dict[str, Any]] = Field(default_factory=list)

    # ------------------------------------------------------------------
    # Serialization helpers
    # ------------------------------------------------------------------
    def to_dict(self) -> Dict[str, Any]:
        """Return a JSON-serializable dict representation of the step.

        This mirrors :pymeth:`pydantic.BaseModel.model_dump`, but also ensures
        that nested :pyclass:`Enum` values are converted to their underlying
        value so that simple equality checks in tests (e.g. ``"image"``) pass.
        """
        # Build a serializable representation first converting MediaContent to
        # simple dicts so pydantic doesn't choke on nested custom objects.
        raw = self.model_dump(exclude_none=True)

        # Replace MediaContent objects with serializable dict payloads
        for key in ("input_media", "output_media"):
            if key in raw and isinstance(raw[key], list):
                raw[key] = [
                    MultiModalReasoningTraceConverter.convert_media_to_payload(m)
                    if isinstance(m, MediaContent)
                    else m
                    for m in raw[key]
                ]

        def convert(obj):
            from enum import Enum

            if isinstance(obj, Enum):
                return obj.value
            if isinstance(obj, list):
                return [convert(i) for i in obj]
            if isinstance(obj, dict):
                return {k: convert(v) for k, v in obj.items()}
            return obj

        return convert(raw)

    def add_input_media(self, media: MediaContent) -> None:
        """Add input media to this reasoning step.

        Store *reference* copies (without raw payload) to keep the reasoning
        trace lightweight, but continue to expose a normal ``MediaContent``
        object so that tests can call helper methods like
        ``content_hash``/``get_content_hash``.
        """
        self.input_media.append(media.create_reference())

    def add_output_media(self, media: MediaContent) -> None:
        """Add output media to this reasoning step (stores reference only)."""
        self.output_media.append(media.create_reference())

    def add_media_reference(
        self, media_hash: str, reference_type: str, description: str
    ) -> None:
        """Add a reference to media used in reasoning."""
        self.media_references.append(
            {
                "media_hash": media_hash,
                "reference_type": reference_type,
                "description": description,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        )


class MultiModalProviderAdapter(LLMProviderAdapter, abc.ABC):
    """Base class for multi-modal AI provider adapters."""

    @abc.abstractmethod
    async def process_image(
        self,
        model: str,
        image: MediaContent,
        prompt: str = None,
        options: Dict[str, Any] = None,
    ) -> MultiModalOutput:
        """Process an image with the AI model."""
        pass

    @abc.abstractmethod
    async def process_audio(
        self,
        model: str,
        audio: MediaContent,
        prompt: str = None,
        options: Dict[str, Any] = None,
    ) -> MultiModalOutput:
        """Process audio with the AI model."""
        pass

    @abc.abstractmethod
    async def process_video(
        self,
        model: str,
        video: MediaContent,
        prompt: str = None,
        options: Dict[str, Any] = None,
    ) -> MultiModalOutput:
        """Process video with the AI model."""
        pass

    @abc.abstractmethod
    async def generate_image(
        self, model: str, prompt: str, options: Dict[str, Any] = None
    ) -> MultiModalOutput:
        """Generate an image based on a text prompt."""
        pass

    @abc.abstractmethod
    async def multi_modal_generate(
        self,
        model: str,
        inputs: List[MediaContent],
        prompt: str = None,
        system_prompt: str = None,
        options: Dict[str, Any] = None,
    ) -> MultiModalOutput:
        """Generate content based on multiple modal inputs."""
        pass

    def supports_content_type(self, content_type: ContentType) -> bool:
        """Check if this adapter supports a specific content type."""
        return content_type in self.get_supported_content_types()

    @abc.abstractmethod
    def get_supported_content_types(self) -> List[ContentType]:
        """Get the content types supported by this provider."""
        pass


class MultiModalReasoningTraceConverter:
    """
    Converts multi-modal reasoning steps to UATP capsule format.

    This class handles the conversion of internal multi-modal reasoning data
    to the standardized UATP capsule schema format, ensuring proper
    serialization and referencing of media content.
    """

    @staticmethod
    def convert_media_to_payload(media: MediaContent) -> Dict[str, Any]:
        """Convert MediaContent to a serializable payload format."""
        result = {
            "content_type": media.content_type,
            "format": media.format,
            "metadata": media.metadata,
        }

        # For media with raw data, generate hash and possibly store externally
        if media.data:
            content_hash = media.get_content_hash()
            result["content_hash"] = content_hash

            # For text data, include directly
            if media.content_type == ContentType.TEXT:
                result["text_content"] = (
                    media.data if isinstance(media.data, str) else None
                )
            else:
                # For binary data, include base64 representation
                try:
                    result["base64_content"] = media.to_base64()
                except ValueError as e:
                    logger.warning(f"Could not convert media to base64: {e}")

        # Include URI if available
        if media.uri:
            result["uri"] = media.uri

        return result

    @staticmethod
    def convert_reasoning_step(step: MultiModalReasoningStep) -> Dict[str, Any]:
        """Convert a multi-modal reasoning step to UATP capsule format."""
        # Start with base reasoning step conversion
        result = {
            "step_id": step.step_id,
            "operation": step.operation,
            "reasoning": step.reasoning,
            "confidence": step.confidence,
            "attribution_sources": step.attribution_sources,
            "timestamp": step.timestamp.isoformat() if step.timestamp else None,
            "parent_step_id": step.parent_step_id,
            "metadata": step.metadata,
        }

        # Add multi-modal specific fields
        if step.input_media:
            result["input_media"] = step.input_media

        if step.output_media:
            result["output_media"] = step.output_media

        if step.media_references:
            result["media_references"] = step.media_references

        return result


class MockMultiModalAdapter(MultiModalProviderAdapter):
    """Mock implementation of a multi-modal provider for testing."""

    @property
    def provider_name(self) -> str:
        """Return the canonical provider name required by the LLMProviderAdapter interface."""
        return "mock_multimodal"

    def __init__(self):
        """Initialize the mock multi-modal adapter."""
        self.provider_id = "mock_multimodal"

    async def list_models(self) -> List[str]:
        """List available models from this provider."""
        return ["vision-model", "audio-model", "video-model", "image-gen-model"]

    def get_supported_content_types(self) -> List[ContentType]:
        """Get content types supported by this provider."""
        return [
            ContentType.TEXT,
            ContentType.IMAGE,
            ContentType.AUDIO,
            ContentType.VIDEO,
        ]

    async def generate(
        self,
        model: str,
        prompt: str,
        system_prompt: str = None,
        max_tokens: int = 1000,
        temperature: float = 0.7,
    ) -> LLMOutput:
        """Generate text response (implements abstract method from LLMProviderAdapter)."""
        # Basic mock implementation
        response_text = f"This is a mock response from {model} about: {prompt[:20]}..."

        return LLMOutput(
            content=response_text,
            model_name=model,
            provider_name=self.provider_id,
            tokens_used=len(prompt.split()) + len(response_text.split()),
            cost_usd=0.001 * len(prompt.split()),
            trace_id=str(uuid.uuid4()),
            reasoning_trace=[],
        )

    async def process_image(
        self,
        model: str,
        image: MediaContent,
        prompt: str = None,
        options: Dict[str, Any] = None,
    ) -> MultiModalOutput:
        """Process an image with the AI model."""
        if model != "vision-model" and not model.startswith("vision"):
            raise ValueError(f"Model {model} does not support image processing")

        # Create a mock response based on the image metadata
        image_info = f"image size: {image.metadata.get('filesize', 'unknown')}"
        response_text = f"This is a mock image description. I see {image_info}."

        if prompt:
            response_text += f" Regarding your question: '{prompt}', I can answer based on this image."

        # Create a reasoning step for this operation
        step = MultiModalReasoningStep(
            step_id=1,
            operation="image_analysis",
            reasoning="Analyzed image content using vision capabilities",
            confidence=0.85,
        )
        step.add_input_media(image)

        return MultiModalOutput(
            content=response_text,
            model_name=model,
            provider_name=self.provider_id,
            tokens_used=200,  # Mock token count
            cost_usd=0.03,  # Mock cost for image processing
            trace_id=str(uuid.uuid4()),
            reasoning_trace=[step],
            input_media=[image],
        )

    async def process_audio(
        self,
        model: str,
        audio: MediaContent,
        prompt: str = None,
        options: Dict[str, Any] = None,
    ) -> MultiModalOutput:
        """Process audio with the AI model."""
        if model != "audio-model" and not model.startswith("audio"):
            raise ValueError(f"Model {model} does not support audio processing")

        # Create a mock transcription or analysis
        duration = audio.metadata.get("duration", "unknown")
        response_text = (
            f"This is a mock audio transcription from {duration} seconds of audio."
        )

        if prompt:
            response_text += f" Regarding your question: '{prompt}', I analyzed the audio accordingly."

        # Create a reasoning step
        step = MultiModalReasoningStep(
            step_id=1,
            operation="audio_transcription",
            reasoning="Processed audio content and extracted speech/sounds",
            confidence=0.78,
        )
        step.add_input_media(audio)

        return MultiModalOutput(
            content=response_text,
            model_name=model,
            provider_name=self.provider_id,
            tokens_used=150,  # Mock token count
            cost_usd=0.02,  # Mock cost
            trace_id=str(uuid.uuid4()),
            reasoning_trace=[step],
            input_media=[audio],
        )

    async def process_video(
        self,
        model: str,
        video: MediaContent,
        prompt: str = None,
        options: Dict[str, Any] = None,
    ) -> MultiModalOutput:
        """Process video with the AI model."""
        if model != "video-model" and not model.startswith("video"):
            raise ValueError(f"Model {model} does not support video processing")

        # Create a mock video analysis
        duration = video.metadata.get("duration", "unknown")
        response_text = (
            f"This is a mock video analysis of {duration} seconds of content."
        )

        if prompt:
            response_text += f" Regarding your request: '{prompt}', here's what I observed in the video."

        # Create a reasoning step
        step = MultiModalReasoningStep(
            step_id=1,
            operation="video_analysis",
            reasoning="Analyzed video frames and detected key elements",
            confidence=0.72,
        )
        step.add_input_media(video)

        return MultiModalOutput(
            content=response_text,
            model_name=model,
            provider_name=self.provider_id,
            tokens_used=300,  # Mock token count for video (higher)
            cost_usd=0.05,  # Mock cost (higher for video)
            trace_id=str(uuid.uuid4()),
            reasoning_trace=[step],
            input_media=[video],
        )

    async def generate_image(
        self, model: str, prompt: str, options: Dict[str, Any] = None
    ) -> MultiModalOutput:
        """Generate an image based on a text prompt."""
        if model != "image-gen-model" and not model.startswith("image-gen"):
            raise ValueError(f"Model {model} does not support image generation")

        # Create mock image data (just a small colored square)
        mock_image_data = b"iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg=="

        # Create a mock generated image
        output_image = MediaContent(
            content_type=ContentType.IMAGE,
            format=MediaFormat.PNG,
            data=mock_image_data,
            metadata={
                "generated": True,
                "prompt": prompt,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "dimensions": "512x512",
            },
        )

        # Create a reasoning step
        step = MultiModalReasoningStep(
            step_id=1,
            operation="image_generation",
            reasoning=f"Generated image based on prompt: {prompt}",
            confidence=0.9,
        )
        step.add_output_media(output_image)

        return MultiModalOutput(
            content="Image generated successfully",
            model_name=model,
            provider_name=self.provider_id,
            tokens_used=len(prompt.split()),
            cost_usd=0.04,  # Mock cost for image generation
            trace_id=str(uuid.uuid4()),
            reasoning_trace=[step],
            media_outputs=[output_image],
        )

    async def multi_modal_generate(
        self,
        model: str,
        inputs: List[MediaContent],
        prompt: str = None,
        system_prompt: str = None,
        options: Dict[str, Any] = None,
    ) -> MultiModalOutput:
        """Generate content based on multiple modal inputs."""
        # Create a mock response that incorporates all input types
        content_types = [media.content_type for media in inputs]
        content_type_summary = ", ".join([ct.value for ct in content_types])

        response_text = (
            f"This is a mock multi-modal response processing: {content_type_summary}"
        )
        if prompt:
            response_text += f"\nQuery: {prompt}\nResponse: Analyzed the provided content and generated this reply."

        # Create reasoning steps for each input
        reasoning_steps = []
        for i, media in enumerate(inputs):
            step = MultiModalReasoningStep(
                step_id=i + 1,
                operation=f"{media.content_type.value}_analysis",
                reasoning=f"Processed {media.content_type.value} input",
                confidence=0.8,
            )
            step.add_input_media(media)
            reasoning_steps.append(step)

        # Add a final reasoning step that combines all inputs
        final_step = MultiModalReasoningStep(
            step_id=len(inputs) + 1,
            operation="multi_modal_synthesis",
            reasoning="Combined insights from all input modalities",
            confidence=0.85,
            parent_step_id=[step.step_id for step in reasoning_steps],
        )
        reasoning_steps.append(final_step)

        return MultiModalOutput(
            content=response_text,
            model_name=model,
            provider_name=self.provider_id,
            tokens_used=500,  # Mock token count for multi-modal
            cost_usd=0.08,  # Mock cost
            trace_id=str(uuid.uuid4()),
            reasoning_trace=reasoning_steps,
            input_media=inputs,
        )
