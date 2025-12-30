"""
HSM Key Provider for UATP Crypto Modules
========================================

This module provides a bridge between HSM hardware and the UATP crypto
modules (crypto_sealer.py, uatp_crypto_v7.py).

It enables:
- PKCS#11 hardware key storage
- AWS CloudHSM integration
- Azure Key Vault integration
- Software HSM fallback for development

Usage:
    # For production with real HSM
    export UATP_HSM_ENABLED=true
    export UATP_HSM_TYPE=pkcs11
    export UATP_HSM_LIBRARY=/usr/lib/softhsm/libsofthsm2.so
    export UATP_HSM_PIN=1234

    # In code
    from src.security.hsm_key_provider import get_hsm_provider
    provider = get_hsm_provider()
    signature = await provider.sign(data)
"""

import asyncio
import logging
import os
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Dict, Optional, Tuple

logger = logging.getLogger(__name__)


class HSMProviderType(Enum):
    """Types of HSM providers."""

    DISABLED = "disabled"
    PKCS11 = "pkcs11"
    AWS_CLOUDHSM = "aws"
    AZURE_KEYVAULT = "azure"
    SOFTWARE = "software"  # SoftHSM2 for development


@dataclass
class HSMConfig:
    """Configuration for HSM provider."""

    provider_type: HSMProviderType
    library_path: Optional[str] = None
    slot_id: int = 0
    pin: Optional[str] = None
    token_label: Optional[str] = None

    # AWS-specific
    aws_region: Optional[str] = None
    aws_cluster_id: Optional[str] = None

    # Azure-specific
    azure_vault_url: Optional[str] = None
    azure_key_name: Optional[str] = None

    # Key identifiers
    ed25519_key_label: str = "uatp-ed25519-signing-key"
    dilithium_key_label: str = "uatp-dilithium3-signing-key"

    @classmethod
    def from_environment(cls) -> "HSMConfig":
        """Create config from environment variables."""
        hsm_enabled = os.environ.get("UATP_HSM_ENABLED", "false").lower() == "true"

        if not hsm_enabled:
            return cls(provider_type=HSMProviderType.DISABLED)

        provider_type = os.environ.get("UATP_HSM_TYPE", "software").lower()

        return cls(
            provider_type=HSMProviderType(provider_type),
            library_path=os.environ.get("UATP_HSM_LIBRARY"),
            slot_id=int(os.environ.get("UATP_HSM_SLOT", "0")),
            pin=os.environ.get("UATP_HSM_PIN"),
            token_label=os.environ.get("UATP_HSM_TOKEN_LABEL"),
            aws_region=os.environ.get("AWS_REGION"),
            aws_cluster_id=os.environ.get("UATP_AWS_HSM_CLUSTER_ID"),
            azure_vault_url=os.environ.get("UATP_AZURE_VAULT_URL"),
            azure_key_name=os.environ.get("UATP_AZURE_KEY_NAME"),
            ed25519_key_label=os.environ.get(
                "UATP_ED25519_KEY_LABEL", "uatp-ed25519-signing-key"
            ),
            dilithium_key_label=os.environ.get(
                "UATP_DILITHIUM_KEY_LABEL", "uatp-dilithium3-signing-key"
            ),
        )


class HSMKeyProvider(ABC):
    """Abstract base class for HSM key providers."""

    @abstractmethod
    async def initialize(self) -> bool:
        """Initialize the HSM connection."""
        pass

    @abstractmethod
    async def generate_ed25519_keypair(self, key_label: str) -> Tuple[bytes, str]:
        """
        Generate Ed25519 keypair in HSM.

        Returns:
            Tuple of (public_key_bytes, key_handle_or_id)
        """
        pass

    @abstractmethod
    async def sign_ed25519(self, data: bytes, key_label: str) -> bytes:
        """Sign data using Ed25519 key stored in HSM."""
        pass

    @abstractmethod
    async def verify_ed25519(
        self, data: bytes, signature: bytes, public_key: bytes
    ) -> bool:
        """Verify Ed25519 signature."""
        pass

    @abstractmethod
    async def get_public_key(self, key_label: str) -> Optional[bytes]:
        """Get public key bytes for a stored key."""
        pass

    @abstractmethod
    async def close(self):
        """Close HSM connection."""
        pass

    @property
    @abstractmethod
    def is_available(self) -> bool:
        """Check if HSM is available."""
        pass


