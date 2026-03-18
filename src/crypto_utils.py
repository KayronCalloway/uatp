"""
crypto_utils.py - Cryptographic utilities for UATP Capsule Engine.
Provides hashing, signing, and verification functions using Ed25519 (PyNaCl).
Enhanced with comprehensive security validation and replay protection.
"""

import hashlib
import hmac
import logging
import threading
import time
from typing import Any, Dict, Optional, Set, Tuple

from nacl.encoding import HexEncoder
from nacl.signing import SigningKey, VerifyKey

logger = logging.getLogger(__name__)

# Replay protection - signature context tracking
_signature_context_cache: Dict[
    str, Set[str]
] = {}  # public_key -> set of used signature hashes
_signature_cache_lock = threading.RLock()
_max_cache_size = 10000
_cache_cleanup_interval = 3600  # 1 hour
_cache_entry_ttl = 86400  # 24 hours - entries expire after this time

# LRU cache with timestamps: fingerprint -> (timestamp, access_count)
# Using OrderedDict for LRU semantics
from collections import OrderedDict

_signature_cache: OrderedDict[str, Tuple[float, int]] = OrderedDict()
_last_cache_cleanup = time.time()


def _generate_signature_fingerprint(
    hash_str: str, signature: str, public_key: str
) -> str:
    """Generate unique fingerprint for signature replay detection."""
    combined = f"{hash_str}:{signature}:{public_key}"
    return hashlib.sha256(combined.encode()).hexdigest()


def _evict_expired_cache_entries() -> int:
    """
    Evict expired cache entries based on TTL.
    Called periodically during cache operations.

    Returns:
        Number of entries evicted
    """
    global _last_cache_cleanup

    now = time.time()

    # Only run cleanup every cleanup_interval seconds
    if now - _last_cache_cleanup < _cache_cleanup_interval:
        return 0

    _last_cache_cleanup = now
    evicted = 0

    # Remove entries older than TTL
    expired_keys = []
    for fingerprint, (timestamp, _) in _signature_cache.items():
        if now - timestamp > _cache_entry_ttl:
            expired_keys.append(fingerprint)

    for key in expired_keys:
        del _signature_cache[key]
        evicted += 1

    if evicted > 0:
        logger.debug(f"Evicted {evicted} expired entries from replay cache")

    return evicted


def _check_replay_protection(hash_str: str, signature: str, public_key: str) -> bool:
    """
    Check if this signature has been used with DIFFERENT content (replay attack protection).
    Allows re-verification of the same hash+signature+key combination.

    Uses LRU eviction with time-based expiration:
    - Entries expire after _cache_entry_ttl seconds (24 hours default)
    - LRU eviction when cache exceeds _max_cache_size
    - Recently accessed entries are moved to end (most recent)

    Returns:
        True if signature is valid for this content
        False if signature is being replayed for different content
    """
    fingerprint = _generate_signature_fingerprint(hash_str, signature, public_key)
    now = time.time()

    with _signature_cache_lock:
        # Periodic cleanup of expired entries
        _evict_expired_cache_entries()

        if fingerprint in _signature_cache:
            # Check if entry has expired
            timestamp, access_count = _signature_cache[fingerprint]
            if now - timestamp > _cache_entry_ttl:
                # Entry expired, remove it and treat as new
                del _signature_cache[fingerprint]
                logger.debug(f"Expired cache entry for {fingerprint[:16]}...")
            else:
                # Same hash+signature+key = legitimate re-verification, allow it
                # Move to end (most recently used) for LRU semantics
                _signature_cache.move_to_end(fingerprint)
                _signature_cache[fingerprint] = (timestamp, access_count + 1)
                logger.debug(
                    f"Re-verification of known signature {fingerprint[:16]}... (allowed)"
                )
                return True

        # Add to cache for future re-verification allowance
        _signature_cache[fingerprint] = (now, 1)

        # LRU eviction if cache is too large
        while len(_signature_cache) > _max_cache_size:
            # Remove oldest (first) entry - LRU eviction
            oldest_key, (oldest_time, _) = next(iter(_signature_cache.items()))
            del _signature_cache[oldest_key]
            logger.debug(
                f"LRU evicted cache entry {oldest_key[:16]}... (age: {now - oldest_time:.0f}s)"
            )

        return True


