"""
Unit tests for UATP 7.2 Training Provenance Schema

Tests:
- Model registration
- Training session management
- Model lineage queries
- Capsule schema validation
"""

import pytest
from datetime import datetime, timezone
from typing import Dict, Any

from pydantic import ValidationError

from src.capsule_schema import (
    CapsuleType,
    CapsuleStatus,
    DatasetReference,
    TrainingProvenancePayload,
    ModelRegistrationPayload,
    TrainingProvenanceCapsule,
    ModelRegistrationCapsule,
    Verification,
)
from src.utils.uatp_envelope import (
    wrap_in_uatp_envelope,
    detect_capsule_version,
    create_training_context,
    is_envelope_format,
)
from src.services.model_registry_service import ModelRegistryService


class TestCapsuleSchemaUATP72:
    """Test UATP 7.2 capsule types and payloads."""

    def test_capsule_type_enum_has_72_types(self):
        """Verify UATP 7.2 capsule types are registered."""
        assert CapsuleType.TRAINING_PROVENANCE == "training_provenance"
        assert CapsuleType.MODEL_REGISTRATION == "model_registration"
        assert CapsuleType.WORKFLOW_STEP == "workflow_step"
        assert CapsuleType.WORKFLOW_COMPLETE == "workflow_complete"
        assert CapsuleType.HARDWARE_ATTESTATION == "hardware_attestation"
        assert CapsuleType.EDGE_SYNC == "edge_sync"
        assert CapsuleType.MODEL_LICENSE == "model_license"
        assert CapsuleType.MODEL_ARTIFACT == "model_artifact"

    def test_dataset_reference_validation(self):
        """Test DatasetReference model validation."""
        ds_ref = DatasetReference(
            dataset_id="ds_001",
            dataset_name="OpenAssistant",
            version="1.0.0",
            source_url="https://huggingface.co/datasets/oasst1",
            license="Apache-2.0",
            content_hash="abc123def456",
            record_count=100000,
        )
        assert ds_ref.dataset_id == "ds_001"
        assert ds_ref.record_count == 100000

    def test_dataset_reference_minimal(self):
        """Test DatasetReference with minimal required fields."""
        ds_ref = DatasetReference(
            dataset_id="ds_002",
            dataset_name="Custom Dataset",
            version="0.1",
        )
        assert ds_ref.source_url is None
        assert ds_ref.content_hash is None


class TestTrainingProvenancePayload:
    """Test TrainingProvenancePayload validation."""

    def test_valid_training_provenance(self):
        """Test creating a valid training provenance payload."""
        payload = TrainingProvenancePayload(
            session_id="train_20260302_abc123",
            model_id="model_001",
            session_type="fine_tuning",
            dataset_refs=[
                DatasetReference(
                    dataset_id="ds_001",
                    dataset_name="Training Data",
                    version="1.0",
                )
            ],
            started_at=datetime.now(timezone.utc),
            status="completed",
        )
        assert payload.session_type == "fine_tuning"
        assert len(payload.dataset_refs) == 1

    def test_training_provenance_with_hyperparams(self):
        """Test training provenance with hyperparameters."""
        payload = TrainingProvenancePayload(
            session_id="train_20260302_def456",
            model_id="model_002",
            session_type="rlhf",
            dataset_refs=[
                DatasetReference(
                    dataset_id="ds_002",
                    dataset_name="RLHF Data",
                    version="2.0",
                )
            ],
            hyperparameters={
                "learning_rate": 1e-5,
                "batch_size": 32,
                "epochs": 3,
                "warmup_steps": 100,
            },
            compute_resources={
                "gpus": 8,
                "gpu_type": "A100",
                "total_gpu_hours": 48,
            },
            started_at=datetime.now(timezone.utc),
            completed_at=datetime.now(timezone.utc),
            metrics={
                "loss": 0.05,
                "reward_score": 0.92,
            },
            status="completed",
        )
        assert payload.hyperparameters["learning_rate"] == 1e-5
        assert payload.compute_resources["gpus"] == 8


