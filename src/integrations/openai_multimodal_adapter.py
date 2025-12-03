"""
OpenAI Multi-modal Adapter for UATP Capsule Engine.

This module implements the MultiModalProviderAdapter interface for OpenAI's
multi-modal models, including GPT-4 Vision and DALL-E image generation.
"""

import base64
import logging
import os
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List

import httpx

from src.integrations.multimodal_adapters import (
    ContentType,
    MediaContent,
    MediaFormat,
    MultiModalOutput,
    MultiModalProviderAdapter,
    MultiModalReasoningStep,
)

logger = logging.getLogger(__name__)


class OpenAIMultiModalAdapter(MultiModalProviderAdapter):
    """
    Adapter for OpenAI's multi-modal capabilities.

    Supports:
    - GPT-4 Vision for image analysis
    - DALL-E for image generation
    - Text completion via the standard GPT models

    Environment variables:
    - OPENAI_API_KEY: Required for authentication
    """

    def __init__(self):
        """Initialize the OpenAI multi-modal adapter."""
        self.provider_id = "openai"
        self.api_key = os.environ.get("OPENAI_API_KEY")

        if not self.api_key:
            logger.warning("OPENAI_API_KEY not found in environment variables")

        self.api_base = "https://api.openai.com/v1"
        self.client = httpx.AsyncClient(
            timeout=60.0
        )  # Increased timeout for image processing

        # Pricing data ($ per 1k tokens as of mid-2023, subject to change)
        self.pricing = {
            "gpt-4-vision-preview": {"input": 0.01, "output": 0.03},
            "gpt-4": {"input": 0.03, "output": 0.06},
            "gpt-4-32k": {"input": 0.06, "output": 0.12},
            "gpt-3.5-turbo": {"input": 0.0015, "output": 0.002},
            "dall-e-3": {"image": 0.04},  # Per image at standard quality
            "dall-e-2": {"image": 0.02},  # Per image at standard quality
        }

    async def list_models(self) -> List[str]:
        """List available models from this provider."""
        vision_models = ["gpt-4-vision-preview"]
        image_gen_models = ["dall-e-3", "dall-e-2"]
        text_models = ["gpt-4", "gpt-3.5-turbo", "gpt-4-32k"]

        return vision_models + image_gen_models + text_models

    def get_supported_content_types(self) -> List[ContentType]:
        """Get the content types supported by this provider."""
        return [ContentType.TEXT, ContentType.IMAGE]

    def _calculate_cost(
        self, model: str, input_tokens: int, output_tokens: int, images: int = 0
    ) -> float:
        """Calculate the cost of a request."""
        model_pricing = self.pricing.get(model, {"input": 0.0, "output": 0.0})

        # Calculate token-based cost
        input_cost = (input_tokens / 1000) * model_pricing.get("input", 0.0)
        output_cost = (output_tokens / 1000) * model_pricing.get("output", 0.0)

        # Calculate image cost if applicable
        image_cost = 0.0
        if model in ["dall-e-3", "dall-e-2"]:
            image_cost = images * model_pricing.get("image", 0.0)

        return input_cost + output_cost + image_cost

    async def generate(
        self,
        model: str,
        prompt: str,
        system_prompt: str = None,
        max_tokens: int = 1000,
        temperature: float = 0.7,
    ) -> MultiModalOutput:
        """Generate text response with the specified model."""
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY not set in environment variables")

        # Basic validation
        if model.startswith("dall-e"):
            raise ValueError(
                f"Model {model} is for image generation, not text. Use generate_image instead."
            )

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
        }

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": model,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
        }

        try:
            async with self.client as client:
                response = await client.post(
                    f"{self.api_base}/chat/completions", headers=headers, json=payload
                )
                response.raise_for_status()
                response_json = response.json()

                # Extract response
                response_text = response_json["choices"][0]["message"]["content"]
                usage = response_json["usage"]
                input_tokens = usage["prompt_tokens"]
                output_tokens = usage["completion_tokens"]

                # Calculate cost
                cost = self._calculate_cost(model, input_tokens, output_tokens)

                # Create reasoning step
                step = MultiModalReasoningStep(
                    step_id=1,
                    operation="text_generation",
                    reasoning=f"Generated text response using {model}",
                    confidence=0.9,  # Assumed confidence
                )

                return MultiModalOutput(
                    content=response_text,
                    model=model,
                    provider=self.provider_id,
                    total_tokens=input_tokens + output_tokens,
                    cost=cost,
                    trace_id=response_json.get("id", str(uuid.uuid4())),
                    timestamp=datetime.now(timezone.utc),
                    reasoning_steps=[step],
                    metadata={
                        "usage": usage,
                        "model": model,
                        "finish_reason": response_json["choices"][0].get(
                            "finish_reason"
                        ),
                    },
                )

        except httpx.HTTPError as e:
            logger.error(f"HTTP error during OpenAI generate: {e}")
            raise
        except Exception as e:
            logger.error(f"Error during OpenAI generate: {e}")
            raise

    async def process_image(
        self,
        model: str,
        image: MediaContent,
        prompt: str = None,
        options: Dict[str, Any] = None,
    ) -> MultiModalOutput:
        """Process an image with GPT-4 Vision."""
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY not set in environment variables")

        # Validate model
        if model != "gpt-4-vision-preview":
            raise ValueError(
                f"Model {model} does not support image processing. Use gpt-4-vision-preview."
            )

        options = options or {}
        max_tokens = options.get("max_tokens", 300)

        # Get image base64 data
        if not isinstance(image.data, (str, bytes)):
            raise ValueError("Image data must be string or bytes")

        image_b64 = image.to_base64() if isinstance(image.data, bytes) else image.data

        # Build the API request
        content = []

        # Add prompt text if provided
        if prompt:
            content.append({"type": "text", "text": prompt})

        # Add the image
        content.append(
            {
                "type": "image_url",
                "image_url": {
                    "url": f"data:image/{image.format.value};base64,{image_b64}",
                    "detail": options.get("detail", "auto"),  # 'auto', 'low', or 'high'
                },
            }
        )

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
        }

        payload = {
            "model": model,
            "messages": [{"role": "user", "content": content}],
            "max_tokens": max_tokens,
        }

        try:
            async with self.client as client:
                response = await client.post(
                    f"{self.api_base}/chat/completions", headers=headers, json=payload
                )
                response.raise_for_status()
                response_json = response.json()

                # Extract response
                response_text = response_json["choices"][0]["message"]["content"]
                usage = response_json.get("usage", {})
                input_tokens = usage.get(
                    "prompt_tokens", 1000
                )  # Estimate if not provided
                output_tokens = usage.get(
                    "completion_tokens", len(response_text.split())
                )

                # Calculate cost (image processing costs more)
                cost = self._calculate_cost(model, input_tokens, output_tokens)

                # Create reasoning step
                step = MultiModalReasoningStep(
                    step_id=1,
                    operation="image_analysis",
                    reasoning=f"Analyzed image content using {model}",
                    confidence=0.85,
                )
                step.add_input_media(image)

                return MultiModalOutput(
                    content=response_text,
                    model=model,
                    provider=self.provider_id,
                    total_tokens=input_tokens + output_tokens,
                    cost=cost,
                    trace_id=response_json.get("id", str(uuid.uuid4())),
                    timestamp=datetime.now(timezone.utc),
                    reasoning_steps=[step],
                    input_media=[image],
                    metadata={
                        "usage": usage,
                        "model": model,
                        "detail_level": options.get("detail", "auto"),
                        "finish_reason": response_json["choices"][0].get(
                            "finish_reason"
                        ),
                    },
                )

        except httpx.HTTPError as e:
            logger.error(f"HTTP error during OpenAI image processing: {e}")
            raise
        except Exception as e:
            logger.error(f"Error during OpenAI image processing: {e}")
            raise

    async def generate_image(
        self, model: str, prompt: str, options: Dict[str, Any] = None
    ) -> MultiModalOutput:
        """Generate an image with DALL-E."""
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY not set in environment variables")

        # Validate model
        if not model.startswith("dall-e"):
            raise ValueError(
                f"Model {model} does not support image generation. Use dall-e-3 or dall-e-2."
            )

        options = options or {}
        size = options.get("size", "1024x1024")
        quality = options.get("quality", "standard")

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
        }

        payload = {
            "model": model,
            "prompt": prompt,
            "n": 1,
            "size": size,
            "quality": quality,
            "response_format": "b64_json",
        }

        try:
            async with self.client as client:
                response = await client.post(
                    f"{self.api_base}/images/generations", headers=headers, json=payload
                )
                response.raise_for_status()
                response_json = response.json()

                # Get image data
                image_data = response_json["data"][0]["b64_json"]
                image_bytes = base64.b64decode(image_data)

                # Create output image
                output_image = MediaContent(
                    content_type=ContentType.IMAGE,
                    format=MediaFormat.PNG,  # DALL-E returns PNG
                    data=image_bytes,
                    metadata={
                        "generated": True,
                        "prompt": prompt,
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                        "dimensions": size,
                        "quality": quality,
                        "model": model,
                    },
                )

                # Calculate cost based on the model
                cost = self.pricing.get(model, {}).get("image", 0.0)

                # Create reasoning step
                step = MultiModalReasoningStep(
                    step_id=1,
                    operation="image_generation",
                    reasoning=f"Generated image based on prompt: {prompt}",
                    confidence=0.9,
                )
                step.add_output_media(output_image)

                return MultiModalOutput(
                    content=f"Image generated successfully with {model}",
                    model=model,
                    provider=self.provider_id,
                    total_tokens=len(prompt.split()),  # Approximate token count
                    cost=cost,
                    trace_id=str(uuid.uuid4()),
                    timestamp=datetime.now(timezone.utc),
                    reasoning_steps=[step],
                    media_outputs=[output_image],
                    metadata={
                        "prompt": prompt,
                        "size": size,
                        "quality": quality,
                        "model": model,
                    },
                )

        except httpx.HTTPError as e:
            logger.error(f"HTTP error during OpenAI image generation: {e}")
            raise
        except Exception as e:
            logger.error(f"Error during OpenAI image generation: {e}")
            raise

    async def process_audio(
        self,
        model: str,
        audio: MediaContent,
        prompt: str = None,
        options: Dict[str, Any] = None,
    ) -> MultiModalOutput:
        """Process audio with the AI model."""
        # OpenAI has Whisper for audio, but we'll implement this later
        raise NotImplementedError("Audio processing not yet implemented for OpenAI")

    async def process_video(
        self,
        model: str,
        video: MediaContent,
        prompt: str = None,
        options: Dict[str, Any] = None,
    ) -> MultiModalOutput:
        """Process video with the AI model."""
        # OpenAI doesn't have dedicated video processing yet
        raise NotImplementedError("Video processing not yet implemented for OpenAI")

    async def multi_modal_generate(
        self,
        model: str,
        inputs: List[MediaContent],
        prompt: str = None,
        system_prompt: str = None,
        options: Dict[str, Any] = None,
    ) -> MultiModalOutput:
        """Generate content based on multiple modal inputs."""
        # For OpenAI, we need to handle each input type separately based on capabilities

        # If there are images in the inputs, use GPT-4 Vision
        images = [media for media in inputs if media.content_type == ContentType.IMAGE]

        if images:
            if model != "gpt-4-vision-preview":
                model = "gpt-4-vision-preview"
                logger.info(f"Switching to {model} to handle image inputs")

            # Currently only supports one image at a time, so take the first one
            return await self.process_image(
                model=model, image=images[0], prompt=prompt, options=options
            )

        # If no images, fall back to text generation
        return await self.generate(
            model=model,
            prompt=prompt,
            system_prompt=system_prompt,
            max_tokens=options.get("max_tokens", 1000) if options else 1000,
            temperature=options.get("temperature", 0.7) if options else 0.7,
        )


