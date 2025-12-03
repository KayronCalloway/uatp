"""
Consent Management System
Complete privacy and consent management for UATP
"""

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class ConsentType(Enum):
    """Types of user consent"""

    DATA_COLLECTION = "data_collection"
    ATTRIBUTION_TRACKING = "attribution_tracking"
    CONVERSATION_STORAGE = "conversation_storage"
    ANALYTICS = "analytics"
    MARKETING = "marketing"
    THIRD_PARTY_SHARING = "third_party_sharing"
    AI_TRAINING = "ai_training"
    CROSS_PLATFORM = "cross_platform"
    LOCATION_TRACKING = "location_tracking"
    BIOMETRIC_DATA = "biometric_data"


class ConsentStatus(Enum):
    """Consent status options"""

    GRANTED = "granted"
    DENIED = "denied"
    WITHDRAWN = "withdrawn"
    EXPIRED = "expired"
    PENDING = "pending"


class DataCategory(Enum):
    """Categories of data"""

    PERSONAL_INFO = "personal_info"
    CONVERSATION_DATA = "conversation_data"
    USAGE_ANALYTICS = "usage_analytics"
    LOCATION_DATA = "location_data"
    DEVICE_INFO = "device_info"
    BIOMETRIC_DATA = "biometric_data"
    FINANCIAL_DATA = "financial_data"
    ATTRIBUTION_DATA = "attribution_data"


@dataclass
class ConsentRecord:
    """Individual consent record"""

    consent_id: str
    user_id: str
    consent_type: ConsentType
    status: ConsentStatus
    granted_at: datetime
    expires_at: Optional[datetime] = None
    withdrawn_at: Optional[datetime] = None

    # Consent details
    purpose: str = ""
    legal_basis: str = ""
    data_categories: List[DataCategory] = field(default_factory=list)
    third_parties: List[str] = field(default_factory=list)
    retention_period: Optional[int] = None  # days

    # Tracking
    consent_version: str = "1.0"
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None

    # Metadata
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ConsentTemplate:
    """Template for consent requests"""

    template_id: str
    consent_type: ConsentType
    title: str
    description: str
    purpose: str
    legal_basis: str
    data_categories: List[DataCategory]
    third_parties: List[str] = field(default_factory=list)
    retention_period: Optional[int] = None
    required: bool = False
    default_granted: bool = False

    # Localization
    translations: Dict[str, Dict[str, str]] = field(default_factory=dict)


@dataclass
class PrivacyPreferences:
    """User privacy preferences"""

    user_id: str
    updated_at: datetime

    # Data control preferences
    data_minimization: bool = True
    pseudonymization: bool = True
    anonymization_delay: int = 30  # days

    # Sharing preferences
    allow_analytics: bool = False
    allow_marketing: bool = False
    allow_third_party: bool = False

    # Notification preferences
    consent_reminders: bool = True
    privacy_updates: bool = True

    # Export/deletion preferences
    auto_delete_old_data: bool = True
    data_retention_days: int = 365

    # Metadata
    preferences_version: str = "1.0"
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class DataProcessingActivity:
    """Record of data processing activities"""

    activity_id: str
    user_id: str
    activity_type: str
    data_categories: List[DataCategory]
    purpose: str
    legal_basis: str
    timestamp: datetime

    # Processing details
    processor: str
    data_source: str
    data_recipients: List[str] = field(default_factory=list)

    # Consent reference
    consent_id: Optional[str] = None

    # Retention
    retention_period: Optional[int] = None
    scheduled_deletion: Optional[datetime] = None

    # Metadata
    metadata: Dict[str, Any] = field(default_factory=dict)


