"""
UATP Chain Sealer

This module provides functionality for creating and verifying chain seals.
Chain seals provide cryptographic finality and legal admissibility for capsule chains.
"""

import base64
import datetime
import hashlib
import json
import os
import time
import uuid
from datetime import timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

import nacl.encoding
import nacl.signing
from nacl.exceptions import BadSignatureError


class ChainSealer:
    """
    Creates and verifies cryptographic seals for capsule chains.
    Seals provide legal admissibility and tamper-evidence.
    """

    def __init__(self, seals_dir: str = None, signing_key_hex: str = None):
        """
        Initialize the ChainSealer.

        Args:
            seals_dir: Directory to store seal data (defaults to 'chain_seals' in the current directory)
            signing_key_hex: Hex-encoded Ed25519 signing key
        """
        self.seals_dir = seals_dir or os.getenv("UATP_SEALS_PATH", "chain_seals")

        # Create seals directory if it doesn't exist
        os.makedirs(self.seals_dir, exist_ok=True)

        # Load or create signing key
        signing_key_hex = signing_key_hex or os.getenv("UATP_SIGNING_KEY")
        if signing_key_hex:
            seed = bytes.fromhex(signing_key_hex)
            self.signing_key = nacl.signing.SigningKey(seed)
        else:
            # Generate a new key
            self.signing_key = nacl.signing.SigningKey.generate()
            print(
                f"WARNING: No signing key provided. Generated a new key: {self.signing_key.encode(nacl.encoding.HexEncoder).decode('utf-8')}"
            )

        # Get the verify key
        self.verify_key = self.signing_key.verify_key
        self.verify_key_hex = self.verify_key.encode(nacl.encoding.HexEncoder).decode(
            "utf-8"
        )

    def _get_seal_path(self, chain_id: str, seal_id: str = None) -> str:
        """Get the path to store a chain seal."""
        if not seal_id:
            return os.path.join(self.seals_dir, f"{chain_id}_seals.json")
        return os.path.join(self.seals_dir, f"{chain_id}_{seal_id}.json")

    def _get_chain_state_hash(
        self, chain_id: str, chain_data: Optional[List[Dict[str, Any]]] = None
    ) -> str:
        """
        Compute a hash representing the current state of the chain.

        Args:
            chain_id: Identifier for the chain
            chain_data: Optional list of capsules in the chain

        Returns:
            SHA-256 hash of the canonicalized chain data
        """
        # If chain_data is provided, use it directly
        if chain_data is not None:
            # Canonicalize the chain data
            canonical_data = json.dumps(
                chain_data, sort_keys=True, separators=(",", ":")
            )
            return hashlib.sha256(canonical_data.encode("utf-8")).hexdigest()

        # Otherwise, check for chain file based on ID
        chain_path = os.getenv("UATP_CHAIN_PATH", "capsule_chain.jsonl")
        if not os.path.exists(chain_path):
            raise FileNotFoundError(f"Chain file not found: {chain_path}")

        # Read the chain file and compute hash
        with open(chain_path) as f:
            chain_data = [json.loads(line) for line in f if line.strip()]

        # Compute hash from the chain data
        canonical_data = json.dumps(chain_data, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(canonical_data.encode("utf-8")).hexdigest()

    def seal_chain(
        self,
        chain_id: str,
        signer_id: str,
        seal_note: str = "",
        chain_data: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        """
        Create a cryptographic seal for the current state of a chain.

        Args:
            chain_id: Identifier for the chain
            signer_id: Identifier for the signer (e.g., user, organization)
            seal_note: Optional note about the purpose of this seal
            chain_data: Optional list of capsules in the chain

        Returns:
            Dictionary containing the seal data
        """
        # Generate a unique seal ID
        timestamp = datetime.datetime.now(timezone.utc).isoformat()
        seal_id = f"seal-{int(time.time())}-{uuid.uuid4().hex[:8]}"

        # Compute the chain state hash
        chain_state_hash = self._get_chain_state_hash(chain_id, chain_data)

        # Create the seal data
        seal_data = {
            "seal_id": seal_id,
            "chain_id": chain_id,
            "timestamp": timestamp,
            "signer_id": signer_id,
            "chain_state_hash": chain_state_hash,
            "note": seal_note,
        }

        # Canonicalize the data for signing
        canonical_data = json.dumps(seal_data, sort_keys=True, separators=(",", ":"))

        # Sign the data
        signature = self.signing_key.sign(canonical_data.encode("utf-8"))
        signature_hex = base64.b64encode(signature.signature).decode("utf-8")

        # Add the signature to the seal data
        seal_data["signature"] = signature_hex
        seal_data["verify_key"] = self.verify_key_hex

        # Save the seal
        seal_path = self._get_seal_path(chain_id, seal_id)
        with open(seal_path, "w") as f:
            json.dump(seal_data, f, indent=2)

        # Add to seals index
        self._update_seals_index(chain_id, seal_data)

        return seal_data

    def _update_seals_index(self, chain_id: str, seal_data: Dict[str, Any]) -> None:
        """Update the index file for a chain's seals."""
        index_path = self._get_seal_path(chain_id)

        # Read existing index or create new one
        seals = []
        if os.path.exists(index_path):
            try:
                with open(index_path) as f:
                    data = json.load(f)
                    seals = data.get("seals", [])
            except Exception:
                pass

        # Add the new seal reference
        seals.append(
            {
                "seal_id": seal_data["seal_id"],
                "timestamp": seal_data["timestamp"],
                "signer_id": seal_data["signer_id"],
                "note": seal_data["note"],
            }
        )

        # Write the updated index
        with open(index_path, "w") as f:
            json.dump({"chain_id": chain_id, "seals": seals}, f, indent=2)

    def list_seals(self, chain_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        List all seals for a chain or all chains.

        Args:
            chain_id: Optional ID of the chain to list seals for

        Returns:
            List of seal data dictionaries
        """
        seals = []

        # If chain_id is provided, load seals for that chain
        if chain_id:
            index_path = self._get_seal_path(chain_id)
            if os.path.exists(index_path):
                with open(index_path) as f:
                    data = json.load(f)
                    seals.extend(data.get("seals", []))
            return seals

        # Otherwise, load seals for all chains
        for file_path in Path(self.seals_dir).glob("*_seals.json"):
            with open(file_path) as f:
                data = json.load(f)
                for seal in data.get("seals", []):
                    seal["chain_id"] = data.get("chain_id", "unknown")
                    seals.append(seal)

        return seals

    def verify_seal(
        self, chain_id: str, verify_key_hex: str, seal_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Verify a chain seal against the current chain state.

        Args:
            chain_id: ID of the chain to verify
            verify_key_hex: Hex-encoded verification key
            seal_id: Optional specific seal ID to verify

        Returns:
            Dictionary with verification results
        """
        # Find the seal to verify
        seals = self.list_seals(chain_id)
        if not seals:
            return {"verified": False, "error": "No seals found for this chain"}

        # If seal_id is specified, find that specific seal
        target_seal = None
        if seal_id:
            for seal in seals:
                if seal.get("seal_id") == seal_id:
                    target_seal = seal
                    break

            if not target_seal:
                return {"verified": False, "error": f"Seal not found: {seal_id}"}
        else:
            # Use the most recent seal
            target_seal = sorted(
                seals, key=lambda s: s.get("timestamp", ""), reverse=True
            )[0]
            seal_id = target_seal.get("seal_id")

        # Load the full seal data
        seal_path = self._get_seal_path(chain_id, seal_id)
        if not os.path.exists(seal_path):
            return {
                "verified": False,
                "error": f"Seal file not found: {seal_path}",
                "chain_id": chain_id,
                "seal_id": seal_id,
            }

        with open(seal_path) as f:
            seal_data = json.load(f)

        # Extract signature and data to verify
        signature_b64 = seal_data.get("signature")
        stored_verify_key = seal_data.get("verify_key")

        if not signature_b64 or not stored_verify_key:
            return {
                "verified": False,
                "error": "Seal is missing signature or verify key",
                "chain_id": chain_id,
                "seal_id": seal_id,
            }

        # Verify that the provided key matches the one in the seal
        if verify_key_hex != stored_verify_key:
            return {
                "verified": False,
                "error": "Verification key does not match the key used to sign the seal",
                "chain_id": chain_id,
                "seal_id": seal_id,
                "expected_key": stored_verify_key,
            }

        # Create a copy of the seal data without the signature for verification
        verification_data = {
            k: v for k, v in seal_data.items() if k not in ["signature", "verify_key"]
        }
        canonical_data = json.dumps(
            verification_data, sort_keys=True, separators=(",", ":")
        )

        # Verify the signature
        try:
            verify_key = nacl.signing.VerifyKey(bytes.fromhex(verify_key_hex))
            signature = base64.b64decode(signature_b64)
            verify_key.verify(canonical_data.encode("utf-8"), signature)

            # Signature is valid, now check if chain state still matches
            current_chain_hash = self._get_chain_state_hash(chain_id)
            stored_chain_hash = seal_data.get("chain_state_hash")

            chain_unchanged = current_chain_hash == stored_chain_hash

            return {
                "verified": True,
                "chain_id": chain_id,
                "seal_id": seal_id,
                "signer_id": seal_data.get("signer_id"),
                "timestamp": seal_data.get("timestamp"),
                "chain_unchanged": chain_unchanged,
                "note": seal_data.get("note", ""),
            }

        except BadSignatureError:
            return {
                "verified": False,
                "error": "Invalid signature",
                "chain_id": chain_id,
                "seal_id": seal_id,
            }
        except Exception as e:
            return {
                "verified": False,
                "error": f"Verification error: {str(e)}",
                "chain_id": chain_id,
                "seal_id": seal_id,
            }

    def get_chain_sealer_status(self) -> Dict[str, Any]:
        """
        Get the status of the chain sealer, including the verification key.

        Returns:
            Dictionary with status information
        """
        return {
            "status": "active",
            "seals_dir": self.seals_dir,
            "verify_key": self.verify_key_hex,
            "seal_count": len(self.list_seals()),
        }