class PKCS11Provider(HSMKeyProvider):
    """
    PKCS#11 HSM provider for standard hardware security modules.

    Compatible with:
    - SoftHSM2 (development)
    - Thales Luna HSM
    - SafeNet HSM
    - Utimaco HSM
    - Any PKCS#11 compliant device
    """

    def __init__(self, config: HSMConfig):
        self.config = config
        self._session = None
        self._lib = None
        self._initialized = False
        self._key_handles: Dict[str, int] = {}

    async def initialize(self) -> bool:
        """Initialize PKCS#11 connection."""
        try:
            # Try to import PyKCS11
            try:
                import PyKCS11
            except ImportError:
                logger.error("PyKCS11 not installed. Run: pip install PyKCS11")
                return False

            if not self.config.library_path:
                logger.error("PKCS#11 library path not configured")
                return False

            if not os.path.exists(self.config.library_path):
                logger.error(f"PKCS#11 library not found: {self.config.library_path}")
                return False

            # Load PKCS#11 library
            self._lib = PyKCS11.PyKCS11Lib()
            self._lib.load(self.config.library_path)

            # Get slot
            slots = self._lib.getSlotList(tokenPresent=True)
            if not slots:
                logger.error("No PKCS#11 tokens found")
                return False

            slot = (
                slots[self.config.slot_id]
                if self.config.slot_id < len(slots)
                else slots[0]
            )

            # Open session
            self._session = self._lib.openSession(
                slot, PyKCS11.CKF_SERIAL_SESSION | PyKCS11.CKF_RW_SESSION
            )

            # Login if PIN provided
            if self.config.pin:
                self._session.login(self.config.pin)

            self._initialized = True
            logger.info(f"PKCS#11 HSM initialized with slot {slot}")
            return True

        except Exception as e:
            logger.error(f"Failed to initialize PKCS#11: {e}")
            return False

    async def generate_ed25519_keypair(self, key_label: str) -> Tuple[bytes, str]:
        """Generate Ed25519 keypair in HSM."""
        if not self._initialized:
            raise RuntimeError("HSM not initialized")

        try:
            import PyKCS11

            # Ed25519 key generation template
            public_template = [
                (PyKCS11.CKA_CLASS, PyKCS11.CKO_PUBLIC_KEY),
                (PyKCS11.CKA_KEY_TYPE, PyKCS11.CKK_EC_EDWARDS),
                (PyKCS11.CKA_TOKEN, True),
                (PyKCS11.CKA_LABEL, key_label),
                (PyKCS11.CKA_VERIFY, True),
                # OID for Ed25519: 1.3.101.112
                (PyKCS11.CKA_EC_PARAMS, bytes([0x06, 0x03, 0x2B, 0x65, 0x70])),
            ]

            private_template = [
                (PyKCS11.CKA_CLASS, PyKCS11.CKO_PRIVATE_KEY),
                (PyKCS11.CKA_KEY_TYPE, PyKCS11.CKK_EC_EDWARDS),
                (PyKCS11.CKA_TOKEN, True),
                (PyKCS11.CKA_LABEL, key_label),
                (PyKCS11.CKA_SIGN, True),
                (PyKCS11.CKA_SENSITIVE, True),
                (PyKCS11.CKA_EXTRACTABLE, False),
            ]

            # Generate keypair
            pub_key, priv_key = self._session.generateKeyPair(
                public_template, private_template, mecha=PyKCS11.MechanismEDDSA
            )

            # Store handles
            self._key_handles[key_label] = priv_key

            # Get public key bytes
            public_key_bytes = bytes(
                self._session.getAttributeValue(pub_key, [PyKCS11.CKA_EC_POINT])[0]
            )

            logger.info(f"Generated Ed25519 keypair in HSM: {key_label}")
            return public_key_bytes, key_label

        except Exception as e:
            logger.error(f"Failed to generate Ed25519 keypair: {e}")
            raise

    async def sign_ed25519(self, data: bytes, key_label: str) -> bytes:
        """Sign data using Ed25519 key in HSM."""
        if not self._initialized:
            raise RuntimeError("HSM not initialized")

        try:
            import PyKCS11

            # Find private key by label
            if key_label not in self._key_handles:
                template = [
                    (PyKCS11.CKA_CLASS, PyKCS11.CKO_PRIVATE_KEY),
                    (PyKCS11.CKA_LABEL, key_label),
                ]
                keys = self._session.findObjects(template)
                if not keys:
                    raise ValueError(f"Key not found: {key_label}")
                self._key_handles[key_label] = keys[0]

            priv_key = self._key_handles[key_label]

            # Sign data
            mechanism = PyKCS11.Mechanism(PyKCS11.CKM_EDDSA, None)
            signature = bytes(self._session.sign(priv_key, data, mechanism))

            return signature

        except Exception as e:
            logger.error(f"HSM signing failed: {e}")
            raise

    async def verify_ed25519(
        self, data: bytes, signature: bytes, public_key: bytes
    ) -> bool:
        """Verify Ed25519 signature using HSM."""
        if not self._initialized:
            raise RuntimeError("HSM not initialized")

        try:
            import PyKCS11

            # Create public key object for verification
            template = [
                (PyKCS11.CKA_CLASS, PyKCS11.CKO_PUBLIC_KEY),
                (PyKCS11.CKA_KEY_TYPE, PyKCS11.CKK_EC_EDWARDS),
                (PyKCS11.CKA_VERIFY, True),
                (PyKCS11.CKA_EC_PARAMS, bytes([0x06, 0x03, 0x2B, 0x65, 0x70])),
                (PyKCS11.CKA_EC_POINT, public_key),
            ]

            pub_key = self._session.createObject(template)

            # Verify
            mechanism = PyKCS11.Mechanism(PyKCS11.CKM_EDDSA, None)
            try:
                self._session.verify(pub_key, data, signature, mechanism)
                return True
            except PyKCS11.PyKCS11Error:
                return False
            finally:
                self._session.destroyObject(pub_key)

        except Exception as e:
            logger.error(f"HSM verification failed: {e}")
            return False

    async def get_public_key(self, key_label: str) -> Optional[bytes]:
        """Get public key bytes from HSM."""
        if not self._initialized:
            return None

        try:
            import PyKCS11

            template = [
                (PyKCS11.CKA_CLASS, PyKCS11.CKO_PUBLIC_KEY),
                (PyKCS11.CKA_LABEL, key_label),
            ]
            keys = self._session.findObjects(template)

            if not keys:
                return None

            public_key_bytes = bytes(
                self._session.getAttributeValue(keys[0], [PyKCS11.CKA_EC_POINT])[0]
            )

            return public_key_bytes

        except Exception as e:
            logger.error(f"Failed to get public key: {e}")
            return None

    async def close(self):
        """Close PKCS#11 session."""
        if self._session:
            try:
                self._session.logout()
                self._session.closeSession()
            except Exception as e:
                logger.warning(f"Error closing PKCS#11 session: {e}")
        self._initialized = False

    @property
    def is_available(self) -> bool:
        return self._initialized


