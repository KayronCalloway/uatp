"""
UATP Python SDK - Federation Module

Provides global coordination and federation capabilities for planetary-scale UATP network.
"""

import asyncio
import logging
from dataclasses import dataclass
from typing import Dict, List, Optional, Any, Union
from datetime import datetime, timezone
from enum import Enum

logger = logging.getLogger(__name__)


class NodeStatus(Enum):
    """Status of a federation node."""

    ACTIVE = "active"
    INACTIVE = "inactive"
    SYNCING = "syncing"
    MAINTENANCE = "maintenance"
    UNREACHABLE = "unreachable"


class NetworkHealth(Enum):
    """Overall network health status."""

    HEALTHY = "healthy"
    DEGRADED = "degraded"
    CRITICAL = "critical"
    PARTITIONED = "partitioned"


@dataclass
class Node:
    """A node in the UATP federation network."""

    node_id: str
    node_name: str
    endpoint: str
    region: str
    country: str
    status: NodeStatus
    last_seen: datetime

    # Network metrics
    latency_ms: float
    throughput_tps: float  # transactions per second
    reliability_score: float  # 0.0 to 1.0

    # Governance participation
    voting_power: float
    governance_participation: float

    # Economic metrics
    attributions_processed: int
    rewards_distributed: float

    # Technical specifications
    version: str
    capabilities: List[str]
    supported_protocols: List[str]

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format."""
        return {
            "node_id": self.node_id,
            "node_name": self.node_name,
            "endpoint": self.endpoint,
            "region": self.region,
            "country": self.country,
            "status": self.status.value,
            "last_seen": self.last_seen.isoformat(),
            "latency_ms": self.latency_ms,
            "throughput_tps": self.throughput_tps,
            "reliability_score": self.reliability_score,
            "voting_power": self.voting_power,
            "governance_participation": self.governance_participation,
            "attributions_processed": self.attributions_processed,
            "rewards_distributed": self.rewards_distributed,
            "version": self.version,
            "capabilities": self.capabilities,
            "supported_protocols": self.supported_protocols,
        }


@dataclass
class FederationMetrics:
    """Global federation network metrics."""

    total_nodes: int
    active_nodes: int
    network_health: NetworkHealth
    global_consensus_rate: float
    average_latency_ms: float
    total_throughput_tps: float

    # Geographic distribution
    nodes_by_region: Dict[str, int]
    nodes_by_country: Dict[str, int]

    # Economic metrics
    global_attribution_volume: int
    cross_node_transactions: int
    federation_rewards_distributed: float

    # Governance metrics
    active_proposals: int
    global_voting_participation: float
    consensus_protocols_active: List[str]

    timestamp: datetime

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format."""
        return {
            "total_nodes": self.total_nodes,
            "active_nodes": self.active_nodes,
            "network_health": self.network_health.value,
            "global_consensus_rate": self.global_consensus_rate,
            "average_latency_ms": self.average_latency_ms,
            "total_throughput_tps": self.total_throughput_tps,
            "nodes_by_region": self.nodes_by_region,
            "nodes_by_country": self.nodes_by_country,
            "global_attribution_volume": self.global_attribution_volume,
            "cross_node_transactions": self.cross_node_transactions,
            "federation_rewards_distributed": self.federation_rewards_distributed,
            "active_proposals": self.active_proposals,
            "global_voting_participation": self.global_voting_participation,
            "consensus_protocols_active": self.consensus_protocols_active,
            "timestamp": self.timestamp.isoformat(),
        }