class TestModelRegistrationPayload:
    """Test ModelRegistrationPayload validation."""

    def test_base_model_registration(self):
        """Test registering a base model."""
        payload = ModelRegistrationPayload(
            model_id="llama-3-70b",
            model_hash="sha256:abc123...",
            model_type="base",
            version="3.0.0",
            name="Llama 3 70B",
            description="Large language model",
            capabilities=["text_generation", "reasoning"],
        )
        assert payload.model_type == "base"
        assert payload.base_model_id is None

    def test_fine_tuned_model_registration(self):
        """Test registering a fine-tuned model with lineage."""
        payload = ModelRegistrationPayload(
            model_id="custom-llama-70b",
            model_hash="sha256:def456...",
            model_type="fine_tune",
            version="1.0.0",
            base_model_id="llama-3-70b",
            training_config={
                "method": "full_fine_tuning",
                "framework": "pytorch",
            },
            dataset_provenance=[
                DatasetReference(
                    dataset_id="custom_ds",
                    dataset_name="Custom Training Data",
                    version="1.0",
                )
            ],
            license_info={
                "type": "proprietary",
                "allows_commercial": True,
            },
        )
        assert payload.base_model_id == "llama-3-70b"
        assert payload.model_type == "fine_tune"


class TestTrainingProvenanceCapsule:
    """Test TrainingProvenanceCapsule creation."""

    def test_create_training_provenance_capsule(self):
        """Test creating a complete training provenance capsule."""
        capsule = TrainingProvenanceCapsule(
            capsule_id="caps_2026_03_02_abc123def456789a",
            version="7.2",
            timestamp=datetime.now(timezone.utc),
            status=CapsuleStatus.SEALED,
            verification=Verification(
                signature="ed25519:" + "0" * 128,
                merkle_root="sha256:" + "0" * 64,
            ),
            training_provenance=TrainingProvenancePayload(
                session_id="train_20260302_xyz",
                model_id="model_123",
                session_type="sft",
                dataset_refs=[
                    DatasetReference(
                        dataset_id="ds_123",
                        dataset_name="SFT Data",
                        version="1.0",
                    )
                ],
                started_at=datetime.now(timezone.utc),
                status="completed",
            ),
        )
        assert capsule.capsule_type == CapsuleType.TRAINING_PROVENANCE
        assert capsule.version == "7.2"


class TestModelRegistrationCapsule:
    """Test ModelRegistrationCapsule creation."""

    def test_create_model_registration_capsule(self):
        """Test creating a complete model registration capsule."""
        capsule = ModelRegistrationCapsule(
            capsule_id="caps_2026_03_02_def456abc123789b",
            version="7.2",
            timestamp=datetime.now(timezone.utc),
            status=CapsuleStatus.SEALED,
            verification=Verification(
                signature="ed25519:" + "0" * 128,
                merkle_root="sha256:" + "0" * 64,
            ),
            model_registration=ModelRegistrationPayload(
                model_id="new_model_456",
                model_hash="sha256:ghi789...",
                model_type="adapter",
                version="1.0.0",
                base_model_id="base_model_123",
            ),
        )
        assert capsule.capsule_type == CapsuleType.MODEL_REGISTRATION
        assert capsule.model_registration.model_type == "adapter"


class TestUATPEnvelope72:
    """Test UATP 7.2 envelope functionality."""

    def test_envelope_version_detection_71(self):
        """Test version detection for 7.1 envelope."""
        envelope = wrap_in_uatp_envelope(
            payload_data={"test": "data"},
            capsule_id="caps_test",
            capsule_type="reasoning_trace",
        )
        version = detect_capsule_version(envelope)
        assert version == "7.1"

    def test_envelope_version_detection_72_with_training_context(self):
        """Test version detection for 7.2 envelope with training_context."""
        training_ctx = create_training_context(
            model_id="model_001",
            session_id="train_001",
            training_type="fine_tuning",
        )
        envelope = wrap_in_uatp_envelope(
            payload_data={"test": "data"},
            capsule_id="caps_test",
            capsule_type="training_provenance",
            training_context=training_ctx,
        )
        version = detect_capsule_version(envelope)
        assert version == "7.2"
        assert "training_context" in envelope
        assert envelope["_envelope"]["version"] == "7.2"

    def test_create_training_context(self):
        """Test creating training context."""
        ctx = create_training_context(
            model_id="model_001",
            session_id="train_001",
            base_model_id="base_model_001",
            training_type="rlhf",
            dataset_refs=[
                {"dataset_id": "ds_001", "version": "1.0"}
            ],
            hyperparameters={"lr": 1e-5},
        )
        assert ctx["model_id"] == "model_001"
        assert ctx["base_model_id"] == "base_model_001"
        assert ctx["training_type"] == "rlhf"
        assert "timestamp" in ctx

    def test_envelope_backward_compatibility(self):
        """Test that 7.1 capsules remain valid in 7.2 system."""
        # Create a 7.1 envelope (no 7.2 features)
        envelope = wrap_in_uatp_envelope(
            payload_data={"reasoning": "test"},
            capsule_id="caps_legacy",
            capsule_type="reasoning_trace",
        )

        assert is_envelope_format(envelope)
        assert "attribution" in envelope
        assert "lineage" in envelope
        assert "chain_context" in envelope
        # No 7.2 features
        assert "training_context" not in envelope
        assert "workflow_context" not in envelope