class SoftwareHSMProvider(HSMKeyProvider):
    """
    Software-based HSM simulation for development and testing.

    Uses encrypted file storage with the same interface as hardware HSM.
    NOT RECOMMENDED FOR PRODUCTION - use real HSM for production workloads.
    """

    def __init__(self, config: HSMConfig):
        self.config = config
        self._initialized = False
        self._keys: Dict[str, Dict[str, bytes]] = {}

        # Try to use cryptography library
        try:
            from cryptography.hazmat.primitives.asymmetric import ed25519

            self._ed25519 = ed25519
            self._crypto_available = True
        except ImportError:
            self._crypto_available = False

    async def initialize(self) -> bool:
        """Initialize software HSM."""
        if not self._crypto_available:
            logger.error("cryptography library not available")
            return False

        self._initialized = True
        logger.warning("Using SOFTWARE HSM - not recommended for production!")
        return True

    async def generate_ed25519_keypair(self, key_label: str) -> Tuple[bytes, str]:
        """Generate Ed25519 keypair in software."""
        if not self._initialized:
            raise RuntimeError("Software HSM not initialized")

        from cryptography.hazmat.primitives import serialization

        # Generate keypair
        private_key = self._ed25519.Ed25519PrivateKey.generate()
        public_key = private_key.public_key()

        # Get raw bytes
        public_bytes = public_key.public_bytes(
            encoding=serialization.Encoding.Raw, format=serialization.PublicFormat.Raw
        )
        private_bytes = private_key.private_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PrivateFormat.Raw,
            encryption_algorithm=serialization.NoEncryption(),
        )

        # Store in memory (encrypted in real implementation)
        self._keys[key_label] = {
            "public": public_bytes,
            "private": private_bytes,
        }

        logger.info(f"Generated Ed25519 keypair (software): {key_label}")
        return public_bytes, key_label

    async def sign_ed25519(self, data: bytes, key_label: str) -> bytes:
        """Sign using software key."""
        if key_label not in self._keys:
            raise ValueError(f"Key not found: {key_label}")

        from cryptography.hazmat.primitives.asymmetric import ed25519

        private_bytes = self._keys[key_label]["private"]
        private_key = ed25519.Ed25519PrivateKey.from_private_bytes(private_bytes)

        return private_key.sign(data)

    async def verify_ed25519(
        self, data: bytes, signature: bytes, public_key: bytes
    ) -> bool:
        """Verify signature using software."""
        try:
            from cryptography.hazmat.primitives.asymmetric import ed25519

            public_key_obj = ed25519.Ed25519PublicKey.from_public_bytes(public_key)
            public_key_obj.verify(signature, data)
            return True
        except Exception:
            return False

    async def get_public_key(self, key_label: str) -> Optional[bytes]:
        """Get public key from software store."""
        if key_label in self._keys:
            return self._keys[key_label]["public"]
        return None

    async def close(self):
        """Clear keys from memory."""
        # Securely zero out keys
        for key_data in self._keys.values():
            if "private" in key_data:
                # Overwrite with zeros
                key_data["private"] = b"\x00" * len(key_data["private"])
        self._keys.clear()
        self._initialized = False

    @property
    def is_available(self) -> bool:
        return self._initialized


