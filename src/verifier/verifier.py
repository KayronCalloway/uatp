from src.capsule_schema import Capsule

from src.crypto_utils import verify_capsule as verify_crypto_capsule


class CapsuleVerifier:
    @staticmethod
    def verify_capsule(capsule: Capsule) -> tuple[bool, str]:
        """
        Verifies the cryptographic integrity of a single capsule, checking both its hash and signature.

        Args:
            capsule: The capsule object to verify.

        Returns:
            A tuple containing a boolean indicating success and a string with details.
        """
        if not capsule.signature or not capsule.metadata.get("verify_key"):
            return False, "Capsule is missing signature or verification key."

        verify_key_hex = capsule.metadata["verify_key"]
        signature_hex = capsule.signature

        # Use the robust verification function from our crypto utils
        is_valid, reason = verify_crypto_capsule(
            capsule=capsule, verify_key_hex=verify_key_hex, signature_hex=signature_hex
        )

        return is_valid, reason

    @staticmethod
    def verify_chain(capsules):
        # Assumes capsules are ordered root → leaf
        for i, cap in enumerate(capsules):
            is_valid, reason = CapsuleVerifier.verify_capsule(cap)
            if not is_valid:
                return False, f"Invalid capsule {cap.capsule_id}: {reason}"
            if i > 0:
                if cap.parent_capsule != capsules[i - 1].capsule_id:
                    return False, f"Parent linkage broken at {cap.capsule_id}"
        return True, "Chain is valid"