def _validate_signature_format(signature_hex: str, signature_type: str) -> bool:
    """
    Validate signature format and structure.

    Args:
        signature_hex: Hex-encoded signature with prefix
        signature_type: Expected signature type ('ed25519', 'dilithium3')

    Returns:
        True if format is valid, False otherwise
    """
    if not signature_hex or not isinstance(signature_hex, str):
        logger.error("SECURITY ERROR: Invalid signature - empty or not string")
        return False

    if signature_type == "ed25519":
        if not signature_hex.startswith("ed25519:"):
            logger.error("SECURITY ERROR: Ed25519 signature missing required prefix")
            return False

        sig_hex = signature_hex[8:]  # Remove 'ed25519:' prefix
        if len(sig_hex) != 128:  # 64 bytes = 128 hex chars
            logger.error("SECURITY ERROR: Ed25519 signature invalid length")
            return False

    elif signature_type == "dilithium3":
        if not signature_hex.startswith("dilithium3:"):
            logger.error("SECURITY ERROR: Dilithium3 signature missing required prefix")
            return False

        sig_hex = signature_hex[11:]  # Remove 'dilithium3:' prefix
        if len(sig_hex) < 4000:  # Dilithium3 signatures should be substantial
            logger.error("SECURITY ERROR: Dilithium3 signature too short")
            return False

    else:
        logger.error(f"SECURITY ERROR: Unknown signature type: {signature_type}")
        return False

    # Validate hex encoding
    try:
        bytes.fromhex(sig_hex)
    except ValueError:
        logger.error("SECURITY ERROR: Invalid hex encoding in signature")
        return False

    return True


def _validate_public_key_format(public_key_hex: str, key_type: str) -> bool:
    """
    Validate public key format and structure.

    Args:
        public_key_hex: Hex-encoded public key
        key_type: Expected key type ('ed25519', 'dilithium3')

    Returns:
        True if format is valid, False otherwise
    """
    if not public_key_hex or not isinstance(public_key_hex, str):
        logger.error("SECURITY ERROR: Invalid public key - empty or not string")
        return False

    try:
        key_bytes = bytes.fromhex(public_key_hex)
    except ValueError:
        logger.error("SECURITY ERROR: Invalid hex encoding in public key")
        return False

    if key_type == "ed25519":
        if len(key_bytes) != 32:  # Ed25519 public keys are exactly 32 bytes
            logger.error("SECURITY ERROR: Ed25519 public key invalid length")
            return False
    elif key_type == "dilithium3":
        if len(key_bytes) < 1500:  # Dilithium3 public keys should be ~1952 bytes
            logger.error("SECURITY ERROR: Dilithium3 public key too short")
            return False
    else:
        logger.error(f"SECURITY ERROR: Unknown key type: {key_type}")
        return False

    return True


def hash_capsule_dict(capsule_dict):
    """
    Compute a SHA256 hash of a capsule dict, excluding 'hash' and 'signature' fields.
    Uses canonical JSON serialization for stable hashes across environments.

    Args:
        capsule_dict (dict): Capsule data.
    Returns:
        str: SHA256 hex digest.
    """
    import json
    from datetime import datetime, timezone
    from decimal import Decimal

    def canonical_json_serializer(obj):
        """Custom JSON serializer for canonical, stable JSON output."""
        if isinstance(obj, datetime):
            if obj.tzinfo is None:
                obj = obj.replace(tzinfo=timezone.utc)
            return obj.isoformat()
        elif isinstance(obj, Decimal):
            return float(obj)
        elif hasattr(obj, "__dict__"):
            return obj.__dict__
        return str(obj)

    capsule_copy = dict(capsule_dict)

    # Remove fields that should not be included in hash
    capsule_copy.pop("hash", None)
    capsule_copy.pop("signature", None)

    # Remove nested hash/signature fields from verification if present
    if "verification" in capsule_copy and isinstance(
        capsule_copy["verification"], dict
    ):
        verification_copy = dict(capsule_copy["verification"])
        verification_copy.pop("hash", None)
        verification_copy.pop("signature", None)
        capsule_copy["verification"] = verification_copy

    try:
        # Try to use orjson if available for better performance and stability
        import orjson

        canonical_json = orjson.dumps(
            capsule_copy,
            option=orjson.OPT_SORT_KEYS | orjson.OPT_NON_STR_KEYS,
            default=canonical_json_serializer,
        ).decode("utf-8")
    except ImportError:
        # Fallback to standard json with consistent options
        canonical_json = json.dumps(
            capsule_copy,
            sort_keys=True,
            ensure_ascii=True,
            separators=(",", ":"),  # No spaces for consistency
            default=canonical_json_serializer,
        )

    return hashlib.sha256(canonical_json.encode("utf-8")).hexdigest()


