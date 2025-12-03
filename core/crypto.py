"""
Cryptographic utilities for UATP capsules
"""
import ecdsa
from ecdsa import SigningKey, VerifyingKey


def generate_key_pair(curve=ecdsa.SECP256k1):
    """Generate a key pair (private and public keys) in hex format"""
    sk = SigningKey.generate(curve=curve)
    vk = sk.get_verifying_key()
    return {"private_key": sk.to_string().hex(), "public_key": vk.to_string().hex()}


def sign_data(data, private_key_hex):
    """Sign data using a private key (in hex) and return signature in hex"""
    sk = SigningKey.from_string(bytes.fromhex(private_key_hex), curve=ecdsa.SECP256k1)
    signature = sk.sign(data.encode())
    return signature.hex()


def verify_signature(data, signature_hex, public_key_hex):
    """Verify signature using public key (in hex)"""
    vk = VerifyingKey.from_string(bytes.fromhex(public_key_hex), curve=ecdsa.SECP256k1)
    try:
        return vk.verify(bytes.fromhex(signature_hex), data.encode())
    except ecdsa.BadSignatureError:
        return False
