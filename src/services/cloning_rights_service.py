"""
Cloning Rights Service for UATP Capsule Engine

This service manages licensing for moral models and defines cloning rights,
providing comprehensive licensing models for AI model intellectual property.
"""

import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from src.capsule_schema import (
    CapsuleStatus,
    CloningRightsCapsule,
    CloningRightsPayload,
    Verification,
)

logger = logging.getLogger(__name__)


@dataclass
class LicenseRegistry:
    """Registry for tracking active licenses and their status."""

    active_licenses: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    expired_licenses: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    revoked_licenses: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    license_usage_logs: Dict[str, List[Dict[str, Any]]] = field(default_factory=dict)


@dataclass
class ModelRights:
    """Represents the rights and restrictions for a specific model."""

    model_id: str
    owner_agent_id: str
    base_license_type: str
    default_restrictions: List[str]
    royalty_rates: Dict[str, float]
    moral_constraints: List[str]
    creation_date: datetime
    last_updated: datetime


class CloningRightsService:
    """Service for managing model licensing and cloning rights."""

    def __init__(self):
        self.license_registry = LicenseRegistry()
        self.model_rights_db: Dict[str, ModelRights] = {}
        self.license_templates: Dict[str, Dict[str, Any]] = (
            self._init_license_templates()
        )

    def _init_license_templates(self) -> Dict[str, Dict[str, Any]]:
        """Initialize standard license templates."""
        return {
            "exclusive": {
                "description": "Exclusive license with full rights transfer",
                "cloning_permitted": True,
                "modification_permitted": True,
                "redistribution_permitted": True,
                "attribution_required": False,
                "default_royalty": 0.0,
                "usage_restrictions": [],
            },
            "non_exclusive": {
                "description": "Non-exclusive license with shared usage rights",
                "cloning_permitted": False,
                "modification_permitted": True,
                "redistribution_permitted": False,
                "attribution_required": True,
                "default_royalty": 0.15,
                "usage_restrictions": ["commercial_use_restricted"],
            },
            "research": {
                "description": "Research-only license for academic purposes",
                "cloning_permitted": False,
                "modification_permitted": True,
                "redistribution_permitted": False,
                "attribution_required": True,
                "default_royalty": 0.0,
                "usage_restrictions": ["research_only", "no_commercial_use"],
            },
            "commercial": {
                "description": "Commercial license with full business usage rights",
                "cloning_permitted": False,
                "modification_permitted": True,
                "redistribution_permitted": True,
                "attribution_required": True,
                "default_royalty": 0.25,
                "usage_restrictions": ["attribution_in_product"],
            },
            "open_source": {
                "description": "Open source license with community sharing",
                "cloning_permitted": True,
                "modification_permitted": True,
                "redistribution_permitted": True,
                "attribution_required": True,
                "default_royalty": 0.0,
                "usage_restrictions": ["share_alike", "open_source_derivatives"],
            },
        }

    def register_model_rights(
        self,
        model_id: str,
        owner_agent_id: str,
        base_license_type: str = "non_exclusive",
        moral_constraints: Optional[List[str]] = None,
    ) -> ModelRights:
        """Register rights for a new model."""

        if model_id in self.model_rights_db:
            raise ValueError(f"Model {model_id} already has registered rights")

        template = self.license_templates.get(
            base_license_type, self.license_templates["non_exclusive"]
        )

        rights = ModelRights(
            model_id=model_id,
            owner_agent_id=owner_agent_id,
            base_license_type=base_license_type,
            default_restrictions=template["usage_restrictions"],
            royalty_rates={base_license_type: template["default_royalty"]},
            moral_constraints=moral_constraints or [],
            creation_date=datetime.now(timezone.utc),
            last_updated=datetime.now(timezone.utc),
        )

        self.model_rights_db[model_id] = rights

        logger.info(
            f"Registered rights for model {model_id} with {base_license_type} license"
        )
        return rights

    def create_license_capsule(
        self,
        model_id: str,
        license_type: str,
        licensor_agent_id: str,
        licensee_agent_id: Optional[str] = None,
        custom_terms: Optional[Dict[str, Any]] = None,
        license_fee: Optional[float] = None,
        duration_days: Optional[int] = None,
    ) -> CloningRightsCapsule:
        """Create a licensing capsule for a model."""

        # Verify model exists and licensor has rights
        if model_id not in self.model_rights_db:
            raise ValueError(f"Model {model_id} not found in rights database")

        model_rights = self.model_rights_db[model_id]
        if model_rights.owner_agent_id != licensor_agent_id:
            raise ValueError(f"Agent {licensor_agent_id} does not own model {model_id}")

        # Get license template
        template = self.license_templates.get(license_type)
        if not template:
            raise ValueError(f"Unknown license type: {license_type}")

        # Calculate expiration date
        expiration_date = None
        if duration_days:
            expiration_date = datetime.now(timezone.utc) + timedelta(days=duration_days)

        # Merge custom terms with template
        license_terms = {**template}
        if custom_terms:
            license_terms.update(custom_terms)

        # Create payload
        payload = CloningRightsPayload(
            model_id=model_id,
            license_type=license_type,
            licensor_agent_id=licensor_agent_id,
            licensee_agent_id=licensee_agent_id,
            license_terms=license_terms,
            usage_restrictions=template["usage_restrictions"].copy(),
            royalty_percentage=template["default_royalty"] * 100,
            expiration_date=expiration_date,
            cloning_permitted=template["cloning_permitted"],
            modification_permitted=template["modification_permitted"],
            redistribution_permitted=template["redistribution_permitted"],
            attribution_required=template["attribution_required"],
            license_fee=license_fee,
            moral_constraints=model_rights.moral_constraints.copy(),
        )

        # Create capsule
        capsule_id = f"caps_{datetime.now(timezone.utc).strftime('%Y_%m_%d')}_{uuid.uuid4().hex[:16]}"

        capsule = CloningRightsCapsule(
            capsule_id=capsule_id,
            timestamp=datetime.now(timezone.utc),
            status=CapsuleStatus.DRAFT,
            verification=Verification(
                signature=f"ed25519:{'0' * 128}", merkle_root=f"sha256:{'0' * 64}"
            ),
            cloning_rights=payload,
        )

        # Register license
        license_id = f"license_{uuid.uuid4().hex[:16]}"
        self.license_registry.active_licenses[license_id] = {
            "capsule_id": capsule_id,
            "model_id": model_id,
            "license_type": license_type,
            "licensor_agent_id": licensor_agent_id,
            "licensee_agent_id": licensee_agent_id,
            "created_date": datetime.now(timezone.utc),
            "expiration_date": expiration_date,
            "status": "active",
        }

        logger.info(
            f"Created {license_type} license capsule {capsule_id} for model {model_id}"
        )
        return capsule

    def validate_usage(
        self, model_id: str, agent_id: str, usage_type: str
    ) -> Dict[str, Any]:
        """Validate if an agent can use a model in a specific way."""

        if model_id not in self.model_rights_db:
            return {
                "allowed": False,
                "reason": "Model not found in rights database",
                "license_required": True,
            }

        model_rights = self.model_rights_db[model_id]

        # Owner can always use their own model
        if model_rights.owner_agent_id == agent_id:
            return {
                "allowed": True,
                "reason": "Model owner has full rights",
                "license_id": None,
            }

        # Check for valid licenses
        valid_licenses = []
        for _license_id, license_info in self.license_registry.active_licenses.items():
            if license_info["model_id"] == model_id and (
                license_info["licensee_agent_id"] == agent_id
                or license_info["licensee_agent_id"] is None
            ):
                # Check expiration
                if license_info["expiration_date"]:
                    if datetime.now(timezone.utc) > license_info["expiration_date"]:
                        continue

                valid_licenses.append(license_info)

        if not valid_licenses:
            return {
                "allowed": False,
                "reason": "No valid license found for this agent",
                "license_required": True,
            }

        # Check usage restrictions for the best available license
        best_license = max(
            valid_licenses, key=lambda x: self._license_priority(x["license_type"])
        )

        # Validate specific usage type
        restrictions = self._get_usage_restrictions(best_license["license_type"])
        if usage_type in restrictions:
            return {
                "allowed": False,
                "reason": f"Usage type '{usage_type}' is restricted by license",
                "license_id": best_license["capsule_id"],
            }

        return {
            "allowed": True,
            "reason": f"Valid {best_license['license_type']} license found",
            "license_id": best_license["capsule_id"],
        }

    def _license_priority(self, license_type: str) -> int:
        """Return priority score for license types (higher = more permissive)."""
        priorities = {
            "exclusive": 5,
            "commercial": 4,
            "open_source": 3,
            "non_exclusive": 2,
            "research": 1,
        }
        return priorities.get(license_type, 0)

    def _get_usage_restrictions(self, license_type: str) -> List[str]:
        """Get usage restrictions for a license type."""
        template = self.license_templates.get(license_type, {})
        return template.get("usage_restrictions", [])

    def log_usage(
        self,
        model_id: str,
        agent_id: str,
        usage_type: str,
        license_id: Optional[str] = None,
    ) -> None:
        """Log usage of a licensed model."""

        usage_log = {
            "timestamp": datetime.now(timezone.utc),
            "model_id": model_id,
            "agent_id": agent_id,
            "usage_type": usage_type,
            "license_id": license_id,
        }

        if model_id not in self.license_registry.license_usage_logs:
            self.license_registry.license_usage_logs[model_id] = []

        self.license_registry.license_usage_logs[model_id].append(usage_log)

        logger.info(
            f"Logged usage: {usage_type} of model {model_id} by agent {agent_id}"
        )

    def get_model_licenses(self, model_id: str) -> List[Dict[str, Any]]:
        """Get all licenses for a specific model."""

        licenses = []
        for license_id, license_info in self.license_registry.active_licenses.items():
            if license_info["model_id"] == model_id:
                licenses.append({"license_id": license_id, **license_info})

        return sorted(licenses, key=lambda x: x["created_date"], reverse=True)

    def get_agent_licenses(self, agent_id: str) -> List[Dict[str, Any]]:
        """Get all licenses held by a specific agent."""

        licenses = []
        for license_id, license_info in self.license_registry.active_licenses.items():
            if (
                license_info["licensee_agent_id"] == agent_id
                or license_info["licensor_agent_id"] == agent_id
            ):
                licenses.append({"license_id": license_id, **license_info})

        return sorted(licenses, key=lambda x: x["created_date"], reverse=True)

    def revoke_license(
        self,
        license_id: str,
        revocation_reason: str,
        refund_amount: Optional[float] = None,
        revoking_agent_id: str = "system",
    ) -> Dict[str, Any]:
        """Revoke an active license with enhanced tracking."""

        if license_id not in self.license_registry.active_licenses:
            return {"success": False, "reason": "License not found"}

        license_info = self.license_registry.active_licenses.pop(license_id)
        license_info["revocation_date"] = datetime.now(timezone.utc)
        license_info["revocation_reason"] = revocation_reason
        license_info["revoking_agent_id"] = revoking_agent_id
        license_info["refund_amount"] = refund_amount
        license_info["status"] = "revoked"

        self.license_registry.revoked_licenses[license_id] = license_info

        logger.info(f"Revoked license {license_id}: {revocation_reason}")
        return {"success": True, "revocation_date": license_info["revocation_date"]}

    def transfer_license(
        self,
        license_id: str,
        new_licensee_agent_id: str,
        transfer_reason: str,
        transfer_fee: Optional[float] = None,
        authorizing_agent_id: str = "system",
    ) -> Dict[str, Any]:
        """Transfer a license to a new agent."""

        if license_id not in self.license_registry.active_licenses:
            return {"success": False, "reason": "License not found"}

        license_info = self.license_registry.active_licenses[license_id]
        old_licensee = license_info["licensee_agent_id"]

        # Create transfer record
        transfer_id = f"transfer_{uuid.uuid4().hex[:16]}"
        transfer_record = {
            "transfer_id": transfer_id,
            "license_id": license_id,
            "old_licensee": old_licensee,
            "new_licensee": new_licensee_agent_id,
            "transfer_reason": transfer_reason,
            "transfer_fee": transfer_fee,
            "authorizing_agent_id": authorizing_agent_id,
            "transfer_date": datetime.now(timezone.utc),
            "status": "completed",
        }

        # Update license
        license_info["licensee_agent_id"] = new_licensee_agent_id
        license_info["last_updated"] = datetime.now(timezone.utc)
        license_info["transfer_history"] = license_info.get("transfer_history", [])
        license_info["transfer_history"].append(transfer_record)

        logger.info(
            f"Transferred license {license_id} from {old_licensee} to {new_licensee_agent_id}"
        )

        return {
            "success": True,
            "transfer_id": transfer_id,
            "old_licensee": old_licensee,
            "new_licensee": new_licensee_agent_id,
        }

    def create_batch_licenses(
        self,
        model_ids: List[str],
        license_type: str,
        licensor_agent_id: str,
        licensee_agent_id: str,
        bulk_discount: Optional[float] = None,
    ) -> Dict[str, Any]:
        """Create licenses for multiple models in batch."""

        batch_id = f"batch_{uuid.uuid4().hex[:16]}"
        results = {}
        total_discount = 0.0

        for model_id in model_ids:
            try:
                # Create individual license
                capsule = self.create_license_capsule(
                    model_id=model_id,
                    license_type=license_type,
                    licensor_agent_id=licensor_agent_id,
                    licensee_agent_id=licensee_agent_id,
                )

                # Apply bulk discount if specified
                if bulk_discount:
                    discount_amount = bulk_discount * 100  # Placeholder calculation
                    total_discount += discount_amount

                results[model_id] = {
                    "success": True,
                    "license_id": f"license_{uuid.uuid4().hex[:16]}",
                    "capsule_id": capsule.capsule_id,
                }

            except Exception as e:
                results[model_id] = {"success": False, "error": str(e)}

        results["batch_id"] = batch_id
        results["total_discount"] = total_discount

        logger.info(f"Created batch {batch_id} with {len(model_ids)} licenses")
        return results

    def run_compliance_check(
        self, model_id: str, check_type: str, time_range_days: int = 30
    ) -> Dict[str, Any]:
        """Run comprehensive compliance check on a model."""

        if model_id not in self.model_rights_db:
            raise ValueError(f"Model {model_id} not found in rights database")

        self.model_rights_db[model_id]
        violations = []
        recommendations = []
        compliance_score = 1.0

        # Check usage compliance
        if check_type in ["usage", "all"]:
            usage_logs = self.license_registry.license_usage_logs.get(model_id, [])
            recent_usage = [
                log
                for log in usage_logs
                if (datetime.now(timezone.utc) - log["timestamp"]).days
                <= time_range_days
            ]

            # Check for unauthorized usage
            unauthorized_usage = [
                log
                for log in recent_usage
                if not self._is_usage_authorized(
                    model_id, log["agent_id"], log["usage_type"]
                )
            ]

            if unauthorized_usage:
                violations.append(
                    {
                        "type": "unauthorized_usage",
                        "count": len(unauthorized_usage),
                        "severity": "high",
                    }
                )
                compliance_score *= 0.7
                recommendations.append("Review and restrict unauthorized access")

        # Check moral constraints compliance
        if check_type in ["ethical", "all"]:
            moral_violations = self._check_moral_constraints(model_id, time_range_days)
            if moral_violations:
                violations.extend(moral_violations)
                compliance_score *= 0.8
                recommendations.append("Strengthen ethical guidelines enforcement")

        # Check legal compliance
        if check_type in ["legal", "all"]:
            legal_issues = self._check_legal_compliance(model_id, time_range_days)
            if legal_issues:
                violations.extend(legal_issues)
                compliance_score *= 0.6
                recommendations.append("Address legal compliance issues immediately")

        return {
            "compliance_score": max(0.0, compliance_score),
            "violations": violations,
            "recommendations": recommendations,
            "check_details": {
                "model_id": model_id,
                "check_type": check_type,
                "time_range_days": time_range_days,
                "total_usage_events": len(usage_logs)
                if check_type in ["usage", "all"]
                else 0,
            },
        }

    def get_license_utilization_analytics(
        self,
        time_range_days: int = 30,
        model_id: Optional[str] = None,
        agent_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Get detailed license utilization analytics."""

        end_date = datetime.now(timezone.utc)
        start_date = end_date - timedelta(days=time_range_days)

        # Filter licenses based on criteria
        filtered_licenses = {}
        for license_id, license_info in self.license_registry.active_licenses.items():
            if model_id and license_info["model_id"] != model_id:
                continue
            if agent_id and license_info["licensee_agent_id"] != agent_id:
                continue
            if license_info["created_date"] >= start_date:
                filtered_licenses[license_id] = license_info

        # Calculate utilization metrics
        total_licenses = len(filtered_licenses)
        active_usage = 0
        usage_by_type = {}
        revenue_by_model = {}

        for license_id, license_info in filtered_licenses.items():
            model_usage_logs = self.license_registry.license_usage_logs.get(
                license_info["model_id"], []
            )
            recent_usage = [
                log
                for log in model_usage_logs
                if start_date <= log["timestamp"] <= end_date
            ]

            if recent_usage:
                active_usage += 1

                for log in recent_usage:
                    usage_type = log["usage_type"]
                    usage_by_type[usage_type] = usage_by_type.get(usage_type, 0) + 1

                    # Calculate revenue (placeholder)
                    revenue = 10.0  # Base usage fee
                    model_id_key = license_info["model_id"]
                    revenue_by_model[model_id_key] = (
                        revenue_by_model.get(model_id_key, 0) + revenue
                    )

        utilization_rate = (active_usage / total_licenses) if total_licenses > 0 else 0

        return {
            "time_range": {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "days": time_range_days,
            },
            "summary": {
                "total_licenses": total_licenses,
                "active_licenses": active_usage,
                "utilization_rate": utilization_rate,
                "total_revenue": sum(revenue_by_model.values()),
            },
            "usage_by_type": usage_by_type,
            "revenue_by_model": revenue_by_model,
            "filters_applied": {"model_id": model_id, "agent_id": agent_id},
        }

    def _is_usage_authorized(
        self, model_id: str, agent_id: str, usage_type: str
    ) -> bool:
        """Check if usage is authorized for an agent."""
        validation_result = self.validate_usage(model_id, agent_id, usage_type)
        return validation_result["allowed"]

    def _check_moral_constraints(
        self, model_id: str, time_range_days: int
    ) -> List[Dict[str, Any]]:
        """Check for moral constraint violations."""
        violations = []

        if model_id in self.model_rights_db:
            model_rights = self.model_rights_db[model_id]
            moral_constraints = model_rights.moral_constraints

            # Simulate moral constraint checking
            if "no_harmful_content" in moral_constraints:
                # Placeholder: would integrate with content analysis
                violations.append(
                    {
                        "type": "moral_constraint_violation",
                        "constraint": "no_harmful_content",
                        "severity": "medium",
                        "description": "Potential harmful content detected in recent usage",
                    }
                )

        return violations

    def _check_legal_compliance(
        self, model_id: str, time_range_days: int
    ) -> List[Dict[str, Any]]:
        """Check for legal compliance issues."""
        violations = []

        # Simulate legal compliance checking
        # In real implementation, this would integrate with legal databases

        return violations


# Global service instance
cloning_rights_service = CloningRightsService()
