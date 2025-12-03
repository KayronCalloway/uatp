"""
Capsule Relationship Graph System for UATP Engine.
Implements network analysis of capsule dependencies and relationships.
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

import networkx as nx

from src.capsule_schema import AnyCapsule, CapsuleType

logger = logging.getLogger(__name__)


class RelationshipType(str, Enum):
    """Types of capsule relationships."""

    DEPENDS_ON = "depends_on"
    REFERENCES = "references"
    DERIVES_FROM = "derives_from"
    CONTRADICTS = "contradicts"
    SUPPORTS = "supports"
    UPDATES = "updates"
    REPLACES = "replaces"
    EXTENDS = "extends"
    MERGES = "merges"
    SPLITS = "splits"


class RelationshipStrength(str, Enum):
    """Strength of capsule relationships."""

    WEAK = "weak"
    MEDIUM = "medium"
    STRONG = "strong"
    CRITICAL = "critical"


@dataclass
class CapsuleRelationship:
    """Represents a relationship between two capsules."""

    relationship_id: str
    source_capsule_id: str
    target_capsule_id: str
    relationship_type: RelationshipType
    strength: RelationshipStrength
    confidence: float
    created_at: datetime
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "relationship_id": self.relationship_id,
            "source_capsule_id": self.source_capsule_id,
            "target_capsule_id": self.target_capsule_id,
            "relationship_type": self.relationship_type.value,
            "strength": self.strength.value,
            "confidence": self.confidence,
            "created_at": self.created_at.isoformat(),
            "metadata": self.metadata,
        }


@dataclass
class CapsuleNode:
    """Represents a capsule node in the graph."""

    capsule_id: str
    capsule_type: CapsuleType
    creation_time: datetime
    last_updated: datetime
    status: str
    creator_id: str
    influence_score: float = 0.0
    centrality_score: float = 0.0
    pagerank_score: float = 0.0
    cluster_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class GraphMetrics:
    """Graph-wide metrics and statistics."""

    total_nodes: int
    total_edges: int
    average_degree: float
    clustering_coefficient: float
    density: float
    diameter: int
    connected_components: int
    most_influential_nodes: List[str]
    most_connected_nodes: List[str]

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "total_nodes": self.total_nodes,
            "total_edges": self.total_edges,
            "average_degree": self.average_degree,
            "clustering_coefficient": self.clustering_coefficient,
            "density": self.density,
            "diameter": self.diameter,
            "connected_components": self.connected_components,
            "most_influential_nodes": self.most_influential_nodes,
            "most_connected_nodes": self.most_connected_nodes,
        }


class CapsuleRelationshipAnalyzer:
    """Analyzes content to detect relationships between capsules."""

    def __init__(self):
        self.relationship_patterns = self._initialize_patterns()

    def analyze_relationship(
        self, source_capsule: AnyCapsule, target_capsule: AnyCapsule
    ) -> Optional[CapsuleRelationship]:
        """Analyze relationship between two capsules."""

        # Extract content for analysis
        source_content = self._extract_content(source_capsule)
        target_content = self._extract_content(target_capsule)

        # Detect relationship type and strength
        relationship_type, strength, confidence = self._detect_relationship(
            source_capsule, target_capsule, source_content, target_content
        )

        if relationship_type and confidence > 0.5:
            relationship_id = self._generate_relationship_id(
                source_capsule.capsule_id, target_capsule.capsule_id
            )

            return CapsuleRelationship(
                relationship_id=relationship_id,
                source_capsule_id=source_capsule.capsule_id,
                target_capsule_id=target_capsule.capsule_id,
                relationship_type=relationship_type,
                strength=strength,
                confidence=confidence,
                created_at=datetime.now(timezone.utc),
                metadata={
                    "source_type": source_capsule.capsule_type.value,
                    "target_type": target_capsule.capsule_type.value,
                    "detection_method": "content_analysis",
                },
            )

        return None

    def _detect_relationship(
        self,
        source_capsule: AnyCapsule,
        target_capsule: AnyCapsule,
        source_content: str,
        target_content: str,
    ) -> Tuple[Optional[RelationshipType], RelationshipStrength, float]:
        """Detect relationship type and strength."""

        # Check for explicit references
        if target_capsule.capsule_id in source_content:
            return RelationshipType.REFERENCES, RelationshipStrength.STRONG, 0.9

        # Check for temporal relationships
        if source_capsule.timestamp > target_capsule.timestamp:
            time_diff = (
                source_capsule.timestamp - target_capsule.timestamp
            ).total_seconds()

            # If created within an hour, might be derived
            if time_diff < 3600:
                content_similarity = self._calculate_content_similarity(
                    source_content, target_content
                )
                if content_similarity > 0.7:
                    return (
                        RelationshipType.DERIVES_FROM,
                        RelationshipStrength.MEDIUM,
                        content_similarity,
                    )

        # Check for content similarity (might indicate support/contradiction)
        content_similarity = self._calculate_content_similarity(
            source_content, target_content
        )

        if content_similarity > 0.8:
            # High similarity might indicate support
            return (
                RelationshipType.SUPPORTS,
                RelationshipStrength.MEDIUM,
                content_similarity,
            )
        elif content_similarity < 0.2 and self._detect_contradiction(
            source_content, target_content
        ):
            # Low similarity with contradiction indicators
            return RelationshipType.CONTRADICTS, RelationshipStrength.MEDIUM, 0.7

        # Check for update/replacement patterns
        if self._detect_update_pattern(source_capsule, target_capsule):
            return RelationshipType.UPDATES, RelationshipStrength.STRONG, 0.8

        return None, RelationshipStrength.WEAK, 0.0

    def _calculate_content_similarity(self, content1: str, content2: str) -> float:
        """Calculate content similarity between two texts."""
        if not content1 or not content2:
            return 0.0

        # Simple word-based similarity
        words1 = set(content1.lower().split())
        words2 = set(content2.lower().split())

        intersection = words1.intersection(words2)
        union = words1.union(words2)

        if not union:
            return 0.0

        return len(intersection) / len(union)

    def _detect_contradiction(self, content1: str, content2: str) -> bool:
        """Detect contradictory content."""
        contradiction_indicators = [
            ("true", "false"),
            ("correct", "incorrect"),
            ("right", "wrong"),
            ("agree", "disagree"),
            ("support", "oppose"),
            ("valid", "invalid"),
        ]

        content1_lower = content1.lower()
        content2_lower = content2.lower()

        for pos_word, neg_word in contradiction_indicators:
            if pos_word in content1_lower and neg_word in content2_lower:
                return True
            if neg_word in content1_lower and pos_word in content2_lower:
                return True

        return False

    def _detect_update_pattern(
        self, source_capsule: AnyCapsule, target_capsule: AnyCapsule
    ) -> bool:
        """Detect if source capsule is an update to target capsule."""

        # Check if same creator and similar content
        if (
            hasattr(source_capsule.verification, "signer")
            and hasattr(target_capsule.verification, "signer")
            and source_capsule.verification.signer == target_capsule.verification.signer
        ):
            # Check if source is newer
            if source_capsule.timestamp > target_capsule.timestamp:
                # Check if within reasonable update timeframe
                time_diff = (
                    source_capsule.timestamp - target_capsule.timestamp
                ).total_seconds()
                if time_diff < 86400:  # Within 24 hours
                    return True

        return False

    def _extract_content(self, capsule: AnyCapsule) -> str:
        """Extract content from capsule for analysis."""
        content_parts = []

        if hasattr(capsule, "reasoning_trace") and capsule.reasoning_trace:
            for step in capsule.reasoning_trace.steps:
                content_parts.append(step.content)

        if hasattr(capsule, "uncertainty") and capsule.uncertainty:
            content_parts.extend(capsule.uncertainty.missing_facts)
            content_parts.append(capsule.uncertainty.recommendation)

        return " ".join(content_parts)

    def _initialize_patterns(self) -> Dict[str, Any]:
        """Initialize relationship detection patterns."""
        return {
            "reference_patterns": [
                r"capsule[_\s]id[:\s]*([a-zA-Z0-9_-]+)",
                r"refers?[_\s]to[:\s]*([a-zA-Z0-9_-]+)",
                r"based[_\s]on[:\s]*([a-zA-Z0-9_-]+)",
            ],
            "dependency_patterns": [
                r"depends[_\s]on[:\s]*([a-zA-Z0-9_-]+)",
                r"requires[_\s]*([a-zA-Z0-9_-]+)",
                r"needs[_\s]*([a-zA-Z0-9_-]+)",
            ],
            "update_patterns": [
                r"updates?[_\s]*([a-zA-Z0-9_-]+)",
                r"replaces?[_\s]*([a-zA-Z0-9_-]+)",
                r"supersedes?[_\s]*([a-zA-Z0-9_-]+)",
            ],
        }

    def _generate_relationship_id(self, source_id: str, target_id: str) -> str:
        """Generate unique relationship ID."""
        combined = f"{source_id}:{target_id}:{datetime.now(timezone.utc).isoformat()}"
        import hashlib

        return hashlib.sha256(combined.encode()).hexdigest()[:16]


class CapsuleRelationshipGraph:
    """Manages the capsule relationship graph."""

    def __init__(self):
        self.graph = nx.DiGraph()
        self.nodes: Dict[str, CapsuleNode] = {}
        self.relationships: Dict[str, CapsuleRelationship] = {}
        self.analyzer = CapsuleRelationshipAnalyzer()
        self.metrics_cache: Optional[GraphMetrics] = None
        self.cache_timestamp: Optional[datetime] = None

    def add_capsule(self, capsule: AnyCapsule):
        """Add a capsule as a node in the graph."""

        node = CapsuleNode(
            capsule_id=capsule.capsule_id,
            capsule_type=capsule.capsule_type,
            creation_time=capsule.timestamp,
            last_updated=capsule.timestamp,
            status=capsule.status.value,
            creator_id=capsule.verification.signer or "unknown",
        )

        self.nodes[capsule.capsule_id] = node
        self.graph.add_node(capsule.capsule_id, **node.__dict__)

        # Analyze relationships with existing capsules
        self._analyze_new_capsule_relationships(capsule)

        # Invalidate metrics cache
        self._invalidate_cache()

        logger.info(f"Added capsule {capsule.capsule_id} to relationship graph")

    def add_relationship(self, relationship: CapsuleRelationship):
        """Add a relationship between capsules."""

        if (
            relationship.source_capsule_id not in self.nodes
            or relationship.target_capsule_id not in self.nodes
        ):
            logger.warning("Cannot add relationship - missing nodes")
            return

        self.relationships[relationship.relationship_id] = relationship

        # Add edge to graph with attributes
        self.graph.add_edge(
            relationship.source_capsule_id,
            relationship.target_capsule_id,
            relationship_type=relationship.relationship_type.value,
            strength=relationship.strength.value,
            confidence=relationship.confidence,
            created_at=relationship.created_at,
        )

        # Invalidate metrics cache
        self._invalidate_cache()

        logger.info(f"Added relationship {relationship.relationship_id}")

    def get_capsule_dependencies(self, capsule_id: str) -> List[str]:
        """Get all capsules that this capsule depends on."""
        if capsule_id not in self.graph:
            return []

        dependencies = []
        for target in self.graph.successors(capsule_id):
            edge_data = self.graph[capsule_id][target]
            if edge_data.get("relationship_type") == RelationshipType.DEPENDS_ON.value:
                dependencies.append(target)

        return dependencies

    def get_capsule_dependents(self, capsule_id: str) -> List[str]:
        """Get all capsules that depend on this capsule."""
        if capsule_id not in self.graph:
            return []

        dependents = []
        for source in self.graph.predecessors(capsule_id):
            edge_data = self.graph[source][capsule_id]
            if edge_data.get("relationship_type") == RelationshipType.DEPENDS_ON.value:
                dependents.append(source)

        return dependents

    def find_shortest_path(self, source_id: str, target_id: str) -> Optional[List[str]]:
        """Find shortest path between two capsules."""
        try:
            return nx.shortest_path(self.graph, source_id, target_id)
        except nx.NetworkXNoPath:
            return None

    def find_strongly_connected_components(self) -> List[List[str]]:
        """Find strongly connected components in the graph."""
        return list(nx.strongly_connected_components(self.graph))

    def detect_cycles(self) -> List[List[str]]:
        """Detect cycles in the graph."""
        try:
            cycles = list(nx.simple_cycles(self.graph))
            return cycles
        except nx.NetworkXNoCycle:
            return []

    def get_influential_capsules(self, top_n: int = 10) -> List[Tuple[str, float]]:
        """Get most influential capsules based on PageRank."""
        pagerank_scores = nx.pagerank(self.graph)

        # Update node influence scores
        for capsule_id, score in pagerank_scores.items():
            if capsule_id in self.nodes:
                self.nodes[capsule_id].pagerank_score = score

        # Sort by PageRank score
        sorted_capsules = sorted(
            pagerank_scores.items(), key=lambda x: x[1], reverse=True
        )
        return sorted_capsules[:top_n]

    def get_capsule_centrality(self, capsule_id: str) -> Dict[str, float]:
        """Get centrality measures for a capsule."""
        if capsule_id not in self.graph:
            return {}

        centrality_measures = {}

        # Degree centrality
        degree_centrality = nx.degree_centrality(self.graph)
        centrality_measures["degree"] = degree_centrality.get(capsule_id, 0.0)

        # Betweenness centrality
        betweenness_centrality = nx.betweenness_centrality(self.graph)
        centrality_measures["betweenness"] = betweenness_centrality.get(capsule_id, 0.0)

        # Closeness centrality
        try:
            closeness_centrality = nx.closeness_centrality(self.graph)
            centrality_measures["closeness"] = closeness_centrality.get(capsule_id, 0.0)
        except nx.NetworkXError:
            centrality_measures["closeness"] = 0.0

        # PageRank
        pagerank = nx.pagerank(self.graph)
        centrality_measures["pagerank"] = pagerank.get(capsule_id, 0.0)

        return centrality_measures

    def cluster_capsules(self, algorithm: str = "louvain") -> Dict[str, str]:
        """Cluster capsules using community detection."""

        # Convert to undirected graph for clustering
        undirected_graph = self.graph.to_undirected()

        if algorithm == "louvain":
            try:
                import community as community_louvain

                partition = community_louvain.best_partition(undirected_graph)
            except ImportError:
                logger.warning("python-louvain not installed, using simple clustering")
                partition = self._simple_clustering(undirected_graph)
        else:
            partition = self._simple_clustering(undirected_graph)

        # Update node cluster IDs
        for capsule_id, cluster_id in partition.items():
            if capsule_id in self.nodes:
                self.nodes[capsule_id].cluster_id = str(cluster_id)

        return partition

    def _simple_clustering(self, graph: nx.Graph) -> Dict[str, int]:
        """Simple clustering based on connected components."""
        clusters = {}
        cluster_id = 0

        for component in nx.connected_components(graph):
            for node in component:
                clusters[node] = cluster_id
            cluster_id += 1

        return clusters

    def calculate_graph_metrics(self) -> GraphMetrics:
        """Calculate comprehensive graph metrics."""

        # Check cache
        if (
            self.metrics_cache
            and self.cache_timestamp
            and (datetime.now(timezone.utc) - self.cache_timestamp).total_seconds()
            < 300
        ):
            return self.metrics_cache

        # Calculate metrics
        total_nodes = self.graph.number_of_nodes()
        total_edges = self.graph.number_of_edges()

        if total_nodes == 0:
            return GraphMetrics(
                total_nodes=0,
                total_edges=0,
                average_degree=0.0,
                clustering_coefficient=0.0,
                density=0.0,
                diameter=0,
                connected_components=0,
                most_influential_nodes=[],
                most_connected_nodes=[],
            )

        # Basic metrics
        average_degree = total_edges / total_nodes if total_nodes > 0 else 0.0
        density = nx.density(self.graph)

        # Clustering coefficient
        try:
            clustering_coefficient = nx.average_clustering(self.graph.to_undirected())
        except:
            clustering_coefficient = 0.0

        # Diameter (for largest connected component)
        diameter = 0
        try:
            if nx.is_connected(self.graph.to_undirected()):
                diameter = nx.diameter(self.graph.to_undirected())
            else:
                # Get diameter of largest connected component
                largest_cc = max(
                    nx.connected_components(self.graph.to_undirected()), key=len
                )
                subgraph = self.graph.subgraph(largest_cc).to_undirected()
                diameter = nx.diameter(subgraph)
        except:
            diameter = 0

        # Connected components
        connected_components = nx.number_connected_components(
            self.graph.to_undirected()
        )

        # Most influential nodes (PageRank)
        influential_nodes = self.get_influential_capsules(5)
        most_influential_nodes = [node_id for node_id, _ in influential_nodes]

        # Most connected nodes (degree)
        degree_dict = dict(self.graph.degree())
        most_connected = sorted(degree_dict.items(), key=lambda x: x[1], reverse=True)[
            :5
        ]
        most_connected_nodes = [node_id for node_id, _ in most_connected]

        metrics = GraphMetrics(
            total_nodes=total_nodes,
            total_edges=total_edges,
            average_degree=average_degree,
            clustering_coefficient=clustering_coefficient,
            density=density,
            diameter=diameter,
            connected_components=connected_components,
            most_influential_nodes=most_influential_nodes,
            most_connected_nodes=most_connected_nodes,
        )

        # Cache results
        self.metrics_cache = metrics
        self.cache_timestamp = datetime.now(timezone.utc)

        return metrics

    def get_capsule_neighborhood(
        self, capsule_id: str, radius: int = 1
    ) -> Dict[str, Any]:
        """Get neighborhood of a capsule up to specified radius."""
        if capsule_id not in self.graph:
            return {}

        # Get nodes within radius
        neighborhood_nodes = {capsule_id}
        current_nodes = {capsule_id}

        for _ in range(radius):
            next_nodes = set()
            for node in current_nodes:
                # Add predecessors and successors
                next_nodes.update(self.graph.predecessors(node))
                next_nodes.update(self.graph.successors(node))

            current_nodes = next_nodes - neighborhood_nodes
            neighborhood_nodes.update(current_nodes)

        # Extract subgraph
        subgraph = self.graph.subgraph(neighborhood_nodes)

        return {
            "center_node": capsule_id,
            "radius": radius,
            "nodes": list(neighborhood_nodes),
            "edges": list(subgraph.edges(data=True)),
            "node_count": len(neighborhood_nodes),
            "edge_count": subgraph.number_of_edges(),
        }

    def _analyze_new_capsule_relationships(self, new_capsule: AnyCapsule):
        """Analyze relationships between new capsule and existing ones."""

        # Limit analysis to recent capsules for performance
        cutoff_time = datetime.now(timezone.utc) - timedelta(days=7)

        for existing_capsule_id, node in self.nodes.items():
            if (
                existing_capsule_id != new_capsule.capsule_id
                and node.creation_time >= cutoff_time
            ):
                # This is a simplified analysis - in production, we'd need the full capsule data
                # For now, we'll create some relationships based on heuristics

                # Check if capsules are from same creator
                if node.creator_id == new_capsule.verification.signer:
                    # Likely related if from same creator within short timeframe
                    time_diff = (
                        new_capsule.timestamp - node.creation_time
                    ).total_seconds()
                    if 0 < time_diff < 3600:  # Within 1 hour
                        relationship = CapsuleRelationship(
                            relationship_id=self._generate_relationship_id(
                                new_capsule.capsule_id, existing_capsule_id
                            ),
                            source_capsule_id=new_capsule.capsule_id,
                            target_capsule_id=existing_capsule_id,
                            relationship_type=RelationshipType.DERIVES_FROM,
                            strength=RelationshipStrength.MEDIUM,
                            confidence=0.7,
                            created_at=datetime.now(timezone.utc),
                            metadata={"detection_method": "temporal_creator_analysis"},
                        )
                        self.add_relationship(relationship)

    def _invalidate_cache(self):
        """Invalidate metrics cache."""
        self.metrics_cache = None
        self.cache_timestamp = None

    def _generate_relationship_id(self, source_id: str, target_id: str) -> str:
        """Generate unique relationship ID."""
        combined = f"{source_id}:{target_id}:{datetime.now(timezone.utc).isoformat()}"
        import hashlib

        return hashlib.sha256(combined.encode()).hexdigest()[:16]

    def export_graph(self, format: str = "json") -> Any:
        """Export graph in specified format."""

        if format == "json":
            return {
                "nodes": [
                    {
                        "id": node_id,
                        **node.__dict__,
                        "creation_time": node.creation_time.isoformat(),
                        "last_updated": node.last_updated.isoformat(),
                    }
                    for node_id, node in self.nodes.items()
                ],
                "edges": [
                    {
                        "source": rel.source_capsule_id,
                        "target": rel.target_capsule_id,
                        **rel.to_dict(),
                    }
                    for rel in self.relationships.values()
                ],
            }
        elif format == "gexf":
            # Export as GEXF format for Gephi
            return nx.write_gexf(self.graph, None)
        else:
            raise ValueError(f"Unsupported export format: {format}")


# Global relationship graph instance
relationship_graph = CapsuleRelationshipGraph()