class TestModelRegistryService:
    """Test ModelRegistryService capsule creation methods."""

    def test_create_model_registration_capsule(self):
        """Test service method for creating model registration capsule."""
        service = ModelRegistryService()
        capsule = service.create_model_registration_capsule(
            model_id="test_model",
            model_hash="sha256:abc123",
            model_type="base",
            version="1.0.0",
            name="Test Model",
            description="A test model",
            capabilities=["text_generation"],
        )

        assert capsule.capsule_type == CapsuleType.MODEL_REGISTRATION
        assert capsule.version == "7.2"
        assert capsule.model_registration.model_id == "test_model"
        assert capsule.model_registration.model_type == "base"

    def test_create_training_provenance_capsule(self):
        """Test service method for creating training provenance capsule."""
        service = ModelRegistryService()
        now = datetime.now(timezone.utc)
        capsule = service.create_training_provenance_capsule(
            session_id="train_test_001",
            model_id="test_model",
            session_type="fine_tuning",
            dataset_refs=[
                {
                    "dataset_id": "ds_001",
                    "dataset_name": "Test Dataset",
                    "version": "1.0",
                }
            ],
            started_at=now,
            completed_at=now,
            hyperparameters={"lr": 1e-4},
            metrics={"loss": 0.01},
            status="completed",
        )

        assert capsule.capsule_type == CapsuleType.TRAINING_PROVENANCE
        assert capsule.version == "7.2"
        assert capsule.training_provenance.session_type == "fine_tuning"
        assert len(capsule.training_provenance.dataset_refs) == 1


class TestVersionPatternValidation:
    """Test version string validation."""

    def test_valid_version_70(self):
        """Test version 7.0 is valid."""
        capsule = ModelRegistrationCapsule(
            capsule_id="caps_2026_03_02_a1b2c3d4e5f6a7b8",
            version="7.0",
            timestamp=datetime.now(timezone.utc),
            status=CapsuleStatus.DRAFT,
            verification=Verification(),
            model_registration=ModelRegistrationPayload(
                model_id="test",
                model_hash="abc",
                model_type="base",
                version="1.0",
            ),
        )
        assert capsule.version == "7.0"

    def test_valid_version_71(self):
        """Test version 7.1 is valid."""
        capsule = ModelRegistrationCapsule(
            capsule_id="caps_2026_03_02_b1c2d3e4f5a6b7c8",
            version="7.1",
            timestamp=datetime.now(timezone.utc),
            status=CapsuleStatus.DRAFT,
            verification=Verification(),
            model_registration=ModelRegistrationPayload(
                model_id="test",
                model_hash="abc",
                model_type="base",
                version="1.0",
            ),
        )
        assert capsule.version == "7.1"

    def test_valid_version_72(self):
        """Test version 7.2 is valid."""
        capsule = ModelRegistrationCapsule(
            capsule_id="caps_2026_03_02_c1d2e3f4a5b6c7d8",
            version="7.2",
            timestamp=datetime.now(timezone.utc),
            status=CapsuleStatus.DRAFT,
            verification=Verification(),
            model_registration=ModelRegistrationPayload(
                model_id="test",
                model_hash="abc",
                model_type="base",
                version="1.0",
            ),
        )
        assert capsule.version == "7.2"

    def test_valid_version_73(self):
        """Test version 7.3 is valid (UATP 7.3 ANE Training Provenance)."""
        capsule = ModelRegistrationCapsule(
            capsule_id="caps_2026_03_02_d1e2f3a4b5c6d7e8",
            version="7.3",
            timestamp=datetime.now(timezone.utc),
            status=CapsuleStatus.DRAFT,
            verification=Verification(),
            model_registration=ModelRegistrationPayload(
                model_id="test",
                model_hash="abc",
                model_type="base",
                version="1.0",
            ),
        )
        assert capsule.version == "7.3"

    def test_invalid_version_75(self):
        """Test version 7.5 is invalid (not yet supported)."""
        with pytest.raises(ValidationError):
            ModelRegistrationCapsule(
                capsule_id="caps_2026_03_02_d1e2f3a4b5c6d7e8",
                version="7.5",
                timestamp=datetime.now(timezone.utc),
                status=CapsuleStatus.DRAFT,
                verification=Verification(),
                model_registration=ModelRegistrationPayload(
                    model_id="test",
                    model_hash="abc",
                    model_type="base",
                    version="1.0",
                ),
            )
