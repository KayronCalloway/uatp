"""
Unit tests for Capsule Privacy System.
"""

from datetime import datetime, timezone
from unittest.mock import MagicMock, Mock, patch

import pytest

from src.capsule_schema import CapsuleType
from src.privacy.capsule_privacy import (
    DEFAULT_PRIVACY_POLICIES,
    CapsulePrivacyEngine,
    PrivacyLevel,
    PrivacyPolicy,
    PrivateCapsule,
    privacy_engine,
)


class TestPrivacyLevel:
    """Tests for PrivacyLevel enum."""

    def test_privacy_levels_defined(self):
        """Test all privacy levels are defined."""
        assert PrivacyLevel.PUBLIC == "public"
        assert PrivacyLevel.SELECTIVE == "selective"
        assert PrivacyLevel.PRIVATE == "private"
        assert PrivacyLevel.CONFIDENTIAL == "confidential"

    def test_all_levels_exist(self):
        """Test all expected levels exist."""
        levels = ["PUBLIC", "SELECTIVE", "PRIVATE", "CONFIDENTIAL"]

        for level in levels:
            assert hasattr(PrivacyLevel, level)


class TestPrivacyPolicy:
    """Tests for PrivacyPolicy dataclass."""

    def test_create_policy(self):
        """Test creating a privacy policy."""
        policy = PrivacyPolicy(
            privacy_level=PrivacyLevel.SELECTIVE,
            disclosed_fields={"capsule_id", "timestamp"},
            redacted_fields={"reasoning_trace"},
            proof_required=True,
            authorized_viewers=["user_1", "user_2"],
        )

        assert policy.privacy_level == PrivacyLevel.SELECTIVE
        assert "capsule_id" in policy.disclosed_fields
        assert "reasoning_trace" in policy.redacted_fields
        assert policy.proof_required is True

    def test_allows_field_public(self):
        """Test public policy allows all fields."""
        policy = PrivacyPolicy(
            privacy_level=PrivacyLevel.PUBLIC,
            disclosed_fields=set(),
            redacted_fields=set(),
            proof_required=False,
            authorized_viewers=["*"],
        )

        assert policy.allows_field("any_field") is True
        assert policy.allows_field("sensitive_data") is True

    def test_allows_field_selective(self):
        """Test selective policy allows only disclosed fields."""
        policy = PrivacyPolicy(
            privacy_level=PrivacyLevel.SELECTIVE,
            disclosed_fields={"field1", "field2"},
            redacted_fields=set(),
            proof_required=True,
            authorized_viewers=[],
        )

        assert policy.allows_field("field1") is True
        assert policy.allows_field("field3") is False

    def test_allows_field_private(self):
        """Test private policy blocks redacted fields."""
        policy = PrivacyPolicy(
            privacy_level=PrivacyLevel.PRIVATE,
            disclosed_fields=set(),
            redacted_fields={"secret1", "secret2"},
            proof_required=True,
            authorized_viewers=[],
        )

        assert policy.allows_field("public_field") is True
        assert policy.allows_field("secret1") is False


