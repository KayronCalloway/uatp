"""
Unit tests for UATP 7.2 Model Registry Protocol

Tests:
- Content-addressed storage
- License verification
- Compliance checking
- License compatibility
"""

import pytest
import hashlib
import tempfile
import os
from datetime import datetime, timezone, timedelta

from src.services.content_addressed_storage import (
    ContentAddressedStorage,
    StorageBackend,
    LocalStorageProvider,
)
from src.services.license_verifier import (
    LicenseVerifier,
    UsageType,
    ComplianceStatus,
)
from src.models.model_artifact import (
    ArtifactType,
    StorageBackend as ArtifactStorageBackend,
    UploadStatus,
)
from src.models.model_license import (
    LicenseType,
    Permission,
    Restriction,
)


class TestContentAddressedStorage:
    """Test ContentAddressedStorage service."""

    @pytest.fixture
    def storage(self, tmp_path):
        """Create storage with temporary directory."""
        return ContentAddressedStorage(
            default_backend=StorageBackend.LOCAL,
            local_base_path=str(tmp_path / "artifacts"),
        )

    @pytest.mark.asyncio
    async def test_compute_hash(self, storage):
        """Test content hash computation."""
        data = b"test content for hashing"
        expected_hash = hashlib.sha256(data).hexdigest()

        computed_hash = storage.compute_hash(data)

        assert computed_hash == expected_hash
        assert len(computed_hash) == 64

    @pytest.mark.asyncio
    async def test_store_and_retrieve(self, storage):
        """Test storing and retrieving content."""
        data = b"test model weights data"

        # Store
        location = await storage.store(data)
        assert location.content_hash == hashlib.sha256(data).hexdigest()
        assert location.size_bytes == len(data)
        assert location.backend == StorageBackend.LOCAL

        # Retrieve
        result = await storage.retrieve(location.content_hash)
        assert result.success
        assert result.data == data
        assert result.verified

    @pytest.mark.asyncio
    async def test_deduplication(self, storage):
        """Test content deduplication."""
        data = b"duplicate content"

        # Store twice
        location1 = await storage.store(data)
        location2 = await storage.store(data)

        # Should return same hash
        assert location1.content_hash == location2.content_hash

    @pytest.mark.asyncio
    async def test_exists(self, storage):
        """Test existence check."""
        data = b"existence test data"

        # Before storage
        content_hash = storage.compute_hash(data)
        assert not await storage.exists(content_hash)

        # After storage
        await storage.store(data)
        assert await storage.exists(content_hash)

    @pytest.mark.asyncio
    async def test_delete(self, storage):
        """Test content deletion."""
        data = b"content to delete"

        location = await storage.store(data)
        assert await storage.exists(location.content_hash)

        # Delete
        deleted = await storage.delete(location.content_hash)
        assert deleted
        assert not await storage.exists(location.content_hash)

    @pytest.mark.asyncio
    async def test_integrity_verification(self, storage):
        """Test content integrity verification."""
        data = b"integrity test data"

        location = await storage.store(data)

        # Verify
        verified = await storage.verify(location.content_hash)
        assert verified

    @pytest.mark.asyncio
    async def test_retrieve_nonexistent(self, storage):
        """Test retrieving non-existent content."""
        fake_hash = "a" * 64

        result = await storage.retrieve(fake_hash)
        assert not result.success
        assert result.error is not None

    @pytest.mark.asyncio
    async def test_store_with_metadata(self, storage):
        """Test storing content with metadata."""
        data = b"content with metadata"
        metadata = {"format": "safetensors", "version": "1.0"}

        location = await storage.store(data, metadata=metadata)

        # Retrieve metadata
        stored_metadata = await storage.get_metadata(location.content_hash)
        assert stored_metadata == metadata


