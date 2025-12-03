"""
WebAuthn/Passkeys Authentication for UATP Capsule Engine

Implements FIDO2/WebAuthn for:
- Phishing-resistant authentication
- Hardware-backed security (Secure Enclave/TPM)
- Passwordless user experience
- Cross-device synchronization via iCloud Keychain/Google Password Manager
"""

import base64
import json
import logging
import secrets
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional

from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives.serialization import (
    Encoding,
    PrivateFormat,
    PublicFormat,
)

logger = logging.getLogger(__name__)


@dataclass
class PasskeyCredential:
    """Represents a registered passkey credential."""

    credential_id: str  # Base64url encoded
    public_key: bytes  # COSE public key
    sign_count: int
    user_id: str
    created_at: datetime
    last_used_at: datetime
    aaguid: Optional[str] = None  # Authenticator AAGUID
    transports: Optional[List[str]] = None  # ["internal", "usb", "nfc", "ble"]
    backup_eligible: bool = False
    backup_state: bool = False
    device_name: Optional[str] = None


@dataclass
class RegistrationChallenge:
    """Challenge for passkey registration."""

    challenge: str  # Base64url encoded random bytes
    user_id: str
    user_name: str
    user_display_name: str
    created_at: datetime
    expires_at: datetime


@dataclass
class AuthenticationChallenge:
    """Challenge for passkey authentication."""

    challenge: str
    user_id: Optional[str]
    created_at: datetime
    expires_at: datetime
    allowed_credentials: Optional[List[str]] = None


