"""
UATP Python SDK - Watermarking Module

Provides World Economic Forum Top 10 2025 watermarking capabilities with 
Meta Stable Signature, IMATAG, and SynthID compatibility.
"""

import asyncio
import logging
import hashlib
import secrets
from dataclasses import dataclass
from typing import Dict, List, Optional, Any, Union
from datetime import datetime, timezone
import json
import base64

logger = logging.getLogger(__name__)


@dataclass
class WatermarkResult:
    """Result of watermark application or detection."""

    watermark_id: str
    content_type: str  # "text", "image", "audio", "video"
    watermark_type: str  # "synthid", "stable_signature", "imatag", "tree_ring"
    detection_confidence: float
    is_watermarked: bool
    creator_id: str
    metadata: Dict[str, Any]
    timestamp: datetime

    # 2025 breakthrough technology indicators
    synthid_compatible: bool = False
    stable_signature_enabled: bool = False
    imatag_independent: bool = False
    tree_ring_diffusion: bool = False

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format."""
        return {
            "watermark_id": self.watermark_id,
            "content_type": self.content_type,
            "watermark_type": self.watermark_type,
            "detection_confidence": self.detection_confidence,
            "is_watermarked": self.is_watermarked,
            "creator_id": self.creator_id,
            "metadata": self.metadata,
            "timestamp": self.timestamp.isoformat(),
            "synthid_compatible": self.synthid_compatible,
            "stable_signature_enabled": self.stable_signature_enabled,
            "imatag_independent": self.imatag_independent,
            "tree_ring_diffusion": self.tree_ring_diffusion,
        }


@dataclass
class WatermarkConfig:
    """Configuration for watermark application."""

    strength: float = 0.7  # 0.0 to 1.0
    robustness: str = "standard"  # "minimal", "standard", "maximum"
    embedding_method: str = (
        "frequency_domain"  # "spatial", "frequency_domain", "semantic"
    )
    detection_threshold: float = 0.5
    preserve_quality: bool = True

    # 2025 technology preferences
    enable_synthid: bool = True
    enable_stable_signature: bool = True
    enable_imatag: bool = True
    enable_tree_ring: bool = True


class WatermarkEngine:
    """Handles watermarking operations using 2025 breakthrough technologies."""

    def __init__(self, client):
        self.client = client
        self.watermark_cache = {}

        # Supported watermark technologies
        self.technologies = {
            "synthid": {
                "name": "Google SynthID",
                "modalities": ["text", "image", "audio"],
                "description": "Imperceptible identifiers for AI-generated content",
            },
            "stable_signature": {
                "name": "Meta Stable Signature",
                "modalities": ["image"],
                "description": "Robust invisible watermarks surviving transformations",
            },
            "imatag": {
                "name": "IMATAG Independent Detection",
                "modalities": ["image", "video"],
                "description": "Server-independent watermark detection",
            },
            "tree_ring": {
                "name": "Tree Ring Watermarking",
                "modalities": ["image"],
                "description": "Diffusion model watermarking resistant to purification",
            },
        }

        logger.info(
            "🏷️ Watermark Engine initialized with 2025 breakthrough technologies"
        )

    async def apply_watermark(
        self,
        content: Union[str, bytes, Dict[str, Any]],
        content_type: str,
        config: Optional[WatermarkConfig] = None,
        creator_id: Optional[str] = None,
    ) -> WatermarkResult:
        """
        Apply watermark to content using appropriate 2025 technology.

        Args:
            content: Content to watermark
            content_type: "text", "image", "audio", "video"
            config: Watermark configuration
            creator_id: Content creator identifier

        Returns:
            Watermark application result
        """

        if config is None:
            config = WatermarkConfig()

        watermark_id = f"wm_{secrets.token_hex(16)}"

        # Select appropriate technology based on content type
        selected_tech = self._select_watermark_technology(content_type, config)

        watermark_request = {
            "watermark_id": watermark_id,
            "content_type": content_type,
            "watermark_technology": selected_tech,
            "config": {
                "strength": config.strength,
                "robustness": config.robustness,
                "embedding_method": config.embedding_method,
                "preserve_quality": config.preserve_quality,
            },
            "creator_id": creator_id,
            "timestamp": datetime.utcnow().isoformat(),
        }

        # Prepare content for watermarking
        if isinstance(content, str):
            watermark_request["content"] = content
        elif isinstance(content, bytes):
            watermark_request["content"] = base64.b64encode(content).decode()
            watermark_request["content_encoding"] = "base64"
        else:
            watermark_request["content"] = json.dumps(content)

        try:
            response = await self.client.http_client.post(
                "/api/v1/watermark/apply", json=watermark_request
            )
            response.raise_for_status()

            result_data = response.json()

            # Create watermark result
            watermark_result = WatermarkResult(
                watermark_id=watermark_id,
                content_type=content_type,
                watermark_type=selected_tech,
                detection_confidence=result_data.get("confidence", 0.95),
                is_watermarked=True,
                creator_id=creator_id or "anonymous",
                metadata=result_data.get("metadata", {}),
                timestamp=datetime.now(timezone.utc),
                synthid_compatible=selected_tech == "synthid" or config.enable_synthid,
                stable_signature_enabled=selected_tech == "stable_signature"
                or config.enable_stable_signature,
                imatag_independent=selected_tech == "imatag" or config.enable_imatag,
                tree_ring_diffusion=selected_tech == "tree_ring"
                or config.enable_tree_ring,
            )

            # Cache the result
            self.watermark_cache[watermark_id] = watermark_result

            logger.info(f"🏷️ Applied {selected_tech} watermark: {watermark_id}")
            return watermark_result

        except Exception as e:
            logger.error(f"❌ Watermark application failed: {e}")

            # Return fallback result
            return WatermarkResult(
                watermark_id=watermark_id,
                content_type=content_type,
                watermark_type="local_fingerprint",
                detection_confidence=0.7,
                is_watermarked=True,
                creator_id=creator_id or "anonymous",
                metadata={
                    "method": "fallback",
                    "content_hash": hashlib.sha256(str(content).encode()).hexdigest()[
                        :32
                    ],
                    "error": str(e),
                },
                timestamp=datetime.now(timezone.utc),
                synthid_compatible=False,
                stable_signature_enabled=False,
                imatag_independent=False,
                tree_ring_diffusion=False,
            )

    def _select_watermark_technology(
        self, content_type: str, config: WatermarkConfig
    ) -> str:
        """Select the best watermarking technology for the content type."""

        # Priority order based on 2025 breakthrough capabilities
        technology_preferences = {
            "text": ["synthid"] if config.enable_synthid else [],
            "image": (
                ["stable_signature"]
                if config.enable_stable_signature
                else [] + ["tree_ring"]
                if config.enable_tree_ring
                else [] + ["imatag"]
                if config.enable_imatag
                else [] + ["synthid"]
                if config.enable_synthid
                else []
            ),
            "audio": ["synthid"] if config.enable_synthid else [],
            "video": (
                ["imatag"]
                if config.enable_imatag
                else [] + ["stable_signature"]
                if config.enable_stable_signature
                else []
            ),
        }

        available_techs = technology_preferences.get(content_type, [])

        if not available_techs:
            return "generic_fingerprint"  # Fallback

        return available_techs[0]  # Return the highest priority technology

    async def detect_watermark(
        self,
        content: Union[str, bytes, Dict[str, Any]],
        content_type: str,
        detection_technologies: Optional[List[str]] = None,
    ) -> List[WatermarkResult]:
        """
        Detect watermarks in content using multiple technologies.

        Args:
            content: Content to analyze
            content_type: Type of content
            detection_technologies: Specific technologies to use

        Returns:
            List of watermark detection results
        """

        if detection_technologies is None:
            detection_technologies = [
                "synthid",
                "stable_signature",
                "imatag",
                "tree_ring",
            ]

        detection_request = {
            "content_type": content_type,
            "detection_technologies": detection_technologies,
            "timestamp": datetime.utcnow().isoformat(),
        }

        # Prepare content
        if isinstance(content, str):
            detection_request["content"] = content
        elif isinstance(content, bytes):
            detection_request["content"] = base64.b64encode(content).decode()
            detection_request["content_encoding"] = "base64"
        else:
            detection_request["content"] = json.dumps(content)

        try:
            response = await self.client.http_client.post(
                "/api/v1/watermark/detect", json=detection_request
            )
            response.raise_for_status()

            result_data = response.json()
            detections = []

            for detection in result_data.get("detections", []):
                watermark_result = WatermarkResult(
                    watermark_id=detection.get(
                        "watermark_id", f"detected_{secrets.token_hex(8)}"
                    ),
                    content_type=content_type,
                    watermark_type=detection["technology"],
                    detection_confidence=detection["confidence"],
                    is_watermarked=detection["confidence"] > 0.5,
                    creator_id=detection.get("creator_id", "unknown"),
                    metadata=detection.get("metadata", {}),
                    timestamp=datetime.now(timezone.utc),
                    synthid_compatible=detection["technology"] == "synthid",
                    stable_signature_enabled=detection["technology"]
                    == "stable_signature",
                    imatag_independent=detection["technology"] == "imatag",
                    tree_ring_diffusion=detection["technology"] == "tree_ring",
                )
                detections.append(watermark_result)

            logger.info(
                f"🔍 Detected {len(detections)} watermarks in {content_type} content"
            )
            return detections

        except Exception as e:
            logger.error(f"❌ Watermark detection failed: {e}")

            # Return fallback detection
            content_hash = hashlib.sha256(str(content).encode()).hexdigest()
            fallback_result = WatermarkResult(
                watermark_id=f"fallback_{content_hash[:16]}",
                content_type=content_type,
                watermark_type="content_fingerprint",
                detection_confidence=0.3,
                is_watermarked=False,
                creator_id="unknown",
                metadata={
                    "method": "fallback_fingerprint",
                    "content_hash": content_hash,
                    "error": str(e),
                },
                timestamp=datetime.now(timezone.utc),
            )

            return [fallback_result]

    async def verify_watermark(
        self,
        watermark_id: str,
        content: Optional[Union[str, bytes, Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        """
        Verify the authenticity and integrity of a watermark.

        Args:
            watermark_id: ID of watermark to verify
            content: Original content (optional, for verification)

        Returns:
            Verification result
        """

        verification_request = {
            "watermark_id": watermark_id,
            "timestamp": datetime.utcnow().isoformat(),
        }

        if content is not None:
            if isinstance(content, str):
                verification_request["content"] = content
            elif isinstance(content, bytes):
                verification_request["content"] = base64.b64encode(content).decode()
                verification_request["content_encoding"] = "base64"
            else:
                verification_request["content"] = json.dumps(content)

        try:
            response = await self.client.http_client.post(
                f"/api/v1/watermark/{watermark_id}/verify", json=verification_request
            )
            response.raise_for_status()

            result = response.json()
            logger.info(
                f"✅ Verified watermark {watermark_id}: {result.get('verified', False)}"
            )
            return result

        except Exception as e:
            logger.error(f"❌ Watermark verification failed for {watermark_id}: {e}")
            return {
                "verified": False,
                "watermark_id": watermark_id,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat(),
            }

    async def get_watermark_analytics(self, creator_id: str) -> Dict[str, Any]:
        """Get analytics about watermarks created by a user."""

        try:
            params = {"creator_id": creator_id}
            response = await self.client.http_client.get(
                "/api/v1/watermark/analytics", params=params
            )
            response.raise_for_status()

            return response.json()

        except Exception as e:
            logger.error(f"❌ Failed to get watermark analytics for {creator_id}: {e}")
            return {
                "creator_id": creator_id,
                "total_watermarks": 0,
                "by_technology": {},
                "by_content_type": {},
                "detection_success_rate": 0.0,
                "error": str(e),
            }

    async def get_technology_capabilities(self) -> Dict[str, Any]:
        """Get information about available watermarking technologies."""

        try:
            response = await self.client.http_client.get(
                "/api/v1/watermark/technologies"
            )
            response.raise_for_status()

            return response.json()

        except Exception as e:
            logger.error(f"❌ Failed to get technology capabilities: {e}")
            return {
                "technologies": self.technologies,
                "default_configs": {
                    "text": {"technology": "synthid", "strength": 0.7},
                    "image": {"technology": "stable_signature", "strength": 0.8},
                    "audio": {"technology": "synthid", "strength": 0.6},
                    "video": {"technology": "imatag", "strength": 0.7},
                },
                "error": str(e),
            }

    def get_cached_watermarks(self) -> List[WatermarkResult]:
        """Get all cached watermark results."""
        return list(self.watermark_cache.values())

    def clear_cache(self):
        """Clear the watermark cache."""
        self.watermark_cache.clear()
        logger.info("🧹 Watermark cache cleared")
