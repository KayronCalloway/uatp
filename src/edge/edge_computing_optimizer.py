"""
Edge Computing and Global Performance Optimization System
Provides intelligent request routing, edge caching, and performance optimization
"""

import asyncio
import json
import logging
import statistics
import time
from dataclasses import asdict, dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

import aioredis
from pydantic import BaseModel, Field

from ..attribution.cross_conversation_tracker import CrossConversationTracker
from ..capsules.specialized_capsules import create_specialized_capsule
from ..engine.capsule_engine import CapsuleEngine

logger = logging.getLogger(__name__)


class EdgeLocation(Enum):
    """Available edge locations"""

    US_EAST_1 = "us-east-1"
    US_WEST_2 = "us-west-2"
    EU_WEST_1 = "eu-west-1"
    AP_SOUTHEAST_1 = "ap-southeast-1"
    AP_NORTHEAST_1 = "ap-northeast-1"
    SA_EAST_1 = "sa-east-1"


class CacheStrategy(Enum):
    """Cache strategies for different content types"""

    AGGRESSIVE = "aggressive"
    STANDARD = "standard"
    MINIMAL = "minimal"
    NO_CACHE = "no_cache"


class OptimizationLevel(Enum):
    """Optimization levels for different scenarios"""

    MAXIMUM = "maximum"
    BALANCED = "balanced"
    CONSERVATIVE = "conservative"


@dataclass
class EdgeNode:
    """Edge computing node information"""

    location: EdgeLocation
    name: str
    endpoint: str
    capacity: int
    current_load: float
    latency_ms: float
    health_status: str
    capabilities: List[str]
    last_updated: datetime

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data["location"] = self.location.value
        data["last_updated"] = self.last_updated.isoformat()
        return data


@dataclass
class CacheEntry:
    """Cache entry with metadata"""

    key: str
    value: Any
    ttl: int
    strategy: CacheStrategy
    content_type: str
    size_bytes: int
    hit_count: int
    created_at: datetime
    last_accessed: datetime

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data["strategy"] = self.strategy.value
        data["created_at"] = self.created_at.isoformat()
        data["last_accessed"] = self.last_accessed.isoformat()
        return data


@dataclass
class PerformanceMetrics:
    """Performance metrics for optimization"""

    location: EdgeLocation
    request_count: int
    avg_latency: float
    p95_latency: float
    p99_latency: float
    error_rate: float
    cache_hit_rate: float
    bandwidth_usage: float
    cpu_usage: float
    memory_usage: float
    timestamp: datetime

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data["location"] = self.location.value
        data["timestamp"] = self.timestamp.isoformat()
        return data


class EdgeOptimizationRequest(BaseModel):
    """Request for edge optimization"""

    user_location: str
    content_type: str
    optimization_level: OptimizationLevel
    cache_strategy: CacheStrategy
    performance_requirements: Dict[str, Any] = Field(default_factory=dict)
    user_context: Dict[str, Any] = Field(default_factory=dict)