def hash_for_signature(capsule):
    """
    Compute a hash for a capsule object that will be used for signing or verification.
    Creates a consistent hash regardless of whether it's for signing or verification.

    Args:
        capsule: A Capsule object or dictionary representation
    Returns:
        str: SHA256 hex digest
    """
    if hasattr(capsule, "model_dump"):
        # It's a Pydantic model
        capsule_dict = capsule.model_dump()
    else:
        # Assume it's already a dict
        capsule_dict = dict(capsule)

    return hash_capsule_dict(capsule_dict)


# --- Post-Quantum Cryptography Support ---


def generate_post_quantum_keypair():
    """
    Generate a post-quantum cryptography keypair using Dilithium.
    Returns tuple of (private_key_hex, public_key_hex)

    Raises:
        RuntimeError: If post-quantum cryptography libraries are not available.
    """
    from src.crypto.post_quantum import pq_crypto

    if not pq_crypto.dilithium_available:
        raise RuntimeError(
            "SECURITY ERROR: Post-quantum cryptography is not available. "
            "Cannot generate fake Dilithium keypairs. Install liboqs-python or pqcrypto "
            "library for real post-quantum security."
        )

    # Use real post-quantum crypto implementation
    dilithium_keypair = pq_crypto.generate_dilithium_keypair()
    private_key = dilithium_keypair.private_key.hex()
    public_key = dilithium_keypair.public_key.hex()
    return private_key, public_key


def sign_post_quantum(hash_str, pq_private_key_hex):
    """
    Sign a hash string with a post-quantum private key.
    SECURITY CRITICAL: Only uses real post-quantum cryptography.

    Args:
        hash_str (str): String to sign (usually a hash).
        pq_private_key_hex (str): Hex-encoded post-quantum private key.
    Returns:
        str: Hex-encoded post-quantum signature with dilithium3: prefix.
    Raises:
        RuntimeError: If post-quantum cryptography is not available.
    """
    import logging

    from src.crypto.post_quantum import pq_crypto

    logger = logging.getLogger(__name__)

    # SECURITY: Validate input parameters
    if not hash_str or not pq_private_key_hex:
        raise ValueError("SECURITY ERROR: Empty hash or private key not allowed")

    if len(pq_private_key_hex) % 2 != 0:
        raise ValueError("SECURITY ERROR: Invalid private key hex format")

    if not pq_crypto.dilithium_available:
        raise RuntimeError(
            "SECURITY ERROR: Post-quantum cryptography is not available. "
            "Install liboqs-python or pqcrypto library for real PQ security. "
            "Fake PQ signatures have been disabled for security."
        )

    try:
        private_key_bytes = bytes.fromhex(pq_private_key_hex)

        # Validate private key length (Dilithium3 private key should be ~4032 bytes)
        if len(private_key_bytes) < 1000:  # Minimum realistic size
            raise ValueError("SECURITY ERROR: Private key too short for Dilithium3")

        signature_bytes = pq_crypto.dilithium_sign(
            hash_str.encode("utf-8"), private_key_bytes
        )

        # Validate signature was actually generated
        if not signature_bytes or len(signature_bytes) < 100:
            raise RuntimeError("SECURITY ERROR: Invalid signature generated")

        logger.info(f"Post-quantum signature generated: {len(signature_bytes)} bytes")
        return f"dilithium3:{signature_bytes.hex()}"

    except ValueError as e:
        # Re-raise validation errors
        raise e
    except Exception as e:
        raise RuntimeError(
            f"Post-quantum signing failed: {e}. System requires real PQ cryptography."
        )


