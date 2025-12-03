"""
Consent Capsule System for UATP Capsule Engine.

This critical module implements granular consent management and permission tracking
for AI rights and data usage. It provides comprehensive consent lifecycle management,
usage permission enforcement, and traceback capabilities for all AI interactions
and data processing operations.
"""

import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple
from collections import defaultdict

from src.audit.events import audit_emitter
from src.capsule_schema import CapsuleStatus

logger = logging.getLogger(__name__)


class ConsentType(str, Enum):
    """Types of consent that can be granted."""

    DATA_PROCESSING = "data_processing"
    AI_TRAINING = "ai_training"
    ECONOMIC_ATTRIBUTION = "economic_attribution"
    RESEARCH_PARTICIPATION = "research_participation"
    CREATIVE_USAGE = "creative_usage"
    EMOTIONAL_ANALYSIS = "emotional_analysis"
    BEHAVIORAL_TRACKING = "behavioral_tracking"
    CROSS_PLATFORM_SHARING = "cross_platform_sharing"
    COMMERCIAL_USE = "commercial_use"
    DERIVATIVE_WORKS = "derivative_works"
    LINEAGE_TRACKING = "lineage_tracking"
    TEMPORAL_ATTRIBUTION = "temporal_attribution"


class ConsentStatus(str, Enum):
    """Status of consent grants."""

    ACTIVE = "active"
    REVOKED = "revoked"
    EXPIRED = "expired"
    PENDING = "pending"
    SUSPENDED = "suspended"
    CONDITIONAL = "conditional"


class PermissionScope(str, Enum):
    """Scope of permissions granted."""

    GLOBAL = "global"  # All platforms/systems
    PLATFORM_SPECIFIC = "platform_specific"  # Specific platform only
    SESSION_LIMITED = "session_limited"  # Current session only
    TIME_LIMITED = "time_limited"  # Specific time period
    PURPOSE_LIMITED = "purpose_limited"  # Specific purpose only
    ENTITY_LIMITED = "entity_limited"  # Specific entities only


class ConsentSource(str, Enum):
    """Source of consent grant."""

    EXPLICIT_USER_GRANT = "explicit_user_grant"
    IMPLICIT_AGREEMENT = "implicit_agreement"
    LEGAL_REQUIREMENT = "legal_requirement"
    SYSTEM_DEFAULT = "system_default"
    INHERITED_PERMISSION = "inherited_permission"
    CONTRACTUAL_AGREEMENT = "contractual_agreement"


@dataclass
class ConsentCondition:
    """Specific conditions attached to consent."""

    condition_id: str
    condition_type: str  # "time_limit", "usage_limit", "purpose_restriction", etc.
    parameters: Dict[str, Any] = field(default_factory=dict)
    is_satisfied: bool = True
    violation_count: int = 0

    def check_condition(self, context: Dict[str, Any]) -> bool:
        """Check if condition is satisfied in given context."""
        if self.condition_type == "time_limit":
            expiry = datetime.fromisoformat(self.parameters.get("expiry_date"))
            return datetime.now(timezone.utc) <= expiry
        elif self.condition_type == "usage_limit":
            max_uses = self.parameters.get("max_uses", 0)
            current_uses = context.get("usage_count", 0)
            return current_uses < max_uses
        elif self.condition_type == "purpose_restriction":
            allowed_purposes = self.parameters.get("allowed_purposes", [])
            current_purpose = context.get("purpose")
            return current_purpose in allowed_purposes
        elif self.condition_type == "entity_restriction":
            allowed_entities = self.parameters.get("allowed_entities", [])
            current_entity = context.get("requesting_entity")
            return current_entity in allowed_entities
        else:
            return True


