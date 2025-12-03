"""
Custom Model Integration System
Supports integration with proprietary and custom AI models
"""

import asyncio
import json
import logging
from abc import ABC, abstractmethod
from dataclasses import asdict, dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

import aiohttp
import yaml

from ..attribution.cross_conversation_tracker import CrossConversationTracker
from ..capsules.specialized_capsules import create_specialized_capsule
from ..economic.fcde_engine import FCDEEngine
from ..engine.capsule_engine import CapsuleEngine

logger = logging.getLogger(__name__)


class ModelType(Enum):
    """Types of custom models supported"""

    PROPRIETARY_LLM = "proprietary_llm"
    CUSTOM_FINE_TUNED = "custom_fine_tuned"
    DOMAIN_SPECIFIC = "domain_specific"
    MULTIMODAL_CUSTOM = "multimodal_custom"
    SPECIALIZED_REASONING = "specialized_reasoning"
    CUSTOM_EMBEDDING = "custom_embedding"
    PRIVATE_DEPLOYMENT = "private_deployment"


class IntegrationProtocol(Enum):
    """Integration protocols for custom models"""

    REST_API = "rest_api"
    GRPC = "grpc"
    WEBSOCKET = "websocket"
    STREAMING = "streaming"
    BATCH = "batch"
    WEBHOOK = "webhook"


class AuthenticationMethod(Enum):
    """Authentication methods for custom models"""

    API_KEY = "api_key"
    OAUTH2 = "oauth2"
    JWT = "jwt"
    CERTIFICATE = "certificate"
    CUSTOM_HEADER = "custom_header"
    NONE = "none"


@dataclass
class CustomModelConfig:
    """Configuration for a custom model integration"""

    model_id: str
    model_name: str
    model_type: ModelType
    provider: str
    version: str
    endpoint_url: str
    protocol: IntegrationProtocol
    authentication: AuthenticationMethod
    capabilities: List[str]
    parameters: Dict[str, Any]
    rate_limits: Dict[str, Any]
    cost_structure: Dict[str, Any]
    metadata: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class ModelResponse:
    """Response from a custom model"""

    model_id: str
    response_data: Any
    metadata: Dict[str, Any]
    processing_time: float
    tokens_used: int
    confidence: float
    attribution_data: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class CustomModelAdapter(ABC):
    """Abstract base class for custom model adapters"""

    @abstractmethod
    async def initialize(self, config: CustomModelConfig) -> bool:
        """Initialize the custom model adapter"""
        pass

    @abstractmethod
    async def process_request(self, request: Dict[str, Any]) -> ModelResponse:
        """Process a request using the custom model"""
        pass

    @abstractmethod
    async def health_check(self) -> Dict[str, Any]:
        """Check the health of the custom model"""
        pass

    @abstractmethod
    def get_supported_capabilities(self) -> List[str]:
        """Get the capabilities supported by this model"""
        pass

    @abstractmethod
    async def cleanup(self) -> bool:
        """Cleanup resources"""
        pass