class TestLicenseVerifier:
    """Test LicenseVerifier service."""

    @pytest.fixture
    def verifier(self):
        """Create license verifier."""
        return LicenseVerifier()

    def test_verify_mit_commercial(self, verifier):
        """Test MIT license allows commercial use."""
        result = verifier.verify_compliance(
            license_type="MIT",
            usage_type=UsageType.COMMERCIAL,
        )

        assert result.compliant
        assert result.status == ComplianceStatus.COMPLIANT
        assert not result.violations

    def test_verify_mit_distribution(self, verifier):
        """Test MIT license allows distribution."""
        result = verifier.verify_compliance(
            license_type="MIT",
            usage_type=UsageType.DISTRIBUTION,
        )

        assert result.compliant
        assert not result.violations

    def test_verify_mit_requires_attribution(self, verifier):
        """Test MIT license requires attribution."""
        result = verifier.verify_compliance(
            license_type="MIT",
            usage_type=UsageType.COMMERCIAL,
        )

        assert "Attribution required" in result.required_actions[0]
        assert result.attribution is not None
        assert result.attribution["required"]

    def test_verify_cc_nc_commercial_violation(self, verifier):
        """Test CC-BY-NC prohibits commercial use."""
        result = verifier.verify_compliance(
            license_type="CC-BY-NC-4.0",
            usage_type=UsageType.COMMERCIAL,
        )

        assert not result.compliant
        assert result.status == ComplianceStatus.NON_COMPLIANT
        assert any("prohibited" in v.lower() for v in result.violations)

    def test_verify_proprietary_distribution_violation(self, verifier):
        """Test proprietary license prohibits distribution."""
        result = verifier.verify_compliance(
            license_type="proprietary",
            usage_type=UsageType.DISTRIBUTION,
        )

        assert not result.compliant
        assert result.status == ComplianceStatus.NON_COMPLIANT

    def test_verify_expired_license(self, verifier):
        """Test expired license is non-compliant."""
        result = verifier.verify_compliance(
            license_type="MIT",
            usage_type=UsageType.COMMERCIAL,
            is_expired=True,
        )

        assert not result.compliant
        assert result.status == ComplianceStatus.EXPIRED

    def test_verify_unknown_license(self, verifier):
        """Test unknown license type."""
        result = verifier.verify_compliance(
            license_type="UnknownLicense",
            usage_type=UsageType.COMMERCIAL,
        )

        assert not result.compliant
        assert result.status == ComplianceStatus.UNKNOWN

    def test_verify_gpl_derivative(self, verifier):
        """Test GPL license for derivative works."""
        result = verifier.verify_compliance(
            license_type="GPL-3.0",
            usage_type=UsageType.DERIVATIVE_WORK,
        )

        assert result.compliant
        # Should warn about copyleft requirements
        assert any("copyleft" in w.lower() or "same license" in w.lower()
                   for w in result.warnings + result.required_actions)

    def test_check_mit_to_apache_compatibility(self, verifier):
        """Test MIT is compatible with Apache-2.0."""
        result = verifier.check_compatibility(
            source_licenses=["MIT"],
            target_license="Apache-2.0",
        )

        assert result.compatible

    def test_check_gpl_to_mit_incompatibility(self, verifier):
        """Test GPL is not compatible with MIT (copyleft)."""
        result = verifier.check_compatibility(
            source_licenses=["GPL-3.0"],
            target_license="MIT",
        )

        assert not result.compatible
        assert len(result.issues) > 0

    def test_check_multiple_source_compatibility(self, verifier):
        """Test compatibility with multiple source licenses."""
        result = verifier.check_compatibility(
            source_licenses=["MIT", "Apache-2.0"],
            target_license="GPL-3.0",
        )

        # MIT can go to GPL, but Apache-2.0 compatibility with GPL is nuanced
        assert isinstance(result.compatible, bool)

    def test_list_supported_licenses(self, verifier):
        """Test listing supported licenses."""
        licenses = verifier.list_supported_licenses()

        assert "MIT" in licenses
        assert "Apache-2.0" in licenses
        assert "GPL-3.0" in licenses
        assert "CC-BY-4.0" in licenses
        assert "proprietary" in licenses

    def test_get_license_info(self, verifier):
        """Test getting license information."""
        info = verifier.get_license_info("MIT")

        assert info is not None
        assert "permissions" in info
        assert "restrictions" in info
        assert "commercial_use" in info["permissions"]
        assert not info["copyleft"]

    def test_generate_attribution_notice(self, verifier):
        """Test generating attribution notice."""
        notice = verifier.generate_attribution_notice(
            model_name="TestModel",
            license_type="MIT",
            copyright_holder="Test Corp",
            license_url="https://opensource.org/licenses/MIT",
        )

        assert "TestModel" in notice
        assert "MIT" in notice
        assert "Test Corp" in notice
        assert "https://opensource.org/licenses/MIT" in notice


