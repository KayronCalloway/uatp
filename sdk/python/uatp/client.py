"""
UATP Client - Core SDK functionality

Zero-Trust Architecture:
- Private keys NEVER leave your device
- All signing happens locally using Ed25519
- Only content hash sent to server for RFC 3161 timestamping
- Capsules can be verified independently without UATP
"""

import hashlib
import logging
import os
import platform
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Union

import requests

from .crypto import LocalSigner, SignedCapsule, verify_capsule_standalone

logger = logging.getLogger(__name__)


def _derive_device_passphrase() -> str:
    """
    Derive a device-bound passphrase from machine-specific info.

    SECURITY BOUNDARY: This is a CONVENIENCE feature, not a security feature.

    What it provides:
    - Zero-friction onboarding (no passphrase to remember)
    - Deterministic per-machine keys
    - Keys still never leave the device

    What it does NOT provide:
    - High entropy (inputs are hostname/username/arch - often guessable)
    - Protection against local attackers who know the machine
    - Portability (keys tied to specific machine)

    For production/sensitive use: Pass an explicit passphrase with device_bound=False.
    """
    # Gather machine-specific info
    machine_info = [
        platform.node(),  # Hostname
        os.getenv("USER", os.getenv("USERNAME", "")),  # Username
        platform.machine(),  # CPU architecture
        str(os.path.expanduser("~")),  # Home directory path
    ]

    # Hash to create deterministic passphrase
    combined = ":".join(machine_info)
    device_hash = hashlib.sha256(combined.encode()).hexdigest()

    # Use first 32 chars as passphrase
    # NOTE: Entropy is LIMITED by uniqueness of hostname/username/arch, NOT 128 bits.
    # This is a convenience fallback, not high-security. Use explicit passphrase for production.
    return f"device_{device_hash[:32]}"


