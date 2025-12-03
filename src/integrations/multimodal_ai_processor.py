"""
Multi-Modal AI Processing System
Handles text, image, audio, and video processing with unified attribution
"""

import base64
import io
import logging
from dataclasses import asdict, dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Union

import aiofiles
import moviepy as mp
import speech_recognition as sr
from PIL import Image
from pydantic import BaseModel, Field, validator

from ..attribution.cross_conversation_tracker import CrossConversationTracker
from ..capsules.specialized_capsules import create_specialized_capsule
from ..economic.fcde_engine import FCDEEngine
from ..engine.capsule_engine import CapsuleEngine

logger = logging.getLogger(__name__)


class MediaType(Enum):
    """Supported media types for multi-modal processing"""

    TEXT = "text"
    IMAGE = "image"
    AUDIO = "audio"
    VIDEO = "video"
    DOCUMENT = "document"


class ProcessingMode(Enum):
    """Processing modes for different AI capabilities"""

    ANALYSIS = "analysis"
    GENERATION = "generation"
    TRANSFORMATION = "transformation"
    EXTRACTION = "extraction"


@dataclass
class MediaInput:
    """Input media for processing"""

    media_type: MediaType
    content: Union[str, bytes]
    metadata: Dict[str, Any]
    source_uri: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class ProcessingResult:
    """Result of multi-modal processing"""

    media_type: MediaType
    processing_mode: ProcessingMode
    output: Any
    confidence: float
    processing_time: float
    attribution_data: Dict[str, Any]
    capsule_id: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class MultiModalRequest(BaseModel):
    """Request for multi-modal AI processing"""

    media_inputs: List[Dict[str, Any]]
    processing_mode: ProcessingMode
    target_media_type: Optional[MediaType] = None
    processing_options: Dict[str, Any] = Field(default_factory=dict)
    attribution_context: Dict[str, Any] = Field(default_factory=dict)

    @validator("media_inputs")
    def validate_media_inputs(cls, v):
        if not v:
            raise ValueError("At least one media input is required")
        return v