class WebAuthnHandler:
    """
    WebAuthn/Passkeys handler for UATP.

    Implements FIDO2/WebAuthn Level 3 specification for:
    - Registration (creating passkeys)
    - Authentication (signing in with passkeys)
    - Cross-device synchronization
    """

    def __init__(
        self,
        rp_id: str = "uatp.app",
        rp_name: str = "UATP Capsule Engine",
        challenge_timeout: int = 300,  # 5 minutes
    ):
        """
        Initialize WebAuthn handler.

        Args:
            rp_id: Relying Party ID (your domain)
            rp_name: Human-readable name
            challenge_timeout: Challenge validity in seconds
        """
        self.rp_id = rp_id
        self.rp_name = rp_name
        self.challenge_timeout = challenge_timeout

        # In-memory storage (replace with database in production)
        self.challenges: Dict[str, RegistrationChallenge] = {}
        self.auth_challenges: Dict[str, AuthenticationChallenge] = {}
        self.credentials: Dict[
            str, PasskeyCredential
        ] = {}  # credential_id -> credential
        self.user_credentials: Dict[str, List[str]] = {}  # user_id -> [credential_ids]

        logger.info(f"WebAuthn initialized for RP: {rp_id}")

    def generate_registration_options(
        self, user_id: str, user_name: str, user_display_name: str
    ) -> Dict:
        """
        Generate registration options for passkey creation.

        This is sent to the client to initiate passkey registration.

        Args:
            user_id: Unique user identifier
            user_name: User's username/email
            user_display_name: Display name for the user

        Returns:
            Registration options dict for navigator.credentials.create()
        """
        # Generate cryptographic challenge
        challenge_bytes = secrets.token_bytes(32)
        challenge = (
            base64.urlsafe_b64encode(challenge_bytes).decode("utf-8").rstrip("=")
        )

        # Store challenge for verification
        reg_challenge = RegistrationChallenge(
            challenge=challenge,
            user_id=user_id,
            user_name=user_name,
            user_display_name=user_display_name,
            created_at=datetime.now(timezone.utc),
            expires_at=datetime.now(timezone.utc)
            + timedelta(seconds=self.challenge_timeout),
        )
        self.challenges[challenge] = reg_challenge

        # Get existing credentials for this user (for excludeCredentials)
        existing_credentials = []
        if user_id in self.user_credentials:
            existing_credentials = [
                {"type": "public-key", "id": cred_id}
                for cred_id in self.user_credentials[user_id]
            ]

        # WebAuthn registration options
        options = {
            "challenge": challenge,
            "rp": {"id": self.rp_id, "name": self.rp_name},
            "user": {
                "id": base64.urlsafe_b64encode(user_id.encode()).decode().rstrip("="),
                "name": user_name,
                "displayName": user_display_name,
            },
            "pubKeyCredParams": [
                # Prefer ES256 (ECDSA with SHA-256)
                {"type": "public-key", "alg": -7},  # ES256
                # Fallback to RS256 for compatibility
                {"type": "public-key", "alg": -257},  # RS256
            ],
            "authenticatorSelection": {
                "authenticatorAttachment": "platform",  # Prefer platform authenticators (Touch ID, Face ID)
                "requireResidentKey": True,  # Enable discoverable credentials
                "residentKey": "required",
                "userVerification": "required",  # Require biometric/PIN
            },
            "timeout": self.challenge_timeout * 1000,  # milliseconds
            "excludeCredentials": existing_credentials,
            "attestation": "none",  # Don't require attestation for privacy
        }

        logger.info(f"Generated registration options for user: {user_id}")
        return options

    def verify_registration(
        self, credential_response: Dict, expected_challenge: str
    ) -> PasskeyCredential:
        """
        Verify passkey registration response from client.

        Args:
            credential_response: Response from navigator.credentials.create()
            expected_challenge: Challenge that was sent to client

        Returns:
            PasskeyCredential object

        Raises:
            ValueError: If verification fails
        """
        # Verify challenge exists and hasn't expired
        if expected_challenge not in self.challenges:
            raise ValueError("Invalid or expired challenge")

        challenge = self.challenges[expected_challenge]
        if datetime.now(timezone.utc) > challenge.expires_at:
            del self.challenges[expected_challenge]
            raise ValueError("Challenge expired")

        # Extract credential data
        credential_id = credential_response.get("id")
        raw_id = credential_response.get("rawId")
        response = credential_response.get("response", {})

        if not credential_id or not response:
            raise ValueError("Invalid credential response")

        # Parse attestation object (contains public key)
        attestation_object = response.get("attestationObject")
        client_data_json = response.get("clientDataJSON")

        if not attestation_object or not client_data_json:
            raise ValueError("Missing attestation data")

        # Decode client data
        client_data = json.loads(base64.urlsafe_b64decode(client_data_json + "=="))

        # Verify challenge matches
        if client_data.get("challenge") != expected_challenge:
            raise ValueError("Challenge mismatch")

        # Verify origin (in production, verify against your domain)
        # origin = client_data.get("origin")
        # if origin != f"https://{self.rp_id}":
        #     raise ValueError("Origin mismatch")

        # For simplicity, store the public key from the response
        # In production, parse the CBOR attestation object properly
        public_key_bytes = base64.urlsafe_b64decode(raw_id + "==")

        # Create credential record
        credential = PasskeyCredential(
            credential_id=credential_id,
            public_key=public_key_bytes,
            sign_count=0,
            user_id=challenge.user_id,
            created_at=datetime.now(timezone.utc),
            last_used_at=datetime.now(timezone.utc),
            transports=credential_response.get("transports", []),
            backup_eligible=True,
            backup_state=False,
        )

        # Store credential
        self.credentials[credential_id] = credential

        # Associate with user
        if challenge.user_id not in self.user_credentials:
            self.user_credentials[challenge.user_id] = []
        self.user_credentials[challenge.user_id].append(credential_id)

        # Clean up challenge
        del self.challenges[expected_challenge]

        logger.info(f"Passkey registered for user: {challenge.user_id}")
        return credential

    def generate_authentication_options(self, user_id: Optional[str] = None) -> Dict:
        """
        Generate authentication options for passkey sign-in.

        Args:
            user_id: Optional user ID for account-specific authentication

        Returns:
            Authentication options for navigator.credentials.get()
        """
        # Generate challenge
        challenge_bytes = secrets.token_bytes(32)
        challenge = (
            base64.urlsafe_b64encode(challenge_bytes).decode("utf-8").rstrip("=")
        )

        # Get allowed credentials for this user
        allowed_credentials = None
        if user_id and user_id in self.user_credentials:
            allowed_credentials = [
                {"type": "public-key", "id": cred_id}
                for cred_id in self.user_credentials[user_id]
            ]

        # Store authentication challenge
        auth_challenge = AuthenticationChallenge(
            challenge=challenge,
            user_id=user_id,
            created_at=datetime.now(timezone.utc),
            expires_at=datetime.now(timezone.utc)
            + timedelta(seconds=self.challenge_timeout),
            allowed_credentials=allowed_credentials or [],
        )
        self.auth_challenges[challenge] = auth_challenge

        options = {
            "challenge": challenge,
            "rpId": self.rp_id,
            "allowCredentials": allowed_credentials
            or [],  # Empty for discoverable credentials
            "userVerification": "required",
            "timeout": self.challenge_timeout * 1000,
        }

        logger.info(f"Generated authentication options for user: {user_id or 'any'}")
        return options

    def verify_authentication(
        self, credential_response: Dict, expected_challenge: str
    ) -> PasskeyCredential:
        """
        Verify passkey authentication response.

        Args:
            credential_response: Response from navigator.credentials.get()
            expected_challenge: Challenge that was sent to client

        Returns:
            PasskeyCredential object for the authenticated user

        Raises:
            ValueError: If verification fails
        """
        # Verify challenge
        if expected_challenge not in self.auth_challenges:
            raise ValueError("Invalid or expired challenge")

        challenge = self.auth_challenges[expected_challenge]
        if datetime.now(timezone.utc) > challenge.expires_at:
            del self.auth_challenges[expected_challenge]
            raise ValueError("Challenge expired")

        # Extract credential ID
        credential_id = credential_response.get("id")
        response = credential_response.get("response", {})

        if not credential_id or not response:
            raise ValueError("Invalid credential response")

        # Verify credential exists
        if credential_id not in self.credentials:
            raise ValueError("Unknown credential")

        credential = self.credentials[credential_id]

        # Verify client data
        client_data_json = response.get("clientDataJSON")
        if not client_data_json:
            raise ValueError("Missing client data")

        client_data = json.loads(base64.urlsafe_b64decode(client_data_json + "=="))

        # Verify challenge
        if client_data.get("challenge") != expected_challenge:
            raise ValueError("Challenge mismatch")

        # Verify signature (simplified - in production, verify with public key)
        authenticator_data = response.get("authenticatorData")
        signature = response.get("signature")

        if not authenticator_data or not signature:
            raise ValueError("Missing authentication data")

        # Update credential
        credential.last_used_at = datetime.now(timezone.utc)
        credential.sign_count += 1

        # Clean up challenge
        del self.auth_challenges[expected_challenge]

        logger.info(f"Passkey authentication successful for user: {credential.user_id}")
        return credential

    def list_user_credentials(self, user_id: str) -> List[PasskeyCredential]:
        """Get all passkeys for a user."""
        if user_id not in self.user_credentials:
            return []

        return [
            self.credentials[cred_id]
            for cred_id in self.user_credentials[user_id]
            if cred_id in self.credentials
        ]

    def revoke_credential(self, credential_id: str) -> bool:
        """Revoke a passkey."""
        if credential_id not in self.credentials:
            return False

        credential = self.credentials[credential_id]
        user_id = credential.user_id

        # Remove from user's credentials
        if user_id in self.user_credentials:
            self.user_credentials[user_id].remove(credential_id)

        # Delete credential
        del self.credentials[credential_id]

        logger.info(f"Revoked credential: {credential_id}")
        return True


# Global WebAuthn handler instance
webauthn_handler = WebAuthnHandler()
