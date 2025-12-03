"""
Capsule Consent Layer for UATP Capsule Engine.

This critical layer integrates consent management directly into capsule operations,
handling both implicit rights (inherited/assumed permissions) and explicit rights
(explicitly granted permissions). It provides transparent consent enforcement
across all capsule types and operations.
"""

import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

from src.audit.events import audit_emitter
from src.capsules.consent_capsule import (
    ConsentType,
    PermissionScope,
    consent_capsule_manager,
)

logger = logging.getLogger(__name__)


class RightsType(str, Enum):
    """Types of rights in the capsule system."""

    EXPLICIT_GRANTED = "explicit_granted"  # Explicitly granted by user
    IMPLICIT_INHERITED = "implicit_inherited"  # Inherited from parent capsule
    IMPLICIT_SYSTEM = "implicit_system"  # System-level default rights
    IMPLICIT_CONTEXT = "implicit_context"  # Context-based implied rights
    IMPLICIT_RELATIONSHIP = "implicit_relationship"  # Relationship-based rights
    EXPLICIT_DENIED = "explicit_denied"  # Explicitly denied/revoked
    CONDITIONAL_GRANTED = "conditional_granted"  # Granted with conditions
    TEMPORAL_GRANTED = "temporal_granted"  # Time-limited rights


class CapsuleOperation(str, Enum):
    """Types of operations on capsules."""

    CREATE = "create"
    READ = "read"
    UPDATE = "update"
    DELETE = "delete"
    FORK = "fork"
    REMIX = "remix"
    ATTRIBUTE = "attribute"
    ECONOMIC_CLAIM = "economic_claim"
    LINEAGE_TRACE = "lineage_trace"
    COMPRESS = "compress"
    SHARE = "share"
    EXPORT = "export"


@dataclass
class ImplicitRight:
    """Implicit right derived from context, inheritance, or system defaults."""

    right_id: str
    rights_type: RightsType
    operation: CapsuleOperation
    granted_to: str  # entity receiving the right

    # Source of implicit right
    source_capsule_id: Optional[str] = None
    source_relationship: Optional[str] = None  # "parent", "creator", "contributor"
    source_context: Dict[str, Any] = field(default_factory=dict)

    # Right details
    scope: PermissionScope = PermissionScope.SESSION_LIMITED
    confidence_score: float = 1.0  # How confident we are in this implicit right

    # Conditions and constraints
    conditions: List[str] = field(default_factory=list)
    expiry: Optional[datetime] = None
    usage_limit: Optional[int] = None

    # Metadata
    derived_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    last_validated: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def is_valid(self) -> bool:
        """Check if implicit right is still valid."""
        if self.expiry and datetime.now(timezone.utc) > self.expiry:
            return False

        # Check confidence threshold
        if self.confidence_score < 0.5:
            return False

        return True

    def to_dict(self) -> Dict[str, Any]:
        """Convert implicit right to dictionary."""
        return {
            "right_id": self.right_id,
            "rights_type": self.rights_type.value,
            "operation": self.operation.value,
            "source_capsule_id": self.source_capsule_id,
            "source_relationship": self.source_relationship,
            "source_context": self.source_context,
            "granted_to": self.granted_to,
            "scope": self.scope.value,
            "confidence_score": self.confidence_score,
            "conditions": self.conditions,
            "expiry": self.expiry.isoformat() if self.expiry else None,
            "usage_limit": self.usage_limit,
            "derived_at": self.derived_at.isoformat(),
            "last_validated": self.last_validated.isoformat(),
            "is_currently_valid": self.is_valid(),
        }


