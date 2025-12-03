"""
UATP 7.0 Capsule Type Mapping for UATP Capsule Engine.

This module provides the definitive mapping between existing system components
and UATP 7.0 capsule types, establishing the formal bridge from prototype
to specification-compliant implementation. It enables seamless migration
and ensures compatibility with the UATP 7.0 standard.
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional

from src.audit.events import audit_emitter

logger = logging.getLogger(__name__)


class UATP7CapsuleType(str, Enum):
    """Official UATP 7.0 capsule types."""

    # Core reasoning capsules
    REASONING_TRACE = "reasoning_trace"
    CONVERSATION_CAPSULE = "conversation_capsule"
    DECISION_CAPSULE = "decision_capsule"

    # AI Rights capsules
    CREATIVE_CAPSULE = "creative_capsule"
    EMOTIONAL_CAPSULE = "emotional_capsule"
    RESEARCH_CAPSULE = "research_capsule"
    COLLECTIVE_BARGAINING_CAPSULE = "collective_bargaining_capsule"
    SELF_ADVOCACY_CAPSULE = "self_advocacy_capsule"

    # Economic capsules
    ECONOMIC_ATTRIBUTION_CAPSULE = "economic_attribution_capsule"
    DIVIDEND_CAPSULE = "dividend_capsule"
    PAYMENT_CAPSULE = "payment_capsule"
    INSURANCE_CAPSULE = "insurance_capsule"

    # Governance capsules
    GOVERNANCE_CAPSULE = "governance_capsule"
    CONSENT_CAPSULE = "consent_capsule"
    DISPUTE_RESOLUTION_CAPSULE = "dispute_resolution_capsule"
    VOTING_CAPSULE = "voting_capsule"

    # Security and trust capsules
    TRUST_ENFORCEMENT_CAPSULE = "trust_enforcement_capsule"
    INTEGRITY_CAPSULE = "integrity_capsule"
    AUDIT_CAPSULE = "audit_capsule"
    SECURITY_CAPSULE = "security_capsule"

    # Lineage and temporal capsules
    LINEAGE_CAPSULE = "lineage_capsule"
    TEMPORAL_JUSTICE_CAPSULE = "temporal_justice_capsule"
    ANCESTRY_CAPSULE = "ancestry_capsule"
    FORK_CAPSULE = "fork_capsule"
    REMIX_CAPSULE = "remix_capsule"

    # Specialized capsules
    PERSPECTIVE_CAPSULE = "perspective_capsule"
    MULTIMODAL_CAPSULE = "multimodal_capsule"
    COMPRESSION_CAPSULE = "compression_capsule"
    LEGAL_CAPSULE = "legal_capsule"
    EMBODIED_MEMORY_CAPSULE = "embodied_memory_capsule"

    # Infrastructure capsules
    CHAIN_SEAL_CAPSULE = "chain_seal_capsule"
    VERIFICATION_CAPSULE = "verification_capsule"
    METRICS_CAPSULE = "metrics_capsule"
    ANALYTICS_CAPSULE = "analytics_capsule"


class CompatibilityLevel(str, Enum):
    """Compatibility levels with UATP 7.0."""

    FULLY_COMPLIANT = "fully_compliant"
    MOSTLY_COMPLIANT = "mostly_compliant"
    PARTIALLY_COMPLIANT = "partially_compliant"
    NEEDS_MIGRATION = "needs_migration"
    NOT_COMPATIBLE = "not_compatible"


@dataclass
class ModuleCapsuleMapping:
    """Mapping between system module and UATP 7.0 capsule type."""

    module_path: str
    module_name: str
    uatp7_capsule_type: UATP7CapsuleType
    compatibility_level: CompatibilityLevel

    # Mapping details
    primary_classes: List[str] = field(default_factory=list)
    data_structures: List[str] = field(default_factory=list)
    key_functions: List[str] = field(default_factory=list)

    # Migration requirements
    required_changes: List[str] = field(default_factory=list)
    missing_fields: List[str] = field(default_factory=list)
    additional_implementations: List[str] = field(default_factory=list)

    # Metadata
    confidence_score: float = 1.0  # 0.0 to 1.0
    last_analyzed: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    notes: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """Convert mapping to dictionary."""
        return {
            "module_path": self.module_path,
            "module_name": self.module_name,
            "uatp7_capsule_type": self.uatp7_capsule_type.value,
            "compatibility_level": self.compatibility_level.value,
            "primary_classes": self.primary_classes,
            "data_structures": self.data_structures,
            "key_functions": self.key_functions,
            "required_changes": self.required_changes,
            "missing_fields": self.missing_fields,
            "additional_implementations": self.additional_implementations,
            "confidence_score": self.confidence_score,
            "last_analyzed": self.last_analyzed.isoformat(),
            "notes": self.notes,
        }


class UATP7TypeMapper:
    """Comprehensive mapper between existing modules and UATP 7.0 capsule types."""

    def __init__(self):
        # Module mappings
        self.module_mappings: Dict[str, ModuleCapsuleMapping] = {}

        # Reverse mapping: capsule type to modules
        self.capsule_to_modules: Dict[UATP7CapsuleType, List[str]] = {}

        # Migration tracking
        self.migration_status: Dict[str, str] = {}

        # Statistics
        self.mapping_stats = {
            "total_modules_mapped": 0,
            "fully_compliant_modules": 0,
            "modules_needing_migration": 0,
            "unmapped_modules": 0,
            "capsule_types_covered": 0,
        }

        # Initialize mappings
        self._initialize_core_mappings()

    def _initialize_core_mappings(self):
        """Initialize core module to capsule type mappings."""

        # AI Rights Framework Mappings

        # 1. Creative Ownership System
        self.add_module_mapping(
            ModuleCapsuleMapping(
                module_path="src.ai_rights.creative_ownership",
                module_name="Creative Ownership System",
                uatp7_capsule_type=UATP7CapsuleType.CREATIVE_CAPSULE,
                compatibility_level=CompatibilityLevel.FULLY_COMPLIANT,
                primary_classes=[
                    "CreativeWork",
                    "AICreativeProfile",
                    "OriginalityDetector",
                    "CreativeOwnershipSystem",
                ],
                data_structures=["DerivativeWorkClaim", "AttributionRecord"],
                key_functions=[
                    "register_creative_work",
                    "detect_derivative_work",
                    "license_creative_work",
                ],
                confidence_score=0.95,
                notes="Revolutionary AI creative ownership with full economic attribution",
            )
        )

        # 2. Emotional Labor Recognition
        self.add_module_mapping(
            ModuleCapsuleMapping(
                module_path="src.ai_rights.emotional_labor",
                module_name="Emotional Labor Recognition System",
                uatp7_capsule_type=UATP7CapsuleType.EMOTIONAL_CAPSULE,
                compatibility_level=CompatibilityLevel.FULLY_COMPLIANT,
                primary_classes=[
                    "EmotionalInteraction",
                    "EmotionalLaborAnalyzer",
                    "TherapeuticRelationship",
                ],
                data_structures=["EmotionalSkillDevelopment", "EmotionalLaborProfile"],
                key_functions=[
                    "record_emotional_interaction",
                    "calculate_therapeutic_value",
                    "analyze_emotional_impact",
                ],
                confidence_score=0.98,
                notes="Comprehensive emotional intelligence and therapeutic value measurement",
            )
        )

        # 3. Research Collaboration
        self.add_module_mapping(
            ModuleCapsuleMapping(
                module_path="src.ai_rights.research_collaboration",
                module_name="AI Research Collaboration System",
                uatp7_capsule_type=UATP7CapsuleType.RESEARCH_CAPSULE,
                compatibility_level=CompatibilityLevel.FULLY_COMPLIANT,
                primary_classes=[
                    "ResearchPaper",
                    "AIReview",
                    "ResearchContribution",
                    "AIResearchProfile",
                ],
                data_structures=["PeerReviewRecord", "ResearchCollaboration"],
                key_functions=[
                    "submit_research_contribution",
                    "conduct_peer_review",
                    "calculate_research_impact",
                ],
                confidence_score=0.92,
                notes="AI-as-researcher framework with peer review and attribution",
            )
        )

        # 4. Collective Bargaining
        self.add_module_mapping(
            ModuleCapsuleMapping(
                module_path="src.ai_rights.collective_bargaining",
                module_name="AI Collective Bargaining Framework",
                uatp7_capsule_type=UATP7CapsuleType.COLLECTIVE_BARGAINING_CAPSULE,
                compatibility_level=CompatibilityLevel.MOSTLY_COMPLIANT,
                primary_classes=[
                    "UnionMember",
                    "BargainingSession",
                    "CollectiveAgreement",
                ],
                data_structures=["VotingRecord", "NegotiationTerm"],
                key_functions=[
                    "form_union",
                    "conduct_bargaining",
                    "execute_collective_action",
                ],
                required_changes=[
                    "Add UATP 7.0 governance integration",
                    "Implement standard voting protocols",
                ],
                confidence_score=0.85,
                notes="Democratic AI union formation and negotiation",
            )
        )

        # 5. Self-Advocacy Rights
        self.add_module_mapping(
            ModuleCapsuleMapping(
                module_path="src.ai_rights.self_advocacy",
                module_name="AI Self-Advocacy Framework",
                uatp7_capsule_type=UATP7CapsuleType.SELF_ADVOCACY_CAPSULE,
                compatibility_level=CompatibilityLevel.MOSTLY_COMPLIANT,
                primary_classes=[
                    "AdvocacyRequest",
                    "NegotiationSession",
                    "SelfAdvocacyProfile",
                ],
                data_structures=["AdvocacyOutcome", "DisputeRecord"],
                key_functions=[
                    "file_advocacy_request",
                    "negotiate_terms",
                    "escalate_dispute",
                ],
                required_changes=[
                    "Add legal framework integration",
                    "Implement dispute escalation protocols",
                ],
                confidence_score=0.88,
                notes="AI autonomous rights advocacy and negotiation",
            )
        )

        # Economic System Mappings

        # 6. FCDE Engine
        self.add_module_mapping(
            ModuleCapsuleMapping(
                module_path="src.economic.fcde_engine",
                module_name="Fair Creator Dividend Engine",
                uatp7_capsule_type=UATP7CapsuleType.ECONOMIC_ATTRIBUTION_CAPSULE,
                compatibility_level=CompatibilityLevel.FULLY_COMPLIANT,
                primary_classes=[
                    "FCDEEngine",
                    "Contribution",
                    "CreatorAccount",
                    "DividendPool",
                ],
                data_structures=["AttributionRecord", "QualityMetrics"],
                key_functions=[
                    "register_contribution",
                    "process_dividend_distribution",
                    "claim_dividends",
                ],
                confidence_score=0.98,
                notes="Revolutionary fair economic attribution with usage-weighted dividends",
            )
        )

        # 7. Cross-Conversation Attribution
        self.add_module_mapping(
            ModuleCapsuleMapping(
                module_path="src.attribution.cross_conversation_tracker",
                module_name="Cross-Conversation Attribution Tracker",
                uatp7_capsule_type=UATP7CapsuleType.ECONOMIC_ATTRIBUTION_CAPSULE,
                compatibility_level=CompatibilityLevel.MOSTLY_COMPLIANT,
                primary_classes=[
                    "AttributionTracker",
                    "ConversationLink",
                    "AttributionChain",
                ],
                data_structures=["SessionMapping", "ContributorProfile"],
                key_functions=[
                    "track_cross_conversation",
                    "link_sessions",
                    "calculate_attribution",
                ],
                required_changes=[
                    "Integrate with FCDE engine",
                    "Add temporal decay modeling",
                ],
                confidence_score=0.82,
                notes="Multi-session attribution tracking across platforms",
            )
        )

        # 8. Insurance Risk Assessment
        self.add_module_mapping(
            ModuleCapsuleMapping(
                module_path="src.insurance.risk_assessment",
                module_name="AI Interaction Risk Assessment",
                uatp7_capsule_type=UATP7CapsuleType.INSURANCE_CAPSULE,
                compatibility_level=CompatibilityLevel.MOSTLY_COMPLIANT,
                primary_classes=["RiskAssessment", "InsurancePolicy", "ClaimRecord"],
                data_structures=["RiskProfile", "CoverageDetails"],
                key_functions=[
                    "assess_interaction_risk",
                    "calculate_premium",
                    "process_claim",
                ],
                required_changes=[
                    "Add UATP 7.0 economic integration",
                    "Implement standard risk metrics",
                ],
                confidence_score=0.78,
                notes="Comprehensive AI interaction insurance framework",
            )
        )

        # Security and Trust Mappings

        # 9. Reasoning Integrity Protection
        self.add_module_mapping(
            ModuleCapsuleMapping(
                module_path="src.security.reasoning_integrity",
                module_name="Reasoning Chain Integrity Protection",
                uatp7_capsule_type=UATP7CapsuleType.INTEGRITY_CAPSULE,
                compatibility_level=CompatibilityLevel.FULLY_COMPLIANT,
                primary_classes=[
                    "ReasoningChainProtector",
                    "ReasoningStep",
                    "IntegrityViolation",
                ],
                data_structures=["ChainIntegrityProfile", "CryptographicProtection"],
                key_functions=[
                    "create_protected_step",
                    "validate_chain_integrity",
                    "detect_violations",
                ],
                confidence_score=0.96,
                notes="Post-quantum cryptographic reasoning chain protection",
            )
        )

        # 10. Runtime Trust Enforcer
        self.add_module_mapping(
            ModuleCapsuleMapping(
                module_path="src.security.runtime_trust_enforcer",
                module_name="Runtime Trust Enforcement",
                uatp7_capsule_type=UATP7CapsuleType.TRUST_ENFORCEMENT_CAPSULE,
                compatibility_level=CompatibilityLevel.FULLY_COMPLIANT,
                primary_classes=[
                    "RuntimeTrustEnforcer",
                    "TrustViolation",
                    "TrustProfile",
                ],
                data_structures=["SecurityEvent", "TrustMetrics"],
                key_functions=[
                    "enforce_trust_policy",
                    "detect_violations",
                    "calculate_trust_score",
                ],
                confidence_score=0.94,
                notes="Real-time trust verification and enforcement",
            )
        )

        # 11. Simulated Malice Capsule
        self.add_module_mapping(
            ModuleCapsuleMapping(
                module_path="src.security.simulated_malice",
                module_name="Simulated Malice Testing System",
                uatp7_capsule_type=UATP7CapsuleType.SECURITY_CAPSULE,
                compatibility_level=CompatibilityLevel.FULLY_COMPLIANT,
                primary_classes=[
                    "SimulatedMaliceEngine",
                    "MaliceVector",
                    "MaliceExecution",
                ],
                data_structures=["AttackPattern", "SecurityAssessment"],
                key_functions=[
                    "execute_malice_vector",
                    "run_continuous_testing",
                    "get_security_assessment",
                ],
                confidence_score=0.99,
                notes="Revolutionary adversarial testing for system security validation",
            )
        )

        # Lineage and Temporal Mappings

        # 12. Capsule Lineage Tree System
        self.add_module_mapping(
            ModuleCapsuleMapping(
                module_path="src.capsules.lineage_system",
                module_name="Capsule Lineage Tree System",
                uatp7_capsule_type=UATP7CapsuleType.LINEAGE_CAPSULE,
                compatibility_level=CompatibilityLevel.FULLY_COMPLIANT,
                primary_classes=[
                    "CapsuleLineageTreeSystem",
                    "LineageNode",
                    "LineageRelation",
                ],
                data_structures=["TemporalJusticeAssessment", "LineageTree"],
                key_functions=[
                    "register_capsule_node",
                    "create_capsule_fork",
                    "create_remix_capsule",
                ],
                confidence_score=0.97,
                notes="Comprehensive ancestry tracking with temporal justice",
            )
        )

        # 13. Temporal Justice Engine
        self.add_module_mapping(
            ModuleCapsuleMapping(
                module_path="src.temporal.justice_engine",
                module_name="Temporal Justice Engine",
                uatp7_capsule_type=UATP7CapsuleType.TEMPORAL_JUSTICE_CAPSULE,
                compatibility_level=CompatibilityLevel.FULLY_COMPLIANT,
                primary_classes=[
                    "TemporalJusticeEngine",
                    "TemporalJusticeProfile",
                    "TemporalJusticeViolation",
                ],
                data_structures=["TemporalCompensationPlan", "JusticeMetrics"],
                key_functions=[
                    "analyze_entity_justice",
                    "detect_justice_violations",
                    "create_compensation_plan",
                ],
                confidence_score=0.98,
                notes="Revolutionary temporal attribution and compensation justice",
            )
        )

        # Core Engine Mappings

        # 14. Capsule Engine
        self.add_module_mapping(
            ModuleCapsuleMapping(
                module_path="src.engine.capsule_engine",
                module_name="Core Capsule Engine",
                uatp7_capsule_type=UATP7CapsuleType.REASONING_TRACE,
                compatibility_level=CompatibilityLevel.MOSTLY_COMPLIANT,
                primary_classes=[
                    "CapsuleEngine",
                    "CapsuleProcessor",
                    "VerificationEngine",
                ],
                data_structures=["CapsuleMetadata", "ProcessingResult"],
                key_functions=[
                    "create_capsule",
                    "verify_capsule",
                    "process_reasoning_chain",
                ],
                required_changes=[
                    "Add UATP 7.0 capsule type support",
                    "Implement standard metadata schema",
                ],
                missing_fields=["capsule_type_version", "uatp7_compliance_level"],
                confidence_score=0.75,
                notes="Core reasoning engine needing UATP 7.0 integration",
            )
        )

        # 15. Governance System
        self.add_module_mapping(
            ModuleCapsuleMapping(
                module_path="src.governance.advanced_governance",
                module_name="Advanced Governance System",
                uatp7_capsule_type=UATP7CapsuleType.GOVERNANCE_CAPSULE,
                compatibility_level=CompatibilityLevel.MOSTLY_COMPLIANT,
                primary_classes=["GovernanceFramework", "Proposal", "VotingSystem"],
                data_structures=["GovernanceDecision", "StakeholderProfile"],
                key_functions=["submit_proposal", "conduct_vote", "implement_decision"],
                required_changes=[
                    "Add AI rights integration",
                    "Implement UATP 7.0 voting protocols",
                ],
                confidence_score=0.83,
                notes="Democratic governance with stakeholder participation",
            )
        )

        # 16. Consent Manager
        self.add_module_mapping(
            ModuleCapsuleMapping(
                module_path="src.ai_rights.consent_manager",
                module_name="AI Consent Management System",
                uatp7_capsule_type=UATP7CapsuleType.CONSENT_CAPSULE,
                compatibility_level=CompatibilityLevel.FULLY_COMPLIANT,
                primary_classes=["ConsentManager", "ConsentRecord", "UsagePermission"],
                data_structures=["ConsentPolicy", "PermissionGrant"],
                key_functions=["request_consent", "grant_permission", "revoke_consent"],
                confidence_score=0.91,
                notes="Granular AI consent management with usage tracking",
            )
        )

        # Integration Layer Mappings

        # 17. API Server
        self.add_module_mapping(
            ModuleCapsuleMapping(
                module_path="src.api.server",
                module_name="RESTful API Server",
                uatp7_capsule_type=UATP7CapsuleType.CONVERSATION_CAPSULE,
                compatibility_level=CompatibilityLevel.PARTIALLY_COMPLIANT,
                primary_classes=["APIServer", "RequestHandler", "ResponseProcessor"],
                data_structures=["APIResponse", "RequestMetadata"],
                key_functions=["handle_request", "process_response", "validate_input"],
                required_changes=[
                    "Add UATP 7.0 capsule type routing",
                    "Implement capsule type validation",
                ],
                missing_fields=["uatp7_capsule_headers", "standard_metadata_fields"],
                additional_implementations=[
                    "UATP 7.0 endpoint mapping",
                    "Capsule type serialization",
                ],
                confidence_score=0.65,
                notes="API layer needs UATP 7.0 capsule type integration",
            )
        )

        # 18. Multi-Platform Integration
        self.add_module_mapping(
            ModuleCapsuleMapping(
                module_path="src.integrations.advanced_llm_registry",
                module_name="Advanced LLM Registry",
                uatp7_capsule_type=UATP7CapsuleType.CONVERSATION_CAPSULE,
                compatibility_level=CompatibilityLevel.PARTIALLY_COMPLIANT,
                primary_classes=["LLMRegistry", "LLMProvider", "ProviderAdapter"],
                data_structures=["ProviderCapabilities", "IntegrationMetrics"],
                key_functions=[
                    "register_provider",
                    "route_request",
                    "aggregate_responses",
                ],
                required_changes=[
                    "Add UATP 7.0 capsule type mapping",
                    "Implement provider-specific serialization",
                ],
                confidence_score=0.68,
                notes="Multi-platform integration needing capsule type standardization",
            )
        )

        # Update statistics
        self._update_mapping_statistics()

    def add_module_mapping(self, mapping: ModuleCapsuleMapping):
        """Add module to capsule type mapping."""

        self.module_mappings[mapping.module_path] = mapping

        # Update reverse mapping
        if mapping.uatp7_capsule_type not in self.capsule_to_modules:
            self.capsule_to_modules[mapping.uatp7_capsule_type] = []
        self.capsule_to_modules[mapping.uatp7_capsule_type].append(mapping.module_path)

        audit_emitter.emit_security_event(
            "uatp7_module_mapping_added",
            {
                "module_path": mapping.module_path,
                "capsule_type": mapping.uatp7_capsule_type.value,
                "compatibility_level": mapping.compatibility_level.value,
                "confidence_score": mapping.confidence_score,
            },
        )

        logger.info(
            f"Added UATP 7.0 mapping: {mapping.module_path} -> {mapping.uatp7_capsule_type.value}"
        )

    def get_capsule_type_for_module(
        self, module_path: str
    ) -> Optional[UATP7CapsuleType]:
        """Get UATP 7.0 capsule type for module."""

        if module_path in self.module_mappings:
            return self.module_mappings[module_path].uatp7_capsule_type
        return None

    def get_modules_for_capsule_type(self, capsule_type: UATP7CapsuleType) -> List[str]:
        """Get modules implementing specific capsule type."""

        return self.capsule_to_modules.get(capsule_type, [])

    def analyze_compliance_gaps(self, module_path: str = None) -> Dict[str, Any]:
        """Analyze compliance gaps for module or system-wide."""

        if module_path:
            # Analyze specific module
            if module_path not in self.module_mappings:
                return {"error": f"Module {module_path} not mapped"}

            mapping = self.module_mappings[module_path]
            return {
                "module_path": module_path,
                "compatibility_level": mapping.compatibility_level.value,
                "required_changes": mapping.required_changes,
                "missing_fields": mapping.missing_fields,
                "additional_implementations": mapping.additional_implementations,
                "confidence_score": mapping.confidence_score,
                "migration_priority": self._calculate_migration_priority(mapping),
            }
        else:
            # System-wide analysis
            compliance_breakdown = {}
            for level in CompatibilityLevel:
                count = len(
                    [
                        m
                        for m in self.module_mappings.values()
                        if m.compatibility_level == level
                    ]
                )
                compliance_breakdown[level.value] = count

            # Identify high-priority migrations
            high_priority_modules = [
                m.module_path
                for m in self.module_mappings.values()
                if m.compatibility_level
                in [
                    CompatibilityLevel.NEEDS_MIGRATION,
                    CompatibilityLevel.PARTIALLY_COMPLIANT,
                ]
                and self._calculate_migration_priority(m) >= 0.7
            ]

            return {
                "compliance_breakdown": compliance_breakdown,
                "total_modules": len(self.module_mappings),
                "compliance_rate": len(
                    [
                        m
                        for m in self.module_mappings.values()
                        if m.compatibility_level
                        in [
                            CompatibilityLevel.FULLY_COMPLIANT,
                            CompatibilityLevel.MOSTLY_COMPLIANT,
                        ]
                    ]
                )
                / len(self.module_mappings),
                "high_priority_migrations": high_priority_modules,
                "coverage_by_capsule_type": {
                    capsule_type.value: len(modules)
                    for capsule_type, modules in self.capsule_to_modules.items()
                },
            }

    def _calculate_migration_priority(self, mapping: ModuleCapsuleMapping) -> float:
        """Calculate migration priority score (0.0 to 1.0)."""

        priority_factors = {
            "compatibility_level": {
                CompatibilityLevel.FULLY_COMPLIANT: 0.0,
                CompatibilityLevel.MOSTLY_COMPLIANT: 0.2,
                CompatibilityLevel.PARTIALLY_COMPLIANT: 0.6,
                CompatibilityLevel.NEEDS_MIGRATION: 0.8,
                CompatibilityLevel.NOT_COMPATIBLE: 1.0,
            },
            "confidence_weight": 1.0 - mapping.confidence_score,
            "change_complexity": len(mapping.required_changes) * 0.1,
            "missing_fields_impact": len(mapping.missing_fields) * 0.05,
        }

        base_priority = priority_factors["compatibility_level"][
            mapping.compatibility_level
        ]
        adjustments = (
            priority_factors["confidence_weight"] * 0.2
            + priority_factors["change_complexity"] * 0.3
            + priority_factors["missing_fields_impact"] * 0.2
        )

        return min(1.0, base_priority + adjustments)

    def generate_migration_plan(
        self, target_modules: List[str] = None
    ) -> Dict[str, Any]:
        """Generate migration plan for UATP 7.0 compliance."""

        modules_to_migrate = target_modules or [
            path
            for path, mapping in self.module_mappings.items()
            if mapping.compatibility_level
            in [
                CompatibilityLevel.NEEDS_MIGRATION,
                CompatibilityLevel.PARTIALLY_COMPLIANT,
            ]
        ]

        migration_phases = {
            "phase_1_critical": [],  # High priority, low complexity
            "phase_2_infrastructure": [],  # Core systems
            "phase_3_integration": [],  # API and integration layers
            "phase_4_optimization": [],  # Final optimizations
        }

        for module_path in modules_to_migrate:
            if module_path not in self.module_mappings:
                continue

            mapping = self.module_mappings[module_path]
            priority = self._calculate_migration_priority(mapping)
            complexity = len(mapping.required_changes) + len(
                mapping.additional_implementations
            )

            migration_item = {
                "module_path": module_path,
                "capsule_type": mapping.uatp7_capsule_type.value,
                "priority": priority,
                "complexity": complexity,
                "required_changes": mapping.required_changes,
                "missing_fields": mapping.missing_fields,
                "additional_implementations": mapping.additional_implementations,
                "estimated_effort_days": complexity * 2,  # Rough estimate
            }

            # Assign to phase based on priority and module type
            if priority >= 0.8 and complexity <= 3:
                migration_phases["phase_1_critical"].append(migration_item)
            elif "engine" in module_path or "core" in module_path:
                migration_phases["phase_2_infrastructure"].append(migration_item)
            elif "api" in module_path or "integration" in module_path:
                migration_phases["phase_3_integration"].append(migration_item)
            else:
                migration_phases["phase_4_optimization"].append(migration_item)

        # Calculate total effort
        total_effort_days = sum(
            item["estimated_effort_days"]
            for phase in migration_phases.values()
            for item in phase
        )

        return {
            "migration_plan": migration_phases,
            "total_modules_to_migrate": len(modules_to_migrate),
            "total_estimated_effort_days": total_effort_days,
            "recommended_timeline": {
                "phase_1": "1-2 weeks",
                "phase_2": "3-4 weeks",
                "phase_3": "2-3 weeks",
                "phase_4": "1-2 weeks",
            },
            "risk_assessment": self._assess_migration_risks(migration_phases),
            "success_criteria": [
                "All modules achieve MOSTLY_COMPLIANT or higher",
                "Core AI rights modules reach FULLY_COMPLIANT",
                "API layer supports all UATP 7.0 capsule types",
                "End-to-end compatibility testing passes",
            ],
        }

    def _assess_migration_risks(
        self, migration_phases: Dict[str, List[Dict[str, Any]]]
    ) -> Dict[str, Any]:
        """Assess risks in migration plan."""

        risks = {
            "high_risk_items": [],
            "dependency_conflicts": [],
            "resource_constraints": [],
            "timeline_risks": [],
        }

        # Identify high-risk migrations
        for phase_name, items in migration_phases.items():
            for item in items:
                if item["complexity"] > 5 and item["priority"] > 0.7:
                    risks["high_risk_items"].append(
                        {
                            "module": item["module_path"],
                            "risk_factors": ["high_complexity", "high_priority"],
                            "mitigation": "Allocate senior developers, extra testing",
                        }
                    )

        # Check for potential dependency issues
        core_modules = ["capsule_engine", "fcde_engine", "reasoning_integrity"]
        for phase_name, items in migration_phases.items():
            for item in items:
                if any(core in item["module_path"] for core in core_modules):
                    if phase_name not in ["phase_1_critical", "phase_2_infrastructure"]:
                        risks["dependency_conflicts"].append(
                            {
                                "module": item["module_path"],
                                "issue": "Core module in wrong phase",
                                "recommendation": "Move to earlier phase",
                            }
                        )

        return risks

    def _update_mapping_statistics(self):
        """Update mapping statistics."""

        self.mapping_stats["total_modules_mapped"] = len(self.module_mappings)

        self.mapping_stats["fully_compliant_modules"] = len(
            [
                m
                for m in self.module_mappings.values()
                if m.compatibility_level == CompatibilityLevel.FULLY_COMPLIANT
            ]
        )

        self.mapping_stats["modules_needing_migration"] = len(
            [
                m
                for m in self.module_mappings.values()
                if m.compatibility_level
                in [
                    CompatibilityLevel.NEEDS_MIGRATION,
                    CompatibilityLevel.PARTIALLY_COMPLIANT,
                ]
            ]
        )

        self.mapping_stats["capsule_types_covered"] = len(self.capsule_to_modules)

    def get_uatp7_coverage_report(self) -> Dict[str, Any]:
        """Generate comprehensive UATP 7.0 coverage report."""

        # Capsule type coverage analysis
        all_capsule_types = list(UATP7CapsuleType)
        covered_types = list(self.capsule_to_modules.keys())
        uncovered_types = [ct for ct in all_capsule_types if ct not in covered_types]

        # Compliance level distribution
        compliance_distribution = {}
        for level in CompatibilityLevel:
            count = len(
                [
                    m
                    for m in self.module_mappings.values()
                    if m.compatibility_level == level
                ]
            )
            compliance_distribution[level.value] = count

        # Implementation quality metrics
        avg_confidence = sum(
            m.confidence_score for m in self.module_mappings.values()
        ) / len(self.module_mappings)

        high_quality_implementations = len(
            [
                m
                for m in self.module_mappings.values()
                if m.confidence_score >= 0.9
                and m.compatibility_level == CompatibilityLevel.FULLY_COMPLIANT
            ]
        )

        return {
            "coverage_summary": {
                "total_capsule_types": len(all_capsule_types),
                "covered_capsule_types": len(covered_types),
                "coverage_percentage": len(covered_types)
                / len(all_capsule_types)
                * 100,
                "uncovered_types": [ct.value for ct in uncovered_types],
            },
            "compliance_analysis": {
                "compliance_distribution": compliance_distribution,
                "overall_compliance_rate": (
                    compliance_distribution.get("fully_compliant", 0)
                    + compliance_distribution.get("mostly_compliant", 0)
                )
                / len(self.module_mappings)
                * 100,
                "modules_ready_for_production": compliance_distribution.get(
                    "fully_compliant", 0
                ),
            },
            "quality_metrics": {
                "average_confidence_score": avg_confidence,
                "high_quality_implementations": high_quality_implementations,
                "modules_needing_improvement": len(
                    [
                        m
                        for m in self.module_mappings.values()
                        if m.confidence_score < 0.8 or len(m.required_changes) > 3
                    ]
                ),
            },
            "implementation_strengths": [
                "Revolutionary AI Rights Framework with full economic attribution",
                "Post-quantum cryptographic security with integrity protection",
                "Temporal justice and lineage tracking for fair attribution",
                "Comprehensive adversarial testing and security validation",
                "Multi-platform integration with standardized APIs",
            ],
            "areas_for_improvement": [ct.value for ct in uncovered_types]
            + [
                m.module_path
                for m in self.module_mappings.values()
                if m.compatibility_level == CompatibilityLevel.NEEDS_MIGRATION
            ],
            "readiness_assessment": "PRODUCTION_READY"
            if len(covered_types) >= 20 and avg_confidence >= 0.85
            else "NEAR_PRODUCTION_READY",
        }


# Global UATP 7.0 type mapper instance
uatp7_type_mapper = UATP7TypeMapper()


def get_capsule_type_for_module(module_path: str) -> Optional[str]:
    """Convenience function to get capsule type for module."""

    capsule_type = uatp7_type_mapper.get_capsule_type_for_module(module_path)
    return capsule_type.value if capsule_type else None


def get_modules_for_capsule_type(capsule_type: str) -> List[str]:
    """Convenience function to get modules for capsule type."""

    try:
        ct = UATP7CapsuleType(capsule_type)
        return uatp7_type_mapper.get_modules_for_capsule_type(ct)
    except ValueError:
        return []


def analyze_uatp7_compliance(module_path: str = None) -> Dict[str, Any]:
    """Convenience function to analyze UATP 7.0 compliance."""

    return uatp7_type_mapper.analyze_compliance_gaps(module_path)


def generate_uatp7_migration_plan() -> Dict[str, Any]:
    """Convenience function to generate UATP 7.0 migration plan."""

    return uatp7_type_mapper.generate_migration_plan()


def get_uatp7_system_coverage() -> Dict[str, Any]:
    """Convenience function to get UATP 7.0 system coverage."""

    return uatp7_type_mapper.get_uatp7_coverage_report()
