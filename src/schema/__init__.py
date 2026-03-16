"""
UATP Schema - OpenLineage-inspired facet pattern for machine-legible capsules.

This module provides:
- Base facet classes (RunFacet, JobFacet, DatasetFacet)
- Core UATP facets (Signature, Verification, Capsule, Capture, Confidence)
- Entity model (Run, Job, Dataset)
- LineageEvent for complete capsule events

Usage:
    from src.schema import (
        UATPSignatureRunFacet,
        UATPCapsuleDatasetFacet,
        create_capsule_event,
    )

    # Create facets
    sig = UATPSignatureRunFacet(
        algorithm="ed25519",
        signature="abc123...",
        content_hash="sha256:..."
    )

    capsule = UATPCapsuleDatasetFacet(
        capsule_id="caps_123",
        capsule_type="reasoning_trace"
    )

    # Create event
    event = create_capsule_event(
        capsule_id="caps_123",
        capsule_type="reasoning_trace",
        run_facets={"uatp_signature": sig},
        output_facets={"uatp_capsule": capsule}
    )

    # Serialize
    event_dict = event.to_dict()
"""

# Base classes
from src.schema.base import (
    UATP_FACET_VERSION,
    UATP_PRODUCER,
    UATP_SCHEMA_BASE,
    BaseFacet,
    DatasetFacet,
    FacetEntityType,
    FacetRegistry,
    JobFacet,
    RunFacet,
    facets_to_dict,
    utc_now,
)

# Entity model
from src.schema.entities import (
    Dataset,
    Job,
    LineageEvent,
    Run,
    create_capsule_event,
)

# Core facets
from src.schema.facets import (
    UATPCapsuleDatasetFacet,
    UATPCaptureJobFacet,
    UATPConfidenceRunFacet,
    UATPSignatureRunFacet,
    UATPVerificationRunFacet,
)

__all__ = [
    # Base
    "BaseFacet",
    "RunFacet",
    "JobFacet",
    "DatasetFacet",
    "UATP_PRODUCER",
    "UATP_SCHEMA_BASE",
    "UATP_FACET_VERSION",
    "FacetEntityType",
    "FacetRegistry",
    "facets_to_dict",
    "utc_now",
    # Facets
    "UATPSignatureRunFacet",
    "UATPVerificationRunFacet",
    "UATPCapsuleDatasetFacet",
    "UATPCaptureJobFacet",
    "UATPConfidenceRunFacet",
    # Entities
    "Run",
    "Job",
    "Dataset",
    "LineageEvent",
    "create_capsule_event",
]