class RESTAPIAdapter(CustomModelAdapter):
    """Adapter for REST API based custom models"""

    def __init__(self):
        self.config = None
        self.session = None
        self.auth_headers = {}

    async def initialize(self, config: CustomModelConfig) -> bool:
        """Initialize REST API adapter"""
        self.config = config
        self.session = aiohttp.ClientSession()

        # Set up authentication
        if config.authentication == AuthenticationMethod.API_KEY:
            api_key = config.parameters.get("api_key")
            key_header = config.parameters.get("api_key_header", "Authorization")
            self.auth_headers[key_header] = f"Bearer {api_key}"
        elif config.authentication == AuthenticationMethod.CUSTOM_HEADER:
            custom_headers = config.parameters.get("custom_headers", {})
            self.auth_headers.update(custom_headers)

        return True

    async def process_request(self, request: Dict[str, Any]) -> ModelResponse:
        """Process request via REST API"""
        start_time = datetime.now()

        try:
            # Prepare request
            url = self.config.endpoint_url
            headers = {"Content-Type": "application/json", **self.auth_headers}

            # Add custom headers from request
            if "headers" in request:
                headers.update(request["headers"])

            # Prepare payload
            payload = {
                "model": self.config.model_id,
                "input": request.get("input", ""),
                "parameters": {
                    **self.config.parameters,
                    **request.get("parameters", {}),
                },
            }

            # Make request
            async with self.session.post(
                url, json=payload, headers=headers
            ) as response:
                if response.status == 200:
                    response_data = await response.json()

                    processing_time = (datetime.now() - start_time).total_seconds()

                    return ModelResponse(
                        model_id=self.config.model_id,
                        response_data=response_data,
                        metadata={
                            "status_code": response.status,
                            "response_headers": dict(response.headers),
                            "request_id": response.headers.get(
                                "X-Request-ID", "unknown"
                            ),
                        },
                        processing_time=processing_time,
                        tokens_used=response_data.get("usage", {}).get(
                            "total_tokens", 0
                        ),
                        confidence=response_data.get("confidence", 0.95),
                        attribution_data={
                            "provider": self.config.provider,
                            "model": self.config.model_name,
                            "version": self.config.version,
                            "endpoint": self.config.endpoint_url,
                        },
                    )
                else:
                    error_text = await response.text()
                    raise Exception(
                        f"API request failed: {response.status} - {error_text}"
                    )

        except Exception as e:
            logger.error(f"REST API request failed: {str(e)}")
            raise

    async def health_check(self) -> Dict[str, Any]:
        """Check REST API health"""
        try:
            health_url = self.config.parameters.get(
                "health_endpoint", f"{self.config.endpoint_url}/health"
            )

            async with self.session.get(
                health_url, headers=self.auth_headers
            ) as response:
                if response.status == 200:
                    health_data = await response.json()
                    return {
                        "status": "healthy",
                        "response_time": 0.1,  # Mock response time
                        "details": health_data,
                    }
                else:
                    return {
                        "status": "unhealthy",
                        "error": f"Health check failed: {response.status}",
                    }
        except Exception as e:
            return {"status": "error", "error": str(e)}

    def get_supported_capabilities(self) -> List[str]:
        """Get supported capabilities"""
        return self.config.capabilities

    async def cleanup(self) -> bool:
        """Cleanup resources"""
        if self.session:
            await self.session.close()
        return True


class GRPCAdapter(CustomModelAdapter):
    """Adapter for gRPC based custom models"""

    def __init__(self):
        self.config = None
        self.channel = None
        self.stub = None

    async def initialize(self, config: CustomModelConfig) -> bool:
        """Initialize gRPC adapter"""
        self.config = config
        # gRPC initialization would go here
        # For now, this is a mock implementation
        logger.info(f"Initialized gRPC adapter for {config.model_id}")
        return True

    async def process_request(self, request: Dict[str, Any]) -> ModelResponse:
        """Process request via gRPC"""
        start_time = datetime.now()

        # Mock gRPC call
        await asyncio.sleep(0.1)  # Simulate processing time

        processing_time = (datetime.now() - start_time).total_seconds()

        return ModelResponse(
            model_id=self.config.model_id,
            response_data={"output": "Mock gRPC response"},
            metadata={"protocol": "grpc"},
            processing_time=processing_time,
            tokens_used=100,
            confidence=0.90,
            attribution_data={
                "provider": self.config.provider,
                "model": self.config.model_name,
                "version": self.config.version,
            },
        )

    async def health_check(self) -> Dict[str, Any]:
        """Check gRPC health"""
        return {"status": "healthy", "protocol": "grpc", "response_time": 0.05}

    def get_supported_capabilities(self) -> List[str]:
        """Get supported capabilities"""
        return self.config.capabilities

    async def cleanup(self) -> bool:
        """Cleanup resources"""
        if self.channel:
            # Close gRPC channel
            pass
        return True


