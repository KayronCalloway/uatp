"""
Capsule Lineage Tree System (CLTS) for UATP Capsule Engine.

This revolutionary module implements comprehensive capsule ancestry tracking,
forking history, remix attribution, and temporal justice for long-term
impact attribution. It addresses the "Plato problem" by providing mathematical
frameworks for residual value attribution to historical contributors.
"""

import logging
import uuid
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from enum import Enum
from typing import Any, Dict, List, Optional

import networkx as nx

from src.audit.events import audit_emitter

logger = logging.getLogger(__name__)


class LineageRelationType(str, Enum):
    """Types of relationships in capsule lineage."""

    PARENT_CHILD = "parent_child"
    FORK = "fork"
    REMIX = "remix"
    MERGE = "merge"
    INSPIRATION = "inspiration"
    CRITIQUE = "critique"
    EXTENSION = "extension"
    TRANSLATION = "translation"
    ADAPTATION = "adaptation"


class TemporalDecayFunction(str, Enum):
    """Functions for temporal value decay."""

    LINEAR = "linear"
    EXPONENTIAL = "exponential"
    LOGARITHMIC = "logarithmic"
    COMPOUND = "compound"
    NONE = "none"


class AttributionReason(str, Enum):
    """Reasons for attribution assignments."""

    DIRECT_CONTRIBUTION = "direct_contribution"
    ANCESTRAL_KNOWLEDGE = "ancestral_knowledge"
    METHODOLOGICAL_FOUNDATION = "methodological_foundation"
    CONCEPTUAL_FRAMEWORK = "conceptual_framework"
    DATA_PROVISION = "data_provision"
    VERIFICATION_ASSISTANCE = "verification_assistance"
    INSPIRATIONAL_SOURCE = "inspirational_source"
    CRITICAL_FEEDBACK = "critical_feedback"


