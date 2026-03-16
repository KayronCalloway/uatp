"""
Model License SQLAlchemy Model - UATP 7.2 Model Registry Protocol

License tracking and compliance verification for AI models.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, Optional

from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import UUID as PGUUID

from src.core.database import db


class LicenseType(str, Enum):
    """Common open-source and proprietary license types."""

    # Permissive open source
    MIT = "MIT"
    APACHE_2_0 = "Apache-2.0"
    BSD_3_CLAUSE = "BSD-3-Clause"

    # Copyleft
    GPL_3_0 = "GPL-3.0"
    LGPL_3_0 = "LGPL-3.0"
    AGPL_3_0 = "AGPL-3.0"

    # Creative Commons
    CC_BY_4_0 = "CC-BY-4.0"
    CC_BY_SA_4_0 = "CC-BY-SA-4.0"
    CC_BY_NC_4_0 = "CC-BY-NC-4.0"
    CC_BY_NC_SA_4_0 = "CC-BY-NC-SA-4.0"

    # AI-specific
    OPENRAIL = "OpenRAIL"
    OPENRAIL_M = "OpenRAIL-M"
    LLAMA_2_COMMUNITY = "Llama-2-Community"
    LLAMA_3_COMMUNITY = "Llama-3-Community"

    # Proprietary
    PROPRIETARY = "proprietary"
    COMMERCIAL = "commercial"
    EVALUATION_ONLY = "evaluation-only"

    # Custom
    CUSTOM = "custom"


class Permission(str, Enum):
    """License permissions."""

    COMMERCIAL_USE = "commercial_use"
    DERIVATIVE_WORKS = "derivative_works"
    DISTRIBUTION = "distribution"
    MODIFICATION = "modification"
    PRIVATE_USE = "private_use"
    PATENT_USE = "patent_use"


class Restriction(str, Enum):
    """License restrictions."""

    NO_COMMERCIAL = "no_commercial"
    NO_DERIVATIVE = "no_derivative"
    NO_DISTRIBUTION = "no_distribution"
    ATTRIBUTION_REQUIRED = "attribution_required"
    SHARE_ALIKE = "share_alike"
    NO_MEDICAL = "no_medical"
    NO_MILITARY = "no_military"
    NO_SURVEILLANCE = "no_surveillance"
    NO_HARM = "no_harm"
    GEOGRAPHIC_RESTRICTION = "geographic_restriction"


class ModelLicenseModel(db.Base):
    """
    SQLAlchemy model for model licenses.

    Tracks license terms, permissions, restrictions, and compliance
    requirements for AI models.
    """

    __tablename__ = "model_licenses"

    id = Column(Integer, primary_key=True)
    license_id = Column(String(64), unique=True, nullable=False, index=True)
    model_id = Column(
        String(64),
        ForeignKey("model_registry.model_id"),
        nullable=False,
        index=True,
    )

    # License identification
    license_type = Column(String(100), nullable=False)
    license_name = Column(String(255), nullable=True)
    license_url = Column(String(512), nullable=True)
    license_text = Column(Text, nullable=True)

    # Permissions and restrictions
    permissions = Column(JSON, nullable=False)
    restrictions = Column(JSON, nullable=False)
    conditions = Column(JSON, nullable=True)

    # Attribution and usage
    attribution_requirements = Column(JSON, nullable=True)
    usage_limitations = Column(JSON, nullable=True)

    # Validity period
    effective_date = Column(DateTime(timezone=True), nullable=False)
    expiration_date = Column(DateTime(timezone=True), nullable=True)

    # License chain
    supersedes_license_id = Column(String(64), nullable=True)

    # Verification
    verification = Column(JSON, nullable=True)

    # Status
    is_active = Column(Boolean, nullable=False, default=True)

    # Ownership
    owner_id = Column(PGUUID(as_uuid=True), ForeignKey("users.id"), nullable=True)

    # Timestamps
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    def __repr__(self) -> str:
        return f"<ModelLicense(license_id={self.license_id}, type={self.license_type})>"

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "license_id": self.license_id,
            "model_id": self.model_id,
            "license_type": self.license_type,
            "license_name": self.license_name,
            "license_url": self.license_url,
            "license_text": self.license_text,
            "permissions": self.permissions,
            "restrictions": self.restrictions,
            "conditions": self.conditions,
            "attribution_requirements": self.attribution_requirements,
            "usage_limitations": self.usage_limitations,
            "effective_date": self.effective_date.isoformat()
            if self.effective_date
            else None,
            "expiration_date": self.expiration_date.isoformat()
            if self.expiration_date
            else None,
            "supersedes_license_id": self.supersedes_license_id,
            "verification": self.verification,
            "is_active": self.is_active,
            "owner_id": str(self.owner_id) if self.owner_id else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    @property
    def is_expired(self) -> bool:
        """Check if license has expired."""
        if not self.expiration_date:
            return False
        return datetime.now(self.expiration_date.tzinfo) > self.expiration_date

    @property
    def is_perpetual(self) -> bool:
        """Check if license is perpetual (no expiration)."""
        return self.expiration_date is None

    def allows_commercial_use(self) -> bool:
        """Check if license permits commercial use."""
        permissions = self.permissions or []
        restrictions = self.restrictions or []
        return (
            Permission.COMMERCIAL_USE.value in permissions
            and Restriction.NO_COMMERCIAL.value not in restrictions
        )

    def allows_derivative_works(self) -> bool:
        """Check if license permits derivative works."""
        permissions = self.permissions or []
        restrictions = self.restrictions or []
        return (
            Permission.DERIVATIVE_WORKS.value in permissions
            and Restriction.NO_DERIVATIVE.value not in restrictions
        )

    def requires_attribution(self) -> bool:
        """Check if license requires attribution."""
        restrictions = self.restrictions or []
        return Restriction.ATTRIBUTION_REQUIRED.value in restrictions

    def get_required_attribution(self) -> Optional[Dict[str, Any]]:
        """Get required attribution information."""
        if not self.requires_attribution():
            return None
        return self.attribution_requirements