class WebSocketAdapter(CustomModelAdapter):
    """Adapter for WebSocket based custom models"""

    def __init__(self):
        self.config = None
        self.websocket = None

    async def initialize(self, config: CustomModelConfig) -> bool:
        """Initialize WebSocket adapter"""
        self.config = config
        # WebSocket initialization would go here
        logger.info(f"Initialized WebSocket adapter for {config.model_id}")
        return True

    async def process_request(self, request: Dict[str, Any]) -> ModelResponse:
        """Process request via WebSocket"""
        start_time = datetime.now()

        # Mock WebSocket communication
        await asyncio.sleep(0.05)  # Simulate processing time

        processing_time = (datetime.now() - start_time).total_seconds()

        return ModelResponse(
            model_id=self.config.model_id,
            response_data={"output": "Mock WebSocket response"},
            metadata={"protocol": "websocket"},
            processing_time=processing_time,
            tokens_used=75,
            confidence=0.92,
            attribution_data={
                "provider": self.config.provider,
                "model": self.config.model_name,
                "version": self.config.version,
            },
        )

    async def health_check(self) -> Dict[str, Any]:
        """Check WebSocket health"""
        return {
            "status": "healthy",
            "protocol": "websocket",
            "connection_status": "connected",
        }

    def get_supported_capabilities(self) -> List[str]:
        """Get supported capabilities"""
        return self.config.capabilities

    async def cleanup(self) -> bool:
        """Cleanup resources"""
        if self.websocket:
            await self.websocket.close()
        return True


