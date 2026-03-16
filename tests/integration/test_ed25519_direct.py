"""
Integration tests for Ed25519 cryptography.

Tests Ed25519 signing and verification directly using PyNaCl,
without the UATP wrapper layer. Ensures the crypto primitives work correctly.

Run with: pytest tests/integration/test_ed25519_direct.py -v
"""

import pytest
from nacl.encoding import HexEncoder
from nacl.exceptions import BadSignatureError
from nacl.signing import SigningKey, VerifyKey


class TestEd25519Direct:
    """Direct Ed25519 tests without UATP wrappers."""

    def test_keypair_generation(self):
        """Test that Ed25519 keypair generation works."""
        # Generate keypair
        signing_key = SigningKey.generate()
        verify_key = signing_key.verify_key

        # Keys should be the correct length
        # Ed25519 signing key is 32 bytes (seed)
        # Ed25519 verify key is 32 bytes
        signing_key_hex = signing_key.encode(encoder=HexEncoder).decode("utf-8")
        verify_key_hex = verify_key.encode(encoder=HexEncoder).decode("utf-8")

        assert len(signing_key_hex) == 64, (
            "Signing key should be 64 hex chars (32 bytes)"
        )
        assert len(verify_key_hex) == 64, "Verify key should be 64 hex chars (32 bytes)"

    def test_sign_and_verify_roundtrip(self):
        """Test signing data and verifying the signature."""
        # Generate keypair
        signing_key = SigningKey.generate()
        verify_key = signing_key.verify_key

        # Sign some data
        message = b"Hello, UATP!"
        signed = signing_key.sign(message)

        # Signed message contains signature (64 bytes) + original message
        assert len(signed.signature) == 64
        assert signed.message == message

        # Verification should pass
        verify_key.verify(signed)

    def test_signature_format_matches_uatp_spec(self):
        """Test that signature format matches UATP spec (ed25519:hex)."""
        signing_key = SigningKey.generate()

        # Sign a hash-like string (as UATP does)
        hash_str = "abc123def456"
        signature_bytes = signing_key.sign(hash_str.encode("utf-8")).signature

        # UATP format: "ed25519:" + 128 hex chars (64 bytes)
        uatp_signature = f"ed25519:{signature_bytes.hex()}"

        assert uatp_signature.startswith("ed25519:")
        sig_hex_part = uatp_signature.split(":", 1)[1]
        assert len(sig_hex_part) == 128, "Ed25519 signature should be 128 hex chars"

        # Should be valid hex
        try:
            bytes.fromhex(sig_hex_part)
        except ValueError:
            pytest.fail("Signature should be valid hex")

    def test_tampered_data_fails_verification(self):
        """Test that verification fails with tampered data."""
        signing_key = SigningKey.generate()
        verify_key = signing_key.verify_key

        # Sign original message
        original_message = b"original data"
        signature = signing_key.sign(original_message).signature

        # Verification of original should pass
        verify_key.verify(original_message, signature)

        # Verification of tampered message should fail
        tampered_message = b"tampered data"
        with pytest.raises(BadSignatureError):
            verify_key.verify(tampered_message, signature)

    def test_wrong_key_fails_verification(self):
        """Test that verification fails with wrong key."""
        # Create two different keypairs
        signing_key_1 = SigningKey.generate()
        signing_key_2 = SigningKey.generate()
        verify_key_2 = signing_key_2.verify_key

        # Sign with key 1
        message = b"signed by key 1"
        signature = signing_key_1.sign(message).signature

        # Verification with key 2 should fail
        with pytest.raises(BadSignatureError):
            verify_key_2.verify(message, signature)

    def test_hex_encoding_roundtrip(self):
        """Test that keys survive hex encoding/decoding."""
        # Generate original keypair
        original_signing_key = SigningKey.generate()
        original_verify_key = original_signing_key.verify_key

        # Encode to hex
        signing_key_hex = original_signing_key.encode(encoder=HexEncoder).decode(
            "utf-8"
        )
        verify_key_hex = original_verify_key.encode(encoder=HexEncoder).decode("utf-8")

        # Reconstruct from hex
        restored_signing_key = SigningKey(signing_key_hex, encoder=HexEncoder)
        restored_verify_key = VerifyKey(verify_key_hex, encoder=HexEncoder)

        # Sign with original, verify with restored
        message = b"test message"
        signature = original_signing_key.sign(message).signature
        restored_verify_key.verify(message, signature)

        # Sign with restored, verify with original
        signature_2 = restored_signing_key.sign(message).signature
        original_verify_key.verify(message, signature_2)

    def test_deterministic_signatures(self):
        """Test that the same key+message produces the same signature."""
        signing_key = SigningKey.generate()

        message = b"same message"

        # Sign twice
        sig1 = signing_key.sign(message).signature
        sig2 = signing_key.sign(message).signature

        # Ed25519 signatures are deterministic
        assert sig1 == sig2, "Same key+message should produce identical signatures"

    def test_different_messages_different_signatures(self):
        """Test that different messages produce different signatures."""
        signing_key = SigningKey.generate()

        sig1 = signing_key.sign(b"message 1").signature
        sig2 = signing_key.sign(b"message 2").signature

        assert sig1 != sig2, "Different messages should produce different signatures"


class TestEd25519EdgeCases:
    """Edge case tests for Ed25519."""

    def test_empty_message(self):
        """Test signing and verifying empty message."""
        signing_key = SigningKey.generate()
        verify_key = signing_key.verify_key

        empty_message = b""
        signed = signing_key.sign(empty_message)
        verify_key.verify(signed)

    def test_large_message(self):
        """Test signing and verifying large message."""
        signing_key = SigningKey.generate()
        verify_key = signing_key.verify_key

        # 1MB message
        large_message = b"x" * (1024 * 1024)
        signed = signing_key.sign(large_message)
        verify_key.verify(signed)

    def test_unicode_in_message(self):
        """Test signing UTF-8 encoded unicode."""
        signing_key = SigningKey.generate()
        verify_key = signing_key.verify_key

        unicode_message = "Hello, world!"
        signed = signing_key.sign(unicode_message.encode("utf-8"))
        verify_key.verify(signed)


# Run tests if executed directly
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