class EdgeCache:
    """Distributed edge cache system"""

    def __init__(self, redis_url: str):
        self.redis_url = redis_url
        self.redis_pool = None
        self.cache_stats = {"hits": 0, "misses": 0, "evictions": 0, "total_size": 0}

    async def initialize(self) -> bool:
        """Initialize cache system"""
        try:
            self.redis_pool = await aioredis.create_connection_pool(self.redis_url)
            logger.info("Edge cache initialized successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to initialize edge cache: {str(e)}")
            return False

    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        try:
            if not self.redis_pool:
                return None

            redis = await aioredis.Redis(connection_pool=self.redis_pool)

            # Get value and metadata
            cache_data = await redis.hgetall(f"cache:{key}")

            if cache_data:
                # Update access statistics
                await redis.hincrby(f"cache:{key}", "hit_count", 1)
                await redis.hset(
                    f"cache:{key}", "last_accessed", datetime.now().isoformat()
                )

                self.cache_stats["hits"] += 1

                # Return cached value
                return json.loads(cache_data.get("value", "{}"))
            else:
                self.cache_stats["misses"] += 1
                return None

        except Exception as e:
            logger.error(f"Cache get error: {str(e)}")
            return None

    async def set(
        self,
        key: str,
        value: Any,
        ttl: int = 3600,
        strategy: CacheStrategy = CacheStrategy.STANDARD,
        content_type: str = "application/json",
    ) -> bool:
        """Set value in cache"""
        try:
            if not self.redis_pool:
                return False

            redis = await aioredis.Redis(connection_pool=self.redis_pool)

            # Serialize value
            serialized_value = json.dumps(value)
            size_bytes = len(serialized_value.encode("utf-8"))

            # Create cache entry
            cache_entry = {
                "value": serialized_value,
                "ttl": ttl,
                "strategy": strategy.value,
                "content_type": content_type,
                "size_bytes": size_bytes,
                "hit_count": 0,
                "created_at": datetime.now().isoformat(),
                "last_accessed": datetime.now().isoformat(),
            }

            # Store in cache
            await redis.hset(f"cache:{key}", mapping=cache_entry)
            await redis.expire(f"cache:{key}", ttl)

            self.cache_stats["total_size"] += size_bytes

            return True

        except Exception as e:
            logger.error(f"Cache set error: {str(e)}")
            return False

    async def invalidate(self, key: str) -> bool:
        """Invalidate cache entry"""
        try:
            if not self.redis_pool:
                return False

            redis = await aioredis.Redis(connection_pool=self.redis_pool)

            # Get size before deletion
            cache_data = await redis.hgetall(f"cache:{key}")
            if cache_data:
                size_bytes = int(cache_data.get("size_bytes", 0))
                self.cache_stats["total_size"] -= size_bytes

            # Delete from cache
            result = await redis.delete(f"cache:{key}")

            if result:
                self.cache_stats["evictions"] += 1
                return True

            return False

        except Exception as e:
            logger.error(f"Cache invalidate error: {str(e)}")
            return False

    async def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        total_requests = self.cache_stats["hits"] + self.cache_stats["misses"]
        hit_rate = (
            (self.cache_stats["hits"] / total_requests * 100)
            if total_requests > 0
            else 0
        )

        return {
            **self.cache_stats,
            "hit_rate": hit_rate,
            "total_requests": total_requests,
        }