class CustomModelIntegrationSystem:
    """
    System for integrating custom and proprietary AI models
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

        # Registry of custom models
        self.model_registry = {}
        self.model_adapters = {}

        # Adapter factory
        self.adapter_factory = {
            IntegrationProtocol.REST_API: RESTAPIAdapter,
            IntegrationProtocol.GRPC: GRPCAdapter,
            IntegrationProtocol.WEBSOCKET: WebSocketAdapter,
        }

        # Statistics
        self.integration_stats = {
            "total_models": 0,
            "active_models": 0,
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "total_processing_time": 0.0,
            "by_model_type": {mt.value: 0 for mt in ModelType},
            "by_protocol": {ip.value: 0 for ip in IntegrationProtocol},
        }

    async def register_custom_model(self, config: CustomModelConfig) -> bool:
        """Register a new custom model"""
        try:
            # Validate configuration
            if not await self._validate_model_config(config):
                raise ValueError(f"Invalid model configuration for {config.model_id}")

            # Create adapter
            adapter_class = self.adapter_factory.get(config.protocol)
            if not adapter_class:
                raise ValueError(f"Unsupported protocol: {config.protocol}")

            adapter = adapter_class()

            # Initialize adapter
            if not await adapter.initialize(config):
                raise Exception(f"Failed to initialize adapter for {config.model_id}")

            # Register model
            self.model_registry[config.model_id] = config
            self.model_adapters[config.model_id] = adapter

            # Update statistics
            self.integration_stats["total_models"] += 1
            self.integration_stats["active_models"] += 1
            self.integration_stats["by_model_type"][config.model_type.value] += 1
            self.integration_stats["by_protocol"][config.protocol.value] += 1

            logger.info(f"Successfully registered custom model: {config.model_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to register custom model {config.model_id}: {str(e)}")
            return False

    async def unregister_custom_model(self, model_id: str) -> bool:
        """Unregister a custom model"""
        try:
            if model_id not in self.model_registry:
                return False

            # Cleanup adapter
            adapter = self.model_adapters.get(model_id)
            if adapter:
                await adapter.cleanup()
                del self.model_adapters[model_id]

            # Remove from registry
            config = self.model_registry[model_id]
            del self.model_registry[model_id]

            # Update statistics
            self.integration_stats["active_models"] -= 1
            self.integration_stats["by_model_type"][config.model_type.value] -= 1
            self.integration_stats["by_protocol"][config.protocol.value] -= 1

            logger.info(f"Successfully unregistered custom model: {model_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to unregister custom model {model_id}: {str(e)}")
            return False

    async def process_custom_model_request(
        self, model_id: str, request: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Process a request using a custom model"""
        start_time = datetime.now()

        try:
            self.integration_stats["total_requests"] += 1

            # Get model and adapter
            if model_id not in self.model_registry:
                raise ValueError(f"Model not registered: {model_id}")

            config = self.model_registry[model_id]
            adapter = self.model_adapters[model_id]

            # Process request
            response = await adapter.process_request(request)

            # Track attribution
            attribution_data = await self._track_custom_model_attribution(
                config, response, request.get("context", {})
            )

            # Create interaction capsule
            capsule = await self._create_custom_model_capsule(
                config, request, response, attribution_data
            )

            # Update statistics
            self.integration_stats["successful_requests"] += 1
            self.integration_stats["total_processing_time"] += response.processing_time

            return {
                "model_id": model_id,
                "response": response.response_data,
                "metadata": response.metadata,
                "processing_time": response.processing_time,
                "tokens_used": response.tokens_used,
                "confidence": response.confidence,
                "attribution_data": attribution_data,
                "capsule_id": capsule.id if capsule else None,
                "timestamp": datetime.now().isoformat(),
            }

        except Exception as e:
            self.integration_stats["failed_requests"] += 1
            logger.error(f"Custom model request failed: {str(e)}")
            raise

    async def batch_process_requests(
        self, requests: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Process multiple requests in batch"""
        results = []

        # Process requests concurrently
        tasks = []
        for request in requests:
            model_id = request.get("model_id")
            if model_id:
                task = self.process_custom_model_request(model_id, request)
                tasks.append(task)

        # Wait for all requests to complete
        batch_results = await asyncio.gather(*tasks, return_exceptions=True)

        # Process results
        for result in batch_results:
            if isinstance(result, Exception):
                results.append({"status": "error", "error": str(result)})
            else:
                results.append({"status": "success", "data": result})

        return results

    async def health_check_all_models(self) -> Dict[str, Any]:
        """Check health of all registered models"""
        health_results = {}

        for model_id, adapter in self.model_adapters.items():
            try:
                health_result = await adapter.health_check()
                health_results[model_id] = health_result
            except Exception as e:
                health_results[model_id] = {"status": "error", "error": str(e)}

        # Calculate overall health
        healthy_models = sum(
            1 for result in health_results.values() if result.get("status") == "healthy"
        )
        total_models = len(health_results)

        overall_health = {
            "overall_status": "healthy"
            if healthy_models == total_models
            else "degraded",
            "healthy_models": healthy_models,
            "total_models": total_models,
            "health_percentage": (healthy_models / total_models * 100)
            if total_models > 0
            else 0,
            "individual_results": health_results,
            "timestamp": datetime.now().isoformat(),
        }

        return overall_health

    async def get_model_capabilities(
        self, model_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get capabilities of models"""
        if model_id:
            if model_id not in self.model_registry:
                raise ValueError(f"Model not registered: {model_id}")

            adapter = self.model_adapters[model_id]
            return {
                "model_id": model_id,
                "capabilities": adapter.get_supported_capabilities(),
                "config": self.model_registry[model_id].to_dict(),
            }
        else:
            # Return capabilities for all models
            all_capabilities = {}
            for model_id, adapter in self.model_adapters.items():
                all_capabilities[model_id] = {
                    "capabilities": adapter.get_supported_capabilities(),
                    "config": self.model_registry[model_id].to_dict(),
                }
            return all_capabilities

    async def load_models_from_config(self, config_path: str) -> Dict[str, bool]:
        """Load multiple models from configuration file"""
        results = {}

        try:
            with open(config_path) as file:
                if config_path.endswith(".yaml") or config_path.endswith(".yml"):
                    config_data = yaml.safe_load(file)
                else:
                    config_data = json.load(file)

            models_config = config_data.get("custom_models", [])

            for model_config in models_config:
                try:
                    config = CustomModelConfig(
                        model_id=model_config["model_id"],
                        model_name=model_config["model_name"],
                        model_type=ModelType(model_config["model_type"]),
                        provider=model_config["provider"],
                        version=model_config["version"],
                        endpoint_url=model_config["endpoint_url"],
                        protocol=IntegrationProtocol(model_config["protocol"]),
                        authentication=AuthenticationMethod(
                            model_config["authentication"]
                        ),
                        capabilities=model_config["capabilities"],
                        parameters=model_config.get("parameters", {}),
                        rate_limits=model_config.get("rate_limits", {}),
                        cost_structure=model_config.get("cost_structure", {}),
                        metadata=model_config.get("metadata", {}),
                    )

                    success = await self.register_custom_model(config)
                    results[config.model_id] = success

                except Exception as e:
                    logger.error(
                        f"Failed to load model {model_config.get('model_id', 'unknown')}: {str(e)}"
                    )
                    results[model_config.get("model_id", "unknown")] = False

        except Exception as e:
            logger.error(f"Failed to load models from config: {str(e)}")
            raise

        return results

    async def _validate_model_config(self, config: CustomModelConfig) -> bool:
        """Validate model configuration"""
        # Check required fields
        if not config.model_id or not config.endpoint_url:
            return False

        # Check if model already exists
        if config.model_id in self.model_registry:
            return False

        # Validate URL format
        if not config.endpoint_url.startswith(("http://", "https://")):
            return False

        return True

    async def _track_custom_model_attribution(
        self,
        config: CustomModelConfig,
        response: ModelResponse,
        context: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Track attribution for custom model usage"""

        attribution_data = {
            "session_id": context.get("session_id", "unknown"),
            "user_id": context.get("user_id", "unknown"),
            "conversation_id": context.get("conversation_id", "unknown"),
            "model_attribution": {
                "model_id": config.model_id,
                "model_name": config.model_name,
                "model_type": config.model_type.value,
                "provider": config.provider,
                "version": config.version,
                "protocol": config.protocol.value,
                "tokens_used": response.tokens_used,
                "processing_time": response.processing_time,
                "confidence": response.confidence,
            },
            "cost_attribution": {
                "base_cost": config.cost_structure.get("base_cost", 0.0),
                "per_token_cost": config.cost_structure.get("per_token_cost", 0.0),
                "total_cost": config.cost_structure.get("base_cost", 0.0)
                + (
                    response.tokens_used
                    * config.cost_structure.get("per_token_cost", 0.0)
                ),
            },
            "usage_metadata": {
                "endpoint_url": config.endpoint_url,
                "capabilities_used": response.attribution_data.get(
                    "capabilities_used", []
                ),
                "request_metadata": response.metadata,
            },
        }

        return attribution_data

    async def _create_custom_model_capsule(
        self,
        config: CustomModelConfig,
        request: Dict[str, Any],
        response: ModelResponse,
        attribution_data: Dict[str, Any],
    ):
        """Create a capsule for custom model interaction"""

        capsule_data = {
            "type": "custom_model_interaction",
            "model_config": config.to_dict(),
            "request": request,
            "response": response.to_dict(),
            "attribution_data": attribution_data,
            "timestamp": datetime.now().isoformat(),
            "interaction_metadata": {
                "protocol": config.protocol.value,
                "model_type": config.model_type.value,
                "processing_time": response.processing_time,
                "confidence": response.confidence,
            },
        }

        # Create specialized capsule
        capsule = create_specialized_capsule(
            capsule_type="custom_model_interaction",
            data=capsule_data,
            metadata={"source": "custom_model_integration"},
        )

        # Store in capsule engine
        await self.capsule_engine.store_capsule(capsule)

        return capsule

    async def get_integration_statistics(self) -> Dict[str, Any]:
        """Get integration statistics"""
        stats = self.integration_stats.copy()

        if stats["total_requests"] > 0:
            stats["success_rate"] = (
                stats["successful_requests"] / stats["total_requests"]
            )
            stats["average_processing_time"] = (
                stats["total_processing_time"] / stats["total_requests"]
            )
        else:
            stats["success_rate"] = 0.0
            stats["average_processing_time"] = 0.0

        return stats

    async def get_registered_models(self) -> List[Dict[str, Any]]:
        """Get list of registered models"""
        models = []

        for model_id, config in self.model_registry.items():
            model_info = config.to_dict()
            model_info["status"] = (
                "active" if model_id in self.model_adapters else "inactive"
            )
            models.append(model_info)

        return models
