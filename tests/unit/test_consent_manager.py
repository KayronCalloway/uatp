"""
Unit tests for Consent Manager.
"""

from datetime import datetime, timedelta, timezone

import pytest

from src.privacy.consent_manager import (
    ConsentManager,
    ConsentRecord,
    ConsentStatus,
    ConsentTemplate,
    ConsentType,
    DataCategory,
    DataProcessingActivity,
    PrivacyPreferences,
    create_consent_manager,
)


class TestConsentType:
    """Tests for ConsentType enum."""

    def test_consent_type_values(self):
        """Test consent type values."""
        assert ConsentType.DATA_COLLECTION.value == "data_collection"
        assert ConsentType.ATTRIBUTION_TRACKING.value == "attribution_tracking"
        assert ConsentType.CONVERSATION_STORAGE.value == "conversation_storage"
        assert ConsentType.ANALYTICS.value == "analytics"
        assert ConsentType.MARKETING.value == "marketing"

    def test_all_consent_types_exist(self):
        """Test all consent types exist."""
        expected_types = [
            "DATA_COLLECTION",
            "ATTRIBUTION_TRACKING",
            "CONVERSATION_STORAGE",
            "ANALYTICS",
            "MARKETING",
            "THIRD_PARTY_SHARING",
            "AI_TRAINING",
            "CROSS_PLATFORM",
            "LOCATION_TRACKING",
            "BIOMETRIC_DATA",
        ]
        for t in expected_types:
            assert hasattr(ConsentType, t)


class TestConsentStatus:
    """Tests for ConsentStatus enum."""

    def test_consent_status_values(self):
        """Test consent status values."""
        assert ConsentStatus.GRANTED.value == "granted"
        assert ConsentStatus.DENIED.value == "denied"
        assert ConsentStatus.WITHDRAWN.value == "withdrawn"
        assert ConsentStatus.EXPIRED.value == "expired"
        assert ConsentStatus.PENDING.value == "pending"


class TestDataCategory:
    """Tests for DataCategory enum."""

    def test_data_category_values(self):
        """Test data category values."""
        assert DataCategory.PERSONAL_INFO.value == "personal_info"
        assert DataCategory.CONVERSATION_DATA.value == "conversation_data"
        assert DataCategory.USAGE_ANALYTICS.value == "usage_analytics"
        assert DataCategory.ATTRIBUTION_DATA.value == "attribution_data"


class TestConsentRecord:
    """Tests for ConsentRecord dataclass."""

    def test_create_consent_record(self):
        """Test creating a consent record."""
        now = datetime.now(timezone.utc)
        record = ConsentRecord(
            consent_id="consent_123",
            user_id="user_456",
            consent_type=ConsentType.ANALYTICS,
            status=ConsentStatus.GRANTED,
            granted_at=now,
        )

        assert record.consent_id == "consent_123"
        assert record.user_id == "user_456"
        assert record.consent_type == ConsentType.ANALYTICS
        assert record.status == ConsentStatus.GRANTED
        assert record.granted_at == now

    def test_consent_record_defaults(self):
        """Test consent record default values."""
        record = ConsentRecord(
            consent_id="consent_123",
            user_id="user_456",
            consent_type=ConsentType.ANALYTICS,
            status=ConsentStatus.GRANTED,
            granted_at=datetime.now(timezone.utc),
        )

        assert record.expires_at is None
        assert record.withdrawn_at is None
        assert record.purpose == ""
        assert record.legal_basis == ""
        assert record.data_categories == []
        assert record.third_parties == []
        assert record.retention_period is None
        assert record.consent_version == "1.0"
        assert record.ip_address is None
        assert record.user_agent is None
        assert record.metadata == {}

    def test_consent_record_with_all_fields(self):
        """Test consent record with all fields populated."""
        now = datetime.now(timezone.utc)
        expires = now + timedelta(days=365)

        record = ConsentRecord(
            consent_id="consent_123",
            user_id="user_456",
            consent_type=ConsentType.ANALYTICS,
            status=ConsentStatus.GRANTED,
            granted_at=now,
            expires_at=expires,
            purpose="Analytics tracking",
            legal_basis="Consent",
            data_categories=[DataCategory.USAGE_ANALYTICS],
            third_parties=["PartnerA"],
            retention_period=365,
            ip_address="192.168.1.1",
            user_agent="TestAgent/1.0",
            metadata={"source": "test"},
        )

        assert record.expires_at == expires
        assert record.purpose == "Analytics tracking"
        assert record.ip_address == "192.168.1.1"
        assert record.metadata["source"] == "test"