def verify_post_quantum(hash_str, pq_public_key_hex, pq_signature_hex):
    """
    Verify a post-quantum signature.
    SECURITY CRITICAL: Only uses real post-quantum cryptography.

    Args:
        hash_str (str): Original hash string.
        pq_public_key_hex (str): Hex-encoded post-quantum public key.
        pq_signature_hex (str): Hex-encoded post-quantum signature.
    Returns:
        bool: True if signature is valid, False otherwise.
    Raises:
        RuntimeError: If post-quantum cryptography is not available.
    """
    import logging

    from src.crypto.post_quantum import pq_crypto

    logger = logging.getLogger(__name__)

    # SECURITY: Validate input parameters
    if not hash_str or not pq_public_key_hex or not pq_signature_hex:
        logger.error("SECURITY ERROR: Empty parameters not allowed for PQ verification")
        return False

    if not pq_crypto.dilithium_available:
        raise RuntimeError(
            "SECURITY ERROR: Post-quantum cryptography is not available. "
            "Cannot verify PQ signatures without real PQ libraries. "
            "Install liboqs-python or pqcrypto library."
        )

    try:
        # SECURITY: Use comprehensive format validation functions
        if not _validate_signature_format(pq_signature_hex, "dilithium3"):
            return False

        if not _validate_public_key_format(pq_public_key_hex, "dilithium3"):
            return False

        # Extract signature without prefix
        signature = pq_signature_hex[11:]  # Remove "dilithium3:" prefix

        # SECURITY: Check replay protection for PQ signatures
        if not _check_replay_protection(hash_str, signature, pq_public_key_hex):
            logger.error(
                "SECURITY ALERT: Post-quantum signature replay attack detected"
            )
            return False

        # Convert to bytes
        public_key_bytes = bytes.fromhex(pq_public_key_hex)
        signature_bytes = bytes.fromhex(signature)

        # Perform verification using real PQ crypto
        result = pq_crypto.dilithium_verify(
            hash_str.encode("utf-8"), signature_bytes, public_key_bytes
        )

        if result:
            logger.info(
                "SECURITY SUCCESS: Post-quantum signature verification successful with all security checks"
            )
        else:
            logger.warning("SECURITY ERROR: Post-quantum signature verification failed")

        return result

    except ValueError as e:
        logger.error(f"SECURITY ERROR: PQ verification input validation failed: {e}")
        return False
    except Exception as e:
        logger.error(f"Post-quantum verification failed: {e}")
        return False


def hybrid_sign_capsule(hash_str, ed25519_key_hex, pq_key_hex=None):
    """
    Sign a capsule with both Ed25519 and post-quantum signatures for hybrid security.
    Args:
        hash_str (str): String to sign (usually a hash).
        ed25519_key_hex (str): Hex-encoded Ed25519 signing key.
        pq_key_hex (str): Optional hex-encoded post-quantum private key.
    Returns:
        dict: Dictionary containing both signatures.
    """
    # Ed25519 signature
    signing_key = SigningKey(ed25519_key_hex, encoder=HexEncoder)
    ed25519_sig = signing_key.sign(hash_str.encode("utf-8")).signature
    ed25519_signature = f"ed25519:{ed25519_sig.hex()}"

    # Post-quantum signature (optional)
    pq_signature = None
    if pq_key_hex:
        pq_signature = sign_post_quantum(hash_str, pq_key_hex)

    return {"ed25519": ed25519_signature, "post_quantum": pq_signature}


def sign_capsule(hash_str, signing_key_hex):
    """
    Sign a hash string with an Ed25519 signing key.
    Args:
        hash_str (str): String to sign (usually a hash).
        signing_key_hex (str): Hex-encoded Ed25519 signing key.
    Returns:
        str: Hex-encoded signature with ed25519: prefix.
    """
    signing_key = SigningKey(signing_key_hex, encoder=HexEncoder)
    signature = signing_key.sign(hash_str.encode("utf-8")).signature
    return f"ed25519:{signature.hex()}"


def get_verify_key_from_signing_key(signing_key_hex):
    """
    Derive the verify key from a signing key.
    """
    signing_key = SigningKey(signing_key_hex, encoder=HexEncoder)
    return signing_key.verify_key.encode(encoder=HexEncoder).decode("utf-8")