class TestPrivateCapsule:
    """Tests for PrivateCapsule dataclass."""

    @pytest.fixture
    def mock_proof(self):
        """Create a mock ZK proof."""
        proof = Mock()
        proof.to_dict.return_value = {"proof_type": "test", "data": "mock"}
        return proof

    def test_create_private_capsule(self, mock_proof):
        """Test creating a private capsule."""
        policy = PrivacyPolicy(
            privacy_level=PrivacyLevel.SELECTIVE,
            disclosed_fields={"capsule_id"},
            redacted_fields=set(),
            proof_required=True,
            authorized_viewers=[],
        )

        capsule = PrivateCapsule(
            capsule_id="cap_123",
            public_metadata={"capsule_id": "cap_123", "timestamp": "2024-01-01"},
            privacy_policy=policy,
            integrity_proof=mock_proof,
            privacy_proof=mock_proof,
            original_capsule_hash="abc123",
        )

        assert capsule.capsule_id == "cap_123"
        assert capsule.original_capsule_hash == "abc123"

    def test_to_dict(self, mock_proof):
        """Test converting private capsule to dict."""
        policy = PrivacyPolicy(
            privacy_level=PrivacyLevel.PUBLIC,
            disclosed_fields=set(),
            redacted_fields=set(),
            proof_required=False,
            authorized_viewers=["*"],
        )

        capsule = PrivateCapsule(
            capsule_id="cap_1",
            public_metadata={"test": "data"},
            privacy_policy=policy,
            integrity_proof=mock_proof,
            privacy_proof=None,
            original_capsule_hash="hash123",
        )

        result = capsule.to_dict()

        assert "capsule_id" in result
        assert "public_metadata" in result
        assert "privacy_policy" in result
        assert "integrity_proof" in result
        assert "original_capsule_hash" in result

    def test_to_dict_with_privacy_proof(self, mock_proof):
        """Test to_dict with privacy proof."""
        policy = PrivacyPolicy(
            privacy_level=PrivacyLevel.PRIVATE,
            disclosed_fields=set(),
            redacted_fields=set(),
            proof_required=True,
            authorized_viewers=[],
        )

        capsule = PrivateCapsule(
            capsule_id="cap_1",
            public_metadata={},
            privacy_policy=policy,
            integrity_proof=mock_proof,
            privacy_proof=mock_proof,
            original_capsule_hash="hash",
        )

        result = capsule.to_dict()

        assert result["privacy_proof"] is not None

    def test_to_dict_without_privacy_proof(self, mock_proof):
        """Test to_dict without privacy proof."""
        policy = PrivacyPolicy(
            privacy_level=PrivacyLevel.PUBLIC,
            disclosed_fields=set(),
            redacted_fields=set(),
            proof_required=False,
            authorized_viewers=[],
        )

        capsule = PrivateCapsule(
            capsule_id="cap_1",
            public_metadata={},
            privacy_policy=policy,
            integrity_proof=mock_proof,
            privacy_proof=None,
            original_capsule_hash="hash",
        )

        result = capsule.to_dict()

        assert result["privacy_proof"] is None


class TestCapsulePrivacyEngineInit:
    """Tests for CapsulePrivacyEngine initialization."""

    def test_create_engine(self):
        """Test creating privacy engine."""
        engine = CapsulePrivacyEngine()

        assert engine.privacy_policies == {}
        assert engine.private_capsules == {}


class TestCapsulePrivacyEngineSetPrivacyPolicy:
    """Tests for CapsulePrivacyEngine.set_privacy_policy."""

    def test_set_policy(self):
        """Test setting privacy policy."""
        engine = CapsulePrivacyEngine()
        policy = PrivacyPolicy(
            privacy_level=PrivacyLevel.PRIVATE,
            disclosed_fields=set(),
            redacted_fields=set(),
            proof_required=True,
            authorized_viewers=[],
        )

        engine.set_privacy_policy("cap_1", policy)

        assert "cap_1" in engine.privacy_policies
        assert engine.privacy_policies["cap_1"].privacy_level == PrivacyLevel.PRIVATE

    def test_overwrites_existing_policy(self):
        """Test overwrites existing policy."""
        engine = CapsulePrivacyEngine()

        policy1 = PrivacyPolicy(
            privacy_level=PrivacyLevel.PUBLIC,
            disclosed_fields=set(),
            redacted_fields=set(),
            proof_required=False,
            authorized_viewers=[],
        )

        policy2 = PrivacyPolicy(
            privacy_level=PrivacyLevel.PRIVATE,
            disclosed_fields=set(),
            redacted_fields=set(),
            proof_required=True,
            authorized_viewers=[],
        )

        engine.set_privacy_policy("cap_1", policy1)
        engine.set_privacy_policy("cap_1", policy2)

        assert engine.privacy_policies["cap_1"].privacy_level == PrivacyLevel.PRIVATE


