"""
Base classes for UATP Schema - OpenLineage-inspired facet pattern.

Every facet includes:
- _producer: URI identifying the system that created this facet
- _schemaURL: URI to the JSON Schema for validation (versioned)
- _deleted: Optional flag for facet removal with tracking

This ensures machine legibility and interoperability.
"""

import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, ClassVar, Dict, List, Optional, Type

# Pre-compiled regex patterns for facet_key conversion
_CAMEL_TO_SNAKE_1 = re.compile(r"([a-z])([A-Z])")
_CAMEL_TO_SNAKE_2 = re.compile(r"([A-Z]+)([A-Z][a-z])")

# Default producer URI
UATP_PRODUCER = "urn:uatp-capsule-engine:1.0"
UATP_SCHEMA_BASE = "https://uatp.dev/spec/facets"
UATP_FACET_VERSION = "1.0"


class FacetEntityType(Enum):
    """Entity type that a facet attaches to."""

    RUN = "run"
    JOB = "job"
    DATASET = "dataset"
    INPUT = "input"
    OUTPUT = "output"


@dataclass
class BaseFacet:
    """
    Base class for all UATP facets.

    Following OpenLineage convention:
    - _producer: URI of producing system
    - _schemaURL: URI to JSON Schema (versioned)
    - _deleted: Optional flag for facet removal
    - _deleted_at: When facet was deleted
    - _deletion_reason: Why facet was deleted
    """

    _producer: str = field(default=UATP_PRODUCER)
    _schemaURL: str = field(default="")
    _deleted: bool = field(default=False)
    _deleted_at: Optional[datetime] = field(default=None)
    _deletion_reason: Optional[str] = field(default=None)

    # Class-level version (override in subclasses for independent versioning)
    _facet_version: ClassVar[str] = UATP_FACET_VERSION

    def __post_init__(self):
        if not self._schemaURL:
            # Auto-generate versioned schema URL
            version = getattr(self.__class__, "_facet_version", UATP_FACET_VERSION)
            self._schemaURL = (
                f"{UATP_SCHEMA_BASE}/v{version}/{self.__class__.__name__}.json"
            )

    def delete(self, reason: Optional[str] = None) -> None:
        """Mark facet as deleted (tombstone pattern)."""
        self._deleted = True
        self._deleted_at = datetime.now(timezone.utc)
        self._deletion_reason = reason

    def to_dict(self) -> Dict[str, Any]:
        """Convert facet to dictionary for serialization."""
        result = {
            "_producer": self._producer,
            "_schemaURL": self._schemaURL,
        }
        if self._deleted:
            result["_deleted"] = True
            if self._deleted_at:
                result["_deletedAt"] = self._deleted_at.isoformat()
            if self._deletion_reason:
                result["_deletionReason"] = self._deletion_reason

        # Add all non-underscore fields
        for key, value in self.__dict__.items():
            if not key.startswith("_"):
                if hasattr(value, "to_dict"):
                    result[key] = value.to_dict()
                elif isinstance(value, datetime):
                    result[key] = value.isoformat()
                elif isinstance(value, list):
                    result[key] = [
                        v.to_dict() if hasattr(v, "to_dict") else v for v in value
                    ]
                else:
                    result[key] = value

        return result

    @classmethod
    def facet_key(cls) -> str:
        """
        Return the key used in facet dictionaries.
        Convention: uatp_{name} in snake_case.

        Examples:
            UATPSignatureRunFacet -> uatp_signature
            UATPCapsuleDatasetFacet -> uatp_capsule
        """
        name = cls.__name__

        # Remove 'UATP' prefix if present
        if name.startswith("UATP"):
            name = name[4:]

        # Remove 'Facet' suffix if present
        if name.endswith("Facet"):
            name = name[:-5]

        # Remove entity suffix (Run, Job, Dataset)
        for suffix in ("Run", "Job", "Dataset"):
            if name.endswith(suffix):
                name = name[: -len(suffix)]
                break

        # Convert CamelCase to snake_case using pre-compiled patterns
        snake = _CAMEL_TO_SNAKE_1.sub(r"\1_\2", name)
        snake = _CAMEL_TO_SNAKE_2.sub(r"\1_\2", snake)

        return f"uatp_{snake.lower()}"


@dataclass
class RunFacet(BaseFacet):
    """Base for facets attached to Run (capsule execution instance)."""

    pass


@dataclass
class JobFacet(BaseFacet):
    """Base for facets attached to Job (capture type definition)."""

    pass


@dataclass
class DatasetFacet(BaseFacet):
    """Base for facets attached to Dataset (input/output data)."""

    pass


# --- Helper functions ---


def utc_now() -> datetime:
    """Get current UTC datetime."""
    return datetime.now(timezone.utc)


def facets_to_dict(facets: Dict[str, BaseFacet]) -> Dict[str, Dict]:
    """Convert a dict of facets to serializable format."""
    return {key: facet.to_dict() for key, facet in facets.items()}


# --- Facet Registry ---


class FacetRegistry:
    """
    Registry of available facets for discovery and validation.

    Usage:
        FacetRegistry.register(
            UATPSignatureRunFacet,
            entity_type=FacetEntityType.RUN,
            description="Cryptographic signature metadata",
            tags=["security", "verification"],
        )

        # Discover facets
        security_facets = FacetRegistry.list_facets(tag="security")
    """

    _facets: Dict[str, Type[BaseFacet]] = {}
    _metadata: Dict[str, Dict[str, Any]] = {}

    @classmethod
    def register(
        cls,
        facet_class: Type[BaseFacet],
        entity_type: FacetEntityType,
        description: str = "",
        tags: Optional[List[str]] = None,
    ) -> Type[BaseFacet]:
        """
        Register a facet class.

        Can be used as a decorator or called directly.
        """
        key = facet_class.facet_key()
        version = getattr(facet_class, "_facet_version", UATP_FACET_VERSION)

        cls._facets[key] = facet_class
        cls._metadata[key] = {
            "class": facet_class,
            "class_name": facet_class.__name__,
            "key": key,
            "entity_type": entity_type.value,
            "version": version,
            "description": description,
            "tags": tags or [],
            "schema_url": f"{UATP_SCHEMA_BASE}/v{version}/{facet_class.__name__}.json",
        }

        return facet_class

    @classmethod
    def get_facet(cls, key: str) -> Optional[Type[BaseFacet]]:
        """Look up facet class by key."""
        return cls._facets.get(key)

    @classmethod
    def get_metadata(cls, key: str) -> Optional[Dict[str, Any]]:
        """Get metadata for a facet."""
        return cls._metadata.get(key)

    @classmethod
    def list_facets(
        cls,
        entity_type: Optional[FacetEntityType] = None,
        tag: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """List registered facets with optional filtering."""
        results = []
        for key, meta in cls._metadata.items():
            if entity_type and meta["entity_type"] != entity_type.value:
                continue
            if tag and tag not in meta["tags"]:
                continue
            results.append(meta)
        return results

    @classmethod
    def list_keys(cls) -> List[str]:
        """List all registered facet keys."""
        return list(cls._facets.keys())

    @classmethod
    def clear(cls) -> None:
        """Clear registry (for testing)."""
        cls._facets.clear()
        cls._metadata.clear()