@dataclass
class ConsentRecord:
    """Individual consent record with full traceability."""

    consent_id: str
    grantor_id: str  # Who granted the consent
    grantee_id: Optional[str] = None  # Who received the consent (can be system-wide)

    # Consent details
    consent_type: ConsentType = ConsentType.DATA_PROCESSING
    permission_scope: PermissionScope = PermissionScope.SESSION_LIMITED
    consent_source: ConsentSource = ConsentSource.EXPLICIT_USER_GRANT

    # Status and lifecycle
    status: ConsentStatus = ConsentStatus.PENDING
    granted_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    expires_at: Optional[datetime] = None
    revoked_at: Optional[datetime] = None
    last_used_at: Optional[datetime] = None

    # Conditions and restrictions
    conditions: List[ConsentCondition] = field(default_factory=list)
    restrictions: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)

    # Usage tracking
    usage_count: int = 0
    max_usage_count: Optional[int] = None
    affected_data_types: List[str] = field(default_factory=list)
    affected_systems: List[str] = field(default_factory=list)

    # Legal and compliance
    legal_basis: str = ""
    compliance_requirements: List[str] = field(default_factory=list)
    audit_trail: List[Dict[str, Any]] = field(default_factory=list)

    def is_valid(self, context: Dict[str, Any] = None) -> bool:
        """Check if consent is currently valid."""
        context = context or {}

        # Check basic status
        if self.status != ConsentStatus.ACTIVE:
            return False

        # Check expiration
        if self.expires_at and datetime.now(timezone.utc) > self.expires_at:
            return False

        # Check usage limits
        if self.max_usage_count and self.usage_count >= self.max_usage_count:
            return False

        # Check all conditions
        for condition in self.conditions:
            if not condition.check_condition(context):
                return False

        return True

    def record_usage(self, usage_context: Dict[str, Any]):
        """Record usage of this consent."""
        self.usage_count += 1
        self.last_used_at = datetime.now(timezone.utc)

        # Add to audit trail
        self.audit_trail.append(
            {
                "action": "consent_used",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "context": usage_context,
                "usage_number": self.usage_count,
            }
        )

    def revoke(self, reason: str = "", revoker_id: str = ""):
        """Revoke this consent."""
        self.status = ConsentStatus.REVOKED
        self.revoked_at = datetime.now(timezone.utc)

        # Add to audit trail
        self.audit_trail.append(
            {
                "action": "consent_revoked",
                "timestamp": self.revoked_at.isoformat(),
                "reason": reason,
                "revoker_id": revoker_id,
            }
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert consent record to dictionary."""
        return {
            "consent_id": self.consent_id,
            "grantor_id": self.grantor_id,
            "grantee_id": self.grantee_id,
            "consent_type": self.consent_type.value,
            "permission_scope": self.permission_scope.value,
            "consent_source": self.consent_source.value,
            "status": self.status.value,
            "granted_at": self.granted_at.isoformat(),
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "revoked_at": self.revoked_at.isoformat() if self.revoked_at else None,
            "last_used_at": self.last_used_at.isoformat()
            if self.last_used_at
            else None,
            "conditions": [
                {
                    "condition_id": c.condition_id,
                    "condition_type": c.condition_type,
                    "parameters": c.parameters,
                    "is_satisfied": c.is_satisfied,
                    "violation_count": c.violation_count,
                }
                for c in self.conditions
            ],
            "restrictions": self.restrictions,
            "metadata": self.metadata,
            "usage_count": self.usage_count,
            "max_usage_count": self.max_usage_count,
            "affected_data_types": self.affected_data_types,
            "affected_systems": self.affected_systems,
            "legal_basis": self.legal_basis,
            "compliance_requirements": self.compliance_requirements,
            "audit_trail": self.audit_trail,
            "is_currently_valid": self.is_valid(),
        }


@dataclass
class ConsentCapsule:
    """UATP 7.0 Consent Capsule for comprehensive consent management."""

    capsule_id: str
    creation_timestamp: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    # Core consent data
    consent_records: List[ConsentRecord] = field(default_factory=list)
    aggregate_permissions: Dict[str, Set[str]] = field(
        default_factory=lambda: defaultdict(set)
    )

    # Traceability
    related_capsules: List[str] = field(default_factory=list)
    data_lineage: List[Dict[str, Any]] = field(default_factory=list)
    consent_lineage: List[str] = field(default_factory=list)  # Parent consent IDs

    # System metadata
    capsule_status: CapsuleStatus = CapsuleStatus.DRAFT
    processing_logs: List[Dict[str, Any]] = field(default_factory=list)

    def add_consent_record(self, consent: ConsentRecord):
        """Add consent record to capsule."""
        self.consent_records.append(consent)

        # Update aggregate permissions
        scope_key = f"{consent.consent_type.value}:{consent.permission_scope.value}"
        if consent.grantee_id:
            self.aggregate_permissions[scope_key].add(consent.grantee_id)

        # Log addition
        self.processing_logs.append(
            {
                "action": "consent_added",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "consent_id": consent.consent_id,
                "consent_type": consent.consent_type.value,
            }
        )

        audit_emitter.emit_security_event(
            "consent_record_added",
            {
                "capsule_id": self.capsule_id,
                "consent_id": consent.consent_id,
                "grantor_id": consent.grantor_id,
                "consent_type": consent.consent_type.value,
            },
        )

    def check_permission(
        self, request_context: Dict[str, Any]
    ) -> Tuple[bool, List[str]]:
        """Check if permission is granted for given context."""
        requesting_entity = request_context.get("requesting_entity")
        consent_type = request_context.get("consent_type")
        purpose = request_context.get("purpose")

        granted_permissions = []
        permission_granted = False

        for consent in self.consent_records:
            if consent.consent_type.value == consent_type and consent.is_valid(
                request_context
            ):
                # Check if entity matches
                if (
                    consent.grantee_id is None
                    or consent.grantee_id == requesting_entity  # System-wide permission
                ):
                    permission_granted = True
                    granted_permissions.append(consent.consent_id)

                    # Record usage
                    consent.record_usage(request_context)

        # Log permission check
        self.processing_logs.append(
            {
                "action": "permission_checked",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "request_context": request_context,
                "permission_granted": permission_granted,
                "granted_permissions": granted_permissions,
            }
        )

        return permission_granted, granted_permissions

    def revoke_consent(
        self, consent_id: str, reason: str = "", revoker_id: str = ""
    ) -> bool:
        """Revoke specific consent by ID."""
        for consent in self.consent_records:
            if consent.consent_id == consent_id:
                consent.revoke(reason, revoker_id)

                # Update aggregate permissions
                scope_key = (
                    f"{consent.consent_type.value}:{consent.permission_scope.value}"
                )
                if (
                    consent.grantee_id
                    and consent.grantee_id in self.aggregate_permissions[scope_key]
                ):
                    self.aggregate_permissions[scope_key].remove(consent.grantee_id)

                # Log revocation
                self.processing_logs.append(
                    {
                        "action": "consent_revoked",
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                        "consent_id": consent_id,
                        "reason": reason,
                        "revoker_id": revoker_id,
                    }
                )

                audit_emitter.emit_security_event(
                    "consent_revoked",
                    {
                        "capsule_id": self.capsule_id,
                        "consent_id": consent_id,
                        "reason": reason,
                        "revoker_id": revoker_id,
                    },
                )

                return True

        return False

    def get_active_consents(
        self, entity_id: str = None, consent_type: ConsentType = None
    ) -> List[ConsentRecord]:
        """Get active consents, optionally filtered by entity or type."""
        active_consents = []

        for consent in self.consent_records:
            if consent.status == ConsentStatus.ACTIVE and consent.is_valid():
                # Apply filters
                if entity_id and consent.grantee_id != entity_id:
                    continue
                if consent_type and consent.consent_type != consent_type:
                    continue

                active_consents.append(consent)

        return active_consents

    def get_consent_summary(self) -> Dict[str, Any]:
        """Get summary of all consents in capsule."""
        summary = {
            "total_consents": len(self.consent_records),
            "active_consents": len(
                [c for c in self.consent_records if c.status == ConsentStatus.ACTIVE]
            ),
            "revoked_consents": len(
                [c for c in self.consent_records if c.status == ConsentStatus.REVOKED]
            ),
            "expired_consents": len(
                [c for c in self.consent_records if c.status == ConsentStatus.EXPIRED]
            ),
            "consent_types": {},
            "permission_scopes": {},
            "total_usage_count": sum(c.usage_count for c in self.consent_records),
        }

        # Count by type
        for consent in self.consent_records:
            consent_type = consent.consent_type.value
            if consent_type not in summary["consent_types"]:
                summary["consent_types"][consent_type] = {"total": 0, "active": 0}

            summary["consent_types"][consent_type]["total"] += 1
            if consent.status == ConsentStatus.ACTIVE:
                summary["consent_types"][consent_type]["active"] += 1

        # Count by scope
        for consent in self.consent_records:
            scope = consent.permission_scope.value
            if scope not in summary["permission_scopes"]:
                summary["permission_scopes"][scope] = {"total": 0, "active": 0}

            summary["permission_scopes"][scope]["total"] += 1
            if consent.status == ConsentStatus.ACTIVE:
                summary["permission_scopes"][scope]["active"] += 1

        return summary

    def to_dict(self) -> Dict[str, Any]:
        """Convert consent capsule to dictionary."""
        return {
            "capsule_id": self.capsule_id,
            "capsule_type": "consent_capsule",
            "creation_timestamp": self.creation_timestamp.isoformat(),
            "consent_records": [c.to_dict() for c in self.consent_records],
            "aggregate_permissions": {
                k: list(v) for k, v in self.aggregate_permissions.items()
            },
            "related_capsules": self.related_capsules,
            "data_lineage": self.data_lineage,
            "consent_lineage": self.consent_lineage,
            "capsule_status": self.capsule_status.value,
            "processing_logs": self.processing_logs,
            "consent_summary": self.get_consent_summary(),
        }


class ConsentCapsuleManager:
    """Manager for consent capsules with advanced tracking and enforcement."""

    def __init__(self):
        # Capsule storage
        self.consent_capsules: Dict[str, ConsentCapsule] = {}

        # Index structures for fast lookups
        self.grantor_index: Dict[str, List[str]] = defaultdict(
            list
        )  # grantor_id -> capsule_ids
        self.grantee_index: Dict[str, List[str]] = defaultdict(
            list
        )  # grantee_id -> capsule_ids
        self.type_index: Dict[ConsentType, List[str]] = defaultdict(
            list
        )  # type -> capsule_ids

        # Statistics
        self.manager_stats = {
            "total_capsules": 0,
            "total_consents": 0,
            "active_consents": 0,
            "revoked_consents": 0,
            "permission_checks": 0,
            "permission_grants": 0,
            "permission_denials": 0,
        }

    def create_consent_capsule(
        self, initial_consents: List[ConsentRecord] = None
    ) -> str:
        """Create new consent capsule."""
        capsule_id = f"consent_capsule_{uuid.uuid4().hex[:12]}"
        capsule = ConsentCapsule(capsule_id=capsule_id)

        # Add initial consents if provided
        if initial_consents:
            for consent in initial_consents:
                capsule.add_consent_record(consent)

        # Store capsule
        self.consent_capsules[capsule_id] = capsule

        # Update indices
        self._update_indices_for_capsule(capsule)

        # Update statistics
        self.manager_stats["total_capsules"] += 1
        if initial_consents:
            self.manager_stats["total_consents"] += len(initial_consents)
            self.manager_stats["active_consents"] += len(
                [c for c in initial_consents if c.status == ConsentStatus.ACTIVE]
            )

        audit_emitter.emit_security_event(
            "consent_capsule_created",
            {
                "capsule_id": capsule_id,
                "initial_consent_count": len(initial_consents)
                if initial_consents
                else 0,
            },
        )

        logger.info(f"Created consent capsule: {capsule_id}")
        return capsule_id

    def add_consent_to_capsule(self, capsule_id: str, consent: ConsentRecord) -> bool:
        """Add consent record to existing capsule."""
        if capsule_id not in self.consent_capsules:
            return False

        capsule = self.consent_capsules[capsule_id]
        capsule.add_consent_record(consent)

        # Update indices
        self._update_indices_for_capsule(capsule)

        # Update statistics
        self.manager_stats["total_consents"] += 1
        if consent.status == ConsentStatus.ACTIVE:
            self.manager_stats["active_consents"] += 1

        return True

    def check_permission_across_capsules(
        self, request_context: Dict[str, Any]
    ) -> Tuple[bool, List[str]]:
        """Check permission across all relevant capsules."""
        requesting_entity = request_context.get("requesting_entity")
        consent_type_str = request_context.get("consent_type")

        try:
            consent_type = ConsentType(consent_type_str)
        except ValueError:
            return False, []

        # Get relevant capsules
        relevant_capsules = []

        # Add capsules by grantee
        if requesting_entity:
            relevant_capsules.extend(self.grantee_index.get(requesting_entity, []))

        # Add capsules by type
        relevant_capsules.extend(self.type_index.get(consent_type, []))

        # Remove duplicates
        relevant_capsules = list(set(relevant_capsules))

        # Check permission in each relevant capsule
        permission_granted = False
        granted_permissions = []

        for capsule_id in relevant_capsules:
            if capsule_id in self.consent_capsules:
                capsule = self.consent_capsules[capsule_id]
                granted, permissions = capsule.check_permission(request_context)

                if granted:
                    permission_granted = True
                    granted_permissions.extend(permissions)

        # Update statistics
        self.manager_stats["permission_checks"] += 1
        if permission_granted:
            self.manager_stats["permission_grants"] += 1
        else:
            self.manager_stats["permission_denials"] += 1

        audit_emitter.emit_security_event(
            "permission_check_across_capsules",
            {
                "request_context": request_context,
                "permission_granted": permission_granted,
                "capsules_checked": len(relevant_capsules),
                "granted_permissions": len(granted_permissions),
            },
        )

        return permission_granted, granted_permissions

    def revoke_all_consents_for_entity(self, entity_id: str, reason: str = "") -> int:
        """Revoke all consents for specific entity."""
        revoked_count = 0

        # Get capsules where entity is grantor
        grantor_capsules = self.grantor_index.get(entity_id, [])

        for capsule_id in grantor_capsules:
            if capsule_id in self.consent_capsules:
                capsule = self.consent_capsules[capsule_id]

                # Revoke all consents from this grantor
                for consent in capsule.consent_records:
                    if (
                        consent.grantor_id == entity_id
                        and consent.status == ConsentStatus.ACTIVE
                    ):
                        consent.revoke(reason, entity_id)
                        revoked_count += 1

        # Update statistics
        self.manager_stats["active_consents"] -= revoked_count
        self.manager_stats["revoked_consents"] += revoked_count

        audit_emitter.emit_security_event(
            "bulk_consent_revocation",
            {"entity_id": entity_id, "reason": reason, "revoked_count": revoked_count},
        )

        logger.info(f"Revoked {revoked_count} consents for entity: {entity_id}")
        return revoked_count

    def _update_indices_for_capsule(self, capsule: ConsentCapsule):
        """Update index structures for capsule."""
        capsule_id = capsule.capsule_id

        for consent in capsule.consent_records:
            # Update grantor index
            if capsule_id not in self.grantor_index[consent.grantor_id]:
                self.grantor_index[consent.grantor_id].append(capsule_id)

            # Update grantee index
            if (
                consent.grantee_id
                and capsule_id not in self.grantee_index[consent.grantee_id]
            ):
                self.grantee_index[consent.grantee_id].append(capsule_id)

            # Update type index
            if capsule_id not in self.type_index[consent.consent_type]:
                self.type_index[consent.consent_type].append(capsule_id)

    def get_consent_traceability_report(self, entity_id: str) -> Dict[str, Any]:
        """Generate comprehensive consent traceability report for entity."""
        # Get all capsules involving entity
        grantor_capsules = self.grantor_index.get(entity_id, [])
        grantee_capsules = self.grantee_index.get(entity_id, [])
        all_capsules = list(set(grantor_capsules + grantee_capsules))

        report = {
            "entity_id": entity_id,
            "report_timestamp": datetime.now(timezone.utc).isoformat(),
            "capsules_as_grantor": len(grantor_capsules),
            "capsules_as_grantee": len(grantee_capsules),
            "total_related_capsules": len(all_capsules),
            "consent_breakdown": {
                "granted_by_entity": {"total": 0, "active": 0, "revoked": 0},
                "granted_to_entity": {"total": 0, "active": 0, "revoked": 0},
            },
            "consent_types_granted": {},
            "consent_types_received": {},
            "detailed_consents": [],
        }

        for capsule_id in all_capsules:
            if capsule_id in self.consent_capsules:
                capsule = self.consent_capsules[capsule_id]

                for consent in capsule.consent_records:
                    consent_detail = consent.to_dict()
                    consent_detail["capsule_id"] = capsule_id

                    if consent.grantor_id == entity_id:
                        # Entity granted this consent
                        report["consent_breakdown"]["granted_by_entity"]["total"] += 1
                        if consent.status == ConsentStatus.ACTIVE:
                            report["consent_breakdown"]["granted_by_entity"][
                                "active"
                            ] += 1
                        elif consent.status == ConsentStatus.REVOKED:
                            report["consent_breakdown"]["granted_by_entity"][
                                "revoked"
                            ] += 1

                        # Track consent types granted
                        consent_type = consent.consent_type.value
                        if consent_type not in report["consent_types_granted"]:
                            report["consent_types_granted"][consent_type] = 0
                        report["consent_types_granted"][consent_type] += 1

                    if consent.grantee_id == entity_id:
                        # Entity received this consent
                        report["consent_breakdown"]["granted_to_entity"]["total"] += 1
                        if consent.status == ConsentStatus.ACTIVE:
                            report["consent_breakdown"]["granted_to_entity"][
                                "active"
                            ] += 1
                        elif consent.status == ConsentStatus.REVOKED:
                            report["consent_breakdown"]["granted_to_entity"][
                                "revoked"
                            ] += 1

                        # Track consent types received
                        consent_type = consent.consent_type.value
                        if consent_type not in report["consent_types_received"]:
                            report["consent_types_received"][consent_type] = 0
                        report["consent_types_received"][consent_type] += 1

                    report["detailed_consents"].append(consent_detail)

        return report

    def get_system_consent_statistics(self) -> Dict[str, Any]:
        """Get system-wide consent statistics."""
        stats = self.manager_stats.copy()

        # Add detailed breakdown
        stats["consent_type_breakdown"] = {}
        stats["permission_scope_breakdown"] = {}
        stats["consent_source_breakdown"] = {}

        for capsule in self.consent_capsules.values():
            for consent in capsule.consent_records:
                # Count by type
                consent_type = consent.consent_type.value
                if consent_type not in stats["consent_type_breakdown"]:
                    stats["consent_type_breakdown"][consent_type] = {
                        "total": 0,
                        "active": 0,
                    }
                stats["consent_type_breakdown"][consent_type]["total"] += 1
                if consent.status == ConsentStatus.ACTIVE:
                    stats["consent_type_breakdown"][consent_type]["active"] += 1

                # Count by scope
                scope = consent.permission_scope.value
                if scope not in stats["permission_scope_breakdown"]:
                    stats["permission_scope_breakdown"][scope] = {
                        "total": 0,
                        "active": 0,
                    }
                stats["permission_scope_breakdown"][scope]["total"] += 1
                if consent.status == ConsentStatus.ACTIVE:
                    stats["permission_scope_breakdown"][scope]["active"] += 1

                # Count by source
                source = consent.consent_source.value
                if source not in stats["consent_source_breakdown"]:
                    stats["consent_source_breakdown"][source] = {
                        "total": 0,
                        "active": 0,
                    }
                stats["consent_source_breakdown"][source]["total"] += 1
                if consent.status == ConsentStatus.ACTIVE:
                    stats["consent_source_breakdown"][source]["active"] += 1

        return stats


# Global consent capsule manager
consent_capsule_manager = ConsentCapsuleManager()


def create_consent_record(
    grantor_id: str,
    consent_type: ConsentType,
    grantee_id: str = None,
    permission_scope: PermissionScope = PermissionScope.SESSION_LIMITED,
    expires_at: datetime = None,
    conditions: List[ConsentCondition] = None,
    metadata: Dict[str, Any] = None,
) -> ConsentRecord:
    """Convenience function to create consent record."""

    consent_id = f"consent_{uuid.uuid4().hex[:12]}"

    return ConsentRecord(
        consent_id=consent_id,
        grantor_id=grantor_id,
        grantee_id=grantee_id,
        consent_type=consent_type,
        permission_scope=permission_scope,
        status=ConsentStatus.ACTIVE,
        expires_at=expires_at,
        conditions=conditions or [],
        metadata=metadata or {},
    )


def check_system_permission(
    requesting_entity: str,
    consent_type: str,
    purpose: str = "",
    additional_context: Dict[str, Any] = None,
) -> bool:
    """Convenience function to check system-wide permission."""

    context = {
        "requesting_entity": requesting_entity,
        "consent_type": consent_type,
        "purpose": purpose,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }

    if additional_context:
        context.update(additional_context)

    granted, _ = consent_capsule_manager.check_permission_across_capsules(context)
    return granted


def create_consent_capsule_with_records(consents: List[ConsentRecord]) -> str:
    """Convenience function to create consent capsule with initial records."""

    return consent_capsule_manager.create_consent_capsule(consents)


def get_entity_consent_report(entity_id: str) -> Dict[str, Any]:
    """Convenience function to get entity consent report."""

    return consent_capsule_manager.get_consent_traceability_report(entity_id)