class TestCapsulePrivacyEnginePrivatizeCapsule:
    """Tests for CapsulePrivacyEngine.privatize_capsule."""

    @pytest.fixture
    def mock_capsule(self):
        """Create a mock capsule."""
        capsule = Mock()
        capsule.capsule_id = "cap_test"
        capsule.capsule_type = CapsuleType.REASONING_TRACE
        capsule.version = "7.2.0"
        capsule.timestamp = datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        capsule.status = "complete"
        capsule.verification = Mock()
        capsule.verification.signature = "sig123"
        capsule.verification.hash = "hash123"
        capsule.verification.signer = "signer_1"
        capsule.reasoning_trace = Mock()
        capsule.reasoning_trace.steps = [1, 2, 3]
        return capsule

    @pytest.fixture
    def mock_zk_system(self):
        """Mock the ZK system."""
        with patch("src.privacy.capsule_privacy.zk_system") as mock:
            mock_proof = Mock()
            mock_proof.to_dict.return_value = {"proof": "data"}
            mock.prove_capsule_integrity.return_value = mock_proof
            mock.generate_privacy_capsule_proof.return_value = mock_proof
            yield mock

    def test_privatize_capsule(self, mock_capsule, mock_zk_system):
        """Test privatizing a capsule."""
        engine = CapsulePrivacyEngine()
        policy = PrivacyPolicy(
            privacy_level=PrivacyLevel.SELECTIVE,
            disclosed_fields={"capsule_id", "timestamp"},
            redacted_fields=set(),
            proof_required=False,
            authorized_viewers=[],
        )

        result = engine.privatize_capsule(mock_capsule, policy)

        assert isinstance(result, PrivateCapsule)
        assert result.capsule_id == "cap_test"
        assert result.original_capsule_hash is not None

    def test_stores_private_capsule(self, mock_capsule, mock_zk_system):
        """Test stores private capsule."""
        engine = CapsulePrivacyEngine()
        policy = PrivacyPolicy(
            privacy_level=PrivacyLevel.PRIVATE,
            disclosed_fields=set(),
            redacted_fields=set(),
            proof_required=False,
            authorized_viewers=[],
        )

        result = engine.privatize_capsule(mock_capsule, policy)

        assert "cap_test" in engine.private_capsules
        assert engine.private_capsules["cap_test"] == result

    def test_generates_integrity_proof(self, mock_capsule, mock_zk_system):
        """Test generates integrity proof."""
        engine = CapsulePrivacyEngine()
        policy = PrivacyPolicy(
            privacy_level=PrivacyLevel.PUBLIC,
            disclosed_fields=set(),
            redacted_fields=set(),
            proof_required=False,
            authorized_viewers=[],
        )

        result = engine.privatize_capsule(mock_capsule, policy)

        assert mock_zk_system.prove_capsule_integrity.called
        assert result.integrity_proof is not None

    def test_generates_privacy_proof_when_required(self, mock_capsule, mock_zk_system):
        """Test generates privacy proof when required."""
        engine = CapsulePrivacyEngine()
        policy = PrivacyPolicy(
            privacy_level=PrivacyLevel.SELECTIVE,
            disclosed_fields=set(),
            redacted_fields=set(),
            proof_required=True,
            authorized_viewers=[],
        )

        result = engine.privatize_capsule(mock_capsule, policy)

        assert mock_zk_system.generate_privacy_capsule_proof.called
        assert result.privacy_proof is not None

    def test_no_privacy_proof_when_not_required(self, mock_capsule, mock_zk_system):
        """Test no privacy proof when not required."""
        engine = CapsulePrivacyEngine()
        policy = PrivacyPolicy(
            privacy_level=PrivacyLevel.PUBLIC,
            disclosed_fields=set(),
            redacted_fields=set(),
            proof_required=False,
            authorized_viewers=[],
        )

        result = engine.privatize_capsule(mock_capsule, policy)

        assert result.privacy_proof is None


