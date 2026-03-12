"""
Pre-Auth Encoding (PAE) - Sigstore-style pre-authentication encoding.

PAE ensures that the signature covers both the payload and its type,
preventing type confusion attacks.

Format: "DSSEv1" + SP + LEN(type) + SP + type + SP + LEN(body) + SP + body

Where:
- SP is a single space character (0x20)
- LEN(x) is the ASCII decimal representation of the length of x
"""

import base64
from typing import Tuple


def pae_encode(payload_type: str, payload: bytes) -> bytes:
    """
    Encode payload with Pre-Auth Encoding (PAE).

    This is what gets signed, not the raw payload.

    Args:
        payload_type: MIME type of the payload
        payload: Raw payload bytes

    Returns:
        PAE-encoded bytes ready for signing
    """
    # Format: "DSSEv1 <type_len> <type> <payload_len> <payload>"
    type_bytes = payload_type.encode("utf-8")

    parts = [
        b"DSSEv1",
        str(len(type_bytes)).encode("ascii"),
        type_bytes,
        str(len(payload)).encode("ascii"),
        payload,
    ]

    return b" ".join(parts)


def pae_decode(encoded: bytes) -> Tuple[str, bytes]:
    """
    Decode PAE-encoded data.

    Args:
        encoded: PAE-encoded bytes

    Returns:
        Tuple of (payload_type, payload)

    Raises:
        ValueError: If format is invalid
    """
    # Split on first space to get version
    parts = encoded.split(b" ", 1)
    if len(parts) != 2 or parts[0] != b"DSSEv1":
        raise ValueError("Invalid PAE format: expected 'DSSEv1' prefix")

    remaining = parts[1]

    # Get type length
    space_idx = remaining.index(b" ")
    type_len = int(remaining[:space_idx])
    remaining = remaining[space_idx + 1 :]

    # Get type
    payload_type = remaining[:type_len].decode("utf-8")
    remaining = remaining[type_len + 1 :]  # +1 for space

    # Get payload length
    space_idx = remaining.index(b" ")
    payload_len = int(remaining[:space_idx])
    remaining = remaining[space_idx + 1 :]

    # Get payload
    payload = remaining[:payload_len]

    if len(payload) != payload_len:
        raise ValueError(
            f"Payload length mismatch: expected {payload_len}, got {len(payload)}"
        )

    return payload_type, payload


def sign_pae(
    payload_type: str,
    payload: bytes,
    sign_func,
) -> bytes:
    """
    Sign payload using PAE encoding.

    Args:
        payload_type: MIME type of the payload
        payload: Raw payload bytes
        sign_func: Function that takes bytes and returns signature bytes

    Returns:
        Signature over PAE-encoded data
    """
    pae = pae_encode(payload_type, payload)
    return sign_func(pae)


def verify_pae(
    payload_type: str,
    payload: bytes,
    signature: bytes,
    verify_func,
) -> bool:
    """
    Verify PAE-encoded signature.

    Args:
        payload_type: MIME type of the payload
        payload: Raw payload bytes
        signature: Signature to verify
        verify_func: Function that takes (message, signature) and returns bool

    Returns:
        True if signature is valid
    """
    pae = pae_encode(payload_type, payload)
    return verify_func(pae, signature)
