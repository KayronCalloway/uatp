"""
RFC 3161 Timestamp Authority Client
====================================

Provides trusted timestamps for capsules using RFC 3161 protocol.
Supports hybrid mode: online TSA when available, local fallback for dev.

Modes:
- "auto": Try online TSA, fall back to local clock
- "online": Require real TSA (fails if unavailable)
- "local": Use system time only (dev/testing)

Usage:
    from src.security.timestamp_authority import TimestampAuthority

    tsa = TimestampAuthority(mode="auto")
    timestamp_info = tsa.timestamp_hash(hash_bytes)
"""

import hashlib
import logging
import os
from datetime import datetime, timezone
from typing import Any, Dict, Optional, Tuple

logger = logging.getLogger(__name__)

# Free public TSAs (for development and light production use)
PUBLIC_TSAS = [
    "http://timestamp.digicert.com",
    "http://timestamp.sectigo.com",
    "http://freetsa.org/tsr",
    "http://timestamp.globalsign.com/tsa/r6advanced1",
]


class TimestampAuthority:
    """
    RFC 3161 Timestamp Authority client with hybrid online/local support.
    """

    def __init__(
        self,
        mode: str = "auto",
        tsa_url: Optional[str] = None,
        timeout: int = 10,
    ):
        """
        Initialize timestamp authority client.

        Args:
            mode: "auto" | "online" | "local"
            tsa_url: Custom TSA URL (uses default if None)
            timeout: Request timeout in seconds
        """
        if mode not in ("auto", "online", "local"):
            raise ValueError(f"Invalid mode: {mode}. Use 'auto', 'online', or 'local'")

        self.mode = mode
        self.tsa_url = tsa_url or PUBLIC_TSAS[0]
        self.timeout = timeout
        self._asn1_available = self._check_asn1_available()

        if mode == "online" and not self._asn1_available:
            raise ImportError(
                "asn1crypto required for online mode. Install: pip install asn1crypto"
            )

        logger.info(f"TimestampAuthority initialized: mode={mode}, tsa={self.tsa_url}")

    def _check_asn1_available(self) -> bool:
        """Check if asn1crypto is available for RFC 3161."""
        try:
            import asn1crypto  # noqa: F401
            return True
        except ImportError:
            return False

    def _build_ts_request(self, data_hash: bytes) -> bytes:
        """Build RFC 3161 timestamp request."""
        from asn1crypto import algos, core, tsp

        # Create message imprint
        message_imprint = tsp.MessageImprint({
            "hash_algorithm": algos.DigestAlgorithm({"algorithm": "sha256"}),
            "hashed_message": data_hash,
        })

        # Create timestamp request
        ts_request = tsp.TimeStampReq({
            "version": 1,
            "message_imprint": message_imprint,
            "cert_req": True,  # Request TSA certificate in response
            "nonce": core.Integer(int.from_bytes(os.urandom(8), "big")),
        })

        return ts_request.dump()

    def _request_rfc3161(self, data_hash: bytes) -> Optional[bytes]:
        """
        Request timestamp from RFC 3161 TSA.

        Args:
            data_hash: SHA256 hash bytes (32 bytes)

        Returns:
            DER-encoded timestamp token, or None on failure
        """
        import requests
        from asn1crypto import tsp

        try:
            # Build request
            ts_request = self._build_ts_request(data_hash)

            # Send to TSA
            response = requests.post(
                self.tsa_url,
                data=ts_request,
                headers={"Content-Type": "application/timestamp-query"},
                timeout=self.timeout,
            )

            if response.status_code != 200:
                logger.warning(f"TSA returned status {response.status_code}")
                return None

            # Parse response
            ts_response = tsp.TimeStampResp.load(response.content)
            status = ts_response["status"]["status"].native

            if status != "granted":
                status_string = ts_response["status"].get("status_string")
                logger.warning(f"TSA denied request: {status} - {status_string}")
                return None

            # Extract timestamp token
            token = ts_response["time_stamp_token"]
            if token is None:
                logger.warning("TSA response missing timestamp token")
                return None

            return token.dump()

        except requests.exceptions.RequestException as e:
            logger.warning(f"TSA request failed: {e}")
            return None
        except Exception as e:
            logger.error(f"TSA error: {e}")
            return None

    def _local_timestamp(self) -> Dict[str, Any]:
        """Generate local (untrusted) timestamp."""
        return {
            "method": "local_clock",
            "time": datetime.now(timezone.utc).isoformat(),
            "trusted": False,
            "note": "Local system time - not independently verifiable",
        }

    def timestamp_hash(self, data_hash: bytes) -> Dict[str, Any]:
        """
        Get a timestamp for a hash.

        Args:
            data_hash: SHA256 hash bytes (32 bytes)

        Returns:
            Timestamp info dict with method, time, and trust status
        """
        if self.mode == "local":
            return self._local_timestamp()

        if not self._asn1_available:
            if self.mode == "online":
                raise ImportError("asn1crypto required for online timestamps")
            logger.warning("asn1crypto not available, using local timestamp")
            return self._local_timestamp()

        # Try online TSA
        token = self._request_rfc3161(data_hash)

        if token:
            # Parse timestamp from token for convenience
            try:
                from asn1crypto import cms
                content_info = cms.ContentInfo.load(token)
                signed_data = content_info["content"]
                encap_content = signed_data["encap_content_info"]["content"]
                tst_info = encap_content.parsed
                gen_time = tst_info["gen_time"].native

                return {
                    "method": "rfc3161",
                    "rfc3161_token": token.hex(),
                    "tsa_url": self.tsa_url,
                    "time": gen_time.isoformat() if gen_time else None,
                    "trusted": True,
                }
            except Exception as e:
                logger.warning(f"Could not parse timestamp token: {e}")
                return {
                    "method": "rfc3161",
                    "rfc3161_token": token.hex(),
                    "tsa_url": self.tsa_url,
                    "trusted": True,
                }

        # Fallback
        if self.mode == "auto":
            logger.info("TSA unavailable, falling back to local timestamp")
            result = self._local_timestamp()
            result["method"] = "local_clock_fallback"
            result["note"] = "TSA unavailable - fell back to local system time"
            return result

        # mode == "online" and TSA failed
        raise RuntimeError(f"Could not get timestamp from TSA: {self.tsa_url}")

    def timestamp_data(self, data: bytes) -> Dict[str, Any]:
        """
        Timestamp arbitrary data (hashes it first).

        Args:
            data: Raw bytes to timestamp

        Returns:
            Timestamp info dict
        """
        data_hash = hashlib.sha256(data).digest()
        return self.timestamp_hash(data_hash)

    def timestamp_capsule(self, capsule_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Add timestamp to capsule data.

        Args:
            capsule_data: Capsule dict (without verification field)

        Returns:
            Timestamp info to include in verification object
        """
        import json

        # Create canonical representation (same as signing)
        canonical = json.dumps(
            {k: v for k, v in capsule_data.items() if k != "verification"},
            sort_keys=True,
            separators=(",", ":"),
        )
        data_hash = hashlib.sha256(canonical.encode()).digest()

        return self.timestamp_hash(data_hash)

    @staticmethod
    def verify_timestamp(
        data_hash: bytes, timestamp_info: Dict[str, Any]
    ) -> Tuple[bool, Optional[datetime], str]:
        """
        Verify a timestamp.

        Args:
            data_hash: Original SHA256 hash bytes
            timestamp_info: Timestamp dict from timestamp_hash()

        Returns:
            (is_valid, timestamp_time, message)
        """
        method = timestamp_info.get("method", "unknown")

        if method in ("local_clock", "local_clock_fallback"):
            # Local timestamps can't be independently verified
            time_str = timestamp_info.get("time")
            if time_str:
                try:
                    ts_time = datetime.fromisoformat(time_str.replace("Z", "+00:00"))
                    return True, ts_time, "Local timestamp (not independently verifiable)"
                except ValueError:
                    pass
            return False, None, "Invalid local timestamp format"

        if method == "rfc3161":
            token_hex = timestamp_info.get("rfc3161_token")
            if not token_hex:
                return False, None, "Missing RFC 3161 token"

            try:
                from asn1crypto import cms

                token = bytes.fromhex(token_hex)
                content_info = cms.ContentInfo.load(token)
                signed_data = content_info["content"]
                encap_content = signed_data["encap_content_info"]["content"]
                tst_info = encap_content.parsed

                # Verify hash matches
                message_imprint = tst_info["message_imprint"]
                stamped_hash = message_imprint["hashed_message"].native

                if stamped_hash != data_hash:
                    return False, None, "Hash mismatch - data was modified"

                # Extract timestamp
                gen_time = tst_info["gen_time"].native

                # Note: Full verification would also check TSA signature
                # against known TSA certificates. For now we trust the token format.

                return True, gen_time, "RFC 3161 timestamp valid"

            except ImportError:
                return False, None, "asn1crypto required to verify RFC 3161 timestamps"
            except Exception as e:
                return False, None, f"Timestamp verification error: {e}"

        return False, None, f"Unknown timestamp method: {method}"


# Convenience function
def get_timestamp_authority(mode: str = "auto") -> TimestampAuthority:
    """Get a configured TimestampAuthority instance."""
    return TimestampAuthority(mode=mode)