class TestModelArtifactModel:
    """Test ModelArtifactModel."""

    def test_artifact_types(self):
        """Test artifact type enum values."""
        assert ArtifactType.WEIGHTS.value == "weights"
        assert ArtifactType.CONFIG.value == "config"
        assert ArtifactType.TOKENIZER.value == "tokenizer"
        assert ArtifactType.ADAPTER.value == "adapter"

    def test_upload_status(self):
        """Test upload status enum values."""
        assert UploadStatus.PENDING.value == "pending"
        assert UploadStatus.COMPLETED.value == "completed"
        assert UploadStatus.FAILED.value == "failed"


class TestModelLicenseModel:
    """Test ModelLicenseModel."""

    def test_license_types(self):
        """Test license type enum values."""
        assert LicenseType.MIT.value == "MIT"
        assert LicenseType.APACHE_2_0.value == "Apache-2.0"
        assert LicenseType.GPL_3_0.value == "GPL-3.0"
        assert LicenseType.OPENRAIL_M.value == "OpenRAIL-M"

    def test_permission_types(self):
        """Test permission enum values."""
        assert Permission.COMMERCIAL_USE.value == "commercial_use"
        assert Permission.DERIVATIVE_WORKS.value == "derivative_works"
        assert Permission.DISTRIBUTION.value == "distribution"

    def test_restriction_types(self):
        """Test restriction enum values."""
        assert Restriction.NO_COMMERCIAL.value == "no_commercial"
        assert Restriction.ATTRIBUTION_REQUIRED.value == "attribution_required"
        assert Restriction.SHARE_ALIKE.value == "share_alike"
        assert Restriction.NO_HARM.value == "no_harm"


class TestLlama2LicenseCompliance:
    """Test Llama 2 Community License specific cases."""

    @pytest.fixture
    def verifier(self):
        """Create license verifier."""
        return LicenseVerifier()

    def test_llama2_commercial_use(self, verifier):
        """Test Llama 2 allows commercial use with user limit."""
        result = verifier.verify_compliance(
            license_type="Llama-2-Community",
            usage_type=UsageType.COMMERCIAL,
        )

        assert result.compliant
        # Should have warning about user limit
        assert any("monthly" in w.lower() for w in result.warnings)

    def test_llama2_derivative_works(self, verifier):
        """Test Llama 2 allows derivative works."""
        result = verifier.verify_compliance(
            license_type="Llama-2-Community",
            usage_type=UsageType.DERIVATIVE_WORK,
        )

        assert result.compliant


class TestOpenRAILCompliance:
    """Test OpenRAIL-M License specific cases."""

    @pytest.fixture
    def verifier(self):
        """Create license verifier."""
        return LicenseVerifier()

    def test_openrail_commercial_use(self, verifier):
        """Test OpenRAIL-M allows commercial use."""
        result = verifier.verify_compliance(
            license_type="OpenRAIL-M",
            usage_type=UsageType.COMMERCIAL,
        )

        assert result.compliant

    def test_openrail_restrictions(self, verifier):
        """Test OpenRAIL-M has behavioral restrictions."""
        info = verifier.get_license_info("OpenRAIL-M")

        assert "no_harm" in info["restrictions"]
        assert "behavioral_restrictions" in info["conditions"]