@dataclass
class LineageNode:
    """Individual node in the capsule lineage tree."""

    capsule_id: str
    creator_id: str
    creation_timestamp: datetime

    # Lineage relationships
    parent_capsule_ids: List[str] = field(default_factory=list)
    child_capsule_ids: List[str] = field(default_factory=list)
    fork_source_id: Optional[str] = None
    fork_point: Optional[str] = None  # reasoning_step_id where fork occurred

    # Attribution data
    direct_contributors: List[str] = field(default_factory=list)
    ancestral_contributors: Dict[str, Decimal] = field(
        default_factory=dict
    )  # contributor_id -> attribution_weight
    attribution_reasons: Dict[str, AttributionReason] = field(default_factory=dict)

    # Value and economics
    base_value: Decimal = field(default_factory=lambda: Decimal("0"))
    current_value: Decimal = field(default_factory=lambda: Decimal("0"))
    accumulated_value: Decimal = field(default_factory=lambda: Decimal("0"))
    residual_value_distributed: Decimal = field(default_factory=lambda: Decimal("0"))

    # Temporal data
    last_accessed: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    impact_citations: int = 0
    descendant_count: int = 0
    lineage_depth: int = 0

    # Metadata
    capsule_type: str = "reasoning_trace"
    quality_metrics: Dict[str, float] = field(default_factory=dict)
    ethical_flags: List[str] = field(default_factory=list)

    def calculate_temporal_value(
        self, decay_function: TemporalDecayFunction = TemporalDecayFunction.EXPONENTIAL
    ) -> Decimal:
        """Calculate current value considering temporal decay."""

        age_days = (datetime.now(timezone.utc) - self.creation_timestamp).days
        if age_days == 0:
            return self.base_value

        if decay_function == TemporalDecayFunction.NONE:
            return self.base_value
        elif decay_function == TemporalDecayFunction.LINEAR:
            # Linear decay over 365 days
            decay_factor = max(
                Decimal("0.1"),
                Decimal("1.0") - (Decimal(str(age_days)) / Decimal("365")),
            )
        elif decay_function == TemporalDecayFunction.EXPONENTIAL:
            # Exponential decay with half-life of 90 days
            half_life = Decimal("90")
            decay_factor = Decimal("0.5") ** (Decimal(str(age_days)) / half_life)
        elif decay_function == TemporalDecayFunction.LOGARITHMIC:
            # Logarithmic decay - slower initial decay
            import math

            decay_factor = Decimal("1.0") / (
                Decimal("1.0") + Decimal(str(math.log(age_days + 1)))
            )
        elif decay_function == TemporalDecayFunction.COMPOUND:
            # Compound growth then decay based on citation impact
            if self.impact_citations > 0:
                # Value can actually increase with citations
                citation_multiplier = Decimal("1.0") + (
                    Decimal(str(self.impact_citations)) * Decimal("0.1")
                )
                base_with_citations = self.base_value * citation_multiplier
                # Then apply modest decay
                decay_factor = max(
                    Decimal("0.5"),
                    Decimal("1.0") - (Decimal(str(age_days)) / Decimal("730")),
                )  # 2-year decay
                return base_with_citations * decay_factor
            else:
                decay_factor = max(
                    Decimal("0.1"),
                    Decimal("1.0") - (Decimal(str(age_days)) / Decimal("365")),
                )

        return self.base_value * decay_factor

    def add_citation_impact(self):
        """Record that this capsule was cited/referenced."""
        self.impact_citations += 1
        self.last_accessed = datetime.now(timezone.utc)

    def to_dict(self) -> Dict[str, Any]:
        """Convert lineage node to dictionary."""
        return {
            "capsule_id": self.capsule_id,
            "creator_id": self.creator_id,
            "creation_timestamp": self.creation_timestamp.isoformat(),
            "parent_capsule_ids": self.parent_capsule_ids,
            "child_capsule_ids": self.child_capsule_ids,
            "fork_source_id": self.fork_source_id,
            "fork_point": self.fork_point,
            "direct_contributors": self.direct_contributors,
            "ancestral_contributors": {
                k: float(v) for k, v in self.ancestral_contributors.items()
            },
            "attribution_reasons": {
                k: v.value for k, v in self.attribution_reasons.items()
            },
            "base_value": float(self.base_value),
            "current_value": float(self.current_value),
            "accumulated_value": float(self.accumulated_value),
            "residual_value_distributed": float(self.residual_value_distributed),
            "last_accessed": self.last_accessed.isoformat(),
            "impact_citations": self.impact_citations,
            "descendant_count": self.descendant_count,
            "lineage_depth": self.lineage_depth,
            "capsule_type": self.capsule_type,
            "quality_metrics": self.quality_metrics,
            "ethical_flags": self.ethical_flags,
        }


@dataclass
class LineageRelation:
    """Relationship between capsules in the lineage tree."""

    relation_id: str
    source_capsule_id: str
    target_capsule_id: str
    relation_type: LineageRelationType

    # Relationship metadata
    strength: float = 1.0  # 0.0 to 1.0
    attribution_weight: Decimal = field(default_factory=lambda: Decimal("0"))
    creation_timestamp: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    # Contextual information
    description: str = ""
    evidence: Dict[str, Any] = field(default_factory=dict)
    verification_score: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        """Convert relation to dictionary."""
        return {
            "relation_id": self.relation_id,
            "source_capsule_id": self.source_capsule_id,
            "target_capsule_id": self.target_capsule_id,
            "relation_type": self.relation_type.value,
            "strength": self.strength,
            "attribution_weight": float(self.attribution_weight),
            "creation_timestamp": self.creation_timestamp.isoformat(),
            "description": self.description,
            "evidence": self.evidence,
            "verification_score": self.verification_score,
        }