class MultiModalAIProcessor:
    """
    Advanced multi-modal AI processing system with unified attribution
    """

    def __init__(
        self,
        capsule_engine: CapsuleEngine,
        attribution_tracker: CrossConversationTracker,
        fcde_engine: FCDEEngine,
    ):
        self.capsule_engine = capsule_engine
        self.attribution_tracker = attribution_tracker
        self.fcde_engine = fcde_engine

        # AI Provider configurations
        self.providers = {
            "openai": {
                "vision_model": "gpt-4-vision-preview",
                "audio_model": "whisper-1",
                "text_model": "gpt-4-turbo",
                "capabilities": [MediaType.TEXT, MediaType.IMAGE, MediaType.AUDIO],
            },
            "anthropic": {
                "vision_model": "claude-3-opus-20240229",
                "text_model": "claude-3-opus-20240229",
                "capabilities": [MediaType.TEXT, MediaType.IMAGE],
            },
            "google": {
                "vision_model": "gemini-pro-vision",
                "text_model": "gemini-pro",
                "capabilities": [MediaType.TEXT, MediaType.IMAGE, MediaType.VIDEO],
            },
        }

        self.processing_stats = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "processing_time_total": 0.0,
            "by_media_type": {media_type.value: 0 for media_type in MediaType},
        }

    async def process_multimodal_request(
        self, request: MultiModalRequest
    ) -> Dict[str, Any]:
        """
        Process a multi-modal AI request with full attribution tracking
        """
        start_time = datetime.now()
        request_id = f"mm_{int(datetime.now().timestamp())}"

        try:
            self.processing_stats["total_requests"] += 1

            # Parse media inputs
            media_inputs = []
            for media_input_data in request.media_inputs:
                media_input = MediaInput(
                    media_type=MediaType(media_input_data["media_type"]),
                    content=media_input_data["content"],
                    metadata=media_input_data.get("metadata", {}),
                    source_uri=media_input_data.get("source_uri"),
                )
                media_inputs.append(media_input)

            # Process each media input
            processing_results = []
            for media_input in media_inputs:
                result = await self._process_single_media(
                    media_input, request.processing_mode, request.processing_options
                )
                processing_results.append(result)

                # Update statistics
                self.processing_stats["by_media_type"][
                    media_input.media_type.value
                ] += 1

            # Create unified result
            unified_result = await self._create_unified_result(
                processing_results, request.target_media_type
            )

            # Track attribution
            attribution_data = await self._track_multimodal_attribution(
                media_inputs,
                processing_results,
                unified_result,
                request.attribution_context,
            )

            # Create capsule for the multimodal interaction
            capsule = await self._create_multimodal_capsule(
                media_inputs, processing_results, unified_result, attribution_data
            )

            processing_time = (datetime.now() - start_time).total_seconds()
            self.processing_stats["processing_time_total"] += processing_time
            self.processing_stats["successful_requests"] += 1

            return {
                "request_id": request_id,
                "status": "success",
                "processing_time": processing_time,
                "media_inputs_count": len(media_inputs),
                "processing_results": [
                    result.to_dict() for result in processing_results
                ],
                "unified_result": unified_result,
                "attribution_data": attribution_data,
                "capsule_id": capsule.id if capsule else None,
                "timestamp": datetime.now().isoformat(),
            }

        except Exception as e:
            self.processing_stats["failed_requests"] += 1
            logger.error(f"Multi-modal processing failed: {str(e)}")
            raise

    async def _process_single_media(
        self,
        media_input: MediaInput,
        processing_mode: ProcessingMode,
        options: Dict[str, Any],
    ) -> ProcessingResult:
        """Process a single media input"""
        start_time = datetime.now()

        try:
            if media_input.media_type == MediaType.TEXT:
                output = await self._process_text(media_input, processing_mode, options)
            elif media_input.media_type == MediaType.IMAGE:
                output = await self._process_image(
                    media_input, processing_mode, options
                )
            elif media_input.media_type == MediaType.AUDIO:
                output = await self._process_audio(
                    media_input, processing_mode, options
                )
            elif media_input.media_type == MediaType.VIDEO:
                output = await self._process_video(
                    media_input, processing_mode, options
                )
            elif media_input.media_type == MediaType.DOCUMENT:
                output = await self._process_document(
                    media_input, processing_mode, options
                )
            else:
                raise ValueError(f"Unsupported media type: {media_input.media_type}")

            processing_time = (datetime.now() - start_time).total_seconds()

            return ProcessingResult(
                media_type=media_input.media_type,
                processing_mode=processing_mode,
                output=output,
                confidence=output.get("confidence", 0.95),
                processing_time=processing_time,
                attribution_data={
                    "provider": output.get("provider", "unknown"),
                    "model": output.get("model", "unknown"),
                    "tokens_used": output.get("tokens_used", 0),
                    "api_calls": output.get("api_calls", 1),
                },
            )

        except Exception as e:
            logger.error(f"Single media processing failed: {str(e)}")
            raise

    async def _process_text(
        self, media_input: MediaInput, mode: ProcessingMode, options: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Process text input with various AI models"""
        text_content = (
            media_input.content
            if isinstance(media_input.content, str)
            else media_input.content.decode()
        )

        # Choose best provider for text processing
        provider = options.get("provider", "openai")
        model = self.providers[provider]["text_model"]

        if mode == ProcessingMode.ANALYSIS:
            # Analyze text sentiment, entities, topics
            analysis_prompt = f"""
            Analyze the following text for:
            1. Sentiment (positive, negative, neutral)
            2. Key entities (people, places, organizations)
            3. Main topics and themes
            4. Intent and purpose
            5. Emotional tone

            Text: {text_content}

            Provide a structured JSON response.
            """

            result = await self._call_text_model(provider, model, analysis_prompt)

        elif mode == ProcessingMode.GENERATION:
            # Generate content based on text input
            generation_prompt = f"""
            Based on the following input text, generate:
            {options.get('generation_type', 'a creative continuation')}

            Input: {text_content}

            Requirements:
            - Length: {options.get('length', 'medium')}
            - Style: {options.get('style', 'conversational')}
            - Format: {options.get('format', 'text')}
            """

            result = await self._call_text_model(provider, model, generation_prompt)

        elif mode == ProcessingMode.TRANSFORMATION:
            # Transform text (translate, summarize, rewrite)
            transformation_type = options.get("transformation_type", "summarize")
            transform_prompt = f"""
            {transformation_type.capitalize()} the following text:

            {text_content}

            Requirements: {options.get('requirements', 'maintain key information')}
            """

            result = await self._call_text_model(provider, model, transform_prompt)

        else:
            result = {"error": f"Unsupported processing mode for text: {mode}"}

        return {
            "content": result,
            "provider": provider,
            "model": model,
            "confidence": 0.95,
            "tokens_used": len(text_content.split()) * 1.3,  # Estimate
            "api_calls": 1,
        }

    async def _process_image(
        self, media_input: MediaInput, mode: ProcessingMode, options: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Process image input with vision models"""

        # Convert image to base64 if needed
        if isinstance(media_input.content, bytes):
            image_data = base64.b64encode(media_input.content).decode()
        else:
            image_data = media_input.content

        provider = options.get("provider", "openai")
        model = self.providers[provider]["vision_model"]

        if mode == ProcessingMode.ANALYSIS:
            # Analyze image content
            analysis_prompt = options.get(
                "prompt",
                """
            Analyze this image in detail:
            1. Describe what you see
            2. Identify objects, people, animals
            3. Describe the setting and context
            4. Note colors, composition, style
            5. Identify any text or writing
            6. Assess emotional tone or mood

            Provide a structured JSON response.
            """,
            )

            result = await self._call_vision_model(
                provider, model, analysis_prompt, image_data
            )

        elif mode == ProcessingMode.EXTRACTION:
            # Extract specific information from image
            extraction_prompt = f"""
            Extract the following information from this image:
            {options.get('extraction_targets', 'text, objects, people')}

            Format the response as structured JSON.
            """

            result = await self._call_vision_model(
                provider, model, extraction_prompt, image_data
            )

        else:
            result = {"error": f"Unsupported processing mode for image: {mode}"}

        return {
            "content": result,
            "provider": provider,
            "model": model,
            "confidence": 0.90,
            "tokens_used": 1000,  # Estimate for image processing
            "api_calls": 1,
        }

    async def _process_audio(
        self, media_input: MediaInput, mode: ProcessingMode, options: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Process audio input with speech recognition and analysis"""

        audio_data = media_input.content

        if mode == ProcessingMode.EXTRACTION:
            # Speech to text
            recognizer = sr.Recognizer()

            # Convert audio bytes to audio file
            audio_file = io.BytesIO(audio_data)

            with sr.AudioFile(audio_file) as source:
                audio = recognizer.record(source)
                text = recognizer.recognize_google(audio)

            # Analyze the transcribed text
            analysis_prompt = f"""
            Analyze this transcribed audio for:
            1. Speaker sentiment
            2. Key topics discussed
            3. Intent and purpose
            4. Emotional tone
            5. Important entities mentioned

            Transcribed text: {text}

            Provide structured JSON response.
            """

            provider = options.get("provider", "openai")
            model = self.providers[provider]["text_model"]
            analysis_result = await self._call_text_model(
                provider, model, analysis_prompt
            )

            result = {"transcription": text, "analysis": analysis_result}

        elif mode == ProcessingMode.ANALYSIS:
            # Direct audio analysis (if supported by provider)
            result = await self._call_audio_model("openai", "whisper-1", audio_data)

        else:
            result = {"error": f"Unsupported processing mode for audio: {mode}"}

        return {
            "content": result,
            "provider": "openai",
            "model": "whisper-1",
            "confidence": 0.88,
            "tokens_used": 500,  # Estimate
            "api_calls": 1,
        }

    async def _process_video(
        self, media_input: MediaInput, mode: ProcessingMode, options: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Process video input by extracting frames and audio"""

        video_data = media_input.content

        # Save video temporarily
        temp_video_path = f"/tmp/video_{int(datetime.now().timestamp())}.mp4"

        async with aiofiles.open(temp_video_path, "wb") as f:
            await f.write(video_data)

        try:
            # Extract frames and audio
            video = mp.VideoFileClip(temp_video_path)

            # Extract key frames
            frame_times = [video.duration * i / 5 for i in range(5)]  # 5 key frames
            frames = []

            for t in frame_times:
                frame = video.get_frame(t)
                frame_image = Image.fromarray(frame)
                frame_buffer = io.BytesIO()
                frame_image.save(frame_buffer, format="JPEG")
                frames.append(base64.b64encode(frame_buffer.getvalue()).decode())

            # Extract audio
            audio = video.audio
            audio_path = f"/tmp/audio_{int(datetime.now().timestamp())}.wav"
            audio.write_audiofile(audio_path, verbose=False, logger=None)

            with open(audio_path, "rb") as f:
                audio_data = f.read()

            # Process frames and audio
            frame_results = []
            for i, frame_data in enumerate(frames):
                frame_input = MediaInput(
                    media_type=MediaType.IMAGE,
                    content=frame_data,
                    metadata={"frame_time": frame_times[i], "frame_index": i},
                )
                frame_result = await self._process_image(frame_input, mode, options)
                frame_results.append(frame_result)

            # Process audio
            audio_input = MediaInput(
                media_type=MediaType.AUDIO,
                content=audio_data,
                metadata={"source": "video_extraction"},
            )
            audio_result = await self._process_audio(
                audio_input, ProcessingMode.EXTRACTION, options
            )

            # Combine results
            result = {
                "video_analysis": {
                    "duration": video.duration,
                    "fps": video.fps,
                    "resolution": [video.w, video.h],
                },
                "frame_analysis": frame_results,
                "audio_analysis": audio_result,
                "summary": "Video processed successfully",
            }

            # Cleanup
            import os

            os.remove(temp_video_path)
            if os.path.exists(audio_path):
                os.remove(audio_path)

        except Exception as e:
            logger.error(f"Video processing failed: {str(e)}")
            result = {"error": f"Video processing failed: {str(e)}"}

        return {
            "content": result,
            "provider": "local_processing",
            "model": "moviepy_extraction",
            "confidence": 0.85,
            "tokens_used": 2000,  # Estimate
            "api_calls": len(frames) + 1,  # Frame processing + audio processing
        }

    async def _process_document(
        self, media_input: MediaInput, mode: ProcessingMode, options: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Process document input (PDF, Word, etc.)"""

        # Extract text from document
        document_data = media_input.content

        # For now, assume text extraction is handled externally
        # In a real implementation, you'd use libraries like PyPDF2, python-docx, etc.

        if mode == ProcessingMode.EXTRACTION:
            # Extract text and metadata
            extracted_text = "Document text extraction would happen here"

            # Process extracted text
            text_input = MediaInput(
                media_type=MediaType.TEXT,
                content=extracted_text,
                metadata={"source": "document_extraction"},
            )

            text_result = await self._process_text(
                text_input, ProcessingMode.ANALYSIS, options
            )

            result = {"extracted_text": extracted_text, "text_analysis": text_result}

        else:
            result = {"error": f"Unsupported processing mode for document: {mode}"}

        return {
            "content": result,
            "provider": "local_processing",
            "model": "document_extractor",
            "confidence": 0.90,
            "tokens_used": 1500,  # Estimate
            "api_calls": 1,
        }

    async def _call_text_model(
        self, provider: str, model: str, prompt: str
    ) -> Dict[str, Any]:
        """Call text generation model"""
        # This would integrate with actual AI providers
        # For now, return a mock response
        return {
            "response": f"Mock response for prompt: {prompt[:100]}...",
            "model": model,
            "provider": provider,
        }

    async def _call_vision_model(
        self, provider: str, model: str, prompt: str, image_data: str
    ) -> Dict[str, Any]:
        """Call vision model"""
        # This would integrate with actual AI providers
        # For now, return a mock response
        return {
            "response": f"Mock vision analysis for prompt: {prompt[:100]}...",
            "model": model,
            "provider": provider,
            "image_analyzed": True,
        }

    async def _call_audio_model(
        self, provider: str, model: str, audio_data: bytes
    ) -> Dict[str, Any]:
        """Call audio processing model"""
        # This would integrate with actual AI providers
        # For now, return a mock response
        return {
            "transcription": "Mock audio transcription",
            "model": model,
            "provider": provider,
            "audio_duration": len(audio_data) / 16000,  # Estimate
        }

    async def _create_unified_result(
        self,
        processing_results: List[ProcessingResult],
        target_media_type: Optional[MediaType],
    ) -> Dict[str, Any]:
        """Create unified result from multiple processing results"""

        unified_result = {
            "unified_analysis": {
                "total_inputs": len(processing_results),
                "processing_modes": list(
                    {result.processing_mode.value for result in processing_results}
                ),
                "media_types": list(
                    {result.media_type.value for result in processing_results}
                ),
                "average_confidence": sum(
                    result.confidence for result in processing_results
                )
                / len(processing_results),
                "total_processing_time": sum(
                    result.processing_time for result in processing_results
                ),
            },
            "individual_results": [result.to_dict() for result in processing_results],
        }

        # If target media type is specified, attempt conversion
        if target_media_type:
            unified_result["target_conversion"] = await self._convert_to_target_media(
                processing_results, target_media_type
            )

        # Generate summary insights
        unified_result["insights"] = await self._generate_unified_insights(
            processing_results
        )

        return unified_result

    async def _convert_to_target_media(
        self, processing_results: List[ProcessingResult], target_media_type: MediaType
    ) -> Dict[str, Any]:
        """Convert processing results to target media type"""

        # This is a simplified conversion - in reality, you'd use specialized models
        conversion_result = {
            "target_type": target_media_type.value,
            "conversion_status": "success",
            "converted_content": f"Converted content to {target_media_type.value}",
        }

        return conversion_result

    async def _generate_unified_insights(
        self, processing_results: List[ProcessingResult]
    ) -> Dict[str, Any]:
        """Generate unified insights from all processing results"""

        insights = {
            "cross_modal_patterns": [],
            "dominant_themes": [],
            "sentiment_consistency": True,
            "content_coherence": 0.95,
            "recommended_actions": [],
        }

        # Analyze patterns across different media types
        text_results = [r for r in processing_results if r.media_type == MediaType.TEXT]
        image_results = [
            r for r in processing_results if r.media_type == MediaType.IMAGE
        ]
        audio_results = [
            r for r in processing_results if r.media_type == MediaType.AUDIO
        ]

        if text_results and image_results:
            insights["cross_modal_patterns"].append("text_image_correlation")

        if audio_results:
            insights["cross_modal_patterns"].append("audio_content_analysis")

        return insights

    async def _track_multimodal_attribution(
        self,
        media_inputs: List[MediaInput],
        processing_results: List[ProcessingResult],
        unified_result: Dict[str, Any],
        context: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Track attribution for multi-modal processing"""

        attribution_data = {
            "session_id": context.get("session_id", "unknown"),
            "user_id": context.get("user_id", "unknown"),
            "conversation_id": context.get("conversation_id", "unknown"),
            "media_contributions": [],
            "ai_provider_usage": {},
            "processing_costs": {},
            "attribution_weights": {},
        }

        # Track each media input contribution
        for i, (media_input, result) in enumerate(
            zip(media_inputs, processing_results)
        ):
            contribution = {
                "media_type": media_input.media_type.value,
                "source_uri": media_input.source_uri,
                "processing_time": result.processing_time,
                "confidence": result.confidence,
                "provider": result.attribution_data.get("provider", "unknown"),
                "model": result.attribution_data.get("model", "unknown"),
                "tokens_used": result.attribution_data.get("tokens_used", 0),
            }
            attribution_data["media_contributions"].append(contribution)

            # Aggregate provider usage
            provider = result.attribution_data.get("provider", "unknown")
            if provider not in attribution_data["ai_provider_usage"]:
                attribution_data["ai_provider_usage"][provider] = {
                    "total_calls": 0,
                    "total_tokens": 0,
                    "media_types": set(),
                }

            attribution_data["ai_provider_usage"][provider][
                "total_calls"
            ] += result.attribution_data.get("api_calls", 1)
            attribution_data["ai_provider_usage"][provider][
                "total_tokens"
            ] += result.attribution_data.get("tokens_used", 0)
            attribution_data["ai_provider_usage"][provider]["media_types"].add(
                media_input.media_type.value
            )

        # Convert sets to lists for JSON serialization
        for provider_data in attribution_data["ai_provider_usage"].values():
            provider_data["media_types"] = list(provider_data["media_types"])

        # Calculate processing costs
        total_cost = 0.0
        for provider, usage in attribution_data["ai_provider_usage"].items():
            # Simplified cost calculation - in reality, you'd use actual provider pricing
            cost = usage["total_tokens"] * 0.0001  # Mock pricing
            attribution_data["processing_costs"][provider] = cost
            total_cost += cost

        attribution_data["total_cost"] = total_cost

        # Calculate attribution weights
        total_processing_time = sum(
            result.processing_time for result in processing_results
        )
        for i, result in enumerate(processing_results):
            weight = (
                result.processing_time / total_processing_time
                if total_processing_time > 0
                else 1.0 / len(processing_results)
            )
            attribution_data["attribution_weights"][f"input_{i}"] = weight

        return attribution_data

    async def _create_multimodal_capsule(
        self,
        media_inputs: List[MediaInput],
        processing_results: List[ProcessingResult],
        unified_result: Dict[str, Any],
        attribution_data: Dict[str, Any],
    ):
        """Create a capsule for the multi-modal interaction"""

        capsule_data = {
            "type": "multimodal_interaction",
            "media_inputs": [input.to_dict() for input in media_inputs],
            "processing_results": [result.to_dict() for result in processing_results],
            "unified_result": unified_result,
            "attribution_data": attribution_data,
            "timestamp": datetime.now().isoformat(),
            "processing_metadata": {
                "total_media_inputs": len(media_inputs),
                "media_types_processed": list(
                    {input.media_type.value for input in media_inputs}
                ),
                "total_processing_time": sum(
                    result.processing_time for result in processing_results
                ),
                "average_confidence": sum(
                    result.confidence for result in processing_results
                )
                / len(processing_results),
            },
        }

        # Create specialized capsule
        capsule = create_specialized_capsule(
            capsule_type="multimodal_interaction",
            data=capsule_data,
            metadata={"source": "multimodal_ai_processor"},
        )

        # Store in capsule engine
        await self.capsule_engine.store_capsule(capsule)

        return capsule

    async def get_processing_statistics(self) -> Dict[str, Any]:
        """Get processing statistics"""
        stats = self.processing_stats.copy()

        if stats["total_requests"] > 0:
            stats["success_rate"] = (
                stats["successful_requests"] / stats["total_requests"]
            )
            stats["average_processing_time"] = (
                stats["processing_time_total"] / stats["total_requests"]
            )
        else:
            stats["success_rate"] = 0.0
            stats["average_processing_time"] = 0.0

        return stats

    async def get_supported_capabilities(self) -> Dict[str, Any]:
        """Get supported multi-modal capabilities"""

        capabilities = {
            "media_types": [media_type.value for media_type in MediaType],
            "processing_modes": [mode.value for mode in ProcessingMode],
            "providers": self.providers,
            "features": {
                "text_analysis": True,
                "image_analysis": True,
                "audio_transcription": True,
                "video_processing": True,
                "document_extraction": True,
                "cross_modal_insights": True,
                "unified_attribution": True,
                "economic_attribution": True,
            },
        }

        return capabilities