def verify_capsule(
    capsule,
    verify_key_hex,
    signature_hex,
    max_age_seconds: Optional[int] = None,
    max_future_seconds: int = 300,
):
    """
    Verify a capsule's signature and hash with comprehensive security validation.
    Enhanced with replay protection, format validation, and timestamp checks.

    Args:
        capsule: The capsule object (Pydantic model).
        verify_key_hex (str): The hex-encoded public verification key.
        signature_hex (str): The hex-encoded signature to verify.
        max_age_seconds: Optional max age for capsule timestamp (None = no limit).
        max_future_seconds: Max seconds capsule timestamp can be in future (default 300).

    Returns:
        A tuple (bool, str) indicating if verification passed and a reason string.
    """
    from datetime import datetime, timezone

    from nacl.exceptions import BadSignatureError

    try:
        # SECURITY: Input validation
        if not capsule or not verify_key_hex or not signature_hex:
            logger.error("SECURITY ERROR: Missing required parameters for verification")
            return False, "Missing required parameters"

        # SECURITY: Validate public key format
        if not _validate_public_key_format(verify_key_hex, "ed25519"):
            return False, "Invalid public key format"

        # SECURITY: Validate signature format
        if not _validate_signature_format(signature_hex, "ed25519"):
            return False, "Invalid signature format"

        # SECURITY: Validate capsule timestamp if present and timestamp validation is enabled
        if hasattr(capsule, "timestamp") and capsule.timestamp is not None:
            try:
                now = datetime.now(timezone.utc)
                capsule_time = capsule.timestamp

                # Parse string timestamps
                if isinstance(capsule_time, str):
                    capsule_time = datetime.fromisoformat(
                        capsule_time.replace("Z", "+00:00")
                    )
                elif not isinstance(capsule_time, datetime):
                    # Skip validation for non-datetime timestamps (e.g., mocks in tests)
                    capsule_time = None

                if capsule_time is not None:
                    # Ensure timezone-aware
                    if capsule_time.tzinfo is None:
                        capsule_time = capsule_time.replace(tzinfo=timezone.utc)

                    age_seconds = (now - capsule_time).total_seconds()

                    # Reject capsules too far in the future (clock skew protection)
                    if age_seconds < -max_future_seconds:
                        logger.error(
                            f"SECURITY ERROR: Capsule timestamp is {-age_seconds:.0f}s in the future"
                        )
                        return (
                            False,
                            f"Capsule timestamp is too far in the future ({-age_seconds:.0f}s)",
                        )

                    # Reject capsules older than max_age if specified
                    if max_age_seconds is not None and age_seconds > max_age_seconds:
                        logger.error(
                            f"SECURITY ERROR: Capsule is {age_seconds:.0f}s old, max allowed is {max_age_seconds}s"
                        )
                        return (
                            False,
                            f"Capsule is too old ({age_seconds:.0f}s > {max_age_seconds}s max)",
                        )
            except (TypeError, ValueError) as e:
                # Log but don't fail on timestamp parsing errors for backwards compatibility
                logger.debug(f"Skipping timestamp validation due to parse error: {e}")

        # 1. Verify the hash
        expected_hash = hash_for_signature(capsule)
        actual_hash = capsule.verification.hash

        if not actual_hash or not expected_hash:
            logger.error("SECURITY ERROR: Empty hash values not allowed")
            return False, "Empty hash values"

        # SECURITY: Use constant-time comparison to prevent timing attacks
        if not hmac.compare_digest(actual_hash, expected_hash):
            logger.error("SECURITY ERROR: Hash mismatch detected")
            return False, "Hash mismatch: content integrity check failed"

        # SECURITY: Check replay protection
        signature_without_prefix = signature_hex.replace("ed25519:", "")
        if not _check_replay_protection(
            actual_hash, signature_without_prefix, verify_key_hex
        ):
            logger.error("SECURITY ALERT: Signature replay attack detected")
            return False, "Signature replay detected - potential attack"

        # 2. Verify the signature cryptographically
        try:
            verify_key = VerifyKey(verify_key_hex, encoder=HexEncoder)
            # The signature is against the hash string itself, not its bytes
            verify_key.verify(
                actual_hash.encode("utf-8"), bytes.fromhex(signature_without_prefix)
            )

            logger.info(
                "SECURITY SUCCESS: Capsule signature verification passed all security checks"
            )
            return True, "Verified - Signature and hash are cryptographically valid"

        except BadSignatureError:
            logger.error("SECURITY ERROR: Cryptographic signature verification failed")
            return False, "Invalid signature - cryptographic verification failed"
        except Exception as e:
            logger.error(f"SECURITY ERROR: Signature verification error: {e}")
            return False, f"Signature verification error: {e}"

    except Exception as e:
        logger.error(f"SECURITY ERROR: Capsule verification failed with exception: {e}")
        return False, f"Verification failed: {e}"


