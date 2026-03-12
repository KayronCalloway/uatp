"""
Unit tests for UATP Schema facets.
"""

import json
from datetime import datetime, timezone

import pytest

from src.schema import (
    UATP_PRODUCER,
    BaseFacet,
    Dataset,
    FacetEntityType,
    FacetRegistry,
    Job,
    LineageEvent,
    Run,
    UATPCapsuleDatasetFacet,
    UATPCaptureJobFacet,
    UATPConfidenceRunFacet,
    UATPSignatureRunFacet,
    UATPVerificationRunFacet,
    create_capsule_event,
)


class TestFacetKeys:
    """Test facet key generation."""

    def test_signature_facet_key(self):
        assert UATPSignatureRunFacet.facet_key() == "uatp_signature"

    def test_verification_facet_key(self):
        assert UATPVerificationRunFacet.facet_key() == "uatp_verification"

    def test_capsule_facet_key(self):
        assert UATPCapsuleDatasetFacet.facet_key() == "uatp_capsule"

    def test_capture_facet_key(self):
        assert UATPCaptureJobFacet.facet_key() == "uatp_capture"

    def test_confidence_facet_key(self):
        assert UATPConfidenceRunFacet.facet_key() == "uatp_confidence"


class TestSignatureFacet:
    """Tests for UATPSignatureRunFacet."""

    def test_default_values(self):
        facet = UATPSignatureRunFacet()
        assert facet.algorithm == "ed25519"
        assert facet._producer == UATP_PRODUCER
        assert "UATPSignatureRunFacet" in facet._schemaURL

    def test_to_dict(self):
        facet = UATPSignatureRunFacet(
            algorithm="ed25519",
            signature="abc123",
            content_hash="sha256:def456",
        )
        d = facet.to_dict()

        assert d["_producer"] == UATP_PRODUCER
        assert d["algorithm"] == "ed25519"
        assert d["signature"] == "abc123"
        assert d["content_hash"] == "sha256:def456"

    def test_is_hybrid(self):
        facet = UATPSignatureRunFacet(
            signature="abc",
            pq_algorithm="ml-dsa-65",
            pq_signature="xyz",
        )
        assert facet.is_hybrid() == True

        facet_simple = UATPSignatureRunFacet(signature="abc")
        assert facet_simple.is_hybrid() == False

    def test_has_trusted_timestamp(self):
        facet = UATPSignatureRunFacet(
            signature="abc",
            timestamp_token="base64token",
        )
        assert facet.has_trusted_timestamp() == True

        facet_no_ts = UATPSignatureRunFacet(signature="abc")
        assert facet_no_ts.has_trusted_timestamp() == False


class TestVerificationFacet:
    """Tests for UATPVerificationRunFacet."""

    def test_verification_status(self):
        facet = UATPVerificationRunFacet(is_verified=True)
        assert facet.is_fully_verified() == True

        facet.add_error("Signature mismatch")
        assert facet.is_verified == False
        assert facet.is_fully_verified() == False

    def test_add_warning(self):
        facet = UATPVerificationRunFacet(is_verified=True)
        facet.add_warning("Timestamp near expiry")
        assert facet.is_verified == True  # Warning doesn't fail verification
        assert "Timestamp near expiry" in facet.warnings


class TestCapsuleFacet:
    """Tests for UATPCapsuleDatasetFacet."""

    def test_compression_ratio(self):
        facet = UATPCapsuleDatasetFacet(
            is_compressed=True,
            original_size=10000,
            compressed_size=1000,
        )
        assert facet.compression_ratio() == 0.1

    def test_compression_ratio_not_compressed(self):
        facet = UATPCapsuleDatasetFacet(is_compressed=False)
        assert facet.compression_ratio() is None


class TestConfidenceFacet:
    """Tests for UATPConfidenceRunFacet."""

    def test_high_confidence(self):
        facet = UATPConfidenceRunFacet(confidence=0.9)
        assert facet.is_high_confidence() == True
        assert facet.is_high_confidence(threshold=0.95) == False

    def test_calibration_significant(self):
        facet = UATPConfidenceRunFacet(calibration_adjustment=0.1)
        assert facet.is_calibration_significant() == True

        facet_minor = UATPConfidenceRunFacet(calibration_adjustment=0.02)
        assert facet_minor.is_calibration_significant() == False


class TestEntities:
    """Tests for Run, Job, Dataset entities."""

    def test_run_entity(self):
        run = Run(run_id="test-123")
        sig = UATPSignatureRunFacet(signature="abc")
        run.add_facet(sig)

        d = run.to_dict()
        assert d["runId"] == "test-123"
        assert "uatp_signature" in d["facets"]

    def test_job_entity(self):
        job = Job(namespace="uatp://capture-types", name="claude_code")
        capture = UATPCaptureJobFacet(capture_type="claude_code")
        job.add_facet(capture)

        d = job.to_dict()
        assert d["namespace"] == "uatp://capture-types"
        assert d["name"] == "claude_code"
        assert "uatp_capture" in d["facets"]

    def test_dataset_entity(self):
        ds = Dataset(namespace="uatp://capsules", name="caps_123")
        capsule = UATPCapsuleDatasetFacet(capsule_id="caps_123")
        ds.add_facet(capsule)

        d = ds.to_dict()
        assert d["namespace"] == "uatp://capsules"
        assert d["name"] == "caps_123"
        assert "uatp_capsule" in d["facets"]


