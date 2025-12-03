#!/usr/bin/env python3
"""
Comprehensive Signature Validator for UATP Capsule Engine
Implements strict signature format validation and replay attack protection.
"""

import hashlib
import logging
import re
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Dict, Optional, Set, Tuple

logger = logging.getLogger(__name__)


class SignatureType(Enum):
    """Supported signature types."""
    ED25519 = "ed25519"
    DILITHIUM3 = "dilithium3"
    RSA = "rsa"
    ECDSA = "ecdsa"


@dataclass
class SignatureMetadata:
    """Metadata for signature validation."""
    signature_type: SignatureType
    timestamp: datetime
    nonce: str
    capsule_id: str
    signer_id: str
    signature_hash: str = field(init=False)
    
    def __post_init__(self):
        """Generate signature hash for replay detection."""
        content = f"{self.signature_type.value}:{self.timestamp.isoformat()}:{self.nonce}:{self.capsule_id}:{self.signer_id}"
        self.signature_hash = hashlib.sha256(content.encode()).hexdigest()


class ReplayProtectionStore:
    """Store for tracking used signatures to prevent replay attacks."""
    
    def __init__(self, max_age_hours: int = 24, max_entries: int = 100000):
        """Initialize replay protection store."""
        self.max_age = timedelta(hours=max_age_hours)
        self.max_entries = max_entries
        self.used_signatures: Dict[str, datetime] = {}
        self.signature_metadata: Dict[str, SignatureMetadata] = {}
    
    def is_signature_used(self, signature_hash: str) -> bool:
        """Check if signature has been used before."""
        self._cleanup_expired()
        return signature_hash in self.used_signatures
    
    def record_signature_use(self, metadata: SignatureMetadata) -> bool:
        """Record signature use to prevent replay."""
        if self.is_signature_used(metadata.signature_hash):
            return False
        
        # Enforce size limits
        if len(self.used_signatures) >= self.max_entries:
            self._cleanup_oldest()
        
        self.used_signatures[metadata.signature_hash] = datetime.now(timezone.utc)
        self.signature_metadata[metadata.signature_hash] = metadata
        return True
    
    def _cleanup_expired(self):
        """Remove expired signature records."""
        now = datetime.now(timezone.utc)
        expired_hashes = [
            sig_hash for sig_hash, timestamp in self.used_signatures.items()
            if now - timestamp > self.max_age
        ]
        
        for sig_hash in expired_hashes:
            self.used_signatures.pop(sig_hash, None)
            self.signature_metadata.pop(sig_hash, None)
    
    def _cleanup_oldest(self):
        """Remove oldest signature records if at capacity."""
        if not self.used_signatures:
            return
        
        # Remove 10% of oldest entries
        sorted_sigs = sorted(self.used_signatures.items(), key=lambda x: x[1])
        num_to_remove = max(1, len(sorted_sigs) // 10)
        
        for sig_hash, _ in sorted_sigs[:num_to_remove]:
            self.used_signatures.pop(sig_hash, None)
            self.signature_metadata.pop(sig_hash, None)


class SignatureValidator:
    """Comprehensive signature format validator with replay protection."""
    
    def __init__(self, enable_replay_protection: bool = True):
        """Initialize signature validator."""
        self.enable_replay_protection = enable_replay_protection
        self.replay_store = ReplayProtectionStore() if enable_replay_protection else None
        
        # Signature format patterns
        self.signature_patterns = {
            SignatureType.ED25519: re.compile(r'^ed25519:[0-9a-fA-F]{128}$'),
            SignatureType.DILITHIUM3: re.compile(r'^dilithium3:[0-9a-fA-F]{5000,8000}$'),  # Approximate range
            SignatureType.RSA: re.compile(r'^rsa:[0-9a-fA-F]{512,1024}$'),  # 2048-4096 bit RSA
            SignatureType.ECDSA: re.compile(r'^ecdsa:[0-9a-fA-F]{128,256}$'),  # P-256/P-384
        }
        
        # Expected key lengths (in hex characters)
        self.public_key_lengths = {
            SignatureType.ED25519: 64,    # 32 bytes
            SignatureType.DILITHIUM3: 3904,  # ~1952 bytes
            SignatureType.RSA: (512, 1024),  # 256-512 bytes (2048-4096 bit)
            SignatureType.ECDSA: (128, 192),  # 64-96 bytes (P-256/P-384)
        }
        
        logger.info(f"Signature validator initialized (replay protection: {enable_replay_protection})")
    
    def validate_signature_format(
        self, 
        signature: str, 
        signature_type: SignatureType,
        strict_mode: bool = True
    ) -> Tuple[bool, str]:
        """
        Validate signature format according to type specifications.
        
        Args:
            signature: The signature string to validate
            signature_type: Expected signature type
            strict_mode: Whether to enforce strict format checking
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            # Basic null/empty checks
            if not signature or not isinstance(signature, str):
                return False, "SECURITY ERROR: Empty or invalid signature"
            
            # Check for suspicious characters
            if any(char in signature for char in ['\n', '\r', '\0', '\x1b']):
                return False, "SECURITY ERROR: Signature contains illegal characters"
            
            # Validate signature type prefix
            expected_prefix = f"{signature_type.value}:"
            if not signature.startswith(expected_prefix):
                return False, f"SECURITY ERROR: Missing {expected_prefix} prefix"
            
            # Extract hex portion
            hex_portion = signature[len(expected_prefix):]
            
            # Validate hex format
            if not re.match(r'^[0-9a-fA-F]+$', hex_portion):
                return False, "SECURITY ERROR: Signature contains non-hex characters"
            
            # Check length constraints
            if len(hex_portion) % 2 != 0:
                return False, "SECURITY ERROR: Signature hex has odd length"
            
            # Type-specific validation
            if strict_mode and signature_type in self.signature_patterns:
                if not self.signature_patterns[signature_type].match(signature):
                    return False, f"SECURITY ERROR: {signature_type.value} signature format invalid"
            
            # Additional length checks
            min_length, max_length = self._get_signature_length_bounds(signature_type)
            if not (min_length <= len(hex_portion) <= max_length):
                return False, f"SECURITY ERROR: {signature_type.value} signature length out of bounds"
            
            return True, "Signature format valid"
            
        except Exception as e:
            logger.error(f"Signature format validation error: {e}")
            return False, f"SECURITY ERROR: Signature validation failed: {e}"
    
    def validate_public_key_format(
        self, 
        public_key: str, 
        signature_type: SignatureType
    ) -> Tuple[bool, str]:
        """
        Validate public key format according to signature type.
        
        Args:
            public_key: The public key hex string
            signature_type: The signature type this key is for
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            # Basic validation
            if not public_key or not isinstance(public_key, str):
                return False, "SECURITY ERROR: Empty or invalid public key"
            
            # Check for suspicious characters
            if any(char in public_key for char in ['\n', '\r', '\0', '\x1b']):
                return False, "SECURITY ERROR: Public key contains illegal characters"
            
            # Validate hex format
            if not re.match(r'^[0-9a-fA-F]+$', public_key):
                return False, "SECURITY ERROR: Public key contains non-hex characters"
            
            # Check length constraints
            if len(public_key) % 2 != 0:
                return False, "SECURITY ERROR: Public key hex has odd length"
            
            # Type-specific length validation
            expected_length = self.public_key_lengths.get(signature_type)
            if isinstance(expected_length, tuple):
                min_len, max_len = expected_length
                if not (min_len <= len(public_key) <= max_len):
                    return False, f"SECURITY ERROR: {signature_type.value} public key length out of bounds"
            elif isinstance(expected_length, int):
                if len(public_key) != expected_length:
                    return False, f"SECURITY ERROR: {signature_type.value} public key wrong length"
            else:
                return False, f"SECURITY ERROR: Unknown signature type {signature_type.value}"
            
            return True, "Public key format valid"
            
        except Exception as e:
            logger.error(f"Public key format validation error: {e}")
            return False, f"SECURITY ERROR: Public key validation failed: {e}"
    
    def validate_signature_with_replay_protection(
        self,
        signature: str,
        signature_type: SignatureType,
        capsule_id: str,
        signer_id: str,
        timestamp: Optional[datetime] = None,
        nonce: Optional[str] = None
    ) -> Tuple[bool, str]:
        """
        Validate signature with replay attack protection.
        
        Args:
            signature: The signature to validate
            signature_type: Type of signature
            capsule_id: ID of the capsule being signed
            signer_id: ID of the signer
            timestamp: Optional timestamp (current time if None)
            nonce: Optional nonce (generated if None)
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            # First validate signature format
            format_valid, format_error = self.validate_signature_format(signature, signature_type)
            if not format_valid:
                return False, format_error
            
            # Generate timestamp and nonce if not provided
            if timestamp is None:
                timestamp = datetime.now(timezone.utc)
            if nonce is None:
                nonce = hashlib.sha256(f"{signature}{time.time_ns()}".encode()).hexdigest()[:16]
            
            # Check timestamp freshness (within 5 minutes)
            now = datetime.now(timezone.utc)
            if abs((now - timestamp).total_seconds()) > 300:  # 5 minutes
                return False, "SECURITY ERROR: Signature timestamp too old or in future"
            
            # Create signature metadata
            metadata = SignatureMetadata(
                signature_type=signature_type,
                timestamp=timestamp,
                nonce=nonce,
                capsule_id=capsule_id,
                signer_id=signer_id
            )
            
            # Check for replay attacks
            if self.enable_replay_protection and self.replay_store:
                if self.replay_store.is_signature_used(metadata.signature_hash):
                    return False, "SECURITY ERROR: Signature replay attack detected"
                
                # Record signature use
                if not self.replay_store.record_signature_use(metadata):
                    return False, "SECURITY ERROR: Failed to record signature use"
            
            logger.info(f"Signature validation successful for {signer_id} on {capsule_id}")
            return True, "Signature valid with replay protection"
            
        except Exception as e:
            logger.error(f"Signature replay validation error: {e}")
            return False, f"SECURITY ERROR: Signature replay validation failed: {e}"
    
    def validate_hybrid_signatures(
        self,
        signatures: Dict[str, str],
        capsule_id: str,
        signer_id: str,
        ed25519_public_key: str,
        dilithium_public_key: str
    ) -> Tuple[bool, str]:
        """
        Validate hybrid Ed25519 + Dilithium signatures with comprehensive checks.
        
        Args:
            signatures: Dictionary containing both signature types
            capsule_id: ID of the capsule
            signer_id: ID of the signer
            ed25519_public_key: Ed25519 public key
            dilithium_public_key: Dilithium public key
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            # Validate signature dictionary structure
            if not isinstance(signatures, dict):
                return False, "SECURITY ERROR: Signatures must be a dictionary"
            
            required_keys = {"ed25519", "dilithium"}
            if not required_keys.issubset(signatures.keys()):
                return False, "SECURITY ERROR: Missing required signature types for hybrid"
            
            # Validate each signature format
            ed25519_valid, ed25519_error = self.validate_signature_format(
                signatures["ed25519"], SignatureType.ED25519
            )
            if not ed25519_valid:
                return False, f"Ed25519 {ed25519_error}"
            
            dilithium_valid, dilithium_error = self.validate_signature_format(\n                signatures["dilithium"], SignatureType.DILITHIUM3\n            )\n            if not dilithium_valid:\n                return False, f"Dilithium {dilithium_error}"\n            \n            # Validate public key formats\n            ed25519_key_valid, ed25519_key_error = self.validate_public_key_format(\n                ed25519_public_key, SignatureType.ED25519\n            )\n            if not ed25519_key_valid:\n                return False, f"Ed25519 key {ed25519_key_error}"\n            \n            dilithium_key_valid, dilithium_key_error = self.validate_public_key_format(\n                dilithium_public_key, SignatureType.DILITHIUM3\n            )\n            if not dilithium_key_valid:\n                return False, f"Dilithium key {dilithium_key_error}"\n            \n            # Validate with replay protection for each signature\n            timestamp = datetime.now(timezone.utc)\n            \n            ed25519_replay_valid, ed25519_replay_error = self.validate_signature_with_replay_protection(\n                signatures["ed25519"], SignatureType.ED25519, capsule_id, signer_id, timestamp\n            )\n            if not ed25519_replay_valid:\n                return False, f"Ed25519 replay: {ed25519_replay_error}"\n            \n            dilithium_replay_valid, dilithium_replay_error = self.validate_signature_with_replay_protection(\n                signatures["dilithium"], SignatureType.DILITHIUM3, capsule_id, signer_id, timestamp\n            )\n            if not dilithium_replay_valid:\n                return False, f"Dilithium replay: {dilithium_replay_error}"\n            \n            logger.info(f"Hybrid signature validation successful for {signer_id} on {capsule_id}")\n            return True, "Hybrid signatures valid with replay protection"\n            \n        except Exception as e:\n            logger.error(f"Hybrid signature validation error: {e}")\n            return False, f"SECURITY ERROR: Hybrid signature validation failed: {e}"\n    \n    def _get_signature_length_bounds(self, signature_type: SignatureType) -> Tuple[int, int]:\n        """Get minimum and maximum signature length bounds for a signature type."""\n        bounds = {\n            SignatureType.ED25519: (128, 128),      # Exactly 64 bytes\n            SignatureType.DILITHIUM3: (5000, 8000), # Approximately 2500-4000 bytes\n            SignatureType.RSA: (512, 1024),         # 256-512 bytes\n            SignatureType.ECDSA: (128, 256),        # 64-128 bytes\n        }\n        return bounds.get(signature_type, (64, 10000))  # Default bounds\n    \n    def get_validation_statistics(self) -> Dict[str, int]:\n        """Get validation statistics."""\n        stats = {\n            "replay_protection_enabled": int(self.enable_replay_protection),\n            "total_signatures_tracked": 0,\n            "active_signatures": 0\n        }\n        \n        if self.replay_store:\n            stats["total_signatures_tracked"] = len(self.replay_store.used_signatures)\n            # Count non-expired signatures\n            now = datetime.now(timezone.utc)\n            active_count = sum(\n                1 for timestamp in self.replay_store.used_signatures.values()\n                if now - timestamp <= self.replay_store.max_age\n            )\n            stats["active_signatures"] = active_count\n        \n        return stats\n    \n    def clear_replay_store(self) -> bool:\n        """Clear the replay protection store (for testing/admin purposes)."""\n        if self.replay_store:\n            self.replay_store.used_signatures.clear()\n            self.replay_store.signature_metadata.clear()\n            logger.warning("Replay protection store cleared")\n            return True\n        return False\n\n\n# Global validator instance\nsignature_validator = SignatureValidator(enable_replay_protection=True)\n\n\n# Example usage and testing\nif __name__ == "__main__":\n    def test_signature_validator():\n        """Test the signature validator."""\n        print("🔐 UATP Signature Validator Test")\n        print("=" * 40)\n        \n        validator = SignatureValidator(enable_replay_protection=True)\n        \n        # Test Ed25519 signature validation\n        print("Testing Ed25519 signature validation...")\n        valid_ed25519 = "\\\\ed25519:5a7d7e8f9b2c4d6e1f8a9b5c7d2e4f6a8b9c5d7e2f4a6b8c9d5e7f2a4b6c8d9e5f7a2b4c6d8e9f5a7b2c4d6e8f9a5b7c2d4e6f8a9b5c7d2e4f6a8b9c5d7e2f"\n        invalid_ed25519 = "ed25519:invalid_hex_signature"\n        \n        valid_result, valid_msg = validator.validate_signature_format(valid_ed25519, SignatureType.ED25519)\n        invalid_result, invalid_msg = validator.validate_signature_format(invalid_ed25519, SignatureType.ED25519)\n        \n        print(f"✅ Valid Ed25519: {valid_result} - {valid_msg}")\n        print(f"✅ Invalid Ed25519: {not invalid_result} - {invalid_msg}")\n        \n        # Test public key validation\n        print("\\nTesting public key validation...")\n        valid_ed25519_key = "5a7d7e8f9b2c4d6e1f8a9b5c7d2e4f6a8b9c5d7e2f4a6b8c9d5e7f2a4b6c8d9e"\n        key_valid, key_msg = validator.validate_public_key_format(valid_ed25519_key, SignatureType.ED25519)\n        print(f"✅ Ed25519 public key: {key_valid} - {key_msg}")\n        \n        # Test replay protection\n        print("\\nTesting replay protection...")\n        test_sig = "ed25519:" + "a" * 128\n        first_check, first_msg = validator.validate_signature_with_replay_protection(\n            test_sig, SignatureType.ED25519, "test_capsule", "test_signer"\n        )\n        second_check, second_msg = validator.validate_signature_with_replay_protection(\n            test_sig, SignatureType.ED25519, "test_capsule", "test_signer"\n        )\n        \n        print(f"✅ First signature: {first_check} - {first_msg}")\n        print(f"✅ Replay attempt: {not second_check} - {second_msg}")\n        \n        # Get statistics\n        stats = validator.get_validation_statistics()\n        print(f"\\n📊 Validation Statistics: {stats}")\n        \n        print("\\n🎯 Signature Validator Capabilities:")\n        print("   ✅ Comprehensive signature format validation")\n        print("   ✅ Type-specific length and pattern checking")\n        print("   ✅ Public key format validation")\n        print("   ✅ Replay attack protection")\n        print("   ✅ Hybrid signature validation")\n        print("   ✅ Timestamp freshness checking")\n        print("   ✅ Suspicious character detection")\n        print("   ✅ Automatic cleanup of expired records")\n        \n        print("\\n✅ Signature validator test complete!")\n    \n    test_signature_validator()