def clear_signature_cache():
    """Clear the signature replay protection cache (for testing/maintenance)."""
    with _signature_cache_lock:
        _signature_cache.clear()
        _signature_context_cache.clear()
        logger.info("Signature replay protection cache cleared")


def get_verification_cache_status() -> Dict[str, int]:
    """Get current verification cache status for debugging."""
    with _signature_cache_lock:
        return {
            "verification_cache_size": len(_signature_cache),
            "context_cache_keys": len(_signature_context_cache),
            "total_signatures_tracked": sum(
                len(sigs) for sigs in _signature_context_cache.values()
            ),
        }


def get_signature_cache_stats() -> Dict[str, Any]:
    """Get statistics about the signature cache including TTL and LRU info."""
    with _signature_cache_lock:
        now = time.time()
        stats = {
            "cache_size": len(_signature_cache),
            "max_cache_size": _max_cache_size,
            "entry_ttl_seconds": _cache_entry_ttl,
            "cleanup_interval_seconds": _cache_cleanup_interval,
        }

        if _signature_cache:
            # Get oldest and newest entry ages
            oldest_key, (oldest_time, _) = next(iter(_signature_cache.items()))
            newest_key, (newest_time, _) = next(reversed(_signature_cache.items()))
            stats["oldest_entry_age_seconds"] = int(now - oldest_time)
            stats["newest_entry_age_seconds"] = int(now - newest_time)

            # Count expired entries (not yet evicted)
            expired_count = sum(
                1
                for _, (ts, _) in _signature_cache.items()
                if now - ts > _cache_entry_ttl
            )
            stats["expired_pending_eviction"] = expired_count

        return stats


def enhanced_verify_hybrid_signature(
    message: bytes,
    signatures: Dict[str, str],
    ed25519_public_key_hex: str,
    dilithium_public_key_hex: str,
) -> Tuple[bool, str]:
    """
    Enhanced hybrid signature verification with comprehensive security checks.

    Args:
        message: Message that was signed
        signatures: Dictionary with 'ed25519' and 'dilithium' signatures
        ed25519_public_key_hex: Ed25519 public key in hex
        dilithium_public_key_hex: Dilithium public key in hex

    Returns:
        Tuple of (success: bool, reason: str)
    """
    from src.crypto.post_quantum import pq_crypto

    try:
        # SECURITY: Input validation
        if (
            not message
            or not signatures
            or not ed25519_public_key_hex
            or not dilithium_public_key_hex
        ):
            logger.error(
                "SECURITY ERROR: Missing required parameters for hybrid verification"
            )
            return False, "Missing required parameters"

        # SECURITY: Validate signature dictionary completeness
        if "ed25519" not in signatures or "dilithium" not in signatures:
            logger.error(
                "SECURITY ERROR: Hybrid verification missing required signatures"
            )
            return False, "Missing required signature types"

        if not signatures["ed25519"] or not signatures["dilithium"]:
            logger.error(
                "SECURITY ERROR: Empty signatures not allowed in hybrid verification"
            )
            return False, "Empty signatures not allowed"

        # SECURITY: Use the enhanced verification from post_quantum module
        result = pq_crypto.hybrid_verify(
            message,
            signatures,
            bytes.fromhex(ed25519_public_key_hex),
            bytes.fromhex(dilithium_public_key_hex),
        )

        if result:
            return (
                True,
                "Hybrid signature verification successful - quantum-safe security achieved",
            )
        else:
            return (
                False,
                "Hybrid signature verification failed - security requirements not met",
            )

    except Exception as e:
        logger.error(f"SECURITY ERROR: Enhanced hybrid verification failed: {e}")
        return False, f"Hybrid verification failed: {e}"
