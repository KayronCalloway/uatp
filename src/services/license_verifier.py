"""
License Verifier Service - UATP 7.2 Model Registry Protocol

Provides license compliance verification for AI models:
- Usage permission checking
- License compatibility analysis
- Attribution requirement validation
- Restriction enforcement
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Set

logger = logging.getLogger(__name__)


class UsageType(str, Enum):
    """Types of model usage."""

    INFERENCE = "inference"
    FINE_TUNING = "fine_tuning"
    EMBEDDING = "embedding"
    COMMERCIAL = "commercial"
    RESEARCH = "research"
    EDUCATION = "education"
    DERIVATIVE_WORK = "derivative_work"
    DISTRIBUTION = "distribution"
    DEPLOYMENT = "deployment"


class ComplianceStatus(str, Enum):
    """License compliance status."""

    COMPLIANT = "compliant"
    NON_COMPLIANT = "non_compliant"
    REQUIRES_REVIEW = "requires_review"
    EXPIRED = "expired"
    UNKNOWN = "unknown"


@dataclass
class ComplianceResult:
    """Result of compliance verification."""

    status: ComplianceStatus
    compliant: bool
    usage_type: UsageType
    license_type: str
    violations: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    required_actions: List[str] = field(default_factory=list)
    attribution: Optional[Dict[str, Any]] = None
    verified_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "status": self.status.value,
            "compliant": self.compliant,
            "usage_type": self.usage_type.value,
            "license_type": self.license_type,
            "violations": self.violations,
            "warnings": self.warnings,
            "required_actions": self.required_actions,
            "attribution": self.attribution,
            "verified_at": self.verified_at.isoformat(),
        }


@dataclass
class CompatibilityResult:
    """Result of license compatibility check."""

    compatible: bool
    source_licenses: List[str]
    target_license: str
    issues: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "compatible": self.compatible,
            "source_licenses": self.source_licenses,
            "target_license": self.target_license,
            "issues": self.issues,
            "recommendations": self.recommendations,
        }


# License permission and restriction definitions
LICENSE_DEFINITIONS: Dict[str, Dict[str, Any]] = {
    "MIT": {
        "permissions": [
            "commercial_use",
            "derivative_works",
            "distribution",
            "modification",
            "private_use",
        ],
        "restrictions": ["attribution_required"],
        "conditions": ["include_license", "include_copyright"],
        "copyleft": False,
    },
    "Apache-2.0": {
        "permissions": [
            "commercial_use",
            "derivative_works",
            "distribution",
            "modification",
            "private_use",
            "patent_use",
        ],
        "restrictions": ["attribution_required"],
        "conditions": ["include_license", "state_changes"],
        "copyleft": False,
    },
    "GPL-3.0": {
        "permissions": [
            "commercial_use",
            "derivative_works",
            "distribution",
            "modification",
            "private_use",
            "patent_use",
        ],
        "restrictions": ["attribution_required", "share_alike"],
        "conditions": ["include_license", "disclose_source", "same_license"],
        "copyleft": True,
    },
    "CC-BY-4.0": {
        "permissions": [
            "commercial_use",
            "derivative_works",
            "distribution",
            "modification",
            "private_use",
        ],
        "restrictions": ["attribution_required"],
        "conditions": ["include_license", "give_credit"],
        "copyleft": False,
    },
    "CC-BY-NC-4.0": {
        "permissions": [
            "derivative_works",
            "distribution",
            "modification",
            "private_use",
        ],
        "restrictions": ["attribution_required", "no_commercial"],
        "conditions": ["include_license", "give_credit"],
        "copyleft": False,
    },
    "OpenRAIL-M": {
        "permissions": [
            "commercial_use",
            "derivative_works",
            "distribution",
            "modification",
            "private_use",
        ],
        "restrictions": ["attribution_required", "no_harm", "no_illegal"],
        "conditions": ["include_license", "behavioral_restrictions"],
        "copyleft": False,
    },
    "Llama-2-Community": {
        "permissions": [
            "commercial_use",
            "derivative_works",
            "distribution",
            "modification",
            "private_use",
        ],
        "restrictions": ["attribution_required", "monthly_user_limit"],
        "conditions": ["include_license", "acceptable_use"],
        "copyleft": False,
        "special_restrictions": {
            "monthly_active_users": 700_000_000,
        },
    },
    "proprietary": {
        "permissions": ["private_use"],
        "restrictions": ["no_commercial", "no_derivative", "no_distribution"],
        "conditions": ["specific_agreement"],
        "copyleft": False,
    },
}

# License compatibility matrix (source -> target)
LICENSE_COMPATIBILITY: Dict[str, Set[str]] = {
    "MIT": {"MIT", "Apache-2.0", "GPL-3.0", "LGPL-3.0", "CC-BY-4.0", "OpenRAIL-M"},
    "Apache-2.0": {"Apache-2.0", "GPL-3.0", "LGPL-3.0"},
    "CC-BY-4.0": {"CC-BY-4.0", "CC-BY-SA-4.0"},
    "CC-BY-NC-4.0": {"CC-BY-NC-4.0", "CC-BY-NC-SA-4.0"},
    "GPL-3.0": {"GPL-3.0"},  # Copyleft - must remain GPL
    "OpenRAIL-M": {"OpenRAIL-M"},  # Typically self-contained
    "Llama-2-Community": {"Llama-2-Community"},  # Must maintain Llama license
}


class LicenseVerifier:
    """
    Service for verifying license compliance.

    Checks model usage against license terms and provides
    compliance guidance.
    """

    def __init__(self):
        """Initialize license verifier."""
        self.license_definitions = LICENSE_DEFINITIONS
        self.compatibility_matrix = LICENSE_COMPATIBILITY

    def verify_compliance(
        self,
        license_type: str,
        usage_type: UsageType,
        additional_permissions: Optional[List[str]] = None,
        additional_restrictions: Optional[List[str]] = None,
        is_expired: bool = False,
    ) -> ComplianceResult:
        """
        Verify compliance for a specific usage.

        Args:
            license_type: Type of license
            usage_type: Intended usage
            additional_permissions: Additional permissions granted (cannot override base license restrictions)
            additional_restrictions: Additional restrictions applied (additive only)
            is_expired: Whether license has expired

        Returns:
            ComplianceResult with compliance status

        SECURITY NOTE: additional_permissions can only ADD permissions beyond the base license,
        they cannot remove restrictions defined by the license. This prevents callers from
        bypassing license restrictions (e.g., commercial use of GPL models).
        """
        violations = []
        warnings = []
        required_actions = []
        attribution = None

        # Handle expired licenses
        if is_expired:
            return ComplianceResult(
                status=ComplianceStatus.EXPIRED,
                compliant=False,
                usage_type=usage_type,
                license_type=license_type,
                violations=["License has expired"],
            )

        # Get license definition
        license_def = self.license_definitions.get(license_type)
        if not license_def:
            return ComplianceResult(
                status=ComplianceStatus.UNKNOWN,
                compliant=False,
                usage_type=usage_type,
                license_type=license_type,
                violations=[f"Unknown license type: {license_type}"],
                warnings=["Manual review required for unknown license types"],
            )

        # SECURITY: Start with base license permissions and restrictions
        # Additional permissions can be ADDED but cannot override base restrictions
        # Additional restrictions can only ADD more restrictions
        base_permissions = set(license_def.get("permissions", []))
        base_restrictions = set(license_def.get("restrictions", []))

        # Union of permissions (additional permissions can add, not replace)
        effective_permissions = base_permissions.union(
            set(additional_permissions or [])
        )

        # Union of restrictions (can only add more restrictions, never remove)
        effective_restrictions = base_restrictions.union(
            set(additional_restrictions or [])
        )

        # Check usage against permissions and restrictions
        if usage_type == UsageType.COMMERCIAL:
            if "no_commercial" in effective_restrictions:
                violations.append("Commercial use is prohibited by license")
            elif "commercial_use" not in effective_permissions:
                warnings.append("Commercial use not explicitly permitted")

        elif usage_type == UsageType.DERIVATIVE_WORK:
            if "no_derivative" in effective_restrictions:
                violations.append("Derivative works are prohibited by license")
            elif "derivative_works" not in effective_permissions:
                warnings.append("Derivative works not explicitly permitted")

        elif usage_type == UsageType.DISTRIBUTION:
            if "no_distribution" in effective_restrictions:
                violations.append("Distribution is prohibited by license")
            elif "distribution" not in effective_permissions:
                warnings.append("Distribution not explicitly permitted")

        elif usage_type == UsageType.FINE_TUNING:
            if "no_derivative" in effective_restrictions:
                violations.append("Fine-tuning (derivative work) prohibited by license")
            if "modification" not in effective_permissions:
                warnings.append("Modification not explicitly permitted")

        # Check for attribution requirements
        if "attribution_required" in effective_restrictions:
            required_actions.append("Attribution required in documentation")
            attribution = {
                "required": True,
                "format": "Include original license and copyright notice",
            }

        # Check for share-alike requirements
        if "share_alike" in effective_restrictions:
            required_actions.append("Derivative works must use same license")
            if usage_type == UsageType.DERIVATIVE_WORK:
                warnings.append(
                    "Copyleft license requires same licensing for derivatives"
                )

        # Check special restrictions
        special = license_def.get("special_restrictions", {})
        if "monthly_active_users" in special:
            warnings.append(
                f"Commercial use limited to {special['monthly_active_users']:,} monthly users"
            )

        # Determine compliance status
        if violations:
            status = ComplianceStatus.NON_COMPLIANT
            compliant = False
        elif warnings:
            status = ComplianceStatus.REQUIRES_REVIEW
            compliant = True  # Technically compliant but needs attention
        else:
            status = ComplianceStatus.COMPLIANT
            compliant = True

        return ComplianceResult(
            status=status,
            compliant=compliant,
            usage_type=usage_type,
            license_type=license_type,
            violations=violations,
            warnings=warnings,
            required_actions=required_actions,
            attribution=attribution,
        )

    def check_compatibility(
        self,
        source_licenses: List[str],
        target_license: str,
    ) -> CompatibilityResult:
        """
        Check if source licenses are compatible with target license.

        Args:
            source_licenses: Licenses of source/base models
            target_license: Intended license for derivative work

        Returns:
            CompatibilityResult with compatibility status
        """
        issues = []
        recommendations = []
        compatible = True

        for source in source_licenses:
            # Get compatibility set for source
            compat_set = self.compatibility_matrix.get(source, set())

            if target_license not in compat_set:
                compatible = False
                issues.append(
                    f"License '{source}' may not be compatible with '{target_license}'"
                )

            # Check copyleft requirements
            source_def = self.license_definitions.get(source, {})
            if source_def.get("copyleft"):
                if target_license != source:
                    compatible = False
                    issues.append(
                        f"Copyleft license '{source}' requires derivative to use same license"
                    )
                    recommendations.append(f"Use '{source}' for derivative work")

        # Check for restrictive source licenses
        restrictive_sources = [
            s for s in source_licenses if "NC" in s or "proprietary" in s
        ]
        if restrictive_sources:
            recommendations.append(
                f"Note: Source includes restrictive licenses: {restrictive_sources}"
            )

        # Check target license requirements
        target_def = self.license_definitions.get(target_license, {})
        if not target_def:
            issues.append(f"Unknown target license: {target_license}")
            compatible = False

        return CompatibilityResult(
            compatible=compatible,
            source_licenses=source_licenses,
            target_license=target_license,
            issues=issues,
            recommendations=recommendations,
        )

    def get_license_info(self, license_type: str) -> Optional[Dict[str, Any]]:
        """
        Get information about a license type.

        Args:
            license_type: License identifier

        Returns:
            License definition or None
        """
        return self.license_definitions.get(license_type)

    def list_supported_licenses(self) -> List[str]:
        """List all supported license types."""
        return list(self.license_definitions.keys())

    def generate_attribution_notice(
        self,
        model_name: str,
        license_type: str,
        copyright_holder: Optional[str] = None,
        license_url: Optional[str] = None,
    ) -> str:
        """
        Generate attribution notice text.

        Args:
            model_name: Name of the model
            license_type: License type
            copyright_holder: Copyright holder name
            license_url: URL to license text

        Returns:
            Formatted attribution notice
        """
        notice_parts = [f"Model: {model_name}"]

        if copyright_holder:
            notice_parts.append(f"Copyright: {copyright_holder}")

        notice_parts.append(f"License: {license_type}")

        if license_url:
            notice_parts.append(f"License URL: {license_url}")

        return "\n".join(notice_parts)


# Singleton instance
license_verifier = LicenseVerifier()