@dataclass
class TemporalJusticeAssessment:
    """Assessment of temporal justice for long-term attribution."""

    assessment_id: str
    capsule_id: str
    assessment_timestamp: datetime

    # Justice metrics
    total_descendant_value: Decimal
    ancestral_contribution_ratio: Decimal
    temporal_fairness_score: float  # 0.0 to 1.0
    recommended_redistribution: Decimal

    # Detailed analysis
    undercompensated_ancestors: List[str] = field(default_factory=list)
    overcompensated_descendants: List[str] = field(default_factory=list)
    justice_violations: List[str] = field(default_factory=list)

    # Remediation
    proposed_adjustments: Dict[str, Decimal] = field(default_factory=dict)
    redistribution_schedule: Dict[str, datetime] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert assessment to dictionary."""
        return {
            "assessment_id": self.assessment_id,
            "capsule_id": self.capsule_id,
            "assessment_timestamp": self.assessment_timestamp.isoformat(),
            "total_descendant_value": float(self.total_descendant_value),
            "ancestral_contribution_ratio": float(self.ancestral_contribution_ratio),
            "temporal_fairness_score": self.temporal_fairness_score,
            "recommended_redistribution": float(self.recommended_redistribution),
            "undercompensated_ancestors": self.undercompensated_ancestors,
            "overcompensated_descendants": self.overcompensated_descendants,
            "justice_violations": self.justice_violations,
            "proposed_adjustments": {
                k: float(v) for k, v in self.proposed_adjustments.items()
            },
            "redistribution_schedule": {
                k: v.isoformat() for k, v in self.redistribution_schedule.items()
            },
        }


class CapsuleLineageTreeSystem:
    """Comprehensive capsule lineage and temporal justice system."""

    def __init__(self):
        # Core data structures
        self.lineage_nodes: Dict[str, LineageNode] = {}
        self.lineage_relations: Dict[str, LineageRelation] = {}
        self.lineage_graph = nx.DiGraph()

        # Temporal justice tracking
        self.justice_assessments: Dict[str, TemporalJusticeAssessment] = {}
        self.pending_redistributions: Dict[str, Decimal] = defaultdict(
            lambda: Decimal("0")
        )

        # Configuration
        self.config = {
            "default_decay_function": TemporalDecayFunction.EXPONENTIAL,
            "min_attribution_threshold": Decimal("0.001"),
            "max_lineage_depth": 50,
            "justice_assessment_frequency": timedelta(days=30),
            "residual_value_percentage": Decimal("0.15"),  # 15% to ancestors
            "temporal_justice_threshold": 0.7,  # Fairness score threshold
        }

        # Statistics
        self.system_stats = {
            "total_nodes": 0,
            "total_relations": 0,
            "active_lineages": 0,
            "justice_assessments_performed": 0,
            "value_redistributed": Decimal("0"),
            "temporal_violations_detected": 0,
        }

    def generate_node_id(self) -> str:
        """Generate unique lineage node ID."""
        return f"lineage_{uuid.uuid4()}"

    def generate_relation_id(self) -> str:
        """Generate unique relation ID."""
        return f"relation_{uuid.uuid4()}"

    def generate_assessment_id(self) -> str:
        """Generate unique justice assessment ID."""
        return f"justice_{uuid.uuid4()}"

    def register_capsule_node(
        self,
        capsule_id: str,
        creator_id: str,
        capsule_type: str = "reasoning_trace",
        base_value: Decimal = None,
        parent_capsule_ids: List[str] = None,
    ) -> LineageNode:
        """Register new capsule in lineage system."""

        if capsule_id in self.lineage_nodes:
            return self.lineage_nodes[capsule_id]

        parent_capsule_ids = parent_capsule_ids or []
        base_value = base_value or Decimal("100.0")

        # Calculate lineage depth
        lineage_depth = 0
        if parent_capsule_ids:
            parent_depths = [
                self.lineage_nodes[pid].lineage_depth
                for pid in parent_capsule_ids
                if pid in self.lineage_nodes
            ]
            lineage_depth = max(parent_depths) + 1 if parent_depths else 1

        # Create lineage node
        node = LineageNode(
            capsule_id=capsule_id,
            creator_id=creator_id,
            creation_timestamp=datetime.now(timezone.utc),
            parent_capsule_ids=parent_capsule_ids,
            base_value=base_value,
            current_value=base_value,
            lineage_depth=lineage_depth,
            capsule_type=capsule_type,
        )

        # Calculate ancestral contributors
        node.ancestral_contributors = self._calculate_ancestral_attribution(
            parent_capsule_ids
        )

        # Store node
        self.lineage_nodes[capsule_id] = node
        self.lineage_graph.add_node(capsule_id, **node.to_dict())
        self.system_stats["total_nodes"] += 1

        # Add parent relationships
        for parent_id in parent_capsule_ids:
            if parent_id in self.lineage_nodes:
                self.lineage_nodes[parent_id].child_capsule_ids.append(capsule_id)
                self.lineage_nodes[parent_id].descendant_count += 1
                self._create_lineage_relation(
                    parent_id, capsule_id, LineageRelationType.PARENT_CHILD
                )

        audit_emitter.emit_security_event(
            "capsule_lineage_registered",
            {
                "capsule_id": capsule_id,
                "creator_id": creator_id,
                "lineage_depth": lineage_depth,
                "parent_count": len(parent_capsule_ids),
            },
        )

        logger.info(f"Registered capsule lineage node: {capsule_id}")
        return node

    def create_capsule_fork(
        self,
        source_capsule_id: str,
        fork_creator_id: str,
        fork_point: str = None,
        new_capsule_id: str = None,
    ) -> str:
        """Create fork of existing capsule."""

        if source_capsule_id not in self.lineage_nodes:
            raise ValueError(
                f"Source capsule {source_capsule_id} not found in lineage system"
            )

        new_capsule_id = new_capsule_id or f"fork_{uuid.uuid4()}"
        source_node = self.lineage_nodes[source_capsule_id]

        # Create fork node
        fork_node = LineageNode(
            capsule_id=new_capsule_id,
            creator_id=fork_creator_id,
            creation_timestamp=datetime.now(timezone.utc),
            parent_capsule_ids=[source_capsule_id],
            fork_source_id=source_capsule_id,
            fork_point=fork_point,
            base_value=source_node.base_value
            * Decimal("0.8"),  # Reduced base value for forks
            lineage_depth=source_node.lineage_depth + 1,
            capsule_type=source_node.capsule_type,
        )

        # Inherit ancestral contributors with reduced weights
        fork_node.ancestral_contributors = {
            contrib_id: weight * Decimal("0.9")
            for contrib_id, weight in source_node.ancestral_contributors.items()
        }

        # Add original creator as ancestral contributor
        fork_node.ancestral_contributors[source_node.creator_id] = Decimal("0.3")

        # Store fork
        self.lineage_nodes[new_capsule_id] = fork_node
        source_node.child_capsule_ids.append(new_capsule_id)
        source_node.descendant_count += 1

        # Create fork relation
        self._create_lineage_relation(
            source_capsule_id, new_capsule_id, LineageRelationType.FORK
        )

        audit_emitter.emit_security_event(
            "capsule_fork_created",
            {
                "source_capsule_id": source_capsule_id,
                "fork_capsule_id": new_capsule_id,
                "fork_creator_id": fork_creator_id,
                "fork_point": fork_point,
            },
        )

        logger.info(f"Created capsule fork: {source_capsule_id} -> {new_capsule_id}")
        return new_capsule_id

    def create_remix_capsule(
        self,
        source_capsule_ids: List[str],
        remix_creator_id: str,
        attribution_weights: Dict[str, Decimal] = None,
        new_capsule_id: str = None,
    ) -> str:
        """Create remix capsule from multiple sources."""

        new_capsule_id = new_capsule_id or f"remix_{uuid.uuid4()}"
        attribution_weights = attribution_weights or {}

        # Validate source capsules
        for source_id in source_capsule_ids:
            if source_id not in self.lineage_nodes:
                raise ValueError(
                    f"Source capsule {source_id} not found in lineage system"
                )

        # Calculate combined lineage depth and base value
        source_nodes = [self.lineage_nodes[sid] for sid in source_capsule_ids]
        max_depth = max(node.lineage_depth for node in source_nodes)
        combined_value = sum(node.base_value for node in source_nodes) * Decimal(
            "0.6"
        )  # Remix penalty

        # Create remix node
        remix_node = LineageNode(
            capsule_id=new_capsule_id,
            creator_id=remix_creator_id,
            creation_timestamp=datetime.now(timezone.utc),
            parent_capsule_ids=source_capsule_ids,
            base_value=combined_value,
            lineage_depth=max_depth + 1,
            capsule_type="remix_capsule",
        )

        # Calculate complex ancestral attribution
        remix_node.ancestral_contributors = self._calculate_remix_attribution(
            source_nodes, attribution_weights
        )

        # Store remix
        self.lineage_nodes[new_capsule_id] = remix_node

        # Update source nodes
        for source_id in source_capsule_ids:
            source_node = self.lineage_nodes[source_id]
            source_node.child_capsule_ids.append(new_capsule_id)
            source_node.descendant_count += 1

            # Create remix relation
            self._create_lineage_relation(
                source_id, new_capsule_id, LineageRelationType.REMIX
            )

        audit_emitter.emit_security_event(
            "capsule_remix_created",
            {
                "source_capsule_ids": source_capsule_ids,
                "remix_capsule_id": new_capsule_id,
                "remix_creator_id": remix_creator_id,
                "combined_value": float(combined_value),
            },
        )

        logger.info(f"Created remix capsule: {source_capsule_ids} -> {new_capsule_id}")
        return new_capsule_id

    def _calculate_ancestral_attribution(
        self, parent_capsule_ids: List[str]
    ) -> Dict[str, Decimal]:
        """Calculate ancestral contributor weights."""

        ancestral_contributors = {}

        for parent_id in parent_capsule_ids:
            if parent_id not in self.lineage_nodes:
                continue

            parent_node = self.lineage_nodes[parent_id]

            # Direct parent gets attribution
            weight = Decimal("0.2") / len(
                parent_capsule_ids
            )  # Distributed among parents
            ancestral_contributors[parent_node.creator_id] = (
                ancestral_contributors.get(parent_node.creator_id, Decimal("0"))
                + weight
            )

            # Inherit ancestral contributors with decay
            for (
                ancestor_id,
                ancestor_weight,
            ) in parent_node.ancestral_contributors.items():
                decayed_weight = ancestor_weight * Decimal(
                    "0.8"
                )  # 20% decay per generation
                if decayed_weight >= self.config["min_attribution_threshold"]:
                    ancestral_contributors[ancestor_id] = (
                        ancestral_contributors.get(ancestor_id, Decimal("0"))
                        + decayed_weight
                    )

        return ancestral_contributors

    def _calculate_remix_attribution(
        self, source_nodes: List[LineageNode], attribution_weights: Dict[str, Decimal]
    ) -> Dict[str, Decimal]:
        """Calculate complex attribution for remix capsules."""

        remix_attribution = {}
        total_weight = (
            sum(attribution_weights.values())
            if attribution_weights
            else Decimal(str(len(source_nodes)))
        )

        for _i, source_node in enumerate(source_nodes):
            # Get explicit weight or distribute evenly
            node_weight = attribution_weights.get(
                source_node.capsule_id, Decimal("1.0")
            )
            normalized_weight = node_weight / total_weight

            # Direct contributor attribution
            direct_attribution = normalized_weight * Decimal(
                "0.4"
            )  # 40% to direct contributors
            remix_attribution[source_node.creator_id] = (
                remix_attribution.get(source_node.creator_id, Decimal("0"))
                + direct_attribution
            )

            # Ancestral contributor attribution
            ancestral_attribution = normalized_weight * Decimal(
                "0.2"
            )  # 20% to ancestors
            for (
                ancestor_id,
                ancestor_weight,
            ) in source_node.ancestral_contributors.items():
                inherited_weight = ancestral_attribution * ancestor_weight
                if inherited_weight >= self.config["min_attribution_threshold"]:
                    remix_attribution[ancestor_id] = (
                        remix_attribution.get(ancestor_id, Decimal("0"))
                        + inherited_weight
                    )

        return remix_attribution

    def _create_lineage_relation(
        self,
        source_id: str,
        target_id: str,
        relation_type: LineageRelationType,
        strength: float = 1.0,
        attribution_weight: Decimal = None,
    ) -> str:
        """Create relationship between capsules."""

        relation_id = self.generate_relation_id()
        attribution_weight = attribution_weight or Decimal("0.1")

        relation = LineageRelation(
            relation_id=relation_id,
            source_capsule_id=source_id,
            target_capsule_id=target_id,
            relation_type=relation_type,
            strength=strength,
            attribution_weight=attribution_weight,
        )

        self.lineage_relations[relation_id] = relation
        self.lineage_graph.add_edge(source_id, target_id, **relation.to_dict())
        self.system_stats["total_relations"] += 1

        return relation_id

    def assess_temporal_justice(self, capsule_id: str) -> TemporalJusticeAssessment:
        """Assess temporal justice for long-term attribution."""

        if capsule_id not in self.lineage_nodes:
            raise ValueError(f"Capsule {capsule_id} not found in lineage system")

        assessment_id = self.generate_assessment_id()
        node = self.lineage_nodes[capsule_id]

        # Calculate descendant value
        total_descendant_value = self._calculate_descendant_value(capsule_id)

        # Calculate ancestral contribution ratio
        ancestral_total = sum(node.ancestral_contributors.values())
        ancestral_contribution_ratio = ancestral_total

        # Calculate fairness score
        expected_ancestral_share = (
            total_descendant_value * self.config["residual_value_percentage"]
        )
        actual_ancestral_compensation = node.residual_value_distributed

        if expected_ancestral_share > 0:
            compensation_ratio = (
                actual_ancestral_compensation / expected_ancestral_share
            )
            temporal_fairness_score = min(1.0, float(compensation_ratio))
        else:
            temporal_fairness_score = 1.0

        # Identify justice violations
        justice_violations = []
        if temporal_fairness_score < self.config["temporal_justice_threshold"]:
            justice_violations.append("insufficient_ancestral_compensation")

        # Calculate recommended redistribution
        recommended_redistribution = max(
            Decimal("0"), expected_ancestral_share - actual_ancestral_compensation
        )

        # Create assessment
        assessment = TemporalJusticeAssessment(
            assessment_id=assessment_id,
            capsule_id=capsule_id,
            assessment_timestamp=datetime.now(timezone.utc),
            total_descendant_value=total_descendant_value,
            ancestral_contribution_ratio=ancestral_contribution_ratio,
            temporal_fairness_score=temporal_fairness_score,
            recommended_redistribution=recommended_redistribution,
            justice_violations=justice_violations,
        )

        # Store assessment
        self.justice_assessments[assessment_id] = assessment
        self.system_stats["justice_assessments_performed"] += 1

        if justice_violations:
            self.system_stats["temporal_violations_detected"] += 1

        audit_emitter.emit_security_event(
            "temporal_justice_assessed",
            {
                "assessment_id": assessment_id,
                "capsule_id": capsule_id,
                "fairness_score": temporal_fairness_score,
                "violations": len(justice_violations),
                "recommended_redistribution": float(recommended_redistribution),
            },
        )

        logger.info(
            f"Temporal justice assessed for {capsule_id}: score={temporal_fairness_score:.3f}"
        )
        return assessment

    def _calculate_descendant_value(self, capsule_id: str) -> Decimal:
        """Calculate total value generated by descendants."""

        if capsule_id not in self.lineage_nodes:
            return Decimal("0")

        node = self.lineage_nodes[capsule_id]
        total_value = node.accumulated_value

        # Recursively calculate descendant value
        for child_id in node.child_capsule_ids:
            total_value += self._calculate_descendant_value(child_id)

        return total_value

    def execute_temporal_redistribution(self, assessment_id: str) -> Dict[str, Decimal]:
        """Execute temporal justice redistribution."""

        if assessment_id not in self.justice_assessments:
            raise ValueError(f"Justice assessment {assessment_id} not found")

        assessment = self.justice_assessments[assessment_id]
        capsule_id = assessment.capsule_id

        if capsule_id not in self.lineage_nodes:
            raise ValueError(f"Capsule {capsule_id} not found")

        node = self.lineage_nodes[capsule_id]
        redistribution_amounts = {}

        if assessment.recommended_redistribution > 0:
            # Distribute to ancestral contributors proportionally
            total_ancestral_weight = sum(node.ancestral_contributors.values())

            if total_ancestral_weight > 0:
                for ancestor_id, weight in node.ancestral_contributors.items():
                    proportion = weight / total_ancestral_weight
                    amount = assessment.recommended_redistribution * proportion

                    if amount >= self.config["min_attribution_threshold"]:
                        redistribution_amounts[ancestor_id] = amount
                        self.pending_redistributions[ancestor_id] += amount

                # Update node
                node.residual_value_distributed += assessment.recommended_redistribution
                self.system_stats["value_redistributed"] += (
                    assessment.recommended_redistribution
                )

        audit_emitter.emit_security_event(
            "temporal_redistribution_executed",
            {
                "assessment_id": assessment_id,
                "capsule_id": capsule_id,
                "total_redistributed": float(assessment.recommended_redistribution),
                "recipient_count": len(redistribution_amounts),
            },
        )

        logger.info(
            f"Executed temporal redistribution for {capsule_id}: {float(assessment.recommended_redistribution)}"
        )
        return redistribution_amounts

    def get_capsule_lineage_tree(
        self, capsule_id: str, max_depth: int = 10
    ) -> Dict[str, Any]:
        """Get complete lineage tree for capsule."""

        if capsule_id not in self.lineage_nodes:
            raise ValueError(f"Capsule {capsule_id} not found")

        def build_tree(node_id: str, current_depth: int) -> Dict[str, Any]:
            if current_depth >= max_depth or node_id not in self.lineage_nodes:
                return None

            node = self.lineage_nodes[node_id]
            tree_node = {
                "capsule_id": node_id,
                "creator_id": node.creator_id,
                "creation_timestamp": node.creation_timestamp.isoformat(),
                "base_value": float(node.base_value),
                "current_value": float(node.calculate_temporal_value()),
                "lineage_depth": node.lineage_depth,
                "impact_citations": node.impact_citations,
                "descendant_count": node.descendant_count,
                "children": [],
            }

            # Add children
            for child_id in node.child_capsule_ids:
                child_tree = build_tree(child_id, current_depth + 1)
                if child_tree:
                    tree_node["children"].append(child_tree)

            return tree_node

        return build_tree(capsule_id, 0)

    def get_ancestral_path(self, capsule_id: str) -> List[Dict[str, Any]]:
        """Get ancestral path to root capsules."""

        if capsule_id not in self.lineage_nodes:
            return []

        path = []
        visited = set()

        def trace_ancestors(node_id: str):
            if node_id in visited or node_id not in self.lineage_nodes:
                return

            visited.add(node_id)
            node = self.lineage_nodes[node_id]

            path.append(
                {
                    "capsule_id": node_id,
                    "creator_id": node.creator_id,
                    "creation_timestamp": node.creation_timestamp.isoformat(),
                    "lineage_depth": node.lineage_depth,
                    "base_value": float(node.base_value),
                }
            )

            # Trace parents
            for parent_id in node.parent_capsule_ids:
                trace_ancestors(parent_id)

        trace_ancestors(capsule_id)

        # Sort by lineage depth (root first)
        path.sort(key=lambda x: x["lineage_depth"])
        return path

    def get_system_statistics(self) -> Dict[str, Any]:
        """Get comprehensive system statistics."""

        # Calculate additional metrics
        active_lineages = len(
            [node for node in self.lineage_nodes.values() if node.descendant_count > 0]
        )

        avg_lineage_depth = (
            sum(node.lineage_depth for node in self.lineage_nodes.values())
            / len(self.lineage_nodes)
            if self.lineage_nodes
            else 0
        )

        # Value distribution
        total_base_value = sum(node.base_value for node in self.lineage_nodes.values())
        total_current_value = sum(
            node.calculate_temporal_value() for node in self.lineage_nodes.values()
        )

        return {
            "system_stats": self.system_stats,
            "lineage_metrics": {
                "total_nodes": len(self.lineage_nodes),
                "total_relations": len(self.lineage_relations),
                "active_lineages": active_lineages,
                "average_lineage_depth": avg_lineage_depth,
                "max_lineage_depth": max(
                    (node.lineage_depth for node in self.lineage_nodes.values()),
                    default=0,
                ),
            },
            "value_metrics": {
                "total_base_value": float(total_base_value),
                "total_current_value": float(total_current_value),
                "value_distributed": float(self.system_stats["value_redistributed"]),
                "pending_redistributions": float(
                    sum(self.pending_redistributions.values())
                ),
            },
            "justice_metrics": {
                "assessments_performed": self.system_stats[
                    "justice_assessments_performed"
                ],
                "violations_detected": self.system_stats[
                    "temporal_violations_detected"
                ],
                "violation_rate": (
                    self.system_stats["temporal_violations_detected"]
                    / max(1, self.system_stats["justice_assessments_performed"])
                ),
            },
        }


# Global lineage system instance
capsule_lineage_system = CapsuleLineageTreeSystem()


def register_capsule_lineage(
    capsule_id: str,
    creator_id: str,
    parent_capsule_ids: List[str] = None,
    base_value: Decimal = None,
) -> LineageNode:
    """Convenience function to register capsule lineage."""

    return capsule_lineage_system.register_capsule_node(
        capsule_id=capsule_id,
        creator_id=creator_id,
        parent_capsule_ids=parent_capsule_ids or [],
        base_value=base_value,
    )


def create_capsule_fork(
    source_capsule_id: str, fork_creator_id: str, fork_point: str = None
) -> str:
    """Convenience function to create capsule fork."""

    return capsule_lineage_system.create_capsule_fork(
        source_capsule_id=source_capsule_id,
        fork_creator_id=fork_creator_id,
        fork_point=fork_point,
    )


def assess_temporal_justice(capsule_id: str) -> Dict[str, Any]:
    """Convenience function to assess temporal justice."""

    assessment = capsule_lineage_system.assess_temporal_justice(capsule_id)
    return assessment.to_dict()


def get_capsule_ancestry(capsule_id: str) -> Dict[str, Any]:
    """Get comprehensive ancestry information for capsule."""

    lineage_tree = capsule_lineage_system.get_capsule_lineage_tree(capsule_id)
    ancestral_path = capsule_lineage_system.get_ancestral_path(capsule_id)

    if capsule_id in capsule_lineage_system.lineage_nodes:
        node = capsule_lineage_system.lineage_nodes[capsule_id]
        return {
            "capsule_id": capsule_id,
            "lineage_tree": lineage_tree,
            "ancestral_path": ancestral_path,
            "ancestral_contributors": {
                k: float(v) for k, v in node.ancestral_contributors.items()
            },
            "temporal_value": float(node.calculate_temporal_value()),
            "impact_citations": node.impact_citations,
            "descendant_count": node.descendant_count,
        }

    return {"error": "Capsule not found in lineage system"}
