"""
Real Post-Quantum Cryptography Implementation for UATP 7.0
Using actual Dilithium signatures and Kyber key exchange
"""

import hashlib
import logging
import secrets
from dataclasses import dataclass
from typing import Dict, Tuple

logger = logging.getLogger(__name__)


@dataclass
class PQKeyPair:
    """Post-quantum key pair container."""

    private_key: bytes
    public_key: bytes
    algorithm: str
    key_size: int


class PostQuantumCrypto:
    """Real post-quantum cryptography implementation."""

    def __init__(self):
        self.dilithium_available = False
        self.kyber_available = False
        self._init_libraries()

    def _init_libraries(self):
        """Initialize post-quantum cryptography libraries."""
        # Set library path for macOS (SIP strips DYLD_LIBRARY_PATH for security)
        import os
        import sys

        # In development mode, skip PQ crypto if liboqs is not available
        # This prevents the oqs package from auto-installing and hanging
        liboqs_path = os.path.join(os.path.expanduser("~"), "_oqs", "lib")
        is_development = os.getenv("ENVIRONMENT") == "development" or os.getenv("UATP_ENV") != "production"

        if is_development and not os.path.exists(liboqs_path):
            logger.info("Development mode: liboqs not found, using secure simulation (PQ crypto enforced in production only)")
            self.dilithium_available = False
            self.kyber_available = False
            return

        # Configure liboqs library path before importing
        if os.path.exists(liboqs_path):
            # Set environment variable (for child processes)
            os.environ["DYLD_LIBRARY_PATH"] = liboqs_path + ":" + os.environ.get("DYLD_LIBRARY_PATH", "")
            # Also set for current process (Python's ctypes uses this on macOS)
            if hasattr(sys, "setdlopenflags"):
                # Set RTLD_GLOBAL so libraries can find each other
                import ctypes
                sys.setdlopenflags(sys.getdlopenflags() | ctypes.RTLD_GLOBAL)

        # Try to import real PQ libraries
        try:
            # Try pqcrypto library with standardized algorithms first
            import pqcrypto.kem.ml_kem_768
            import pqcrypto.sign.ml_dsa_65

            self.ml_dsa_65 = pqcrypto.sign.ml_dsa_65
            self.ml_kem_768 = pqcrypto.kem.ml_kem_768
            self.dilithium_available = True
            self.kyber_available = True
            logger.info(
                "Using pqcrypto library with NIST-standardized ML-DSA-65 and ML-KEM-768"
            )
        except (ImportError, OSError) as e:
            try:
                # Configure oqs to use our compiled library
                os.environ["OQS_INSTALL_PATH"] = os.path.join(os.path.expanduser("~"), "_oqs")

                # Try liboqs-python as fallback (most comprehensive but requires compilation)
                import oqs

                self.oqs = oqs
                self.dilithium_available = True
                self.kyber_available = True
                logger.info("Using liboqs-python for post-quantum crypto")
            except (ImportError, OSError) as e:
                try:
                    # Try pqcrypto library with legacy names
                    import pqcrypto.kem.kyber768
                    import pqcrypto.sign.dilithium3

                    self.dilithium3 = pqcrypto.sign.dilithium3
                    self.kyber768 = pqcrypto.kem.kyber768
                    self.dilithium_available = True
                    self.kyber_available = True
                    logger.info("Using pqcrypto library for post-quantum crypto")
                except (ImportError, OSError) as e:
                    # Fallback to cryptographically secure simulation
                    logger.warning(f"No PQ libraries found ({e}), using secure simulation")
                    self.dilithium_available = False
                    self.kyber_available = False

        # SECURITY: Enforce strict mode in production
        import os

        if os.getenv("UATP_ENV") == "production" and not (
            self.dilithium_available and self.kyber_available
        ):
            logger.critical(
                "SECURITY FAILURE: Real post-quantum libraries missing in production environment."
            )
            raise SystemExit(
                "CRITICAL SECURITY FAILURE: Real PQ libraries missing in production. System halted."
            )

    def generate_dilithium_keypair(self) -> PQKeyPair:
        """Generate a Dilithium3 signature keypair."""
        if self.dilithium_available and hasattr(self, "ml_dsa_65"):
            # Use pqcrypto with NIST-standardized ML-DSA-65
            try:
                public_key, private_key = self.ml_dsa_65.generate_keypair()
                return PQKeyPair(
                    private_key=private_key,
                    public_key=public_key,
                    algorithm="ML-DSA-65",
                    key_size=len(private_key),
                )
            except Exception as e:
                logger.error(f"Failed to generate ML-DSA keypair: {e}")

        elif self.dilithium_available and hasattr(self, "oqs"):
            # Use liboqs-python
            try:
                sig = self.oqs.Signature("Dilithium3")
                public_key = sig.generate_keypair()
                private_key = sig.export_secret_key()
                return PQKeyPair(
                    private_key=private_key,
                    public_key=public_key,
                    algorithm="Dilithium3",
                    key_size=len(private_key),
                )
            except Exception as e:
                logger.error(f"Failed to generate Dilithium keypair: {e}")

        elif self.dilithium_available and hasattr(self, "dilithium3"):
            # Use pqcrypto legacy
            try:
                public_key, private_key = self.dilithium3.keypair()
                return PQKeyPair(
                    private_key=private_key,
                    public_key=public_key,
                    algorithm="Dilithium3",
                    key_size=len(private_key),
                )
            except Exception as e:
                logger.error(f"Failed to generate Dilithium keypair: {e}")

        # SECURITY: Disable fallback keypair generation
        raise RuntimeError(
            "SECURITY ERROR: Post-quantum cryptography libraries not available. "
            "Cannot generate fake Dilithium keypairs. Install liboqs-python or pqcrypto "
            "for real post-quantum security."
        )

    def generate_kyber_keypair(self) -> PQKeyPair:
        """Generate a Kyber768 KEM keypair."""
        if self.kyber_available and hasattr(self, "ml_kem_768"):
            # Use pqcrypto with NIST-standardized ML-KEM-768
            try:
                public_key, private_key = self.ml_kem_768.generate_keypair()
                return PQKeyPair(
                    private_key=private_key,
                    public_key=public_key,
                    algorithm="ML-KEM-768",
                    key_size=len(private_key),
                )
            except Exception as e:
                logger.error(f"Failed to generate ML-KEM keypair: {e}")

        elif self.kyber_available and hasattr(self, "oqs"):
            try:
                kem = self.oqs.KeyEncapsulation("Kyber768")
                public_key = kem.generate_keypair()
                private_key = kem.export_secret_key()
                return PQKeyPair(
                    private_key=private_key,
                    public_key=public_key,
                    algorithm="Kyber768",
                    key_size=len(private_key),
                )
            except Exception as e:
                logger.error(f"Failed to generate Kyber keypair: {e}")

        elif self.kyber_available and hasattr(self, "kyber768"):
            try:
                public_key, private_key = self.kyber768.keypair()
                return PQKeyPair(
                    private_key=private_key,
                    public_key=public_key,
                    algorithm="Kyber768",
                    key_size=len(private_key),
                )
            except Exception as e:
                logger.error(f"Failed to generate Kyber keypair: {e}")

        # SECURITY: Disable fallback keypair generation
        raise RuntimeError(
            "SECURITY ERROR: Post-quantum cryptography libraries not available. "
            "Cannot generate fake Kyber keypairs. Install liboqs-python or pqcrypto "
            "for real post-quantum security."
        )

    def _generate_secure_fallback_keypair(self, algorithm: str) -> PQKeyPair:
        """DISABLED: Fallback keypair generation creates fake PQ keys."""
        raise RuntimeError(
            "SECURITY ERROR: Post-quantum cryptography libraries not available. "
            "Fallback keypair generation disabled to prevent fake PQ keys. "
            "Install liboqs-python or pqcrypto for real post-quantum security."
        )

    def dilithium_sign(self, message: bytes, private_key: bytes) -> bytes:
        """Sign a message with Dilithium3."""
        if self.dilithium_available and hasattr(self, "ml_dsa_65"):
            # Use pqcrypto with NIST-standardized ML-DSA-65
            try:
                return self.ml_dsa_65.sign(private_key, message)
            except Exception as e:
                logger.error(f"ML-DSA signing failed: {e}")

        elif self.dilithium_available and hasattr(self, "oqs"):
            try:
                sig = self.oqs.Signature("Dilithium3")
                sig.import_secret_key(private_key)
                return sig.sign(message)
            except Exception as e:
                logger.error(f"Dilithium signing failed: {e}")

        elif self.dilithium_available and hasattr(self, "dilithium3"):
            try:
                return self.dilithium3.sign(message, private_key)
            except Exception as e:
                logger.error(f"Dilithium signing failed: {e}")

        # SECURITY: Disable fallback signing
        raise RuntimeError(
            "SECURITY ERROR: Post-quantum cryptography libraries not available. "
            "Cannot create fake Dilithium signatures. Install liboqs-python or pqcrypto."
        )

    def dilithium_verify(
        self, message: bytes, signature: bytes, public_key: bytes
    ) -> bool:
        """Verify a Dilithium3 signature."""
        if self.dilithium_available and hasattr(self, "ml_dsa_65"):
            # Use pqcrypto with NIST-standardized ML-DSA-65
            try:
                return self.ml_dsa_65.verify(public_key, message, signature)
            except Exception as e:
                logger.error(f"ML-DSA verification failed: {e}")
                return False

        elif self.dilithium_available and hasattr(self, "oqs"):
            try:
                sig = self.oqs.Signature("Dilithium3")
                sig.import_public_key(public_key)
                return sig.verify(message, signature, public_key)
            except Exception as e:
                logger.error(f"Dilithium verification failed: {e}")
                return False

        elif self.dilithium_available and hasattr(self, "dilithium3"):
            try:
                return self.dilithium3.verify(signature, message, public_key)
            except Exception as e:
                logger.error(f"Dilithium verification failed: {e}")
                return False

        # SECURITY: Disable fallback verification
        logger.error(
            "SECURITY ERROR: Post-quantum cryptography libraries not available. "
            "Cannot verify Dilithium signatures without real PQ libraries."
        )
        return False

    def _secure_fallback_sign(self, message: bytes, private_key: bytes) -> bytes:
        """DISABLED: Fallback signing creates fake PQ signatures."""
        raise RuntimeError(
            "SECURITY ERROR: Post-quantum cryptography libraries not available. "
            "Cannot create fake PQ signatures. Install liboqs-python or pqcrypto."
        )

    def _secure_fallback_verify(
        self, message: bytes, signature: bytes, public_key: bytes
    ) -> bool:
        """DISABLED: Fallback verification accepts fake PQ signatures."""
        logger.error(
            "SECURITY ERROR: Post-quantum cryptography libraries not available. "
            "Cannot verify real PQ signatures. Install liboqs-python or pqcrypto."
        )
        return False

    def kyber_encapsulate(self, public_key: bytes) -> Tuple[bytes, bytes]:
        """Encapsulate a shared secret using Kyber768."""
        if self.kyber_available and hasattr(self, "ml_kem_768"):
            # Use pqcrypto with NIST-standardized ML-KEM-768
            try:
                ciphertext, shared_secret = self.ml_kem_768.encrypt(public_key)
                return ciphertext, shared_secret
            except Exception as e:
                logger.error(f"ML-KEM encapsulation failed: {e}")

        elif self.kyber_available and hasattr(self, "oqs"):
            try:
                kem = self.oqs.KeyEncapsulation("Kyber768")
                kem.import_public_key(public_key)
                ciphertext, shared_secret = kem.encap_secret(public_key)
                return ciphertext, shared_secret
            except Exception as e:
                logger.error(f"Kyber encapsulation failed: {e}")

        elif self.kyber_available and hasattr(self, "kyber768"):
            try:
                return self.kyber768.encaps(public_key)
            except Exception as e:
                logger.error(f"Kyber encapsulation failed: {e}")

        # SECURITY: Disable fallback key encapsulation
        raise RuntimeError(
            "SECURITY ERROR: Post-quantum cryptography libraries not available. "
            "Cannot perform fake Kyber encapsulation. Install liboqs-python or pqcrypto."
        )

    def kyber_decapsulate(self, ciphertext: bytes, private_key: bytes) -> bytes:
        """Decapsulate a shared secret using Kyber768."""
        if self.kyber_available and hasattr(self, "ml_kem_768"):
            # Use pqcrypto with NIST-standardized ML-KEM-768
            try:
                return self.ml_kem_768.decrypt(private_key, ciphertext)
            except Exception as e:
                logger.error(f"ML-KEM decapsulation failed: {e}")

        elif self.kyber_available and hasattr(self, "oqs"):
            try:
                kem = self.oqs.KeyEncapsulation("Kyber768")
                kem.import_secret_key(private_key)
                return kem.decap_secret(ciphertext)
            except Exception as e:
                logger.error(f"Kyber decapsulation failed: {e}")

        elif self.kyber_available and hasattr(self, "kyber768"):
            try:
                return self.kyber768.decaps(ciphertext, private_key)
            except Exception as e:
                logger.error(f"Kyber decapsulation failed: {e}")

        # SECURITY: Disable fallback key decapsulation
        raise RuntimeError(
            "SECURITY ERROR: Post-quantum cryptography libraries not available. "
            "Cannot perform fake Kyber decapsulation. Install liboqs-python or pqcrypto."
        )

    def hybrid_sign(
        self, message: bytes, ed25519_private: bytes, dilithium_private: bytes
    ) -> Dict[str, str]:
        """Create hybrid Ed25519 + Dilithium signature."""
        from nacl.encoding import HexEncoder
        from nacl.signing import SigningKey

        # Ed25519 signature
        ed25519_key = SigningKey(ed25519_private, encoder=HexEncoder)
        ed25519_sig = ed25519_key.sign(message).signature

        # Dilithium signature
        dilithium_sig = self.dilithium_sign(message, dilithium_private)

        return {
            "ed25519": f"ed25519:{ed25519_sig.hex()}",
            "dilithium": f"dilithium3:{dilithium_sig.hex()}",
        }

    def hybrid_verify(
        self,
        message: bytes,
        signatures: Dict[str, str],
        ed25519_public: bytes,
        dilithium_public: bytes,
    ) -> bool:
        """Verify hybrid Ed25519 + Dilithium signature."""
        from nacl.encoding import HexEncoder
        from nacl.signing import VerifyKey

        try:
            # SECURITY: Validate signature dictionary completeness
            if "ed25519" not in signatures or "dilithium" not in signatures:
                logger.error("Hybrid verification failed: missing required signatures")
                return False

            if not signatures["ed25519"] or not signatures["dilithium"]:
                logger.error("Hybrid verification failed: empty signatures not allowed")
                return False

            # Verify Ed25519 signature format and validity
            if not signatures["ed25519"].startswith("ed25519:"):
                logger.error(
                    "Hybrid verification failed: invalid Ed25519 signature format"
                )
                return False

            ed25519_sig_hex = signatures["ed25519"].replace("ed25519:", "")
            if len(ed25519_sig_hex) % 2 != 0:
                logger.error(
                    "Hybrid verification failed: invalid Ed25519 signature hex"
                )
                return False

            # SECURITY: Validate Ed25519 signature length (should be exactly 64 bytes)
            if len(ed25519_sig_hex) != 128:  # 64 bytes = 128 hex characters
                logger.error(
                    "Hybrid verification failed: invalid Ed25519 signature length"
                )
                return False

            try:
                ed25519_sig = bytes.fromhex(ed25519_sig_hex)
                ed25519_key = VerifyKey(ed25519_public, encoder=HexEncoder)
                ed25519_key.verify(message, ed25519_sig)
                ed25519_valid = True
                logger.debug("Ed25519 signature verification passed")
            except Exception as e:
                logger.error(f"Ed25519 signature verification failed: {e}")
                ed25519_valid = False

            # Verify Dilithium signature format and validity
            if not signatures["dilithium"].startswith("dilithium3:"):
                logger.error(
                    "Hybrid verification failed: invalid Dilithium signature format"
                )
                return False

            dilithium_sig_hex = signatures["dilithium"].replace("dilithium3:", "")
            if len(dilithium_sig_hex) % 2 != 0:
                logger.error(
                    "Hybrid verification failed: invalid Dilithium signature hex"
                )
                return False

            # SECURITY: Validate Dilithium signature length (should be substantial)
            if (
                len(dilithium_sig_hex) < 4000
            ):  # Dilithium3 signatures should be ~3293 bytes
                logger.error(
                    "Hybrid verification failed: Dilithium signature too short"
                )
                return False

            try:
                dilithium_sig = bytes.fromhex(dilithium_sig_hex)
                dilithium_valid = self.dilithium_verify(
                    message, dilithium_sig, dilithium_public
                )
                if dilithium_valid:
                    logger.debug("Dilithium signature verification passed")
                else:
                    logger.error("Dilithium signature verification failed")
            except Exception as e:
                logger.error(
                    f"Dilithium signature verification failed with exception: {e}"
                )
                dilithium_valid = False

            # SECURITY CRITICAL: Both signatures MUST be valid for hybrid security
            if not ed25519_valid:
                logger.error(
                    "SECURITY FAILURE: Hybrid verification failed - Ed25519 signature invalid. "
                    "Hybrid security requires BOTH signatures to be valid."
                )
                return False

            if not dilithium_valid:
                logger.error(
                    "SECURITY FAILURE: Hybrid verification failed - Dilithium signature invalid. "
                    "Hybrid security requires BOTH signatures to be valid."
                )
                return False

            logger.info(
                "SECURITY SUCCESS: Hybrid verification successful - both Ed25519 and Dilithium signatures valid. "
                "This capsule is protected against both classical and quantum attacks."
            )
            return True

        except Exception as e:
            logger.error(f"Hybrid verification failed with exception: {e}")
            return False


# Global instance
pq_crypto = PostQuantumCrypto()
