"""
UATP 7.2 Hardware Attestation Module

Provides integration with hardware security features:
- Apple Secure Enclave
- Android TEE (TrustZone)
- NVIDIA Confidential Computing
- Intel SGX
- ARM TrustZone

All platform integrations are stubs - actual hardware integration
requires platform-specific SDKs and secure boot chains.
"""

from .hardware_attestation import (
    AttestationResult,
    AttestationType,
    HardwareAttestationService,
    hardware_attestation_service,
)

__all__ = [
    "HardwareAttestationService",
    "AttestationType",
    "AttestationResult",
    "hardware_attestation_service",
]