class EdgeRouter:
    """Intelligent edge routing system"""

    def __init__(self):
        self.edge_nodes = {}
        self.routing_table = {}
        self.performance_history = {}
        self.load_balancer_weights = {}

    def register_edge_node(self, edge_node: EdgeNode):
        """Register an edge node"""
        self.edge_nodes[edge_node.location.value] = edge_node
        self.load_balancer_weights[edge_node.location.value] = 1.0
        logger.info(
            f"Registered edge node: {edge_node.name} at {edge_node.location.value}"
        )

    async def find_optimal_edge(
        self,
        user_location: str,
        content_type: str,
        performance_requirements: Dict[str, Any],
    ) -> Optional[EdgeNode]:
        """Find optimal edge node for request"""

        # Get candidate nodes
        candidate_nodes = await self._get_candidate_nodes(user_location, content_type)

        if not candidate_nodes:
            return None

        # Score each node
        scored_nodes = []
        for node in candidate_nodes:
            score = await self._calculate_node_score(
                node, user_location, performance_requirements
            )
            scored_nodes.append((node, score))

        # Sort by score (highest first)
        scored_nodes.sort(key=lambda x: x[1], reverse=True)

        # Return best node
        return scored_nodes[0][0] if scored_nodes else None

    async def _get_candidate_nodes(
        self, user_location: str, content_type: str
    ) -> List[EdgeNode]:
        """Get candidate edge nodes"""
        candidates = []

        # Geographic proximity mapping
        geo_mapping = {
            "us": [EdgeLocation.US_EAST_1, EdgeLocation.US_WEST_2],
            "eu": [EdgeLocation.EU_WEST_1],
            "asia": [EdgeLocation.AP_SOUTHEAST_1, EdgeLocation.AP_NORTHEAST_1],
            "sa": [EdgeLocation.SA_EAST_1],
        }

        # Get nodes by geographic region
        preferred_locations = geo_mapping.get(user_location, list(EdgeLocation))

        for location in preferred_locations:
            node = self.edge_nodes.get(location.value)
            if node and node.health_status == "healthy":
                # Check if node supports required content type
                if self._supports_content_type(node, content_type):
                    candidates.append(node)

        # Add backup nodes from other regions if needed
        if len(candidates) < 2:
            for location, node in self.edge_nodes.items():
                if node.health_status == "healthy" and node not in candidates:
                    if self._supports_content_type(node, content_type):
                        candidates.append(node)

        return candidates

    def _supports_content_type(self, node: EdgeNode, content_type: str) -> bool:
        """Check if node supports content type"""
        # Check node capabilities
        if "multimodal" in node.capabilities and content_type in [
            "image",
            "audio",
            "video",
        ]:
            return True
        if "text_processing" in node.capabilities and content_type == "text":
            return True
        if "reasoning" in node.capabilities and content_type == "reasoning":
            return True

        # Default support
        return "general" in node.capabilities

    async def _calculate_node_score(
        self,
        node: EdgeNode,
        user_location: str,
        performance_requirements: Dict[str, Any],
    ) -> float:
        """Calculate score for edge node"""
        score = 100.0  # Base score

        # Latency factor (lower is better)
        max_latency = performance_requirements.get("max_latency", 200)
        if node.latency_ms <= max_latency:
            score += (max_latency - node.latency_ms) / max_latency * 30
        else:
            score -= (node.latency_ms - max_latency) / max_latency * 50

        # Load factor (lower is better)
        load_penalty = node.current_load * 20
        score -= load_penalty

        # Capacity factor
        capacity_bonus = min(node.capacity / 1000, 10)  # Max 10 points for capacity
        score += capacity_bonus

        # Geographic proximity bonus
        geo_bonus = self._calculate_geo_bonus(node.location, user_location)
        score += geo_bonus

        # Load balancer weight
        weight = self.load_balancer_weights.get(node.location.value, 1.0)
        score *= weight

        return max(0, score)  # Ensure non-negative score

    def _calculate_geo_bonus(
        self, node_location: EdgeLocation, user_location: str
    ) -> float:
        """Calculate geographic proximity bonus"""
        location_bonuses = {
            ("us", EdgeLocation.US_EAST_1): 20,
            ("us", EdgeLocation.US_WEST_2): 15,
            ("eu", EdgeLocation.EU_WEST_1): 20,
            ("asia", EdgeLocation.AP_SOUTHEAST_1): 20,
            ("asia", EdgeLocation.AP_NORTHEAST_1): 15,
            ("sa", EdgeLocation.SA_EAST_1): 20,
        }

        return location_bonuses.get((user_location, node_location), 0)

    async def update_node_metrics(
        self, location: EdgeLocation, metrics: PerformanceMetrics
    ):
        """Update node performance metrics"""
        node = self.edge_nodes.get(location.value)
        if node:
            node.latency_ms = metrics.avg_latency
            node.current_load = metrics.cpu_usage
            node.last_updated = datetime.now()

            # Update performance history
            if location.value not in self.performance_history:
                self.performance_history[location.value] = []

            self.performance_history[location.value].append(metrics)

            # Keep only last 100 metrics
            if len(self.performance_history[location.value]) > 100:
                self.performance_history[location.value] = self.performance_history[
                    location.value
                ][-100:]

            # Update load balancer weights
            await self._update_load_balancer_weights(location)

    async def _update_load_balancer_weights(self, location: EdgeLocation):
        """Update load balancer weights based on performance"""
        history = self.performance_history.get(location.value, [])

        if len(history) < 5:
            return

        # Calculate average performance metrics
        recent_metrics = history[-10:]  # Last 10 measurements
        avg_latency = statistics.mean(m.avg_latency for m in recent_metrics)
        avg_error_rate = statistics.mean(m.error_rate for m in recent_metrics)
        avg_cpu_usage = statistics.mean(m.cpu_usage for m in recent_metrics)

        # Calculate weight based on performance
        weight = 1.0

        # Reduce weight for high latency
        if avg_latency > 200:
            weight *= 0.8
        elif avg_latency > 100:
            weight *= 0.9

        # Reduce weight for high error rate
        if avg_error_rate > 0.05:
            weight *= 0.7
        elif avg_error_rate > 0.01:
            weight *= 0.85

        # Reduce weight for high CPU usage
        if avg_cpu_usage > 80:
            weight *= 0.8
        elif avg_cpu_usage > 60:
            weight *= 0.9

        self.load_balancer_weights[location.value] = weight


