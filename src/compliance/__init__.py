"""
GDPR/CCPA Compliance Module

Implements data subject rights required by GDPR and CCPA:
- Right to Access (data export)
- Right to be Forgotten (data deletion) - already implemented in user_service.py
- Right to Portability (data transfer)
- Right to Rectification (data correction)
- Consent Management

Usage:
    from src.compliance import gdpr_compliance_manager

    # Export user data
    export = await gdpr_compliance_manager.export_user_data(
        user_id="user_123",
        format="json"
    )

    # Record consent
    await gdpr_compliance_manager.record_consent(
        user_id="user_123",
        consent_type="marketing",
        granted=True
    )

    # Check consent
    has_consent = await gdpr_compliance_manager.check_consent(
        user_id="user_123",
        consent_type="analytics"
    )
"""

from .gdpr_ccpa import (
    GDPRComplianceManager,
    gdpr_compliance_manager,
    ConsentRecord,
    DataExport,
    DataDeletionRequest,
)

__all__ = [
    "GDPRComplianceManager",
    "gdpr_compliance_manager",
    "ConsentRecord",
    "DataExport",
    "DataDeletionRequest",
]
