"""
UATP Capsule Engine API Client

A Python client library for interacting with the enhanced UATP Capsule Engine API.
Supports authentication, compression, and chain sealing.
"""

from typing import Any, Dict, List, Optional

import requests


class UATCapsuleEngineClient:
    """Client for interacting with the UATP Capsule Engine API."""

    def __init__(
        self, base_url: str, api_key: Optional[str] = None, compression: bool = False
    ):
        """
        Initialize the UATP Capsule Engine API client.

        Args:
            base_url: The base URL of the API server (e.g., "http://localhost:5000")
            api_key: Optional API key for authentication
            compression: Whether to request compressed responses
        """
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.compression = compression
        self.session = requests.Session()

        # Add API key to headers if provided
        if api_key:
            self.session.headers.update({"X-API-Key": api_key})

    def _get_headers(self) -> Dict[str, str]:
        """Get headers for API requests."""
        headers = {"Content-Type": "application/json"}
        return headers

    def health_check(self) -> Dict[str, Any]:
        """Check the health of the API server."""
        response = self.session.get(f"{self.base_url}/health")
        response.raise_for_status()
        return response.json()

    def list_capsules(self, limit: int = 100, offset: int = 0) -> Dict[str, Any]:
        """
        List capsules in the chain with pagination.

        Args:
            limit: Maximum number of capsules to return
            offset: Starting position in the chain

        Returns:
            Dictionary containing paginated capsules and metadata
        """
        params = {"limit": limit, "offset": offset}

        if self.compression:
            params["compressed"] = "true"

        response = self.session.get(f"{self.base_url}/capsules", params=params)
        response.raise_for_status()
        return response.json()

    def get_capsule(self, capsule_id: str) -> Dict[str, Any]:
        """
        Get a specific capsule by ID.

        Args:
            capsule_id: The ID of the capsule to retrieve

        Returns:
            Dictionary containing the capsule data

        Raises:
            requests.HTTPError: If the capsule is not found
        """
        params = {}
        if self.compression:
            params["compressed"] = "true"

        response = self.session.get(
            f"{self.base_url}/capsules/{capsule_id}", params=params
        )
        response.raise_for_status()
        return response.json()

    def create_capsule(
        self,
        capsule_type: str,
        confidence: float,
        reasoning_trace: Optional[List[str]] = None,
        previous_capsule_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """
        Create a new capsule and add it to the chain.

        Args:
            capsule_type: Type of capsule (e.g., "Refusal", "Introspective", "Joint")
            confidence: Confidence score (0.0 to 1.0)
            reasoning_trace: List of reasoning steps
            previous_capsule_id: ID of the parent capsule (for forks)
            metadata: Additional metadata for the capsule
            **kwargs: Additional fields specific to the capsule type

        Returns:
            Dictionary containing the created capsule and its ID

        Raises:
            requests.HTTPError: If creation fails
        """
        data = {
            "capsule_type": capsule_type,
            "confidence": confidence,
            "reasoning_trace": reasoning_trace or [],
            "metadata": metadata or {},
        }

        if previous_capsule_id:
            data["previous_capsule_id"] = previous_capsule_id

        # Add any additional fields
        data.update(kwargs)

        params = {}
        if self.compression:
            params["compressed"] = "true"

        response = self.session.post(
            f"{self.base_url}/capsules", json=data, params=params
        )
        response.raise_for_status()
        return response.json()

    def list_chain_seals(self) -> Dict[str, Any]:
        """
        List all chain seals.

        Returns:
            Dictionary containing all chain seals

        Raises:
            requests.HTTPError: If the request fails
        """
        response = self.session.get(f"{self.base_url}/chain/seals")
        response.raise_for_status()
        return response.json()

    def seal_chain(
        self, chain_id: str, signer_id: Optional[str] = None, note: Optional[str] = ""
    ) -> Dict[str, Any]:
        """
        Create a finality signature for a chain.

        Args:
            chain_id: Identifier for the chain being sealed
            signer_id: Optional identifier of the signer
            note: Optional note about the purpose of the seal

        Returns:
            Dictionary containing the seal data

        Raises:
            requests.HTTPError: If sealing fails
        """
        data = {
            "chain_id": chain_id,
        }

        if signer_id:
            data["signer_id"] = signer_id

        if note:
            data["note"] = note

        response = self.session.post(f"{self.base_url}/chain/seal", json=data)
        response.raise_for_status()
        return response.json()

    def verify_chain_seal(self, chain_id: str, verify_key: str) -> Dict[str, Any]:
        """
        Verify a chain seal.

        Args:
            chain_id: ID of the sealed chain to verify
            verify_key: Verification key to use

        Returns:
            Dictionary with verification result

        Raises:
            requests.HTTPError: If verification fails
        """
        response = self.session.get(
            f"{self.base_url}/chain/verify-seal/{chain_id}",
            params={"verify_key": verify_key},
        )
        response.raise_for_status()
        return response.json()

    def verify_capsule(self, capsule_id: str) -> Dict[str, Any]:
        """
        Verify a specific capsule by ID.

        Args:
            capsule_id: The ID of the capsule to verify

        Returns:
            Dictionary with verification result

        Raises:
            requests.HTTPError: If the capsule is not found
        """
        response = self.session.get(f"{self.base_url}/capsules/verify/{capsule_id}")
        response.raise_for_status()
        return response.json()

    def get_cqss(self) -> Dict[str, Any]:
        """
        Get CQSS metrics for the entire chain.

        Returns:
            Dictionary containing CQSS metrics

        Raises:
            requests.HTTPError: If the request fails
        """
        response = self.session.get(f"{self.base_url}/cqss")
        response.raise_for_status()
        return response.json()

    def get_chain_forks(self) -> Dict[str, Any]:
        """
        Get information about forks in the chain.

        Returns:
            Dictionary containing fork information

        Raises:
            requests.HTTPError: If the request fails
        """
        response = self.session.get(f"{self.base_url}/chain/forks")
        response.raise_for_status()
        return response.json()

    def get_capsule_stats(self) -> Dict[str, Any]:
        """
        Get statistical information about capsules in the chain.

        Returns:
            Dictionary containing capsule statistics

        Raises:
            requests.HTTPError: If the request fails
        """
        response = self.session.get(f"{self.base_url}/capsules/stats")
        response.raise_for_status()
        return response.json()

    # Helper method for decompressing responses if needed
    def decompress_capsule_if_needed(
        self, capsule_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Decompress a capsule if it's compressed.

        Args:
            capsule_data: Possibly compressed capsule data

        Returns:
            Decompressed capsule data
        """
        if capsule_data.get("compressed") and capsule_data.get("data"):
            import base64
            import json
            import zlib

            # Decompress the data
            compressed_data = base64.b64decode(capsule_data["data"])

            # SECURITY: Bounded decompression
            max_size = 10 * 1024 * 1024  # 10MB limit
            decompressor = zlib.decompressobj()
            decompressed_data = decompressor.decompress(
                compressed_data, max_length=max_size
            )
            if decompressor.unconsumed_tail:
                raise ValueError(
                    f"Decompressed payload exceeds maximum size of {max_size} bytes"
                )

            return json.loads(decompressed_data)
        return capsule_data

    def create_refusal_capsule(
        self,
        confidence: float,
        reasoning_trace: List[str],
        reason_for_rejection: str,
        ethical_policy_id: Optional[str] = None,
        previous_capsule_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Create a Refusal capsule.

        Args:
            confidence: Confidence score (0.0 to 1.0)
            reasoning_trace: List of reasoning steps
            reason_for_rejection: Reason for the refusal
            ethical_policy_id: ID of the ethical policy applied
            previous_capsule_id: ID of the parent capsule (for forks)
            metadata: Additional metadata for the capsule

        Returns:
            Dictionary containing the created capsule and its ID
        """
        return self.create_capsule(
            capsule_type="Refusal",
            confidence=confidence,
            reasoning_trace=reasoning_trace,
            previous_capsule_id=previous_capsule_id,
            metadata=metadata,
            reason_for_rejection=reason_for_rejection,
            ethical_policy_id=ethical_policy_id,
        )

    def create_introspective_capsule(
        self,
        confidence: float,
        reasoning_trace: List[str],
        previous_capsule_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Create an Introspective capsule.

        Args:
            confidence: Confidence score (0.0 to 1.0)
            reasoning_trace: List of reasoning steps
            previous_capsule_id: ID of the parent capsule (for forks)
            metadata: Additional metadata for the capsule

        Returns:
            Dictionary containing the created capsule and its ID
        """
        return self.create_capsule(
            capsule_type="Introspective",
            confidence=confidence,
            reasoning_trace=reasoning_trace,
            previous_capsule_id=previous_capsule_id,
            metadata=metadata,
        )

    def create_joint_capsule(
        self,
        confidence: float,
        reasoning_trace: List[str],
        agreement_terms: str,
        human_signature: Optional[str] = None,
        previous_capsule_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Create a Joint capsule.

        Args:
            confidence: Confidence score (0.0 to 1.0)
            reasoning_trace: List of reasoning steps
            agreement_terms: Terms of the joint agreement
            human_signature: Optional signature from human participant
            previous_capsule_id: ID of the parent capsule (for forks)
            metadata: Additional metadata for the capsule

        Returns:
            Dictionary containing the created capsule and its ID
        """
        return self.create_capsule(
            capsule_type="Joint",
            confidence=confidence,
            reasoning_trace=reasoning_trace,
            agreement_terms=agreement_terms,
            human_signature=human_signature,
            previous_capsule_id=previous_capsule_id,
            metadata=metadata,
        )


# Example usage
if __name__ == "__main__":
    # Create a client instance
    client = UATCapsuleEngineClient("http://localhost:5000")

    # Check API health
    health = client.health_check()
    print(f"API Status: {health['status']}")

    # Create a capsule
    capsule = client.create_introspective_capsule(
        confidence=0.95,
        reasoning_trace=[
            "Step 1: Initial observation",
            "Step 2: Analysis",
            "Step 3: Conclusion",
        ],
        metadata={"source": "client_example", "context": "testing"},
    )

    print(f"Created capsule with ID: {capsule['capsule_id']}")

    # Verify the capsule
    verification = client.verify_capsule(capsule["capsule_id"])
    print(f"Capsule verified: {verification['verified']}")

    # Get CQSS metrics
    cqss = client.get_cqss()
    print(f"Overall CQSS score: {cqss.get('overall_score', 'N/A')}")
