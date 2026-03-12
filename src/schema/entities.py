"""
UATP Entity Model - OpenLineage-inspired entities.

Entities:
- Run: Capsule execution instance (the actual capture)
- Job: Capture type definition (what kind of capture)
- Dataset: Input/output data (source and result)
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional

from src.schema.base import (
    BaseFacet,
    DatasetFacet,
    JobFacet,
    RunFacet,
    facets_to_dict,
    utc_now,
)


@dataclass
class Run:
    """
    A capsule execution instance.

    Represents a single capture event - the actual creation of a capsule.
    """

    run_id: str  # UUID
    facets: Dict[str, RunFacet] = field(default_factory=dict)

    def add_facet(self, facet: RunFacet) -> None:
        """Add a facet using its standard key."""
        key = facet.facet_key()
        self.facets[key] = facet

    def to_dict(self) -> Dict[str, Any]:
        return {
            "runId": self.run_id,
            "facets": facets_to_dict(self.facets),
        }


@dataclass
class Job:
    """
    A capture type definition.

    Represents the methodology/process for capturing - reusable across runs.
    """

    namespace: str  # e.g., "uatp://capture-types"
    name: str  # e.g., "claude_code"
    facets: Dict[str, JobFacet] = field(default_factory=dict)

    def add_facet(self, facet: JobFacet) -> None:
        """Add a facet using its standard key."""
        key = facet.facet_key()
        self.facets[key] = facet

    def to_dict(self) -> Dict[str, Any]:
        return {
            "namespace": self.namespace,
            "name": self.name,
            "facets": facets_to_dict(self.facets),
        }


@dataclass
class Dataset:
    """
    Input or output data.

    For UATP:
    - Input: Source of captured data (GitHub repo, file, conversation)
    - Output: The capsule itself
    """

    namespace: str  # e.g., "uatp://capsules"
    name: str  # e.g., "caps_2026_03_11_..."
    facets: Dict[str, DatasetFacet] = field(default_factory=dict)

    def add_facet(self, facet: DatasetFacet) -> None:
        """Add a facet using its standard key."""
        key = facet.facet_key()
        self.facets[key] = facet

    def to_dict(self) -> Dict[str, Any]:
        return {
            "namespace": self.namespace,
            "name": self.name,
            "facets": facets_to_dict(self.facets),
        }


@dataclass
class LineageEvent:
    """
    A complete OpenLineage-style event.

    Captures the full context of a capsule creation.
    """

    # Event metadata
    event_type: str  # START, RUNNING, COMPLETE, FAIL, ABORT
    event_time: datetime = field(default_factory=utc_now)
    producer: str = "urn:uatp-capsule-engine:1.0"
    schema_url: str = "https://uatp.dev/spec/LineageEvent.json"

    # Core entities
    run: Optional[Run] = None
    job: Optional[Job] = None
    inputs: List[Dataset] = field(default_factory=list)
    outputs: List[Dataset] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        result = {
            "eventType": self.event_type,
            "eventTime": self.event_time.isoformat(),
            "producer": self.producer,
            "schemaURL": self.schema_url,
        }

        if self.run:
            result["run"] = self.run.to_dict()
        if self.job:
            result["job"] = self.job.to_dict()
        if self.inputs:
            result["inputs"] = [d.to_dict() for d in self.inputs]
        if self.outputs:
            result["outputs"] = [d.to_dict() for d in self.outputs]

        return result


# --- Factory functions ---


def create_capsule_event(
    capsule_id: str,
    capsule_type: str,
    event_type: str = "COMPLETE",
    run_facets: Optional[Dict[str, RunFacet]] = None,
    job_facets: Optional[Dict[str, JobFacet]] = None,
    output_facets: Optional[Dict[str, DatasetFacet]] = None,
) -> LineageEvent:
    """
    Create a LineageEvent for a capsule capture.

    This is the primary factory for creating structured capsule events.
    """
    # Create Run (the capture instance)
    run = Run(run_id=capsule_id)
    if run_facets:
        run.facets = {f.facet_key(): f for f in run_facets.values()}

    # Create Job (the capture type)
    job = Job(namespace="uatp://capture-types", name=capsule_type)
    if job_facets:
        job.facets = {f.facet_key(): f for f in job_facets.values()}

    # Create Output Dataset (the capsule itself)
    output = Dataset(namespace="uatp://capsules", name=capsule_id)
    if output_facets:
        output.facets = {f.facet_key(): f for f in output_facets.values()}

    return LineageEvent(
        event_type=event_type,
        run=run,
        job=job,
        outputs=[output],
    )
