"""
Platform Integration API Routes
Handles AI platform API key detection and validation
"""

import logging
import os
from typing import Dict, Any

from quart import Blueprint, request, jsonify
from quart_cors import cors

logger = logging.getLogger(__name__)


def create_platform_blueprint() -> Blueprint:
    """Create platform integration API blueprint"""

    bp = Blueprint("platform_api", __name__, url_prefix="/api/platform")
    cors(
        bp,
        allow_origin=[
            "http://localhost:3000",
            "http://localhost:3001",
            "http://127.0.0.1:3000",
        ],
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        allow_headers=["Content-Type", "Authorization", "X-API-Key"],
        allow_credentials=True,
    )

    @bp.route("/<platform>/detect-key", methods=["GET", "OPTIONS"])
    async def detect_api_key(platform: str):
        """Detect API key from environment variables"""
        if request.method == "OPTIONS":
            return "", 200

        try:
            # Define environment variable names for each platform
            env_var_names = {
                "openai": ["OPENAI_API_KEY"],
                "anthropic": ["ANTHROPIC_API_KEY"],
                "cohere": ["COHERE_API_KEY"],
                "huggingface": ["HUGGINGFACE_API_TOKEN", "HF_TOKEN"],
                "google": ["GOOGLE_API_KEY"],
                "azure": ["AZURE_OPENAI_KEY", "AZURE_OPENAI_API_KEY"],
            }

            platform_vars = env_var_names.get(platform, [f"{platform.upper()}_API_KEY"])

            # Check each possible environment variable
            for env_var in platform_vars:
                api_key = os.getenv(env_var)
                if api_key:
                    # Validate the key format (basic check)
                    is_valid_format = validate_api_key_format(platform, api_key)

                    return jsonify(
                        {
                            "success": True,
                            "detected": True,
                            "source": f"environment_variable_{env_var}",
                            "keyPreview": f"{api_key[:8]}..."
                            if len(api_key) > 8
                            else "***",
                            "valid": is_valid_format,
                            "can_test": True,
                        }
                    )

            # No key found
            return jsonify(
                {
                    "success": True,
                    "detected": False,
                    "message": f"No API key found for {platform}",
                }
            )

        except Exception as e:
            logger.error(f"Failed to detect API key for {platform}: {e}")
            return jsonify({"success": False, "error": str(e)}), 500

    @bp.route("/<platform>/validate-key", methods=["POST", "OPTIONS"])
    async def validate_api_key(platform: str):
        """Validate API key by making a test call"""
        if request.method == "OPTIONS":
            return "", 200

        try:
            data = await request.get_json()
            api_key = data.get("api_key", "").strip()

            if not api_key:
                return (
                    jsonify(
                        {
                            "success": False,
                            "valid": False,
                            "error": "API key is required",
                        }
                    ),
                    400,
                )

            # Basic format validation
            if not validate_api_key_format(platform, api_key):
                return jsonify(
                    {
                        "success": True,
                        "valid": False,
                        "error": f"Invalid {platform} API key format",
                    }
                )

            # Test the API key with a minimal request
            validation_result = await test_api_key(platform, api_key)

            return jsonify(
                {
                    "success": True,
                    "valid": validation_result["valid"],
                    "error": validation_result.get("error"),
                    "details": validation_result.get("details"),
                }
            )

        except Exception as e:
            logger.error(f"Failed to validate API key for {platform}: {e}")
            return jsonify({"success": False, "error": str(e)}), 500

    def validate_api_key_format(platform: str, api_key: str) -> bool:
        """Validate API key format for different platforms"""

        if not api_key or len(api_key) < 10:
            return False

        format_rules = {
            "openai": lambda key: key.startswith("sk-") and len(key) > 20,
            "anthropic": lambda key: key.startswith("sk-ant-") and len(key) > 20,
            "cohere": lambda key: len(key) > 30 and "-" in key,
            "huggingface": lambda key: key.startswith("hf_") or len(key) > 30,
            "google": lambda key: "AI" in key or len(key) > 30,
            "azure": lambda key: len(key) > 20,
        }

        validator = format_rules.get(platform)
        if validator:
            return validator(api_key)

        # Generic validation - just check it's not too short
        return len(api_key) > 15

    async def test_api_key(platform: str, api_key: str) -> Dict[str, Any]:
        """Test API key by making a minimal request to the platform"""

        try:
            if platform == "openai":
                return await test_openai_key(api_key)
            elif platform == "anthropic":
                return await test_anthropic_key(api_key)
            elif platform == "cohere":
                return await test_cohere_key(api_key)
            elif platform == "huggingface":
                return await test_huggingface_key(api_key)
            else:
                # Generic test - just validate format
                return {
                    "valid": validate_api_key_format(platform, api_key),
                    "details": "Format validation only",
                }

        except Exception as e:
            logger.error(f"API key test failed for {platform}: {e}")
            return {"valid": False, "error": f"Test request failed: {str(e)}"}

    async def test_openai_key(api_key: str) -> Dict[str, Any]:
        """Test OpenAI API key"""
        try:
            import openai
            from openai import AsyncOpenAI

            client = AsyncOpenAI(api_key=api_key)

            # Make a minimal request
            response = await client.models.list()

            return {"valid": True, "details": f"Found {len(response.data)} models"}

        except ImportError:
            return {
                "valid": validate_api_key_format("openai", api_key),
                "details": "OpenAI library not available, format validation only",
            }
        except Exception as e:
            error_msg = str(e).lower()
            if "invalid api key" in error_msg or "unauthorized" in error_msg:
                return {"valid": False, "error": "Invalid API key"}
            elif "quota" in error_msg or "billing" in error_msg:
                return {
                    "valid": True,
                    "details": "API key is valid but has billing/quota issues",
                }
            else:
                return {"valid": False, "error": f"API test failed: {str(e)}"}

    async def test_anthropic_key(api_key: str) -> Dict[str, Any]:
        """Test Anthropic API key"""
        try:
            import anthropic

            client = anthropic.AsyncAnthropic(api_key=api_key)

            # Make a minimal request
            response = await client.messages.create(
                model="claude-3-haiku-20240307",
                max_tokens=1,
                messages=[{"role": "user", "content": "Hi"}],
            )

            return {"valid": True, "details": "API key validated successfully"}

        except ImportError:
            return {
                "valid": validate_api_key_format("anthropic", api_key),
                "details": "Anthropic library not available, format validation only",
            }
        except Exception as e:
            error_msg = str(e).lower()
            if "invalid api key" in error_msg or "unauthorized" in error_msg:
                return {"valid": False, "error": "Invalid API key"}
            elif "quota" in error_msg or "billing" in error_msg:
                return {
                    "valid": True,
                    "details": "API key is valid but has billing/quota issues",
                }
            else:
                return {"valid": False, "error": f"API test failed: {str(e)}"}

    async def test_cohere_key(api_key: str) -> Dict[str, Any]:
        """Test Cohere API key"""
        try:
            import cohere

            client = cohere.AsyncClient(api_key)

            # Make a minimal request
            response = await client.tokenize(text="test")

            return {"valid": True, "details": "API key validated successfully"}

        except ImportError:
            return {
                "valid": validate_api_key_format("cohere", api_key),
                "details": "Cohere library not available, format validation only",
            }
        except Exception as e:
            error_msg = str(e).lower()
            if "invalid api key" in error_msg or "unauthorized" in error_msg:
                return {"valid": False, "error": "Invalid API key"}
            else:
                return {"valid": False, "error": f"API test failed: {str(e)}"}

    async def test_huggingface_key(api_key: str) -> Dict[str, Any]:
        """Test Hugging Face API key"""
        try:
            import httpx

            async with httpx.AsyncClient() as client:
                response = await client.get(
                    "https://huggingface.co/api/whoami-v2",
                    headers={"Authorization": f"Bearer {api_key}"},
                )

                if response.status_code == 200:
                    return {"valid": True, "details": "API key validated successfully"}
                elif response.status_code == 401:
                    return {"valid": False, "error": "Invalid API key"}
                else:
                    return {
                        "valid": False,
                        "error": f"Validation failed with status {response.status_code}",
                    }

        except ImportError:
            return {
                "valid": validate_api_key_format("huggingface", api_key),
                "details": "HTTP client not available, format validation only",
            }
        except Exception as e:
            return {"valid": False, "error": f"API test failed: {str(e)}"}

    return bp