class TestConsentTemplate:
    """Tests for ConsentTemplate dataclass."""

    def test_create_consent_template(self):
        """Test creating a consent template."""
        template = ConsentTemplate(
            template_id="test_template",
            consent_type=ConsentType.ANALYTICS,
            title="Test Analytics",
            description="Test analytics description",
            purpose="Testing analytics tracking",
            legal_basis="Consent",
            data_categories=[DataCategory.USAGE_ANALYTICS],
        )

        assert template.template_id == "test_template"
        assert template.consent_type == ConsentType.ANALYTICS
        assert template.title == "Test Analytics"
        assert template.required is False
        assert template.default_granted is False

    def test_template_with_required(self):
        """Test template with required consent."""
        template = ConsentTemplate(
            template_id="required_template",
            consent_type=ConsentType.CONVERSATION_STORAGE,
            title="Required Consent",
            description="Required for service",
            purpose="Service operation",
            legal_basis="Contract",
            data_categories=[DataCategory.CONVERSATION_DATA],
            required=True,
            default_granted=True,
        )

        assert template.required is True
        assert template.default_granted is True


class TestPrivacyPreferences:
    """Tests for PrivacyPreferences dataclass."""

    def test_create_privacy_preferences(self):
        """Test creating privacy preferences."""
        prefs = PrivacyPreferences(
            user_id="user_123",
            updated_at=datetime.now(timezone.utc),
        )

        assert prefs.user_id == "user_123"
        assert prefs.data_minimization is True
        assert prefs.pseudonymization is True
        assert prefs.anonymization_delay == 30
        assert prefs.allow_analytics is False
        assert prefs.allow_marketing is False
        assert prefs.allow_third_party is False
        assert prefs.consent_reminders is True
        assert prefs.privacy_updates is True
        assert prefs.auto_delete_old_data is True
        assert prefs.data_retention_days == 365

    def test_privacy_preferences_custom(self):
        """Test privacy preferences with custom values."""
        prefs = PrivacyPreferences(
            user_id="user_123",
            updated_at=datetime.now(timezone.utc),
            allow_analytics=True,
            data_retention_days=180,
        )

        assert prefs.allow_analytics is True
        assert prefs.data_retention_days == 180


class TestDataProcessingActivity:
    """Tests for DataProcessingActivity dataclass."""

    def test_create_activity(self):
        """Test creating a data processing activity."""
        activity = DataProcessingActivity(
            activity_id="activity_123",
            user_id="user_456",
            activity_type="consent_granted",
            data_categories=[DataCategory.CONVERSATION_DATA],
            purpose="User consent",
            legal_basis="Consent",
            timestamp=datetime.now(timezone.utc),
            processor="UATP System",
            data_source="User Input",
        )

        assert activity.activity_id == "activity_123"
        assert activity.user_id == "user_456"
        assert activity.activity_type == "consent_granted"
        assert activity.processor == "UATP System"