class ConsentManager:
    """Complete consent management system"""

    def __init__(self):
        self.consent_records: Dict[str, ConsentRecord] = {}
        self.consent_templates: Dict[str, ConsentTemplate] = {}
        self.privacy_preferences: Dict[str, PrivacyPreferences] = {}
        self.processing_activities: Dict[str, DataProcessingActivity] = {}

        # Indexes for efficient lookups
        self.user_consents: Dict[str, List[str]] = {}  # user_id -> [consent_ids]
        self.consent_by_type: Dict[ConsentType, List[str]] = {}  # type -> [consent_ids]

        # Initialize default templates
        self._initialize_default_templates()

    def _initialize_default_templates(self):
        """Initialize default consent templates"""

        templates = [
            ConsentTemplate(
                template_id="attribution_tracking",
                consent_type=ConsentType.ATTRIBUTION_TRACKING,
                title="Attribution Tracking",
                description="Track your contributions to AI conversations for fair attribution and payment",
                purpose="To provide fair attribution and compensation for your intellectual contributions",
                legal_basis="Legitimate interest and performance of contract",
                data_categories=[
                    DataCategory.CONVERSATION_DATA,
                    DataCategory.ATTRIBUTION_DATA,
                ],
                retention_period=2555,  # 7 years
                required=True,
                default_granted=True,
            ),
            ConsentTemplate(
                template_id="conversation_storage",
                consent_type=ConsentType.CONVERSATION_STORAGE,
                title="Conversation Storage",
                description="Store your AI conversations for attribution analysis and improvement",
                purpose="To analyze conversations for attribution and improve our services",
                legal_basis="Performance of contract",
                data_categories=[DataCategory.CONVERSATION_DATA],
                retention_period=365,  # 1 year
                required=True,
                default_granted=True,
            ),
            ConsentTemplate(
                template_id="analytics",
                consent_type=ConsentType.ANALYTICS,
                title="Analytics and Insights",
                description="Analyze your usage patterns to provide insights and improve our services",
                purpose="To provide personalized insights and improve our services",
                legal_basis="Legitimate interest",
                data_categories=[
                    DataCategory.USAGE_ANALYTICS,
                    DataCategory.DEVICE_INFO,
                ],
                retention_period=730,  # 2 years
                required=False,
                default_granted=False,
            ),
            ConsentTemplate(
                template_id="marketing",
                consent_type=ConsentType.MARKETING,
                title="Marketing Communications",
                description="Receive updates about new features and attribution opportunities",
                purpose="To inform you about relevant features and opportunities",
                legal_basis="Consent",
                data_categories=[DataCategory.PERSONAL_INFO],
                retention_period=1095,  # 3 years
                required=False,
                default_granted=False,
            ),
            ConsentTemplate(
                template_id="third_party_sharing",
                consent_type=ConsentType.THIRD_PARTY_SHARING,
                title="Third-Party Sharing",
                description="Share anonymized data with research partners and AI companies",
                purpose="To advance AI attribution research and expand platform partnerships",
                legal_basis="Consent",
                data_categories=[DataCategory.ATTRIBUTION_DATA],
                third_parties=["Research Partners", "AI Platform Partners"],
                retention_period=1825,  # 5 years
                required=False,
                default_granted=False,
            ),
            ConsentTemplate(
                template_id="ai_training",
                consent_type=ConsentType.AI_TRAINING,
                title="AI Training Data",
                description="Use your attributed conversations to improve AI attribution models",
                purpose="To improve attribution accuracy and AI understanding",
                legal_basis="Legitimate interest",
                data_categories=[
                    DataCategory.CONVERSATION_DATA,
                    DataCategory.ATTRIBUTION_DATA,
                ],
                retention_period=1825,  # 5 years
                required=False,
                default_granted=False,
            ),
        ]

        for template in templates:
            self.consent_templates[template.template_id] = template

    def generate_consent_id(self) -> str:
        """Generate unique consent ID"""
        timestamp = str(int(datetime.now().timestamp()))
        return f"consent_{timestamp}_{hash(timestamp) % 10000:04d}"

    def generate_activity_id(self) -> str:
        """Generate unique activity ID"""
        timestamp = str(int(datetime.now().timestamp()))
        return f"activity_{timestamp}_{hash(timestamp) % 10000:04d}"

    async def request_consent(
        self,
        user_id: str,
        consent_type: ConsentType,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """Request consent from user"""

        # Get template
        template_id = consent_type.value
        template = self.consent_templates.get(template_id)

        if not template:
            return {"success": False, "error": "Consent template not found"}

        # Check if user already has active consent
        existing_consent = await self.get_user_consent(user_id, consent_type)
        if (
            existing_consent
            and existing_consent["status"] == ConsentStatus.GRANTED.value
        ):
            return {
                "success": False,
                "error": "Consent already granted",
                "existing_consent": existing_consent,
            }

        # Create consent request
        consent_request = {
            "consent_type": consent_type.value,
            "title": template.title,
            "description": template.description,
            "purpose": template.purpose,
            "legal_basis": template.legal_basis,
            "data_categories": [cat.value for cat in template.data_categories],
            "third_parties": template.third_parties,
            "retention_period": template.retention_period,
            "required": template.required,
            "default_granted": template.default_granted,
            "request_metadata": {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "ip_address": ip_address,
                "user_agent": user_agent,
            },
        }

        return {
            "success": True,
            "consent_request": consent_request,
            "template_id": template_id,
        }

    async def grant_consent(
        self,
        user_id: str,
        consent_type: ConsentType,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """Grant consent"""

        # Get template
        template_id = consent_type.value
        template = self.consent_templates.get(template_id)

        if not template:
            return {"success": False, "error": "Consent template not found"}

        # Create consent record
        consent_id = self.generate_consent_id()
        now = datetime.now(timezone.utc)

        expires_at = None
        if template.retention_period:
            expires_at = now + timedelta(days=template.retention_period)

        consent_record = ConsentRecord(
            consent_id=consent_id,
            user_id=user_id,
            consent_type=consent_type,
            status=ConsentStatus.GRANTED,
            granted_at=now,
            expires_at=expires_at,
            purpose=template.purpose,
            legal_basis=template.legal_basis,
            data_categories=template.data_categories,
            third_parties=template.third_parties,
            retention_period=template.retention_period,
            ip_address=ip_address,
            user_agent=user_agent,
            metadata=kwargs,
        )

        # Store consent record
        self.consent_records[consent_id] = consent_record

        # Update indexes
        if user_id not in self.user_consents:
            self.user_consents[user_id] = []
        self.user_consents[user_id].append(consent_id)

        if consent_type not in self.consent_by_type:
            self.consent_by_type[consent_type] = []
        self.consent_by_type[consent_type].append(consent_id)

        # Record processing activity
        await self._record_processing_activity(
            user_id=user_id,
            activity_type="consent_granted",
            data_categories=template.data_categories,
            purpose=template.purpose,
            legal_basis=template.legal_basis,
            consent_id=consent_id,
        )

        logger.info(f"Consent granted: {consent_id} - {user_id} - {consent_type.value}")

        return {
            "success": True,
            "consent_id": consent_id,
            "expires_at": expires_at.isoformat() if expires_at else None,
            "message": "Consent granted successfully",
        }

    async def withdraw_consent(
        self, user_id: str, consent_type: ConsentType, reason: Optional[str] = None
    ) -> Dict[str, Any]:
        """Withdraw consent"""

        # Find active consent
        existing_consent = await self.get_user_consent(user_id, consent_type)
        if not existing_consent:
            return {"success": False, "error": "No active consent found"}

        consent_id = existing_consent["consent_id"]
        consent_record = self.consent_records[consent_id]

        # Update consent record
        consent_record.status = ConsentStatus.WITHDRAWN
        consent_record.withdrawn_at = datetime.now(timezone.utc)
        if reason:
            consent_record.metadata["withdrawal_reason"] = reason

        # Record processing activity
        await self._record_processing_activity(
            user_id=user_id,
            activity_type="consent_withdrawn",
            data_categories=consent_record.data_categories,
            purpose="Consent withdrawal",
            legal_basis="User request",
            consent_id=consent_id,
        )

        logger.info(
            f"Consent withdrawn: {consent_id} - {user_id} - {consent_type.value}"
        )

        return {
            "success": True,
            "consent_id": consent_id,
            "withdrawn_at": consent_record.withdrawn_at.isoformat(),
            "message": "Consent withdrawn successfully",
        }

    async def get_user_consent(
        self, user_id: str, consent_type: ConsentType
    ) -> Optional[Dict[str, Any]]:
        """Get user's consent for a specific type"""

        if user_id not in self.user_consents:
            return None

        # Find most recent consent for this type
        user_consent_ids = self.user_consents[user_id]
        relevant_consents = []

        for consent_id in user_consent_ids:
            consent_record = self.consent_records.get(consent_id)
            if consent_record and consent_record.consent_type == consent_type:
                relevant_consents.append(consent_record)

        if not relevant_consents:
            return None

        # Get most recent consent
        latest_consent = max(relevant_consents, key=lambda x: x.granted_at)

        # Check if expired
        if latest_consent.expires_at and latest_consent.expires_at < datetime.now(
            timezone.utc
        ):
            latest_consent.status = ConsentStatus.EXPIRED

        return {
            "consent_id": latest_consent.consent_id,
            "consent_type": latest_consent.consent_type.value,
            "status": latest_consent.status.value,
            "granted_at": latest_consent.granted_at.isoformat(),
            "expires_at": latest_consent.expires_at.isoformat()
            if latest_consent.expires_at
            else None,
            "withdrawn_at": latest_consent.withdrawn_at.isoformat()
            if latest_consent.withdrawn_at
            else None,
            "purpose": latest_consent.purpose,
            "legal_basis": latest_consent.legal_basis,
            "data_categories": [cat.value for cat in latest_consent.data_categories],
            "third_parties": latest_consent.third_parties,
            "retention_period": latest_consent.retention_period,
        }

    async def get_all_user_consents(self, user_id: str) -> List[Dict[str, Any]]:
        """Get all consents for a user"""

        if user_id not in self.user_consents:
            return []

        user_consent_ids = self.user_consents[user_id]
        consents = []

        for consent_id in user_consent_ids:
            consent_record = self.consent_records.get(consent_id)
            if consent_record:
                # Check if expired
                if (
                    consent_record.expires_at
                    and consent_record.expires_at < datetime.now(timezone.utc)
                ):
                    consent_record.status = ConsentStatus.EXPIRED

                consents.append(
                    {
                        "consent_id": consent_record.consent_id,
                        "consent_type": consent_record.consent_type.value,
                        "status": consent_record.status.value,
                        "granted_at": consent_record.granted_at.isoformat(),
                        "expires_at": consent_record.expires_at.isoformat()
                        if consent_record.expires_at
                        else None,
                        "withdrawn_at": consent_record.withdrawn_at.isoformat()
                        if consent_record.withdrawn_at
                        else None,
                        "purpose": consent_record.purpose,
                        "legal_basis": consent_record.legal_basis,
                        "data_categories": [
                            cat.value for cat in consent_record.data_categories
                        ],
                        "third_parties": consent_record.third_parties,
                        "retention_period": consent_record.retention_period,
                    }
                )

        return sorted(consents, key=lambda x: x["granted_at"], reverse=True)

    async def check_consent_required(
        self, user_id: str, data_categories: List[DataCategory], purpose: str
    ) -> Dict[str, Any]:
        """Check what consents are required for data processing"""

        required_consents = []
        optional_consents = []

        # Check each consent type
        for template in self.consent_templates.values():
            # Check if template data categories overlap with requested categories
            if any(cat in template.data_categories for cat in data_categories):
                existing_consent = await self.get_user_consent(
                    user_id, template.consent_type
                )

                consent_info = {
                    "consent_type": template.consent_type.value,
                    "title": template.title,
                    "description": template.description,
                    "required": template.required,
                    "has_consent": existing_consent is not None
                    and existing_consent["status"] == ConsentStatus.GRANTED.value,
                    "existing_consent": existing_consent,
                }

                if template.required:
                    required_consents.append(consent_info)
                else:
                    optional_consents.append(consent_info)

        missing_required = [c for c in required_consents if not c["has_consent"]]

        return {
            "can_process": len(missing_required) == 0,
            "required_consents": required_consents,
            "optional_consents": optional_consents,
            "missing_required": missing_required,
        }

    async def set_privacy_preferences(
        self, user_id: str, preferences: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Set user privacy preferences"""

        # Get existing preferences or create new
        existing_prefs = self.privacy_preferences.get(user_id)

        if existing_prefs:
            # Update existing preferences
            for key, value in preferences.items():
                if hasattr(existing_prefs, key):
                    setattr(existing_prefs, key, value)
            existing_prefs.updated_at = datetime.now(timezone.utc)
        else:
            # Create new preferences
            prefs = PrivacyPreferences(
                user_id=user_id, updated_at=datetime.now(timezone.utc), **preferences
            )
            self.privacy_preferences[user_id] = prefs

        logger.info(f"Privacy preferences updated: {user_id}")

        return {"success": True, "message": "Privacy preferences updated successfully"}

    async def get_privacy_preferences(self, user_id: str) -> Dict[str, Any]:
        """Get user privacy preferences"""

        prefs = self.privacy_preferences.get(user_id)
        if not prefs:
            # Return default preferences
            return {
                "data_minimization": True,
                "pseudonymization": True,
                "anonymization_delay": 30,
                "allow_analytics": False,
                "allow_marketing": False,
                "allow_third_party": False,
                "consent_reminders": True,
                "privacy_updates": True,
                "auto_delete_old_data": True,
                "data_retention_days": 365,
            }

        return {
            "data_minimization": prefs.data_minimization,
            "pseudonymization": prefs.pseudonymization,
            "anonymization_delay": prefs.anonymization_delay,
            "allow_analytics": prefs.allow_analytics,
            "allow_marketing": prefs.allow_marketing,
            "allow_third_party": prefs.allow_third_party,
            "consent_reminders": prefs.consent_reminders,
            "privacy_updates": prefs.privacy_updates,
            "auto_delete_old_data": prefs.auto_delete_old_data,
            "data_retention_days": prefs.data_retention_days,
            "updated_at": prefs.updated_at.isoformat(),
        }

    async def _record_processing_activity(
        self,
        user_id: str,
        activity_type: str,
        data_categories: List[DataCategory],
        purpose: str,
        legal_basis: str,
        consent_id: Optional[str] = None,
        **kwargs,
    ):
        """Record data processing activity"""

        activity_id = self.generate_activity_id()

        activity = DataProcessingActivity(
            activity_id=activity_id,
            user_id=user_id,
            activity_type=activity_type,
            data_categories=data_categories,
            purpose=purpose,
            legal_basis=legal_basis,
            timestamp=datetime.now(timezone.utc),
            processor="UATP System",
            data_source="User Input",
            consent_id=consent_id,
            metadata=kwargs,
        )

        self.processing_activities[activity_id] = activity

        logger.debug(f"Processing activity recorded: {activity_id}")

    async def get_processing_activities(
        self, user_id: str, limit: int = 50, offset: int = 0
    ) -> Dict[str, Any]:
        """Get user's data processing activities"""

        user_activities = [
            activity
            for activity in self.processing_activities.values()
            if activity.user_id == user_id
        ]

        # Sort by timestamp (newest first)
        user_activities.sort(key=lambda x: x.timestamp, reverse=True)

        # Apply pagination
        paginated_activities = user_activities[offset : offset + limit]

        return {
            "activities": [
                {
                    "activity_id": activity.activity_id,
                    "activity_type": activity.activity_type,
                    "data_categories": [cat.value for cat in activity.data_categories],
                    "purpose": activity.purpose,
                    "legal_basis": activity.legal_basis,
                    "timestamp": activity.timestamp.isoformat(),
                    "processor": activity.processor,
                    "data_source": activity.data_source,
                    "consent_id": activity.consent_id,
                }
                for activity in paginated_activities
            ],
            "pagination": {
                "total": len(user_activities),
                "limit": limit,
                "offset": offset,
                "has_more": offset + limit < len(user_activities),
            },
        }

    async def generate_consent_report(self, user_id: str) -> Dict[str, Any]:
        """Generate comprehensive consent report for user"""

        user_consents = await self.get_all_user_consents(user_id)
        privacy_prefs = await self.get_privacy_preferences(user_id)
        processing_activities = await self.get_processing_activities(user_id, limit=100)

        # Calculate statistics
        active_consents = [
            c for c in user_consents if c["status"] == ConsentStatus.GRANTED.value
        ]
        withdrawn_consents = [
            c for c in user_consents if c["status"] == ConsentStatus.WITHDRAWN.value
        ]
        expired_consents = [
            c for c in user_consents if c["status"] == ConsentStatus.EXPIRED.value
        ]

        return {
            "user_id": user_id,
            "report_generated_at": datetime.now(timezone.utc).isoformat(),
            "consent_summary": {
                "total_consents": len(user_consents),
                "active_consents": len(active_consents),
                "withdrawn_consents": len(withdrawn_consents),
                "expired_consents": len(expired_consents),
            },
            "consents": user_consents,
            "privacy_preferences": privacy_prefs,
            "processing_activities": processing_activities,
            "data_categories_consented": list(
                {
                    cat
                    for consent in active_consents
                    for cat in consent["data_categories"]
                }
            ),
            "legal_bases": list(
                {consent["legal_basis"] for consent in active_consents}
            ),
        }

    async def check_consent_expiry(self):
        """Check for expiring consents and send reminders"""

        now = datetime.now(timezone.utc)
        reminder_threshold = now + timedelta(days=7)  # 7 days before expiry

        expiring_consents = []

        for consent_record in self.consent_records.values():
            if (
                consent_record.expires_at
                and consent_record.status == ConsentStatus.GRANTED
                and consent_record.expires_at <= reminder_threshold
            ):
                expiring_consents.append(consent_record)

        # In production, this would send notifications to users
        logger.info(f"Found {len(expiring_consents)} expiring consents")

        return expiring_consents

    async def cleanup_expired_consents(self):
        """Clean up expired consents"""

        now = datetime.now(timezone.utc)
        updated_count = 0

        for consent_record in self.consent_records.values():
            if (
                consent_record.expires_at
                and consent_record.expires_at < now
                and consent_record.status == ConsentStatus.GRANTED
            ):
                consent_record.status = ConsentStatus.EXPIRED
                updated_count += 1

        logger.info(f"Marked {updated_count} consents as expired")

        return updated_count


# Factory function
def create_consent_manager() -> ConsentManager:
    """Create a consent manager instance"""
    return ConsentManager()


# Example usage
if __name__ == "__main__":

    async def demo_consent_manager():
        """Demonstrate the consent manager"""

        consent_manager = create_consent_manager()
        user_id = "user123"

        # Request consent
        print("🔐 Requesting consent...")
        request_result = await consent_manager.request_consent(
            user_id=user_id,
            consent_type=ConsentType.ATTRIBUTION_TRACKING,
            ip_address="127.0.0.1",
            user_agent="Demo Client",
        )
        print(f"Request result: {request_result}")

        # Grant consent
        print("\n✅ Granting consent...")
        grant_result = await consent_manager.grant_consent(
            user_id=user_id,
            consent_type=ConsentType.ATTRIBUTION_TRACKING,
            ip_address="127.0.0.1",
            user_agent="Demo Client",
        )
        print(f"Grant result: {grant_result}")

        # Check consent
        print("\n🔍 Checking consent...")
        consent_status = await consent_manager.get_user_consent(
            user_id, ConsentType.ATTRIBUTION_TRACKING
        )
        print(f"Consent status: {consent_status}")

        # Set privacy preferences
        print("\n⚙️ Setting privacy preferences...")
        prefs_result = await consent_manager.set_privacy_preferences(
            user_id=user_id,
            preferences={"allow_analytics": True, "data_retention_days": 180},
        )
        print(f"Preferences result: {prefs_result}")

        # Check consent requirements
        print("\n📋 Checking consent requirements...")
        requirements = await consent_manager.check_consent_required(
            user_id=user_id,
            data_categories=[
                DataCategory.CONVERSATION_DATA,
                DataCategory.ATTRIBUTION_DATA,
            ],
            purpose="Attribution tracking",
        )
        print(f"Requirements: {requirements}")

        # Generate consent report
        print("\n📊 Generating consent report...")
        report = await consent_manager.generate_consent_report(user_id)
        print(f"Report: {report}")

    asyncio.run(demo_consent_manager())