class TestCapsulePrivacyEngineVerifyPrivateCapsule:
    """Tests for CapsulePrivacyEngine.verify_private_capsule."""

    @pytest.fixture
    def mock_proof(self):
        """Create a mock ZK proof."""
        proof = Mock()
        proof.to_dict.return_value = {"proof": "data"}
        return proof

    @pytest.fixture
    def private_capsule(self, mock_proof):
        """Create a private capsule."""
        policy = PrivacyPolicy(
            privacy_level=PrivacyLevel.PRIVATE,
            disclosed_fields=set(),
            redacted_fields=set(),
            proof_required=True,
            authorized_viewers=[],
        )

        return PrivateCapsule(
            capsule_id="cap_1",
            public_metadata={},
            privacy_policy=policy,
            integrity_proof=mock_proof,
            privacy_proof=mock_proof,
            original_capsule_hash="hash",
        )

    def test_verify_valid_capsule(self, private_capsule):
        """Test verifying a valid private capsule."""
        engine = CapsulePrivacyEngine()

        with patch("src.privacy.capsule_privacy.zk_system") as mock_zk:
            mock_zk.verify_proof.return_value = True

            result = engine.verify_private_capsule(private_capsule)

            assert result is True

    def test_verify_invalid_integrity_proof(self, private_capsule):
        """Test verification fails for invalid integrity proof."""
        engine = CapsulePrivacyEngine()

        with patch("src.privacy.capsule_privacy.zk_system") as mock_zk:
            mock_zk.verify_proof.return_value = False

            result = engine.verify_private_capsule(private_capsule)

            assert result is False

    def test_verify_without_privacy_proof(self, mock_proof):
        """Test verifying capsule without privacy proof."""
        engine = CapsulePrivacyEngine()
        policy = PrivacyPolicy(
            privacy_level=PrivacyLevel.PUBLIC,
            disclosed_fields=set(),
            redacted_fields=set(),
            proof_required=False,
            authorized_viewers=[],
        )

        capsule = PrivateCapsule(
            capsule_id="cap_1",
            public_metadata={},
            privacy_policy=policy,
            integrity_proof=mock_proof,
            privacy_proof=None,
            original_capsule_hash="hash",
        )

        with patch("src.privacy.capsule_privacy.zk_system") as mock_zk:
            mock_zk.verify_proof.return_value = True

            result = engine.verify_private_capsule(capsule)

            assert result is True

    def test_verify_invalid_privacy_proof(self, private_capsule):
        """Test verification fails for invalid privacy proof."""
        engine = CapsulePrivacyEngine()

        with patch("src.privacy.capsule_privacy.zk_system") as mock_zk:
            # Integrity passes, privacy fails
            mock_zk.verify_proof.side_effect = [True, False]

            result = engine.verify_private_capsule(private_capsule)

            assert result is False

    def test_handles_verification_exception(self, private_capsule):
        """Test handles verification exception."""
        engine = CapsulePrivacyEngine()

        with patch("src.privacy.capsule_privacy.zk_system") as mock_zk:
            mock_zk.verify_proof.side_effect = Exception("Verification error")

            result = engine.verify_private_capsule(private_capsule)

            assert result is False