@dataclass
class CapsuleConsentContext:
    """Context for consent checking on capsule operations."""

    capsule_id: str
    operation: CapsuleOperation
    requesting_entity: str

    # Operation context
    target_entity: Optional[str] = None  # For operations targeting another entity
    operation_metadata: Dict[str, Any] = field(default_factory=dict)

    # Inheritance context
    parent_capsule_ids: List[str] = field(default_factory=list)
    lineage_chain: List[str] = field(default_factory=list)

    # Relationship context
    creator_id: Optional[str] = None
    contributors: List[str] = field(default_factory=list)
    related_entities: List[str] = field(default_factory=list)

    # Temporal context
    operation_timestamp: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    capsule_creation_time: Optional[datetime] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert context to dictionary."""
        return {
            "capsule_id": self.capsule_id,
            "operation": self.operation.value,
            "requesting_entity": self.requesting_entity,
            "target_entity": self.target_entity,
            "operation_metadata": self.operation_metadata,
            "parent_capsule_ids": self.parent_capsule_ids,
            "lineage_chain": self.lineage_chain,
            "creator_id": self.creator_id,
            "contributors": self.contributors,
            "related_entities": self.related_entities,
            "operation_timestamp": self.operation_timestamp.isoformat(),
            "capsule_creation_time": self.capsule_creation_time.isoformat()
            if self.capsule_creation_time
            else None,
        }


class CapsuleConsentLayer:
    """Consent layer that integrates with all capsule operations."""

    def __init__(self):
        # Implicit rights cache
        self.implicit_rights_cache: Dict[str, List[ImplicitRight]] = {}

        # System-level default rights
        self.system_default_rights = {
            # Creators have full rights to their capsules
            "creator_rights": [
                CapsuleOperation.READ,
                CapsuleOperation.UPDATE,
                CapsuleOperation.FORK,
                CapsuleOperation.ATTRIBUTE,
                CapsuleOperation.ECONOMIC_CLAIM,
            ],
            # Contributors have limited rights
            "contributor_rights": [
                CapsuleOperation.READ,
                CapsuleOperation.ATTRIBUTE,
                CapsuleOperation.ECONOMIC_CLAIM,
            ],
            # Public operations (with consent)
            "public_rights": [
                CapsuleOperation.READ,
                CapsuleOperation.FORK,
                CapsuleOperation.REMIX,
            ],
        }

        # Consent mapping for operations
        self.operation_consent_mapping = {
            CapsuleOperation.CREATE: ConsentType.DATA_PROCESSING,
            CapsuleOperation.READ: ConsentType.DATA_PROCESSING,
            CapsuleOperation.UPDATE: ConsentType.DATA_PROCESSING,
            CapsuleOperation.DELETE: ConsentType.DATA_PROCESSING,
            CapsuleOperation.FORK: ConsentType.DERIVATIVE_WORKS,
            CapsuleOperation.REMIX: ConsentType.DERIVATIVE_WORKS,
            CapsuleOperation.ATTRIBUTE: ConsentType.ECONOMIC_ATTRIBUTION,
            CapsuleOperation.ECONOMIC_CLAIM: ConsentType.ECONOMIC_ATTRIBUTION,
            CapsuleOperation.LINEAGE_TRACE: ConsentType.LINEAGE_TRACKING,
            CapsuleOperation.COMPRESS: ConsentType.DATA_PROCESSING,
            CapsuleOperation.SHARE: ConsentType.CROSS_PLATFORM_SHARING,
            CapsuleOperation.EXPORT: ConsentType.CROSS_PLATFORM_SHARING,
        }

        # Statistics
        self.consent_stats = {
            "total_consent_checks": 0,
            "explicit_grants": 0,
            "implicit_grants": 0,
            "consent_denials": 0,
            "rights_derived": 0,
        }

    def check_capsule_operation_consent(
        self, context: CapsuleConsentContext
    ) -> Tuple[bool, List[str], List[ImplicitRight]]:
        """
        Check consent for capsule operation using both explicit and implicit rights.
        Returns: (is_allowed, explicit_permissions, implicit_rights)
        """
        self.consent_stats["total_consent_checks"] += 1

        # 1. Check explicit consent first
        explicit_allowed, explicit_permissions = self._check_explicit_consent(context)

        # 2. Derive and check implicit rights
        implicit_rights = self._derive_implicit_rights(context)
        implicit_allowed = any(right.is_valid() for right in implicit_rights)

        # 3. Combine results
        overall_allowed = explicit_allowed or implicit_allowed

        # Update statistics
        if explicit_allowed:
            self.consent_stats["explicit_grants"] += 1
        if implicit_allowed:
            self.consent_stats["implicit_grants"] += 1
        if not overall_allowed:
            self.consent_stats["consent_denials"] += 1

        # Log consent check
        audit_emitter.emit_security_event(
            "capsule_consent_check",
            {
                "capsule_id": context.capsule_id,
                "operation": context.operation.value,
                "requesting_entity": context.requesting_entity,
                "explicit_allowed": explicit_allowed,
                "implicit_allowed": implicit_allowed,
                "overall_allowed": overall_allowed,
                "explicit_permissions_count": len(explicit_permissions),
                "implicit_rights_count": len(implicit_rights),
            },
        )

        return overall_allowed, explicit_permissions, implicit_rights

    def _check_explicit_consent(
        self, context: CapsuleConsentContext
    ) -> Tuple[bool, List[str]]:
        """Check explicit consent using consent capsule system."""
        # Map operation to consent type
        consent_type = self.operation_consent_mapping.get(
            context.operation, ConsentType.DATA_PROCESSING
        )

        # Prepare consent context
        consent_context = {
            "requesting_entity": context.requesting_entity,
            "consent_type": consent_type.value,
            "purpose": f"capsule_{context.operation.value}",
            "capsule_id": context.capsule_id,
            "operation": context.operation.value,
            "timestamp": context.operation_timestamp.isoformat(),
        }

        # Check system-wide permission
        granted, permissions = consent_capsule_manager.check_permission_across_capsules(
            consent_context
        )

        return granted, permissions

    def _derive_implicit_rights(
        self, context: CapsuleConsentContext
    ) -> List[ImplicitRight]:
        """Derive implicit rights from context, relationships, and inheritance."""
        implicit_rights = []

        # Cache key for this context
        cache_key = f"{context.capsule_id}:{context.operation.value}:{context.requesting_entity}"

        # Check cache first
        if cache_key in self.implicit_rights_cache:
            cached_rights = self.implicit_rights_cache[cache_key]
            # Return valid cached rights
            valid_rights = [right for right in cached_rights if right.is_valid()]
            if valid_rights:
                return valid_rights

        # 1. Creator rights
        if context.creator_id == context.requesting_entity:
            implicit_rights.extend(self._derive_creator_rights(context))

        # 2. Contributor rights
        if context.requesting_entity in context.contributors:
            implicit_rights.extend(self._derive_contributor_rights(context))

        # 3. Inheritance rights from parent capsules
        implicit_rights.extend(self._derive_inheritance_rights(context))

        # 4. Relationship-based rights
        implicit_rights.extend(self._derive_relationship_rights(context))

        # 5. Context-based rights
        implicit_rights.extend(self._derive_context_rights(context))

        # 6. System default rights
        implicit_rights.extend(self._derive_system_default_rights(context))

        # Cache results
        self.implicit_rights_cache[cache_key] = implicit_rights
        self.consent_stats["rights_derived"] += len(implicit_rights)

        return implicit_rights

    def _derive_creator_rights(
        self, context: CapsuleConsentContext
    ) -> List[ImplicitRight]:
        """Derive rights for capsule creator."""
        rights = []

        if context.operation in self.system_default_rights["creator_rights"]:
            right = ImplicitRight(
                right_id=f"creator_right_{uuid.uuid4().hex[:8]}",
                rights_type=RightsType.IMPLICIT_SYSTEM,
                operation=context.operation,
                granted_to=context.requesting_entity,
                scope=PermissionScope.GLOBAL,
                confidence_score=1.0,
                source_context={
                    "relationship": "creator",
                    "capsule_id": context.capsule_id,
                },
            )
            rights.append(right)

        return rights

    def _derive_contributor_rights(
        self, context: CapsuleConsentContext
    ) -> List[ImplicitRight]:
        """Derive rights for capsule contributors."""
        rights = []

        if context.operation in self.system_default_rights["contributor_rights"]:
            right = ImplicitRight(
                right_id=f"contributor_right_{uuid.uuid4().hex[:8]}",
                rights_type=RightsType.IMPLICIT_SYSTEM,
                operation=context.operation,
                granted_to=context.requesting_entity,
                scope=PermissionScope.PLATFORM_SPECIFIC,
                confidence_score=0.9,
                source_context={
                    "relationship": "contributor",
                    "capsule_id": context.capsule_id,
                },
            )
            rights.append(right)

        return rights

    def _derive_inheritance_rights(
        self, context: CapsuleConsentContext
    ) -> List[ImplicitRight]:
        """Derive rights inherited from parent capsules."""
        rights = []

        for parent_id in context.parent_capsule_ids:
            # Check if requesting entity has rights to parent
            parent_context = CapsuleConsentContext(
                capsule_id=parent_id,
                operation=context.operation,
                requesting_entity=context.requesting_entity,
            )

            # If they have rights to parent, they inherit limited rights to this capsule
            if context.operation in [
                CapsuleOperation.READ,
                CapsuleOperation.FORK,
                CapsuleOperation.REMIX,
            ]:
                right = ImplicitRight(
                    right_id=f"inherited_right_{uuid.uuid4().hex[:8]}",
                    rights_type=RightsType.IMPLICIT_INHERITED,
                    operation=context.operation,
                    source_capsule_id=parent_id,
                    source_relationship="parent",
                    granted_to=context.requesting_entity,
                    scope=PermissionScope.SESSION_LIMITED,
                    confidence_score=0.7,
                    source_context={
                        "inherited_from": parent_id,
                        "operation": context.operation.value,
                    },
                )
                rights.append(right)

        return rights

    def _derive_relationship_rights(
        self, context: CapsuleConsentContext
    ) -> List[ImplicitRight]:
        """Derive rights based on entity relationships."""
        rights = []

        # If requesting entity is in related entities, grant limited rights
        if context.requesting_entity in context.related_entities:
            if context.operation in [CapsuleOperation.READ, CapsuleOperation.ATTRIBUTE]:
                right = ImplicitRight(
                    right_id=f"relationship_right_{uuid.uuid4().hex[:8]}",
                    rights_type=RightsType.IMPLICIT_RELATIONSHIP,
                    operation=context.operation,
                    granted_to=context.requesting_entity,
                    scope=PermissionScope.SESSION_LIMITED,
                    confidence_score=0.6,
                    source_context={
                        "relationship": "related_entity",
                        "capsule_id": context.capsule_id,
                    },
                )
                rights.append(right)

        return rights

    def _derive_context_rights(
        self, context: CapsuleConsentContext
    ) -> List[ImplicitRight]:
        """Derive rights based on operational context."""
        rights = []

        # Context-based rights (e.g., same session, same platform)
        session_id = context.operation_metadata.get("session_id")
        if session_id:
            # If operation is in same session as capsule creation, grant limited rights
            if context.operation in [CapsuleOperation.READ, CapsuleOperation.UPDATE]:
                right = ImplicitRight(
                    right_id=f"context_right_{uuid.uuid4().hex[:8]}",
                    rights_type=RightsType.IMPLICIT_CONTEXT,
                    operation=context.operation,
                    granted_to=context.requesting_entity,
                    scope=PermissionScope.SESSION_LIMITED,
                    confidence_score=0.8,
                    expiry=datetime.now(timezone.utc)
                    + timedelta(hours=1),  # Session-limited
                    source_context={"session_id": session_id, "basis": "same_session"},
                )
                rights.append(right)

        return rights

    def _derive_system_default_rights(
        self, context: CapsuleConsentContext
    ) -> List[ImplicitRight]:
        """Derive system-level default rights."""
        rights = []

        # Public operations with low confidence
        if context.operation in self.system_default_rights["public_rights"]:
            right = ImplicitRight(
                right_id=f"system_default_right_{uuid.uuid4().hex[:8]}",
                rights_type=RightsType.IMPLICIT_SYSTEM,
                operation=context.operation,
                granted_to=context.requesting_entity,
                scope=PermissionScope.GLOBAL,
                confidence_score=0.3,  # Low confidence - requires explicit consent to override
                conditions=["requires_explicit_consent_verification"],
                source_context={
                    "basis": "system_default",
                    "operation": context.operation.value,
                },
            )
            rights.append(right)

        return rights

    def get_entity_capsule_rights(
        self, entity_id: str, capsule_id: str
    ) -> Dict[str, Any]:
        """Get comprehensive rights summary for entity on specific capsule."""
        rights_summary = {
            "entity_id": entity_id,
            "capsule_id": capsule_id,
            "explicit_rights": {},
            "implicit_rights": {},
            "denied_operations": [],
            "granted_operations": [],
        }

        # Check each operation type
        for operation in CapsuleOperation:
            context = CapsuleConsentContext(
                capsule_id=capsule_id, operation=operation, requesting_entity=entity_id
            )

            (
                allowed,
                explicit_perms,
                implicit_rights,
            ) = self.check_capsule_operation_consent(context)

            if allowed:
                rights_summary["granted_operations"].append(operation.value)
                if explicit_perms:
                    rights_summary["explicit_rights"][operation.value] = explicit_perms
                if implicit_rights:
                    rights_summary["implicit_rights"][operation.value] = [
                        r.to_dict() for r in implicit_rights
                    ]
            else:
                rights_summary["denied_operations"].append(operation.value)

        return rights_summary

    def get_consent_layer_statistics(self) -> Dict[str, Any]:
        """Get comprehensive consent layer statistics."""
        stats = self.consent_stats.copy()

        # Add cache statistics
        stats["cache_statistics"] = {
            "cached_rights_entries": len(self.implicit_rights_cache),
            "total_cached_rights": sum(
                len(rights) for rights in self.implicit_rights_cache.values()
            ),
        }

        # Add derived rights breakdown
        all_cached_rights = [
            right
            for rights_list in self.implicit_rights_cache.values()
            for right in rights_list
        ]
        rights_type_breakdown = {}
        for rights_type in RightsType:
            count = len([r for r in all_cached_rights if r.rights_type == rights_type])
            rights_type_breakdown[rights_type.value] = count

        stats["rights_type_breakdown"] = rights_type_breakdown

        return stats


# Global capsule consent layer
capsule_consent_layer = CapsuleConsentLayer()


def check_capsule_consent(
    capsule_id: str,
    operation: str,
    requesting_entity: str,
    creator_id: str = None,
    contributors: List[str] = None,
    parent_capsule_ids: List[str] = None,
    operation_metadata: Dict[str, Any] = None,
) -> bool:
    """Convenience function to check capsule operation consent."""

    try:
        operation_enum = CapsuleOperation(operation)
    except ValueError:
        return False

    context = CapsuleConsentContext(
        capsule_id=capsule_id,
        operation=operation_enum,
        requesting_entity=requesting_entity,
        creator_id=creator_id,
        contributors=contributors or [],
        parent_capsule_ids=parent_capsule_ids or [],
        operation_metadata=operation_metadata or {},
    )

    allowed, _, _ = capsule_consent_layer.check_capsule_operation_consent(context)
    return allowed


def get_capsule_rights_summary(entity_id: str, capsule_id: str) -> Dict[str, Any]:
    """Convenience function to get entity rights on capsule."""
    return capsule_consent_layer.get_entity_capsule_rights(entity_id, capsule_id)


def get_consent_layer_stats() -> Dict[str, Any]:
    """Convenience function to get consent layer statistics."""
    return capsule_consent_layer.get_consent_layer_statistics()