class TestLineageEvent:
    """Tests for LineageEvent creation."""

    def test_create_capsule_event(self):
        sig = UATPSignatureRunFacet(signature="test")
        capsule = UATPCapsuleDatasetFacet(capsule_id="caps_123")

        event = create_capsule_event(
            capsule_id="caps_123",
            capsule_type="reasoning_trace",
            run_facets={"sig": sig},
            output_facets={"capsule": capsule},
        )

        d = event.to_dict()

        assert d["eventType"] == "COMPLETE"
        assert d["producer"] == UATP_PRODUCER
        assert d["run"]["runId"] == "caps_123"
        assert d["job"]["namespace"] == "uatp://capture-types"
        assert d["job"]["name"] == "reasoning_trace"
        assert len(d["outputs"]) == 1
        assert d["outputs"][0]["name"] == "caps_123"

    def test_event_serializable(self):
        event = create_capsule_event(
            capsule_id="test",
            capsule_type="test_type",
        )

        # Should be JSON serializable
        json_str = json.dumps(event.to_dict(), default=str)
        assert "test" in json_str


class TestFacetRegistry:
    """Tests for FacetRegistry."""

    def test_register_and_get_facet(self):
        # Clear registry first
        FacetRegistry.clear()

        # Register a facet
        FacetRegistry.register(
            UATPSignatureRunFacet,
            entity_type=FacetEntityType.RUN,
            description="Test signature facet",
            tags=["security"],
        )

        # Get it back
        facet_class = FacetRegistry.get_facet("uatp_signature")
        assert facet_class == UATPSignatureRunFacet

    def test_get_metadata(self):
        FacetRegistry.clear()
        FacetRegistry.register(
            UATPCapsuleDatasetFacet,
            entity_type=FacetEntityType.DATASET,
            description="Capsule metadata",
            tags=["data", "capsule"],
        )

        meta = FacetRegistry.get_metadata("uatp_capsule")
        assert meta is not None
        assert meta["description"] == "Capsule metadata"
        assert "data" in meta["tags"]
        assert meta["entity_type"] == "dataset"

    def test_list_facets_by_entity_type(self):
        FacetRegistry.clear()
        FacetRegistry.register(UATPSignatureRunFacet, FacetEntityType.RUN)
        FacetRegistry.register(UATPVerificationRunFacet, FacetEntityType.RUN)
        FacetRegistry.register(UATPCapsuleDatasetFacet, FacetEntityType.DATASET)

        run_facets = FacetRegistry.list_facets(entity_type=FacetEntityType.RUN)
        assert len(run_facets) == 2

        dataset_facets = FacetRegistry.list_facets(entity_type=FacetEntityType.DATASET)
        assert len(dataset_facets) == 1

    def test_list_facets_by_tag(self):
        FacetRegistry.clear()
        FacetRegistry.register(
            UATPSignatureRunFacet, FacetEntityType.RUN, tags=["security", "crypto"]
        )
        FacetRegistry.register(
            UATPConfidenceRunFacet, FacetEntityType.RUN, tags=["quality"]
        )

        security_facets = FacetRegistry.list_facets(tag="security")
        assert len(security_facets) == 1
        assert security_facets[0]["class_name"] == "UATPSignatureRunFacet"

    def test_list_keys(self):
        FacetRegistry.clear()
        FacetRegistry.register(UATPSignatureRunFacet, FacetEntityType.RUN)
        FacetRegistry.register(UATPCapsuleDatasetFacet, FacetEntityType.DATASET)

        keys = FacetRegistry.list_keys()
        assert "uatp_signature" in keys
        assert "uatp_capsule" in keys

    def test_get_nonexistent_facet(self):
        FacetRegistry.clear()
        assert FacetRegistry.get_facet("nonexistent") is None
        assert FacetRegistry.get_metadata("nonexistent") is None


class TestFacetDeletion:
    """Tests for facet deletion tracking."""

    def test_delete_facet(self):
        facet = UATPSignatureRunFacet(signature="test")
        assert facet._deleted == False

        facet.delete(reason="Superseded by new signature")

        assert facet._deleted == True
        assert facet._deleted_at is not None
        assert facet._deletion_reason == "Superseded by new signature"

    def test_deleted_facet_to_dict(self):
        facet = UATPSignatureRunFacet(signature="test")
        facet.delete(reason="Test deletion")

        d = facet.to_dict()
        assert d["_deleted"] == True
        assert "_deletedAt" in d
        assert d["_deletionReason"] == "Test deletion"