class TestCapsulePrivacyEngineSelectiveDisclosure:
    """Tests for CapsulePrivacyEngine.selective_disclosure."""

    @pytest.fixture
    def setup_engine(self):
        """Setup engine with a private capsule."""
        engine = CapsulePrivacyEngine()

        mock_proof = Mock()
        mock_proof.to_dict.return_value = {"proof": "data"}

        policy = PrivacyPolicy(
            privacy_level=PrivacyLevel.SELECTIVE,
            disclosed_fields={"field1", "field2"},
            redacted_fields=set(),
            proof_required=True,
            authorized_viewers=["user_1", "user_2"],
        )

        private_capsule = PrivateCapsule(
            capsule_id="cap_1",
            public_metadata={
                "field1": "value1",
                "field2": "value2",
                "field3": "value3",
            },
            privacy_policy=policy,
            integrity_proof=mock_proof,
            privacy_proof=mock_proof,
            original_capsule_hash="hash",
        )

        engine.private_capsules["cap_1"] = private_capsule
        return engine

    def test_selective_disclosure_authorized(self, setup_engine):
        """Test selective disclosure for authorized user."""
        engine = setup_engine

        with patch("src.privacy.capsule_privacy.zk_system") as mock_zk:
            mock_proof = Mock()
            mock_proof.to_dict.return_value = {"proof": "data"}
            mock_zk.prove_capsule_privacy.return_value = mock_proof

            result = engine.selective_disclosure(
                capsule_id="cap_1",
                requested_fields={"field1", "field2"},
                requester_id="user_1",
            )

            assert "disclosed_fields" in result
            assert "field1" in result["disclosed_fields"]
            assert "field2" in result["disclosed_fields"]

    def test_selective_disclosure_unauthorized(self, setup_engine):
        """Test selective disclosure for unauthorized user."""
        engine = setup_engine

        with pytest.raises(PermissionError):
            engine.selective_disclosure(
                capsule_id="cap_1",
                requested_fields={"field1"},
                requester_id="unauthorized_user",
            )

    def test_selective_disclosure_public_capsule(self):
        """Test selective disclosure for public capsule."""
        engine = CapsulePrivacyEngine()

        mock_proof = Mock()
        mock_proof.to_dict.return_value = {"proof": "data"}

        policy = PrivacyPolicy(
            privacy_level=PrivacyLevel.PUBLIC,
            disclosed_fields=set(),
            redacted_fields=set(),
            proof_required=False,
            authorized_viewers=["*"],
        )

        private_capsule = PrivateCapsule(
            capsule_id="cap_1",
            public_metadata={"field1": "value1"},
            privacy_policy=policy,
            integrity_proof=mock_proof,
            privacy_proof=None,
            original_capsule_hash="hash",
        )

        engine.private_capsules["cap_1"] = private_capsule

        with patch("src.privacy.capsule_privacy.zk_system") as mock_zk:
            mock_zk.prove_capsule_privacy.return_value = mock_proof

            # Anyone can access public capsule
            result = engine.selective_disclosure(
                capsule_id="cap_1",
                requested_fields={"field1"},
                requester_id="anyone",
            )

            assert result is not None

    def test_selective_disclosure_redacts_fields(self, setup_engine):
        """Test redacts fields not in policy."""
        engine = setup_engine

        with patch("src.privacy.capsule_privacy.zk_system") as mock_zk:
            mock_proof = Mock()
            mock_proof.to_dict.return_value = {"proof": "data"}
            mock_zk.prove_capsule_privacy.return_value = mock_proof

            result = engine.selective_disclosure(
                capsule_id="cap_1",
                requested_fields={"field1", "field3"},  # field3 not disclosed
                requester_id="user_1",
            )

            # field1 should be disclosed, field3 should not
            assert "field1" in result["disclosed_fields"]
            assert "field3" not in result["disclosed_fields"]

    def test_selective_disclosure_capsule_not_found(self):
        """Test selective disclosure for non-existent capsule."""
        engine = CapsulePrivacyEngine()

        with pytest.raises(ValueError, match="not found"):
            engine.selective_disclosure(
                capsule_id="nonexistent",
                requested_fields={"field1"},
                requester_id="user_1",
            )


class TestCapsulePrivacyEngineProveCapsuleProperty:
    """Tests for CapsulePrivacyEngine.prove_capsule_property."""

    @pytest.fixture
    def setup_engine_with_capsule(self):
        """Setup engine with a private capsule."""
        engine = CapsulePrivacyEngine()

        mock_proof = Mock()
        mock_proof.to_dict.return_value = {"proof": "data"}

        policy = PrivacyPolicy(
            privacy_level=PrivacyLevel.PRIVATE,
            disclosed_fields=set(),
            redacted_fields=set(),
            proof_required=True,
            authorized_viewers=[],
        )

        private_capsule = PrivateCapsule(
            capsule_id="cap_1",
            public_metadata={
                "capsule_type": "reasoning_trace",
                "timestamp": 1704110400,
            },
            privacy_policy=policy,
            integrity_proof=mock_proof,
            privacy_proof=mock_proof,
            original_capsule_hash="hash",
        )

        engine.private_capsules["cap_1"] = private_capsule
        return engine

    def test_prove_timestamp_range(self, setup_engine_with_capsule):
        """Test proving timestamp range."""
        engine = setup_engine_with_capsule

        with patch("src.privacy.capsule_privacy.zk_system") as mock_zk:
            mock_proof = Mock()
            mock_zk.prove_range.return_value = mock_proof

            result = engine.prove_capsule_property(
                capsule_id="cap_1",
                property_name="timestamp_range",
                property_value=(1704000000, 1704200000),
            )

            assert mock_zk.prove_range.called
            assert result is not None

    def test_prove_capsule_type(self, setup_engine_with_capsule):
        """Test proving capsule type."""
        engine = setup_engine_with_capsule

        with patch("src.privacy.capsule_privacy.zk_system") as mock_zk:
            mock_proof = Mock()
            mock_zk.prove_capsule_privacy.return_value = mock_proof

            result = engine.prove_capsule_property(
                capsule_id="cap_1",
                property_name="capsule_type",
                property_value="reasoning_trace",
            )

            assert result is not None

    def test_prove_content_length(self, setup_engine_with_capsule):
        """Test proving content length range."""
        engine = setup_engine_with_capsule

        with patch("src.privacy.capsule_privacy.zk_system") as mock_zk:
            mock_proof = Mock()
            mock_zk.prove_range.return_value = mock_proof

            result = engine.prove_capsule_property(
                capsule_id="cap_1",
                property_name="content_length",
                property_value=(10, 1000),
            )

            assert mock_zk.prove_range.called

    def test_unknown_property_raises_error(self, setup_engine_with_capsule):
        """Test unknown property raises error."""
        engine = setup_engine_with_capsule

        with pytest.raises(ValueError, match="Unknown property"):
            engine.prove_capsule_property(
                capsule_id="cap_1",
                property_name="unknown_property",
                property_value="value",
            )

    def test_capsule_not_found_raises_error(self):
        """Test capsule not found raises error."""
        engine = CapsulePrivacyEngine()

        with pytest.raises(ValueError, match="not found"):
            engine.prove_capsule_property(
                capsule_id="nonexistent",
                property_name="timestamp_range",
                property_value=(0, 100),
            )