async def demo_openai_multimodal():
    """Demonstrate the OpenAI multi-modal adapter."""
    import os

    from src.integrations.multimodal_adapters import MediaContent

    # Check if API key is available
    if not os.environ.get("OPENAI_API_KEY"):
        print("OPENAI_API_KEY not set in environment. Aborting demo.")
        return

    adapter = OpenAIMultiModalAdapter()

    # List available models
    models = await adapter.list_models()
    print(f"Available OpenAI models: {models}")

    # Create a simple test image (1x1 pixel, red)
    test_image_data = b"iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg=="
    test_image = MediaContent(
        content_type=ContentType.IMAGE,
        format=MediaFormat.PNG,
        data=test_image_data,
        metadata={"test": "image"},
    )

    # Test image analysis (if vision model is available)
    try:
        vision_result = await adapter.process_image(
            model="gpt-4-vision-preview",
            image=test_image,
            prompt="What can you see in this image?",
        )
        print(f"Vision result: {vision_result.content}")
        print(f"Vision trace ID: {vision_result.trace_id}")
        print(f"Vision cost: ${vision_result.cost:.4f}")
    except Exception as e:
        print(f"Error in vision test: {e}")

    # Test image generation with DALL-E
    try:
        dalle_result = await adapter.generate_image(
            model="dall-e-3", prompt="A beautiful sunset over mountains"
        )
        print(f"DALL-E result: {dalle_result.content}")
        print(f"Image data size: {len(dalle_result.media_outputs[0].data)} bytes")
        print(f"DALL-E cost: ${dalle_result.cost:.2f}")
    except Exception as e:
        print(f"Error in DALL-E test: {e}")

    # Test text generation
    text_result = await adapter.generate(
        model="gpt-3.5-turbo",
        prompt="Explain what multi-modal AI means in one sentence.",
    )
    print(f"Text result: {text_result.content}")
    print(f"Text cost: ${text_result.cost:.4f}")


if __name__ == "__main__":
    import asyncio

    # Run the demo
    asyncio.run(demo_openai_multimodal())
