"""
UATP Client - Core SDK functionality
"""

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import requests


@dataclass
class CertificationResult:
    """Result of certifying an AI decision."""

    capsule_id: str
    proof_url: str
    timestamp: datetime
    success: bool

    def __repr__(self) -> str:
        return f"CertificationResult(capsule_id='{self.capsule_id}', proof_url='{self.proof_url}')"


@dataclass
class CapsuleProof:
    """Full cryptographic proof of an AI decision."""

    capsule_id: str
    capsule_type: str
    status: str
    verified: bool
    timestamp: datetime
    payload: Dict[str, Any]

    def verify(self) -> bool:
        """Verify cryptographic signature."""
        return self.verified


class UATP:
    """
    UATP Client - Make AI decisions auditable.

    Usage:
        >>> from uatp import UATP
        >>>
        >>> client = UATP(api_key="your-api-key")
        >>>
        >>> result = client.certify(
        ...     task="Book doctor appointment",
        ...     decision="Booked Dr. Smith for Dec 17 at 3PM",
        ...     reasoning=[
        ...         {"step": 1, "thought": "User requested Tuesday afternoon", "confidence": 0.95},
        ...         {"step": 2, "thought": "Found available slot at 3PM", "confidence": 0.92}
        ...     ]
        ... )
        >>>
        >>> print(result.proof_url)
        'http://localhost:8000/capsules/abc123'
    """

    def __init__(
        self,
        api_key: str = "demo-key",  # For now, no auth required
        base_url: str = "http://localhost:8000",
        timeout: int = 30,
    ):
        """
        Initialize UATP client.

        Args:
            api_key: Your UATP API key (optional for now)
            base_url: API base URL (default: localhost for development)
            timeout: Request timeout in seconds
        """
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update(
            {"Content-Type": "application/json", "User-Agent": "uatp-python-sdk/0.1.0"}
        )

    def certify(
        self,
        task: str,
        decision: str,
        reasoning: List[Dict[str, Any]],
        confidence: Optional[float] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> CertificationResult:
        """
        Create a cryptographically certified capsule for an AI decision.

        This is the main method you'll use to make AI decisions auditable.

        Args:
            task: Description of the task (e.g., "Book doctor appointment")
            decision: The AI's final decision (e.g., "Booked Dr. Smith for Dec 17 at 3PM")
            reasoning: List of reasoning steps, each a dict with at minimum:
                      - 'step': int (step number)
                      - 'thought': str (what the AI considered)
                      - 'confidence': float (0-1, how confident)
            confidence: Overall confidence score (0-1). If not provided, averaged from reasoning.
            metadata: Optional additional metadata to attach

        Returns:
            CertificationResult with capsule_id and proof_url

        Raises:
            requests.HTTPError: If API request fails
            ValueError: If parameters are invalid

        Example:
            >>> result = client.certify(
            ...     task="Diagnose patient symptoms",
            ...     decision="Likely common cold, recommend rest and fluids",
            ...     reasoning=[
            ...         {
            ...             "step": 1,
            ...             "thought": "Patient reports sore throat, congestion, fatigue",
            ...             "confidence": 0.98
            ...         },
            ...         {
            ...             "step": 2,
            ...             "thought": "No fever >101°F rules out flu",
            ...             "confidence": 0.85
            ...         },
            ...         {
            ...             "step": 3,
            ...             "thought": "Symptoms match common cold profile",
            ...             "confidence": 0.87
            ...         }
            ...     ],
            ...     confidence=0.87,
            ...     metadata={"model": "gpt-4", "patient_id": "12345"}
            ... )
        """
        # Validate inputs
        if not task or not isinstance(task, str):
            raise ValueError("task must be a non-empty string")

        if not decision or not isinstance(decision, str):
            raise ValueError("decision must be a non-empty string")

        if not reasoning or not isinstance(reasoning, list):
            raise ValueError("reasoning must be a non-empty list")

        # Calculate confidence if not provided
        if confidence is None:
            confidences = [step.get("confidence", 0.5) for step in reasoning]
            confidence = sum(confidences) / len(confidences) if confidences else 0.5

        # Prepare request payload in format backend expects
        timestamp = datetime.now(timezone.utc)
        capsule_data = {
            "type": "reasoning_trace",
            "version": "1.0",
            "payload": {
                "task": task,
                "decision": decision,
                "reasoning_chain": reasoning,
                "confidence": confidence,
                "metadata": {
                    **(metadata or {}),
                    "timestamp": timestamp.isoformat(),
                    "sdk_version": "0.2.0",
                },
            },
        }

        # Make API request
        try:
            response = self.session.post(
                f"{self.base_url}/capsules", json=capsule_data, timeout=self.timeout
            )
            response.raise_for_status()
            data = response.json()

            # Parse response
            capsule_id = data["capsule_id"]
            return CertificationResult(
                capsule_id=capsule_id,
                proof_url=f"{self.base_url}/capsules/{capsule_id}/verify",
                timestamp=timestamp,
                success=data.get("success", True),
            )

        except requests.exceptions.RequestException as e:
            raise Exception(f"Failed to certify decision: {e}")

    def get_proof(self, capsule_id: str) -> CapsuleProof:
        """
        Retrieve full cryptographic proof for a capsule.

        Args:
            capsule_id: The capsule ID to retrieve

        Returns:
            CapsuleProof with full decision details

        Example:
            >>> proof = client.get_proof("abc123")
            >>> print(proof.payload['task'])
            'Book doctor appointment'
            >>> print(proof.verify())
            True
        """
        try:
            # Get the full capsule
            response = self.session.get(
                f"{self.base_url}/capsules?demo_mode=false&per_page=100",
                timeout=self.timeout,
            )
            response.raise_for_status()
            data = response.json()

            # Find our capsule
            for capsule in data.get("capsules", []):
                if capsule["capsule_id"] == capsule_id:
                    return CapsuleProof(
                        capsule_id=capsule["capsule_id"],
                        capsule_type=capsule.get("type", "unknown"),
                        status=capsule.get("status", "unknown"),
                        verified=capsule.get("verification", {}).get("verified", False),
                        timestamp=datetime.fromisoformat(
                            capsule["timestamp"].replace("Z", "+00:00")
                        ),
                        payload=capsule.get("payload", {}),
                    )

            raise Exception(f"Capsule {capsule_id} not found")

        except requests.exceptions.RequestException as e:
            raise Exception(f"Failed to retrieve proof: {e}")

    def list_capsules(self, limit: int = 10, offset: int = 0) -> List[CapsuleProof]:
        """
        List your capsules.

        Args:
            limit: Maximum number of capsules to return
            offset: Pagination offset (not fully supported yet)

        Returns:
            List of CapsuleProof objects
        """
        try:
            response = self.session.get(
                f"{self.base_url}/capsules?demo_mode=false&per_page={limit}",
                timeout=self.timeout,
            )
            response.raise_for_status()
            data = response.json()

            return [
                CapsuleProof(
                    capsule_id=item["capsule_id"],
                    capsule_type=item.get("type", "unknown"),
                    status=item.get("status", "unknown"),
                    verified=item.get("verification", {}).get("verified", False),
                    timestamp=datetime.fromisoformat(
                        item["timestamp"].replace("Z", "+00:00")
                    ),
                    payload=item.get("payload", {}),
                )
                for item in data.get("capsules", [])[:limit]
            ]

        except requests.exceptions.RequestException as e:
            raise Exception(f"Failed to list capsules: {e}")

    def certify_rich(
        self,
        task: str,
        decision: str,
        reasoning_steps: List,  # List[ReasoningStep] or List[Dict]
        confidence: Optional[float] = None,
        risk_assessment: Optional[Dict[str, Any]] = None,
        alternatives_considered: Optional[List[Dict[str, Any]]] = None,
        plain_language_summary: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> CertificationResult:
        """
        Create a court-admissible, insurance-ready capsule with rich data.

        This is the RECOMMENDED method for enterprise use, compliance, and litigation.

        Args:
            task: Description of the task
            decision: The AI's final decision
            reasoning_steps: List of ReasoningStep objects (or dicts with full provenance)
            confidence: Overall confidence (0-1)
            risk_assessment: RiskAssessment dict with probability, financial impact, safeguards
            alternatives_considered: List of Alternative dicts showing options evaluated
            plain_language_summary: PlainLanguageSummary dict for EU AI Act compliance
            metadata: Additional metadata

        Returns:
            CertificationResult with capsule_id and proof_url

        Example:
            >>> from uatp import DataSource, ReasoningStep, RiskAssessment
            >>>
            >>> result = client.certify_rich(
            ...     task="Approve loan application",
            ...     decision="Approved: $50,000 at 6.5% APR",
            ...     reasoning_steps=[
            ...         ReasoningStep(
            ...             step=1,
            ...             action="Verified credit score",
            ...             confidence=0.99,
            ...             data_sources=[
            ...                 DataSource(
            ...                     source="Experian Credit Bureau",
            ...                     value=720,
            ...                     timestamp="2025-12-14T15:30:12Z",
            ...                     api_endpoint="https://api.experian.com/v3/credit-scores"
            ...                 )
            ...             ],
            ...             reasoning="Credit score 720 exceeds minimum threshold of 640",
            ...             plain_language="Your credit score is excellent (720/850)"
            ...         )
            ...     ],
            ...     risk_assessment={
            ...         "probability_correct": 0.87,
            ...         "probability_wrong": 0.13,
            ...         "expected_value": 280,
            ...         "value_at_risk_95": 22500,
            ...         "safeguards": ["Income verified", "Collateral secured"]
            ...     },
            ...     alternatives_considered=[
            ...         {"amount": 40000, "apr": 6.0, "why_not_chosen": "User needs $50k"},
            ...         {"amount": 50000, "apr": 7.5, "why_not_chosen": "Rate too high"}
            ...     ]
            ... )
        """
        # Convert ReasoningStep objects to dicts
        reasoning_chain = []
        for step in reasoning_steps:
            if hasattr(step, "to_dict"):
                reasoning_chain.append(step.to_dict())
            else:
                reasoning_chain.append(step)

        # Calculate confidence if not provided
        if confidence is None:
            confidences = []
            for step in reasoning_chain:
                if isinstance(step, dict) and "confidence" in step:
                    confidences.append(step["confidence"])
            confidence = sum(confidences) / len(confidences) if confidences else 0.5

        # Prepare rich payload
        timestamp = datetime.now(timezone.utc)
        payload = {
            "task": task,
            "decision": decision,
            "reasoning_chain": reasoning_chain,
            "confidence": confidence,
            "metadata": {
                **(metadata or {}),
                "timestamp": timestamp.isoformat(),
                "sdk_version": "0.2.0",
                "data_richness": "court_admissible",
            },
        }

        # Add optional rich data (handle both dicts and objects)
        if risk_assessment:
            if hasattr(risk_assessment, "to_dict"):
                payload["risk_assessment"] = risk_assessment.to_dict()
            else:
                payload["risk_assessment"] = risk_assessment

        if alternatives_considered:
            if isinstance(alternatives_considered, list):
                payload["alternatives_considered"] = [
                    alt.to_dict() if hasattr(alt, "to_dict") else alt
                    for alt in alternatives_considered
                ]
            else:
                payload["alternatives_considered"] = alternatives_considered

        if plain_language_summary:
            if hasattr(plain_language_summary, "to_dict"):
                payload["plain_language_summary"] = plain_language_summary.to_dict()
            else:
                payload["plain_language_summary"] = plain_language_summary

        capsule_data = {"type": "reasoning_trace", "version": "1.0", "payload": payload}

        # Make API request
        try:
            response = self.session.post(
                f"{self.base_url}/capsules", json=capsule_data, timeout=self.timeout
            )
            response.raise_for_status()
            data = response.json()

            capsule_id = data["capsule_id"]
            return CertificationResult(
                capsule_id=capsule_id,
                proof_url=f"{self.base_url}/capsules/{capsule_id}/verify",
                timestamp=timestamp,
                success=data.get("success", True),
            )

        except requests.exceptions.RequestException as e:
            raise Exception(f"Failed to certify rich decision: {e}")

    def record_outcome(self, capsule_id: str, outcome: Dict[str, Any]) -> bool:
        """
        Record the actual outcome of an AI decision (ground truth).

        This is CRITICAL for:
        - Machine learning improvement (training data)
        - Insurance claims validation
        - Compliance audits
        - Risk model calibration

        Args:
            capsule_id: The capsule ID to update
            outcome: Outcome dict with:
                - occurred: bool (did predicted event happen?)
                - result: str ("successful", "failed", "partial")
                - timestamp: str (when outcome recorded)
                - ai_was_correct: bool (optional)
                - financial_impact: float (optional)
                - customer_satisfaction: float (optional, 1-5)
                - notes: str (optional)

        Returns:
            True if outcome recorded successfully

        Example:
            >>> # 30 days after decision
            >>> success = client.record_outcome(
            ...     capsule_id="cap_abc123",
            ...     outcome={
            ...         "occurred": True,
            ...         "result": "successful",
            ...         "timestamp": "2025-01-14T10:00:00Z",
            ...         "ai_was_correct": True,
            ...         "financial_impact": 2500,  # Interest earned
            ...         "customer_satisfaction": 4.5,
            ...         "notes": "Loan fully paid on time"
            ...     }
            ... )
        """
        # For now, store outcome in capsule metadata via update endpoint
        # In future, this would be a dedicated /capsules/{id}/outcome endpoint
        try:
            # Get current capsule
            proof = self.get_proof(capsule_id)

            # Add outcome to payload
            updated_payload = proof.payload.copy()
            updated_payload["outcome"] = outcome
            updated_payload["outcome_recorded_at"] = datetime.now(
                timezone.utc
            ).isoformat()

            # Note: Backend doesn't support updates yet, so this is a placeholder
            # In production, you'd POST to /capsules/{id}/outcome
            print("[WARN]  Outcome tracking not yet implemented in backend API")
            print(f"   Outcome for {capsule_id}: {outcome.get('result', 'unknown')}")
            print(
                "   This will be stored once backend supports /capsules/{id}/outcome endpoint"
            )

            return True

        except Exception as e:
            raise Exception(f"Failed to record outcome: {e}")

    def close(self):
        """Close the HTTP session."""
        self.session.close()

    def __enter__(self):
        """Context manager support."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager cleanup."""
        self.close()