class TestCapsulePrivacyEngineCreatePrivacyReport:
    """Tests for CapsulePrivacyEngine.create_privacy_report."""

    def test_report_capsule_not_found(self):
        """Test report for non-existent capsule."""
        engine = CapsulePrivacyEngine()

        result = engine.create_privacy_report("nonexistent")

        assert result["error"] == "Capsule not found"

    def test_creates_privacy_report(self):
        """Test creates privacy report."""
        engine = CapsulePrivacyEngine()

        mock_proof = Mock()
        mock_proof.to_dict.return_value = {"proof": "data"}

        policy = PrivacyPolicy(
            privacy_level=PrivacyLevel.SELECTIVE,
            disclosed_fields={"field1", "field2"},
            redacted_fields={"secret"},
            proof_required=True,
            authorized_viewers=["user_1", "user_2"],
        )

        private_capsule = PrivateCapsule(
            capsule_id="cap_1",
            public_metadata={},
            privacy_policy=policy,
            integrity_proof=mock_proof,
            privacy_proof=mock_proof,
            original_capsule_hash="hash",
        )

        engine.private_capsules["cap_1"] = private_capsule

        with patch("src.privacy.capsule_privacy.zk_system") as mock_zk:
            mock_zk.verify_proof.return_value = True

            result = engine.create_privacy_report("cap_1")

            assert result["capsule_id"] == "cap_1"
            assert result["privacy_level"] == "selective"
            assert "proofs_verified" in result

    def test_report_includes_field_lists(self):
        """Test report includes disclosed and redacted fields."""
        engine = CapsulePrivacyEngine()

        mock_proof = Mock()
        mock_proof.to_dict.return_value = {"proof": "data"}

        policy = PrivacyPolicy(
            privacy_level=PrivacyLevel.PRIVATE,
            disclosed_fields={"a", "b"},
            redacted_fields={"c", "d"},
            proof_required=False,
            authorized_viewers=[],
        )

        private_capsule = PrivateCapsule(
            capsule_id="cap_1",
            public_metadata={},
            privacy_policy=policy,
            integrity_proof=mock_proof,
            privacy_proof=None,
            original_capsule_hash="hash",
        )

        engine.private_capsules["cap_1"] = private_capsule

        with patch("src.privacy.capsule_privacy.zk_system") as mock_zk:
            mock_zk.verify_proof.return_value = True

            result = engine.create_privacy_report("cap_1")

            assert set(result["disclosed_fields"]) == {"a", "b"}
            assert set(result["redacted_fields"]) == {"c", "d"}