class FederationClient:
    """Client for interacting with the global UATP federation."""

    def __init__(self, client, federation_node: Optional[str] = None):
        self.client = client
        self.federation_node = federation_node or "global.uatp.network"
        self.node_cache = {}
        self.metrics_cache = {}
        logger.info(f"🌐 Federation Client initialized for node: {self.federation_node}")

    async def get_network_status(self) -> FederationMetrics:
        """Get current status of the global UATP federation network."""

        try:
            response = await self.client.http_client.get(
                "/api/v1/federation/network-status"
            )
            response.raise_for_status()

            data = response.json()

            metrics = FederationMetrics(
                total_nodes=data.get("total_nodes", 0),
                active_nodes=data.get("active_nodes", 0),
                network_health=NetworkHealth(data.get("network_health", "healthy")),
                global_consensus_rate=data.get("global_consensus_rate", 0.0),
                average_latency_ms=data.get("average_latency_ms", 0.0),
                total_throughput_tps=data.get("total_throughput_tps", 0.0),
                nodes_by_region=data.get("nodes_by_region", {}),
                nodes_by_country=data.get("nodes_by_country", {}),
                global_attribution_volume=data.get("global_attribution_volume", 0),
                cross_node_transactions=data.get("cross_node_transactions", 0),
                federation_rewards_distributed=data.get(
                    "federation_rewards_distributed", 0.0
                ),
                active_proposals=data.get("active_proposals", 0),
                global_voting_participation=data.get(
                    "global_voting_participation", 0.0
                ),
                consensus_protocols_active=data.get("consensus_protocols_active", []),
                timestamp=datetime.now(timezone.utc),
            )

            logger.info(
                f"🌐 Network status: {metrics.active_nodes}/{metrics.total_nodes} nodes active"
            )
            return metrics

        except Exception as e:
            logger.error(f"❌ Failed to get network status: {e}")

            # Return fallback metrics
            return FederationMetrics(
                total_nodes=0,
                active_nodes=0,
                network_health=NetworkHealth.CRITICAL,
                global_consensus_rate=0.0,
                average_latency_ms=0.0,
                total_throughput_tps=0.0,
                nodes_by_region={},
                nodes_by_country={},
                global_attribution_volume=0,
                cross_node_transactions=0,
                federation_rewards_distributed=0.0,
                active_proposals=0,
                global_voting_participation=0.0,
                consensus_protocols_active=[],
                timestamp=datetime.now(timezone.utc),
            )

    async def get_nodes(self, region: Optional[str] = None) -> List[Node]:
        """Get list of federation nodes, optionally filtered by region."""

        try:
            params = {}
            if region:
                params["region"] = region

            response = await self.client.http_client.get(
                "/api/v1/federation/nodes", params=params
            )
            response.raise_for_status()

            data = response.json()
            nodes = []

            for item in data.get("nodes", []):
                node = Node(
                    node_id=item["node_id"],
                    node_name=item["node_name"],
                    endpoint=item["endpoint"],
                    region=item["region"],
                    country=item["country"],
                    status=NodeStatus(item["status"]),
                    last_seen=datetime.fromisoformat(item["last_seen"]),
                    latency_ms=item.get("latency_ms", 0.0),
                    throughput_tps=item.get("throughput_tps", 0.0),
                    reliability_score=item.get("reliability_score", 0.0),
                    voting_power=item.get("voting_power", 0.0),
                    governance_participation=item.get("governance_participation", 0.0),
                    attributions_processed=item.get("attributions_processed", 0),
                    rewards_distributed=item.get("rewards_distributed", 0.0),
                    version=item.get("version", "unknown"),
                    capabilities=item.get("capabilities", []),
                    supported_protocols=item.get("supported_protocols", []),
                )
                nodes.append(node)

                # Cache the node
                self.node_cache[node.node_id] = node

            logger.info(f"🌐 Retrieved {len(nodes)} federation nodes")
            return nodes

        except Exception as e:
            logger.error(f"❌ Failed to get federation nodes: {e}")
            return []

    async def get_node(self, node_id: str) -> Optional[Node]:
        """Get information about a specific federation node."""

        # Check cache first
        if node_id in self.node_cache:
            return self.node_cache[node_id]

        try:
            response = await self.client.http_client.get(
                f"/api/v1/federation/nodes/{node_id}"
            )
            response.raise_for_status()

            data = response.json()

            node = Node(
                node_id=data["node_id"],
                node_name=data["node_name"],
                endpoint=data["endpoint"],
                region=data["region"],
                country=data["country"],
                status=NodeStatus(data["status"]),
                last_seen=datetime.fromisoformat(data["last_seen"]),
                latency_ms=data.get("latency_ms", 0.0),
                throughput_tps=data.get("throughput_tps", 0.0),
                reliability_score=data.get("reliability_score", 0.0),
                voting_power=data.get("voting_power", 0.0),
                governance_participation=data.get("governance_participation", 0.0),
                attributions_processed=data.get("attributions_processed", 0),
                rewards_distributed=data.get("rewards_distributed", 0.0),
                version=data.get("version", "unknown"),
                capabilities=data.get("capabilities", []),
                supported_protocols=data.get("supported_protocols", []),
            )

            # Cache the node
            self.node_cache[node_id] = node
            return node

        except Exception as e:
            logger.error(f"❌ Failed to get node {node_id}: {e}")
            return None

    async def join_federation(
        self,
        node_name: str,
        endpoint: str,
        region: str,
        country: str,
        capabilities: List[str],
    ) -> Dict[str, Any]:
        """Request to join the UATP federation as a new node."""

        join_request = {
            "node_name": node_name,
            "endpoint": endpoint,
            "region": region,
            "country": country,
            "capabilities": capabilities,
            "version": "7.0",
            "supported_protocols": ["UATP", "C2PA", "zkDL++"],
            "timestamp": datetime.utcnow().isoformat(),
        }

        try:
            response = await self.client.http_client.post(
                "/api/v1/federation/join", json=join_request
            )
            response.raise_for_status()

            result = response.json()
            logger.info(
                f"🌐 Federation join request submitted: {result.get('request_id')}"
            )
            return result

        except Exception as e:
            logger.error(f"❌ Federation join request failed: {e}")
            return {"success": False, "error": str(e), "request_id": None}

    async def sync_with_federation(
        self, target_node: Optional[str] = None
    ) -> Dict[str, Any]:
        """Synchronize data with the federation network."""

        sync_request = {
            "target_node": target_node,
            "sync_type": "full",  # "full", "incremental", "governance_only"
            "timestamp": datetime.utcnow().isoformat(),
        }

        try:
            response = await self.client.http_client.post(
                "/api/v1/federation/sync", json=sync_request
            )
            response.raise_for_status()

            result = response.json()
            logger.info(
                f"🔄 Federation sync completed: {result.get('records_synced', 0)} records"
            )
            return result

        except Exception as e:
            logger.error(f"❌ Federation sync failed: {e}")
            return {"success": False, "error": str(e), "records_synced": 0}

    async def submit_global_proposal(
        self,
        title: str,
        description: str,
        proposal_type: str,
        impact_regions: List[str],
        execution_data: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Submit a proposal for global federation governance."""

        proposal_request = {
            "title": title,
            "description": description,
            "proposal_type": proposal_type,
            "scope": "global_federation",
            "impact_regions": impact_regions,
            "execution_data": execution_data,
            "requires_supermajority": proposal_type
            in ["constitutional", "protocol_upgrade"],
            "timestamp": datetime.utcnow().isoformat(),
        }

        try:
            response = await self.client.http_client.post(
                "/api/v1/federation/proposals", json=proposal_request
            )
            response.raise_for_status()

            result = response.json()
            logger.info(f"📋 Global proposal submitted: {result.get('proposal_id')}")
            return result

        except Exception as e:
            logger.error(f"❌ Global proposal submission failed: {e}")
            return {"success": False, "error": str(e), "proposal_id": None}

    async def get_consensus_status(self) -> Dict[str, Any]:
        """Get current consensus status across the federation."""

        try:
            response = await self.client.http_client.get("/api/v1/federation/consensus")
            response.raise_for_status()

            return response.json()

        except Exception as e:
            logger.error(f"❌ Failed to get consensus status: {e}")
            return {
                "consensus_reached": False,
                "participating_nodes": 0,
                "agreement_percentage": 0.0,
                "pending_decisions": [],
                "error": str(e),
            }

    async def get_crisis_status(self) -> Dict[str, Any]:
        """Get crisis management status for the federation."""

        try:
            response = await self.client.http_client.get(
                "/api/v1/federation/crisis-status"
            )
            response.raise_for_status()

            return response.json()

        except Exception as e:
            logger.error(f"❌ Failed to get crisis status: {e}")
            return {
                "crisis_level": "none",
                "active_protocols": [],
                "emergency_measures": [],
                "recovery_timeline": None,
                "error": str(e),
            }

    async def trigger_emergency_protocol(
        self, protocol_type: str, justification: str, duration_hours: int
    ) -> Dict[str, Any]:
        """Trigger an emergency protocol across the federation."""

        emergency_request = {
            "protocol_type": protocol_type,
            "justification": justification,
            "duration_hours": duration_hours,
            "requester_node": self.federation_node,
            "timestamp": datetime.utcnow().isoformat(),
        }

        try:
            response = await self.client.http_client.post(
                "/api/v1/federation/emergency", json=emergency_request
            )
            response.raise_for_status()

            result = response.json()
            logger.warning(f"🚨 Emergency protocol triggered: {protocol_type}")
            return result

        except Exception as e:
            logger.error(f"❌ Emergency protocol trigger failed: {e}")
            return {"success": False, "error": str(e), "protocol_id": None}

    async def get_regional_stats(self, region: str) -> Dict[str, Any]:
        """Get statistics for a specific region in the federation."""

        try:
            params = {"region": region}
            response = await self.client.http_client.get(
                "/api/v1/federation/regional-stats", params=params
            )
            response.raise_for_status()

            return response.json()

        except Exception as e:
            logger.error(f"❌ Failed to get regional stats for {region}: {e}")
            return {
                "region": region,
                "active_nodes": 0,
                "total_nodes": 0,
                "attribution_volume": 0,
                "governance_participation": 0.0,
                "error": str(e),
            }

    def clear_cache(self):
        """Clear all cached federation data."""
        self.node_cache.clear()
        self.metrics_cache.clear()
        logger.info("🧹 Federation cache cleared")