@dataclass
class CapsuleProof:
    """Full cryptographic proof of an AI decision."""

    capsule_id: str
    capsule_type: str
    status: str
    timestamp: datetime
    payload: Dict[str, Any]
    _raw_data: Dict[str, Any]  # Full capsule data for verification

    def verify(self) -> bool:
        """
        Verify cryptographic signature by recomputing.

        This actually checks the signature - not just a cached value.
        If anyone tampers with the capsule, this will return False.

        Returns:
            True if signature is valid, False otherwise.
        """
        result = verify_capsule_standalone(self._raw_data)
        return bool(result.get("valid", False))

    def verify_detailed(self) -> Dict[str, Any]:
        """
        Verify with detailed results.

        Returns:
            Dict with 'valid', 'signature_valid', 'hash_valid', 'errors', etc.
        """
        return verify_capsule_standalone(self._raw_data)


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
        >>> print(result.capsule_id)
        'cap_abc123'
        >>> print(result.signature[:32])
        'a1b2c3d4...'
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: str = "http://localhost:8000",
        timeout: int = 30,
    ):
        """
        Initialize UATP client.

        Args:
            api_key: Your UATP API key. None for local-only mode.
            base_url: API base URL (default: localhost for development)
            timeout: Request timeout in seconds

        Note:
            For production, always provide an explicit api_key and base_url.
            The defaults are for local development only.
        """
        if base_url == "http://localhost:8000":
            logger.warning("UATP client using localhost - set base_url for production")

        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.session = requests.Session()
        headers = {
            "Content-Type": "application/json",
            "User-Agent": "uatp-python-sdk/0.3.0",
        }
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        self.session.headers.update(headers)

    def certify(
        self,
        task: str,
        decision: str,
        reasoning: List[Dict[str, Any]],
        passphrase: Optional[str] = None,
        device_bound: bool = True,
        key_dir: str = "~/.uatp/keys",
        confidence: Optional[float] = None,
        metadata: Optional[Dict[str, Any]] = None,
        request_timestamp: bool = True,
        store_on_server: bool = False,
    ) -> SignedCapsule:
        """
        Create a cryptographically certified capsule for an AI decision.

        ZERO-TRUST: Private key NEVER leaves your device.
        - All signing happens locally using Ed25519
        - Only the content hash is sent to UATP for timestamping
        - Capsules can be verified independently without UATP

        Args:
            task: Description of the task (e.g., "Book doctor appointment")
            decision: The AI's final decision (e.g., "Booked Dr. Smith for Dec 17 at 3PM")
            reasoning: List of reasoning steps, each a dict with at minimum:
                      - 'step': int (step number)
                      - 'thought': str (what the AI considered)
                      - 'confidence': float (0-1, how confident)
            passphrase: Your signing key passphrase. If not provided and device_bound=True,
                       a machine-specific passphrase is derived automatically.
            device_bound: If True (default), derive passphrase from machine info.
                         Set to False if you provide your own passphrase.
            key_dir: Directory for key storage (default: ~/.uatp/keys)
            confidence: Overall confidence score (0-1). Auto-calculated if not provided.
            metadata: Optional additional metadata to attach
            request_timestamp: If True, request RFC 3161 timestamp from external TSA
            store_on_server: If True, store capsule on UATP server for retrieval

        Returns:
            SignedCapsule with cryptographic proof. If store_on_server=True,
            the capsule will have server_stored=True and proof_url set.

        Raises:
            ValueError: If parameters are invalid

        Example:
            >>> # Zero-friction (device-bound key)
            >>> result = client.certify(
            ...     task="Diagnose patient symptoms",
            ...     decision="Likely common cold, recommend rest and fluids",
            ...     reasoning=[
            ...         {"step": 1, "thought": "Patient reports symptoms", "confidence": 0.98},
            ...         {"step": 2, "thought": "Symptoms match cold profile", "confidence": 0.87}
            ...     ]
            ... )
            >>>
            >>> # With custom passphrase (more secure)
            >>> result = client.certify(
            ...     task="Approve loan",
            ...     decision="Approved: $50k at 6.5%",
            ...     reasoning=[{"step": 1, "thought": "Credit score 720"}],
            ...     passphrase="my-secure-passphrase",
            ...     device_bound=False
            ... )
        """
        # Validate inputs
        if not task or not isinstance(task, str):
            raise ValueError("task must be a non-empty string")

        if not decision or not isinstance(decision, str):
            raise ValueError("decision must be a non-empty string")

        if not reasoning or not isinstance(reasoning, list):
            raise ValueError("reasoning must be a non-empty list")

        # Determine passphrase
        if passphrase:
            if len(passphrase) < 8:
                raise ValueError("passphrase must be at least 8 characters")
            signing_passphrase = passphrase
        elif device_bound:
            logger.warning(
                "Using device-bound passphrase (DEVELOPMENT ONLY). "
                "For production, provide an explicit passphrase parameter."
            )
            signing_passphrase = _derive_device_passphrase()
        else:
            raise ValueError("Either provide a passphrase or set device_bound=True")

        # Calculate confidence if not provided
        if confidence is None:
            confidences = [step.get("confidence", 0.5) for step in reasoning]
            confidence = sum(confidences) / len(confidences) if confidences else 0.5

        # Create content for signing
        # IMPORTANT: Include all fields BEFORE signing - type must be part of signed content
        timestamp = datetime.now(timezone.utc)
        content = {
            "type": "reasoning_trace",  # Include type in signed content
            "task": task,
            "decision": decision,
            "reasoning_chain": reasoning,
            "confidence": confidence,
            "metadata": {
                **(metadata or {}),
                "timestamp": timestamp.isoformat(),
                "sdk_version": "0.3.0",
                "signing_mode": "local",
            },
        }

        # Create local signer (auto-generates key if none exists)
        signer = LocalSigner(
            passphrase=signing_passphrase,
            key_dir=key_dir,
            auto_generate=True,
        )

        # Sign locally - private key NEVER leaves device
        signed = signer.sign_capsule(content)

        logger.info(f"Locally signed capsule: {signed.capsule_id}")
        logger.debug(f"Public key: {signed.public_key[:16]}...")

        # Request RFC 3161 timestamp if desired
        if request_timestamp:
            try:
                # Send ONLY the hash to UATP - content stays local
                response = self.session.post(
                    f"{self.base_url}/timestamp",
                    json={"hash": signed.content_hash},
                    timeout=self.timeout,
                )
                if response.ok:
                    ts_data = response.json()
                    signed.timestamp_token = ts_data.get("rfc3161")
                    signed.timestamp_tsa = ts_data.get("tsa")
                    signed.timestamped_at = datetime.now(timezone.utc)
                    logger.info(
                        f"Timestamp obtained from {signed.timestamp_tsa or 'TSA'}"
                    )
                else:
                    logger.warning(
                        f"Timestamp request failed: {response.status_code}. "
                        "Capsule is still valid, just without external timestamp."
                    )
            except requests.exceptions.RequestException as e:
                logger.warning(
                    f"Could not obtain timestamp: {e}. "
                    "Capsule is still valid, just without external timestamp."
                )

        # Store on server if requested
        if store_on_server:
            try:
                # Convert to verifiable format and store
                # IMPORTANT: Do NOT modify capsule_data after signing - content is already
                # included in the signed data via signer.to_verifiable_dict()
                capsule_data = signer.to_verifiable_dict(signed)

                response = self.session.post(
                    f"{self.base_url}/capsules/store",
                    json=capsule_data,
                    timeout=self.timeout,
                )

                if response.ok:
                    data = response.json()
                    # Add server storage info to signed capsule
                    signed.server_stored = True
                    signed.proof_url = (
                        f"{self.base_url}/capsules/{signed.capsule_id}/verify"
                    )
                    logger.info(f"Capsule stored on server: {signed.capsule_id}")
                else:
                    logger.warning(
                        f"Could not store on server: {response.status_code}. "
                        "Capsule is still valid locally."
                    )
                    signed.server_stored = False

            except requests.exceptions.RequestException as e:
                logger.warning(
                    f"Could not store on server: {e}. Capsule is still valid locally."
                )
                signed.server_stored = False

        return signed

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
            # Get capsule directly by ID
            response = self.session.get(
                f"{self.base_url}/capsules/{capsule_id}",
                timeout=self.timeout,
            )
            response.raise_for_status()
            data = response.json()

            # API returns {"capsule": {...}, "verification": {...}}
            # Extract capsule data from nested structure
            capsule = data.get("capsule", data)  # Fallback to data if not nested

            return CapsuleProof(
                capsule_id=capsule.get("capsule_id", capsule.get("id", capsule_id)),
                capsule_type=capsule.get(
                    "type", capsule.get("capsule_type", "unknown")
                ),
                status=capsule.get("status", "unknown"),
                timestamp=datetime.fromisoformat(
                    capsule["timestamp"].replace("Z", "+00:00")
                ),
                payload=capsule.get("payload", {}),
                _raw_data=data,  # Store full response for verification
            )

        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                raise Exception(f"Capsule {capsule_id} not found") from e
            raise Exception(f"Failed to retrieve proof: {e}") from e
        except requests.exceptions.RequestException as e:
            raise Exception(f"Failed to retrieve proof: {e}") from e

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
                    timestamp=datetime.fromisoformat(
                        item["timestamp"].replace("Z", "+00:00")
                    ),
                    payload=item.get("payload", {}),
                    _raw_data=item,
                )
                for item in data.get("capsules", [])[:limit]
            ]

        except requests.exceptions.RequestException as e:
            raise Exception(f"Failed to list capsules: {e}") from e

    def certify_rich(
        self,
        task: str,
        decision: str,
        reasoning_steps: List,  # List[ReasoningStep] or List[Dict]
        passphrase: Optional[str] = None,
        device_bound: bool = True,
        key_dir: str = "~/.uatp/keys",
        confidence: Optional[float] = None,
        risk_assessment: Optional[Dict[str, Any]] = None,
        alternatives_considered: Optional[List[Dict[str, Any]]] = None,
        plain_language_summary: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        request_timestamp: bool = True,
        store_on_server: bool = False,
    ) -> SignedCapsule:
        """
        Create a capsule with enhanced data provenance.

        ZERO-TRUST: Private key NEVER leaves your device.
        This is the RECOMMENDED method for enterprise use with full audit trails.

        Args:
            task: Description of the task
            decision: The AI's final decision
            reasoning_steps: List of ReasoningStep objects (or dicts with full provenance)
            passphrase: Your signing key passphrase. If not provided and device_bound=True,
                       a machine-specific passphrase is derived automatically.
            device_bound: If True (default), derive passphrase from machine info.
            key_dir: Directory for key storage (default: ~/.uatp/keys)
            confidence: Overall confidence (0-1)
            risk_assessment: RiskAssessment dict with probability, financial impact, safeguards
            alternatives_considered: List of Alternative dicts showing options evaluated
            plain_language_summary: PlainLanguageSummary dict for human-readable explanations
            metadata: Additional metadata
            request_timestamp: If True, request RFC 3161 timestamp from external TSA
            store_on_server: If True, store capsule on UATP server for retrieval

        Returns:
            SignedCapsule with cryptographic proof

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
            ...     }
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

        # Build rich metadata
        rich_metadata = {
            **(metadata or {}),
            "data_richness": "enterprise",
        }

        # Add optional rich data
        if risk_assessment:
            if hasattr(risk_assessment, "to_dict"):
                rich_metadata["risk_assessment"] = risk_assessment.to_dict()
            else:
                rich_metadata["risk_assessment"] = risk_assessment

        if alternatives_considered:
            if isinstance(alternatives_considered, list):
                rich_metadata["alternatives_considered"] = [
                    alt.to_dict() if hasattr(alt, "to_dict") else alt
                    for alt in alternatives_considered
                ]
            else:
                rich_metadata["alternatives_considered"] = alternatives_considered

        if plain_language_summary:
            if hasattr(plain_language_summary, "to_dict"):
                rich_metadata["plain_language_summary"] = (
                    plain_language_summary.to_dict()
                )
            else:
                rich_metadata["plain_language_summary"] = plain_language_summary

        # Use main certify method with local signing
        return self.certify(
            task=task,
            decision=decision,
            reasoning=reasoning_chain,
            passphrase=passphrase,
            device_bound=device_bound,
            key_dir=key_dir,
            confidence=confidence,
            metadata=rich_metadata,
            request_timestamp=request_timestamp,
            store_on_server=store_on_server,
        )

    def verify_local(self, capsule_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Verify a locally-signed capsule.

        This can be done by anyone - no UATP infrastructure required.
        Only uses cryptographic data embedded in the capsule.

        Args:
            capsule_data: The capsule to verify (dict format)

        Returns:
            Verification result with:
            - valid: bool - Overall validity
            - signature_valid: bool - Ed25519 signature check
            - hash_valid: bool - Content integrity check
            - timestamp_valid: bool - RFC 3161 timestamp check (if present)

        Example:
            >>> result = client.verify_local(capsule_data)
            >>> if result["valid"]:
            ...     print("Capsule is authentic!")
        """
        return verify_capsule_standalone(capsule_data)

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
        try:
            # POST to the outcome endpoint
            response = self.session.post(
                f"{self.base_url}/capsules/{capsule_id}/outcome",
                params={
                    "outcome_status": outcome.get("result", "unknown"),
                    "notes": outcome.get("notes"),
                    "rating": outcome.get("customer_satisfaction"),
                },
                timeout=self.timeout,
            )

            if response.status_code == 401:
                raise Exception(
                    "Authentication required. Outcome tracking requires a valid API key."
                )

            if response.status_code == 404:
                raise Exception(f"Capsule {capsule_id} not found")

            response.raise_for_status()

            data = response.json()
            logger.info(
                f"Outcome recorded for {capsule_id}: {data.get('outcome_status')}"
            )
            return True

        except requests.exceptions.RequestException as e:
            raise Exception(f"Failed to record outcome: {e}") from e

    def close(self) -> None:
        """Close the HTTP session."""
        self.session.close()

    def __enter__(self) -> "UATP":
        """Context manager support."""
        return self

    def __exit__(
        self,
        exc_type: Optional[type],
        exc_val: Optional[BaseException],
        exc_tb: Optional[Any],
    ) -> None:
        """Context manager cleanup."""
        self.close()