class TestDefaultPrivacyPolicies:
    """Tests for DEFAULT_PRIVACY_POLICIES."""

    def test_public_policy_defined(self):
        """Test public policy is defined."""
        assert "public" in DEFAULT_PRIVACY_POLICIES

        policy = DEFAULT_PRIVACY_POLICIES["public"]
        assert policy.privacy_level == PrivacyLevel.PUBLIC
        assert policy.proof_required is False

    def test_selective_policy_defined(self):
        """Test selective policy is defined."""
        assert "selective" in DEFAULT_PRIVACY_POLICIES

        policy = DEFAULT_PRIVACY_POLICIES["selective"]
        assert policy.privacy_level == PrivacyLevel.SELECTIVE
        assert policy.proof_required is True

    def test_private_policy_defined(self):
        """Test private policy is defined."""
        assert "private" in DEFAULT_PRIVACY_POLICIES

        policy = DEFAULT_PRIVACY_POLICIES["private"]
        assert policy.privacy_level == PrivacyLevel.PRIVATE
        assert "capsule_id" in policy.disclosed_fields

    def test_confidential_policy_defined(self):
        """Test confidential policy is defined."""
        assert "confidential" in DEFAULT_PRIVACY_POLICIES

        policy = DEFAULT_PRIVACY_POLICIES["confidential"]
        assert policy.privacy_level == PrivacyLevel.CONFIDENTIAL
        assert policy.proof_required is True


class TestCapsulePrivacyEngineHelpers:
    """Tests for CapsulePrivacyEngine helper methods."""

    @pytest.fixture
    def mock_capsule(self):
        """Create a mock capsule."""
        capsule = Mock()
        capsule.capsule_id = "cap_test"
        capsule.capsule_type = CapsuleType.REASONING_TRACE
        capsule.version = "7.2.0"
        capsule.timestamp = datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        capsule.status = "complete"
        capsule.verification = Mock()
        capsule.verification.signature = "sig"
        capsule.verification.hash = "hash"
        capsule.verification.signer = "signer"
        capsule.reasoning_trace = Mock()
        capsule.reasoning_trace.steps = [1, 2, 3]
        return capsule

    def test_hash_capsule(self, mock_capsule):
        """Test hashing a capsule."""
        engine = CapsulePrivacyEngine()

        hash_result = engine._hash_capsule(mock_capsule)

        assert isinstance(hash_result, str)
        assert len(hash_result) == 64  # SHA256 hex digest

    def test_hash_capsule_deterministic(self, mock_capsule):
        """Test capsule hashing is deterministic."""
        engine = CapsulePrivacyEngine()

        hash1 = engine._hash_capsule(mock_capsule)
        hash2 = engine._hash_capsule(mock_capsule)

        assert hash1 == hash2

    def test_extract_public_metadata(self, mock_capsule):
        """Test extracting public metadata."""
        engine = CapsulePrivacyEngine()
        policy = PrivacyPolicy(
            privacy_level=PrivacyLevel.SELECTIVE,
            disclosed_fields={"timestamp", "status"},
            redacted_fields=set(),
            proof_required=False,
            authorized_viewers=[],
        )

        metadata = engine._extract_public_metadata(mock_capsule, policy)

        # Always includes basic fields
        assert "capsule_id" in metadata
        assert "capsule_type" in metadata
        assert "version" in metadata

        # Includes allowed fields
        assert "timestamp" in metadata
        assert "status" in metadata

    def test_extract_public_metadata_redacts(self, mock_capsule):
        """Test redacts disallowed fields."""
        engine = CapsulePrivacyEngine()
        policy = PrivacyPolicy(
            privacy_level=PrivacyLevel.SELECTIVE,
            disclosed_fields={"capsule_id"},
            redacted_fields=set(),
            proof_required=False,
            authorized_viewers=[],
        )

        metadata = engine._extract_public_metadata(mock_capsule, policy)

        # Should not include timestamp if not in disclosed_fields
        assert "timestamp" not in metadata

    def test_capsule_to_dict(self, mock_capsule):
        """Test converting capsule to dict."""
        engine = CapsulePrivacyEngine()

        result = engine._capsule_to_dict(mock_capsule)

        assert "capsule_id" in result
        assert "capsule_type" in result
        assert "timestamp" in result
        assert "verification" in result


class TestGlobalPrivacyEngine:
    """Tests for global privacy engine instance."""

    def test_privacy_engine_exists(self):
        """Test global privacy engine exists."""
        assert privacy_engine is not None
        assert isinstance(privacy_engine, CapsulePrivacyEngine)