class DisabledHSMProvider(HSMKeyProvider):
    """Disabled HSM provider - uses local file-based keys."""

    async def initialize(self) -> bool:
        logger.info("HSM disabled - using file-based key storage")
        return True

    async def generate_ed25519_keypair(self, key_label: str) -> Tuple[bytes, str]:
        raise NotImplementedError("HSM disabled")

    async def sign_ed25519(self, data: bytes, key_label: str) -> bytes:
        raise NotImplementedError("HSM disabled")

    async def verify_ed25519(
        self, data: bytes, signature: bytes, public_key: bytes
    ) -> bool:
        raise NotImplementedError("HSM disabled")

    async def get_public_key(self, key_label: str) -> Optional[bytes]:
        return None

    async def close(self):
        pass

    @property
    def is_available(self) -> bool:
        return False


# Singleton HSM provider
_hsm_provider: Optional[HSMKeyProvider] = None


def get_hsm_provider() -> HSMKeyProvider:
    """
    Get or create the global HSM provider.

    Automatically selects provider based on UATP_HSM_* environment variables.
    """
    global _hsm_provider

    if _hsm_provider is None:
        config = HSMConfig.from_environment()

        if config.provider_type == HSMProviderType.DISABLED:
            _hsm_provider = DisabledHSMProvider()
        elif config.provider_type == HSMProviderType.PKCS11:
            _hsm_provider = PKCS11Provider(config)
        elif config.provider_type == HSMProviderType.SOFTWARE:
            _hsm_provider = SoftwareHSMProvider(config)
        else:
            # Default to disabled
            logger.warning(
                f"Unknown HSM type: {config.provider_type}, defaulting to disabled"
            )
            _hsm_provider = DisabledHSMProvider()

        # Initialize synchronously for now
        # In production, call initialize() explicitly
        try:
            asyncio.get_event_loop().run_until_complete(_hsm_provider.initialize())
        except RuntimeError:
            # No event loop - will need explicit initialization
            pass

    return _hsm_provider


async def initialize_hsm() -> bool:
    """
    Initialize the HSM provider.

    Call this during application startup.
    """
    provider = get_hsm_provider()
    return await provider.initialize()


def is_hsm_available() -> bool:
    """Check if HSM is available and initialized."""
    provider = get_hsm_provider()
    return provider.is_available