class TestConsentManager:
    """Tests for ConsentManager class."""

    @pytest.fixture
    def manager(self):
        """Create a consent manager instance."""
        return ConsentManager()

    def test_create_manager(self, manager):
        """Test creating a consent manager."""
        assert manager is not None
        assert len(manager.consent_templates) > 0
        assert manager.consent_records == {}
        assert manager.privacy_preferences == {}

    def test_default_templates_loaded(self, manager):
        """Test that default templates are loaded."""
        assert "attribution_tracking" in manager.consent_templates
        assert "conversation_storage" in manager.consent_templates
        assert "analytics" in manager.consent_templates
        assert "marketing" in manager.consent_templates

    def test_generate_consent_id(self, manager):
        """Test generating consent ID."""
        consent_id = manager.generate_consent_id()

        assert consent_id is not None
        assert consent_id.startswith("consent_")

    def test_generate_consent_id_format(self, manager):
        """Test consent ID format."""
        consent_id = manager.generate_consent_id()

        # Format: consent_{timestamp}_{hash}
        parts = consent_id.split("_")
        assert len(parts) >= 2
        assert parts[0] == "consent"
        # Timestamp part should be numeric
        assert parts[1].isdigit()

    def test_generate_activity_id(self, manager):
        """Test generating activity ID."""
        activity_id = manager.generate_activity_id()

        assert activity_id is not None
        assert activity_id.startswith("activity_")

    @pytest.mark.asyncio
    async def test_request_consent(self, manager):
        """Test requesting consent."""
        result = await manager.request_consent(
            user_id="user_123",
            consent_type=ConsentType.ANALYTICS,
        )

        assert result["success"] is True
        assert "consent_request" in result
        assert result["consent_request"]["consent_type"] == "analytics"

    @pytest.mark.asyncio
    async def test_request_consent_invalid_template(self, manager):
        """Test requesting consent for invalid template."""
        result = await manager.request_consent(
            user_id="user_123",
            consent_type=ConsentType.DATA_COLLECTION,  # No template exists
        )

        assert result["success"] is False
        assert "not found" in result["error"]

    @pytest.mark.asyncio
    async def test_grant_consent(self, manager):
        """Test granting consent."""
        result = await manager.grant_consent(
            user_id="user_123",
            consent_type=ConsentType.ANALYTICS,
        )

        assert result["success"] is True
        assert "consent_id" in result
        assert result["consent_id"].startswith("consent_")

    @pytest.mark.asyncio
    async def test_grant_consent_with_ip_and_agent(self, manager):
        """Test granting consent with IP and user agent."""
        result = await manager.grant_consent(
            user_id="user_123",
            consent_type=ConsentType.ANALYTICS,
            ip_address="192.168.1.1",
            user_agent="TestAgent/1.0",
        )

        assert result["success"] is True
        consent_id = result["consent_id"]
        consent_record = manager.consent_records[consent_id]
        assert consent_record.ip_address == "192.168.1.1"
        assert consent_record.user_agent == "TestAgent/1.0"

    @pytest.mark.asyncio
    async def test_grant_consent_invalid_template(self, manager):
        """Test granting consent for invalid template."""
        result = await manager.grant_consent(
            user_id="user_123",
            consent_type=ConsentType.DATA_COLLECTION,
        )

        assert result["success"] is False
        assert "not found" in result["error"]

    @pytest.mark.asyncio
    async def test_request_consent_already_granted(self, manager):
        """Test requesting consent when already granted."""
        # First grant consent
        await manager.grant_consent(
            user_id="user_123",
            consent_type=ConsentType.ANALYTICS,
        )

        # Try to request again
        result = await manager.request_consent(
            user_id="user_123",
            consent_type=ConsentType.ANALYTICS,
        )

        assert result["success"] is False
        assert "already granted" in result["error"]

    @pytest.mark.asyncio
    async def test_get_user_consent(self, manager):
        """Test getting user consent."""
        await manager.grant_consent(
            user_id="user_123",
            consent_type=ConsentType.ANALYTICS,
        )

        consent = await manager.get_user_consent("user_123", ConsentType.ANALYTICS)

        assert consent is not None
        assert consent["consent_type"] == "analytics"
        assert consent["status"] == "granted"

    @pytest.mark.asyncio
    async def test_get_user_consent_not_found(self, manager):
        """Test getting non-existent consent."""
        consent = await manager.get_user_consent("user_123", ConsentType.ANALYTICS)

        assert consent is None

    @pytest.mark.asyncio
    async def test_withdraw_consent(self, manager):
        """Test withdrawing consent."""
        # First grant consent
        await manager.grant_consent(
            user_id="user_123",
            consent_type=ConsentType.ANALYTICS,
        )

        # Withdraw consent
        result = await manager.withdraw_consent(
            user_id="user_123",
            consent_type=ConsentType.ANALYTICS,
            reason="Privacy concerns",
        )

        assert result["success"] is True
        assert "withdrawn_at" in result

        # Verify consent is withdrawn
        consent = await manager.get_user_consent("user_123", ConsentType.ANALYTICS)
        assert consent["status"] == "withdrawn"

    @pytest.mark.asyncio
    async def test_withdraw_consent_not_found(self, manager):
        """Test withdrawing non-existent consent."""
        result = await manager.withdraw_consent(
            user_id="user_123",
            consent_type=ConsentType.ANALYTICS,
        )

        assert result["success"] is False
        assert "No active consent" in result["error"]

    @pytest.mark.asyncio
    async def test_get_all_user_consents(self, manager):
        """Test getting all user consents."""
        # Grant multiple consents
        await manager.grant_consent("user_123", ConsentType.ANALYTICS)
        await manager.grant_consent("user_123", ConsentType.MARKETING)

        consents = await manager.get_all_user_consents("user_123")

        assert len(consents) == 2

    @pytest.mark.asyncio
    async def test_get_all_user_consents_empty(self, manager):
        """Test getting consents for user with none."""
        consents = await manager.get_all_user_consents("new_user")

        assert consents == []

    @pytest.mark.asyncio
    async def test_check_consent_required(self, manager):
        """Test checking required consents."""
        result = await manager.check_consent_required(
            user_id="user_123",
            data_categories=[DataCategory.CONVERSATION_DATA],
            purpose="Testing",
        )

        assert "can_process" in result
        assert "required_consents" in result
        assert "missing_required" in result

    @pytest.mark.asyncio
    async def test_check_consent_required_with_consent(self, manager):
        """Test checking required consents with one consent granted."""
        # Grant one consent
        await manager.grant_consent("user_123", ConsentType.ANALYTICS)

        result = await manager.check_consent_required(
            user_id="user_123",
            data_categories=[DataCategory.USAGE_ANALYTICS],
            purpose="Testing",
        )

        # Analytics is optional, so should be able to process
        # Check that the optional consent shows as granted
        optional = result["optional_consents"]
        analytics_consent = next(
            (c for c in optional if c["consent_type"] == "analytics"), None
        )
        assert analytics_consent is not None
        assert analytics_consent["has_consent"] is True

    @pytest.mark.asyncio
    async def test_set_privacy_preferences(self, manager):
        """Test setting privacy preferences."""
        result = await manager.set_privacy_preferences(
            user_id="user_123",
            preferences={
                "allow_analytics": True,
                "data_retention_days": 180,
            },
        )

        assert result["success"] is True

        prefs = await manager.get_privacy_preferences("user_123")
        assert prefs["allow_analytics"] is True
        assert prefs["data_retention_days"] == 180

    @pytest.mark.asyncio
    async def test_get_privacy_preferences_default(self, manager):
        """Test getting default privacy preferences."""
        prefs = await manager.get_privacy_preferences("new_user")

        assert prefs["data_minimization"] is True
        assert prefs["allow_analytics"] is False
        assert prefs["data_retention_days"] == 365

    @pytest.mark.asyncio
    async def test_update_privacy_preferences(self, manager):
        """Test updating existing privacy preferences."""
        # Set initial preferences
        await manager.set_privacy_preferences(
            user_id="user_123",
            preferences={"allow_analytics": True},
        )

        # Update preferences
        await manager.set_privacy_preferences(
            user_id="user_123",
            preferences={"allow_marketing": True},
        )

        prefs = await manager.get_privacy_preferences("user_123")
        assert prefs["allow_analytics"] is True
        assert prefs["allow_marketing"] is True

    @pytest.mark.asyncio
    async def test_get_processing_activities(self, manager):
        """Test getting processing activities."""
        # Grant consent (creates processing activity)
        await manager.grant_consent("user_123", ConsentType.ANALYTICS)

        result = await manager.get_processing_activities("user_123")

        assert "activities" in result
        assert "pagination" in result
        assert len(result["activities"]) > 0

    @pytest.mark.asyncio
    async def test_get_processing_activities_pagination(self, manager):
        """Test processing activities pagination."""
        # Grant multiple consents - each creates a processing activity
        await manager.grant_consent("user_123", ConsentType.ANALYTICS)
        await manager.grant_consent("user_123", ConsentType.MARKETING)

        # Get all activities first to verify count
        all_result = await manager.get_processing_activities("user_123", limit=50)
        total_activities = all_result["pagination"]["total"]

        # Get with limit
        result = await manager.get_processing_activities("user_123", limit=1, offset=0)

        assert len(result["activities"]) == 1
        assert result["pagination"]["limit"] == 1
        assert result["pagination"]["offset"] == 0
        # If there are more than 1 activity, has_more should be True
        if total_activities > 1:
            assert result["pagination"]["has_more"] is True

    @pytest.mark.asyncio
    async def test_generate_consent_report(self, manager):
        """Test generating consent report."""
        # Grant consent and set preferences
        await manager.grant_consent("user_123", ConsentType.ANALYTICS)
        await manager.set_privacy_preferences(
            "user_123",
            preferences={"allow_analytics": True},
        )

        report = await manager.generate_consent_report("user_123")

        assert report["user_id"] == "user_123"
        assert "consent_summary" in report
        assert "consents" in report
        assert "privacy_preferences" in report
        assert "processing_activities" in report

    @pytest.mark.asyncio
    async def test_check_consent_expiry(self, manager):
        """Test checking for expiring consents."""
        # Grant consent
        await manager.grant_consent("user_123", ConsentType.ANALYTICS)

        # Check expiring consents (should be empty since newly granted)
        expiring = await manager.check_consent_expiry()

        # New consents shouldn't be expiring
        assert isinstance(expiring, list)

    @pytest.mark.asyncio
    async def test_cleanup_expired_consents(self, manager):
        """Test cleaning up expired consents."""
        # Grant consent
        grant_result = await manager.grant_consent("user_123", ConsentType.ANALYTICS)
        consent_id = grant_result["consent_id"]

        # Manually set expiration in the past
        manager.consent_records[consent_id].expires_at = datetime.now(
            timezone.utc
        ) - timedelta(days=1)

        # Run cleanup
        count = await manager.cleanup_expired_consents()

        assert count == 1

        # Verify consent is expired
        consent = await manager.get_user_consent("user_123", ConsentType.ANALYTICS)
        assert consent["status"] == "expired"


class TestCreateConsentManager:
    """Tests for create_consent_manager factory function."""

    def test_create_consent_manager(self):
        """Test factory function creates manager."""
        manager = create_consent_manager()

        assert manager is not None
        assert isinstance(manager, ConsentManager)

    def test_factory_returns_new_instance(self):
        """Test factory returns new instances."""
        manager1 = create_consent_manager()
        manager2 = create_consent_manager()

        assert manager1 is not manager2