class EdgeComputingOptimizer:
    """
    Comprehensive edge computing and performance optimization system
    """

    def __init__(
        self,
        capsule_engine: CapsuleEngine,
        attribution_tracker: CrossConversationTracker,
        redis_url: str = "redis://localhost:6379",
    ):
        self.capsule_engine = capsule_engine
        self.attribution_tracker = attribution_tracker

        # Initialize components
        self.edge_cache = EdgeCache(redis_url)
        self.edge_router = EdgeRouter()

        # Performance tracking
        self.performance_metrics = {}
        self.optimization_stats = {
            "total_requests": 0,
            "cache_hits": 0,
            "edge_routed": 0,
            "optimization_applied": 0,
            "latency_improved": 0,
            "bandwidth_saved": 0,
        }

        # Initialize edge nodes
        self._initialize_edge_nodes()

    def _initialize_edge_nodes(self):
        """Initialize edge nodes"""
        edge_nodes = [
            EdgeNode(
                location=EdgeLocation.US_EAST_1,
                name="US East Virginia",
                endpoint="https://us-east-1.edge.uatp.ai",
                capacity=1000,
                current_load=25.0,
                latency_ms=15.0,
                health_status="healthy",
                capabilities=["general", "text_processing", "multimodal", "reasoning"],
                last_updated=datetime.now(),
            ),
            EdgeNode(
                location=EdgeLocation.US_WEST_2,
                name="US West Oregon",
                endpoint="https://us-west-2.edge.uatp.ai",
                capacity=800,
                current_load=30.0,
                latency_ms=20.0,
                health_status="healthy",
                capabilities=["general", "text_processing", "multimodal"],
                last_updated=datetime.now(),
            ),
            EdgeNode(
                location=EdgeLocation.EU_WEST_1,
                name="EU West Ireland",
                endpoint="https://eu-west-1.edge.uatp.ai",
                capacity=600,
                current_load=35.0,
                latency_ms=25.0,
                health_status="healthy",
                capabilities=["general", "text_processing", "reasoning"],
                last_updated=datetime.now(),
            ),
            EdgeNode(
                location=EdgeLocation.AP_SOUTHEAST_1,
                name="Asia Pacific Singapore",
                endpoint="https://ap-southeast-1.edge.uatp.ai",
                capacity=400,
                current_load=45.0,
                latency_ms=30.0,
                health_status="healthy",
                capabilities=["general", "text_processing"],
                last_updated=datetime.now(),
            ),
        ]

        for node in edge_nodes:
            self.edge_router.register_edge_node(node)

    async def initialize(self) -> bool:
        """Initialize edge computing system"""
        try:
            # Initialize cache
            cache_initialized = await self.edge_cache.initialize()
            if not cache_initialized:
                logger.warning("Edge cache initialization failed")

            # Start performance monitoring
            asyncio.create_task(self._performance_monitoring_loop())

            logger.info("Edge computing optimizer initialized successfully")
            return True

        except Exception as e:
            logger.error(f"Failed to initialize edge computing optimizer: {str(e)}")
            return False

    async def optimize_request(
        self, request: EdgeOptimizationRequest
    ) -> Dict[str, Any]:
        """Optimize request processing with edge computing"""
        start_time = time.time()

        try:
            self.optimization_stats["total_requests"] += 1

            # Generate cache key
            cache_key = self._generate_cache_key(request)

            # Check cache first
            cached_result = await self.edge_cache.get(cache_key)
            if cached_result:
                self.optimization_stats["cache_hits"] += 1

                return {
                    "status": "cached",
                    "source": "edge_cache",
                    "result": cached_result,
                    "processing_time": (time.time() - start_time) * 1000,
                    "cache_hit": True,
                    "optimization_applied": True,
                }

            # Find optimal edge node
            optimal_node = await self.edge_router.find_optimal_edge(
                request.user_location,
                request.content_type,
                request.performance_requirements,
            )

            if not optimal_node:
                # Process locally if no edge node available
                result = await self._process_locally(request)
                processing_time = (time.time() - start_time) * 1000

                return {
                    "status": "processed",
                    "source": "local",
                    "result": result,
                    "processing_time": processing_time,
                    "cache_hit": False,
                    "optimization_applied": False,
                }

            # Route to edge node
            result = await self._route_to_edge(optimal_node, request)
            processing_time = (time.time() - start_time) * 1000

            # Cache the result
            await self._cache_result(cache_key, result, request.cache_strategy)

            # Track optimization
            await self._track_optimization(
                request, optimal_node, result, processing_time
            )

            self.optimization_stats["edge_routed"] += 1
            self.optimization_stats["optimization_applied"] += 1

            return {
                "status": "processed",
                "source": "edge_node",
                "edge_location": optimal_node.location.value,
                "result": result,
                "processing_time": processing_time,
                "cache_hit": False,
                "optimization_applied": True,
            }

        except Exception as e:
            logger.error(f"Request optimization failed: {str(e)}")

            # Fallback to local processing
            result = await self._process_locally(request)
            processing_time = (time.time() - start_time) * 1000

            return {
                "status": "processed",
                "source": "local_fallback",
                "result": result,
                "processing_time": processing_time,
                "cache_hit": False,
                "optimization_applied": False,
                "error": str(e),
            }

    def _generate_cache_key(self, request: EdgeOptimizationRequest) -> str:
        """Generate cache key for request"""
        key_components = [
            request.content_type,
            request.optimization_level.value,
            str(hash(json.dumps(request.user_context, sort_keys=True))),
        ]

        return f"edge_cache:{':'.join(key_components)}"

    async def _process_locally(
        self, request: EdgeOptimizationRequest
    ) -> Dict[str, Any]:
        """Process request locally"""
        # Mock local processing
        await asyncio.sleep(0.1)  # Simulate processing time

        return {
            "content_type": request.content_type,
            "optimization_level": request.optimization_level.value,
            "result": "Local processing result",
            "processed_at": datetime.now().isoformat(),
        }

    async def _route_to_edge(
        self, edge_node: EdgeNode, request: EdgeOptimizationRequest
    ) -> Dict[str, Any]:
        """Route request to edge node"""
        try:
            # Mock edge processing
            await asyncio.sleep(0.05)  # Simulate edge processing time

            return {
                "content_type": request.content_type,
                "optimization_level": request.optimization_level.value,
                "result": f"Edge processing result from {edge_node.name}",
                "processed_at": datetime.now().isoformat(),
                "edge_location": edge_node.location.value,
            }

        except Exception as e:
            logger.error(f"Edge routing failed: {str(e)}")
            raise

    async def _cache_result(
        self, cache_key: str, result: Dict[str, Any], strategy: CacheStrategy
    ):
        """Cache processing result"""
        ttl_mapping = {
            CacheStrategy.AGGRESSIVE: 3600,  # 1 hour
            CacheStrategy.STANDARD: 1800,  # 30 minutes
            CacheStrategy.MINIMAL: 300,  # 5 minutes
            CacheStrategy.NO_CACHE: 0,  # No cache
        }

        ttl = ttl_mapping.get(strategy, 1800)

        if ttl > 0:
            await self.edge_cache.set(cache_key, result, ttl, strategy)

    async def _track_optimization(
        self,
        request: EdgeOptimizationRequest,
        edge_node: EdgeNode,
        result: Dict[str, Any],
        processing_time: float,
    ):
        """Track optimization metrics"""

        # Create optimization capsule
        capsule_data = {
            "type": "edge_optimization",
            "request": {
                "user_location": request.user_location,
                "content_type": request.content_type,
                "optimization_level": request.optimization_level.value,
                "cache_strategy": request.cache_strategy.value,
            },
            "edge_node": edge_node.to_dict(),
            "result": result,
            "processing_time": processing_time,
            "timestamp": datetime.now().isoformat(),
            "optimization_metadata": {
                "cache_used": False,  # Set based on actual cache usage
                "latency_improvement": max(
                    0, 100 - processing_time
                ),  # Mock improvement
                "bandwidth_saved": 0,  # Mock bandwidth saving
            },
        }

        # Create specialized capsule
        capsule = create_specialized_capsule(
            capsule_type="edge_optimization",
            data=capsule_data,
            metadata={"source": "edge_computing_optimizer"},
        )

        # Store in capsule engine
        await self.capsule_engine.store_capsule(capsule)

    async def _performance_monitoring_loop(self):
        """Continuous performance monitoring"""
        while True:
            try:
                await self._collect_performance_metrics()
                await asyncio.sleep(60)  # Collect metrics every minute
            except Exception as e:
                logger.error(f"Performance monitoring error: {str(e)}")
                await asyncio.sleep(60)

    async def _collect_performance_metrics(self):
        """Collect performance metrics from all edge nodes"""
        for location_str, node in self.edge_router.edge_nodes.items():
            try:
                # Mock metrics collection
                metrics = PerformanceMetrics(
                    location=node.location,
                    request_count=100,  # Mock request count
                    avg_latency=node.latency_ms,
                    p95_latency=node.latency_ms * 1.5,
                    p99_latency=node.latency_ms * 2.0,
                    error_rate=0.01,  # Mock error rate
                    cache_hit_rate=0.75,  # Mock cache hit rate
                    bandwidth_usage=node.current_load,
                    cpu_usage=node.current_load,
                    memory_usage=node.current_load * 0.8,
                    timestamp=datetime.now(),
                )

                # Update node metrics
                await self.edge_router.update_node_metrics(node.location, metrics)

                # Store in performance history
                self.performance_metrics[location_str] = metrics

            except Exception as e:
                logger.error(f"Failed to collect metrics for {location_str}: {str(e)}")

    async def get_optimization_statistics(self) -> Dict[str, Any]:
        """Get edge optimization statistics"""
        cache_stats = await self.edge_cache.get_stats()

        stats = {
            "optimization_stats": self.optimization_stats.copy(),
            "cache_stats": cache_stats,
            "edge_nodes": {
                location: node.to_dict()
                for location, node in self.edge_router.edge_nodes.items()
            },
            "performance_metrics": {
                location: metrics.to_dict()
                for location, metrics in self.performance_metrics.items()
            },
        }

        # Calculate derived metrics
        total_requests = stats["optimization_stats"]["total_requests"]
        if total_requests > 0:
            stats["optimization_stats"]["cache_hit_rate"] = (
                stats["optimization_stats"]["cache_hits"] / total_requests * 100
            )
            stats["optimization_stats"]["edge_routing_rate"] = (
                stats["optimization_stats"]["edge_routed"] / total_requests * 100
            )
            stats["optimization_stats"]["optimization_rate"] = (
                stats["optimization_stats"]["optimization_applied"]
                / total_requests
                * 100
            )

        return stats

    async def get_edge_node_status(
        self, location: Optional[EdgeLocation] = None
    ) -> Dict[str, Any]:
        """Get status of edge nodes"""
        if location:
            node = self.edge_router.edge_nodes.get(location.value)
            if node:
                return {
                    "node": node.to_dict(),
                    "metrics": self.performance_metrics.get(
                        location.value, {}
                    ).to_dict()
                    if location.value in self.performance_metrics
                    else {},
                }
            else:
                return {"error": f"Edge node not found: {location.value}"}
        else:
            return {
                "nodes": {
                    location: node.to_dict()
                    for location, node in self.edge_router.edge_nodes.items()
                },
                "total_nodes": len(self.edge_router.edge_nodes),
                "healthy_nodes": sum(
                    1
                    for node in self.edge_router.edge_nodes.values()
                    if node.health_status == "healthy"
                ),
            }

    async def invalidate_cache(self, cache_key: Optional[str] = None) -> Dict[str, Any]:
        """Invalidate cache entries"""
        if cache_key:
            success = await self.edge_cache.invalidate(cache_key)
            return {"cache_key": cache_key, "invalidated": success}
        else:
            # Invalidate all cache entries (implementation would vary)
            return {"message": "Global cache invalidation not implemented"}

    async def get_cache_statistics(self) -> Dict[str, Any]:
        """Get cache statistics"""
        return await self.edge_cache.get_stats()
