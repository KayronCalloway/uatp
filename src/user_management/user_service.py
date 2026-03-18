"""
User Management Service
Complete user onboarding and management system for UATP
"""

import asyncio
import hashlib
import hmac
import logging
import re
import secrets
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any, Dict, List, Optional

import bcrypt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.models.user import UserModel
from src.models.user_management import IdentityVerificationModel, UserSessionModel

logger = logging.getLogger(__name__)


class UserStatus(Enum):
    """User account status"""

    PENDING = "pending"
    ACTIVE = "active"
    SUSPENDED = "suspended"
    CLOSED = "closed"


class VerificationStatus(Enum):
    """Identity verification status"""

    UNVERIFIED = "unverified"
    PENDING = "pending"
    VERIFIED = "verified"
    REJECTED = "rejected"


class PayoutMethod(Enum):
    """Supported payout methods"""

    PAYPAL = "paypal"
    STRIPE = "stripe"
    CRYPTO = "crypto"
    BANK_TRANSFER = "bank_transfer"
    VENMO = "venmo"
    CASHAPP = "cashapp"


class UserService:
    """Complete user management service"""

    def __init__(self, db_session: AsyncSession):
        self.db = db_session

    def generate_user_id(self) -> str:
        """Generate unique user ID"""
        timestamp = str(int(datetime.now().timestamp()))
        random_part = secrets.token_hex(8)
        return f"user_{timestamp}_{random_part}"

    def generate_verification_id(self) -> str:
        """Generate unique verification ID"""
        timestamp = str(int(datetime.now().timestamp()))
        random_part = secrets.token_hex(6)
        return f"verify_{timestamp}_{random_part}"

    def generate_session_id(self) -> str:
        """Generate unique session ID"""
        return secrets.token_urlsafe(32)

    def validate_email(self, email: str) -> bool:
        """Validate email format"""
        pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
        return re.match(pattern, email) is not None

    def validate_username(self, username: str) -> bool:
        """Validate username format"""
        # Username must be 3-30 characters, alphanumeric plus underscore
        pattern = r"^[a-zA-Z0-9_]{3,30}$"
        return re.match(pattern, username) is not None

    def validate_password(self, password: str) -> Dict[str, Any]:
        """Validate password strength"""
        errors = []

        if len(password) < 8:
            errors.append("Password must be at least 8 characters long")

        if not re.search(r"[A-Z]", password):
            errors.append("Password must contain at least one uppercase letter")

        if not re.search(r"[a-z]", password):
            errors.append("Password must contain at least one lowercase letter")

        if not re.search(r"[0-9]", password):
            errors.append("Password must contain at least one digit")

        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            errors.append("Password must contain at least one special character")

        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "strength": "strong" if len(errors) == 0 else "weak",
        }

    def hash_password(self, password: str) -> str:
        """Hash password using bcrypt.

        SECURITY: bcrypt is designed to be slow and resistant to GPU/ASIC attacks.
        Work factor of 12 provides ~300ms hash time on modern hardware.
        """
        salt = bcrypt.gensalt(rounds=12)
        return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")

    def verify_password(self, password: str, stored_hash: str) -> bool:
        """Verify password against stored hash (bcrypt or legacy PBKDF2).

        SECURITY: Supports both bcrypt and legacy PBKDF2 hashes for migration.
        Legacy hashes use constant-time comparison.
        """
        try:
            # Check for legacy PBKDF2 format (salt:hash)
            if ":" in stored_hash and not stored_hash.startswith("$2"):
                # SECURITY WARNING: Legacy PBKDF2 hash detected
                logger.warning(
                    "SECURITY: Legacy PBKDF2 password hash detected. "
                    "User should change password to upgrade to bcrypt."
                )
                salt, hash_hex = stored_hash.split(":")
                password_hash = hashlib.pbkdf2_hmac(
                    "sha256", password.encode("utf-8"), salt.encode("utf-8"), 480_000
                )
                # Use constant-time comparison
                return hmac.compare_digest(hash_hex, password_hash.hex())

            # Modern bcrypt verification
            return bcrypt.checkpw(password.encode("utf-8"), stored_hash.encode("utf-8"))
        except (ValueError, TypeError) as e:
            logger.warning(f"Password verification error: {e}")
            return False

    def needs_password_rehash(self, stored_hash: str) -> bool:
        """Check if password hash needs to be upgraded.

        Returns True for legacy PBKDF2 hashes or bcrypt with insufficient rounds.
        """
        # Legacy PBKDF2 format needs upgrade
        if ":" in stored_hash and not stored_hash.startswith("$2"):
            return True

        # Check bcrypt rounds
        try:
            if stored_hash.startswith("$2"):
                parts = stored_hash.split("$")
                if len(parts) >= 3:
                    current_rounds = int(parts[2])
                    return current_rounds < 12
        except (ValueError, IndexError):
            pass

        return False

    async def register_user(
        self, email: str, username: str, password: str, full_name: str, **kwargs
    ) -> Dict[str, Any]:
        """Register a new user"""

        # Validation
        if not self.validate_email(email):
            return {"success": False, "error": "Invalid email format"}
        if not self.validate_username(username):
            return {"success": False, "error": "Invalid username format"}

        password_validation = self.validate_password(password)
        if not password_validation["valid"]:
            return {
                "success": False,
                "error": "Password does not meet security requirements",
                "details": password_validation["errors"],
            }

        # Check for existing user
        existing_user_result = await self.db.execute(
            select(UserModel).where(
                (UserModel.email == email) | (UserModel.username == username)
            )
        )
        if existing_user_result.scalars().first():
            return {"success": False, "error": "Email or username already exists"}

        # Create user model
        hashed_password = self.hash_password(password)
        new_user = UserModel(
            email=email,
            username=username,
            full_name=full_name,
            hashed_password=hashed_password,
            **kwargs,
        )

        self.db.add(new_user)
        await self.db.commit()
        await self.db.refresh(new_user)

        logger.info(f"New user registered: {new_user.username} ({new_user.id})")

        return {
            "success": True,
            "user_id": str(new_user.id),
            "message": "User registered successfully. Please verify your email.",
        }

    async def login_user(
        self, email: str, password: str, ip_address: str, user_agent: str
    ) -> Dict[str, Any]:
        """Login user and create session"""

        result = await self.db.execute(
            select(UserModel).where(UserModel.email == email)
        )
        user = result.scalars().first()

        if not user or not self.verify_password(password, user.hashed_password):
            return {"success": False, "error": "Invalid credentials"}

        if user.status != UserStatus.ACTIVE.value:
            return {"success": False, "error": f"Account is {user.status}"}

        session_token = self.generate_session_id()
        expires_at = datetime.now(timezone.utc) + timedelta(days=30)

        new_session = UserSessionModel(
            user_id=user.id,
            session_token=session_token,
            expires_at=expires_at,
            ip_address=ip_address,
            user_agent=user_agent,
        )
        self.db.add(new_session)
        await self.db.commit()

        return {
            "success": True,
            "session_token": session_token,
            "user_id": user.id,
            "username": user.username,
        }

    async def get_user_profile(self, user_id: str) -> Optional[UserModel]:
        """Get user profile by ID"""
        result = await self.db.execute(select(UserModel).where(UserModel.id == user_id))
        return result.scalars().first()

    async def update_user_profile(
        self, user_id: str, updates: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Update user profile"""

        user = await self.get_user_profile(user_id)
        if not user:
            return {"success": False, "error": "User not found"}

        # Validate and apply updates
        updatable_fields = [
            "full_name",
            "attribution_enabled",
            "uba_participation",
            "data_sharing_consent",
            "analytics_consent",
            "marketing_consent",
            "metadata",
        ]

        for key, value in updates.items():
            if key in updatable_fields:
                setattr(user, key, value)

        await self.db.commit()
        logger.info(f"User profile updated: {user_id}")

        return {"success": True, "user_id": user_id}

    async def start_identity_verification(
        self,
        user_id: str,
        method: str,  # e.g., 'email', 'document'
        details: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Start identity verification process"""
        result = await self.db.execute(select(UserModel).where(UserModel.id == user_id))
        user = result.scalars().first()
        if not user:
            return {"success": False, "error": "User not found"}

        verification_token = self.generate_verification_id()
        expires_at = datetime.now(timezone.utc) + timedelta(hours=1)

        new_verification = IdentityVerificationModel(
            user_id=user.id,
            verification_token=verification_token,
            method=method,
            status="pending",
            expires_at=expires_at,
            details=details or {},
        )
        self.db.add(new_verification)

        user.verification_status = VerificationStatus.PENDING.value
        await self.db.commit()

        # In a real system, this would trigger an email or a call to a 3rd party service
        logger.info(f"Started {method} verification for user {user_id}")

        return {"success": True, "verification_token": verification_token}

    async def complete_verification(
        self, verification_token: str, approved: bool, reason: Optional[str] = None
    ) -> Dict[str, Any]:
        """Complete identity verification"""
        result = await self.db.execute(
            select(IdentityVerificationModel)
            .where(IdentityVerificationModel.verification_token == verification_token)
            .options(selectinload(IdentityVerificationModel.user))
        )
        verification = result.scalars().first()

        if not verification:
            return {"success": False, "error": "Verification not found"}

        if verification.expires_at < datetime.now(timezone.utc):
            verification.status = "expired"
            await self.db.commit()
            return {"success": False, "error": "Verification token expired"}

        user = verification.user
        if approved:
            verification.status = "verified"
            verification.verified_at = datetime.now(timezone.utc)
            user.verification_status = VerificationStatus.VERIFIED.value
            logger.info(
                f"Identity verification {verification.id} approved for user {user.id}"
            )
        else:
            verification.status = "failed"
            user.verification_status = VerificationStatus.REJECTED.value
            logger.warning(
                f"Identity verification {verification.id} failed for user {user.id}: {reason}"
            )

        await self.db.commit()

        return {"success": True, "user_id": user.id, "status": user.verification_status}

    async def setup_payout_method(
        self, user_id: str, payout_method: PayoutMethod, payout_details: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Set up user payout method (feature not available)"""
        # Payout methods feature has been removed
        return {
            "success": False,
            "error": "Payout methods feature is not currently available",
        }

    async def delete_user_account(
        self, user_id: str, reason: str = "user_request"
    ) -> Dict[str, Any]:
        """
        Delete user account and all associated data (GDPR compliant)

        Args:
            user_id: User ID to delete
            reason: Reason for deletion (for audit logs)

        Returns:
            Success/failure status and deletion details
        """
        try:
            # Get user to verify existence
            user = await self.get_user_profile(user_id)
            if not user:
                return {"success": False, "error": "User not found"}

            username = user.username
            email = user.email

            # Start transaction for atomic deletion
            # Delete user sessions
            await self.db.execute(
                "DELETE FROM user_sessions WHERE user_id = :user_id",
                {"user_id": user_id},
            )
            logger.info(f"Deleted sessions for user {user_id}")

            # Delete identity verifications
            await self.db.execute(
                "DELETE FROM identity_verifications WHERE user_id = :user_id",
                {"user_id": user_id},
            )
            logger.info(f"Deleted identity verifications for user {user_id}")

            # Delete payout methods (if table exists)
            try:
                await self.db.execute(
                    "DELETE FROM payout_methods WHERE user_id = :user_id",
                    {"user_id": user_id},
                )
                logger.info(f"Deleted payout methods for user {user_id}")
            except Exception as e:
                logger.debug(f"Payout methods table may not exist: {e}")

            # Delete any user-related capsules or attribution data (GDPR Right to be Forgotten)
            try:
                # Delete all capsules created by this user
                await self.db.execute(
                    "DELETE FROM capsules WHERE creator_id = :user_id",
                    {"user_id": user_id},
                )

                # Anonymize capsules where user is mentioned but not creator
                # (preserve data integrity while removing PII)
                await self.db.execute(
                    "UPDATE capsules SET payload = json_set(payload, '$.metadata.user_id', 'deleted_user') "
                    "WHERE json_extract(payload, '$.metadata.user_id') = :user_id",
                    {"user_id": user_id},
                )

                logger.info(f"Deleted capsule data for user {user_id}")
            except Exception as e:
                logger.warning(f"Capsule data cleanup error (non-critical): {e}")

            # Finally delete the user record
            await self.db.execute(
                "DELETE FROM users WHERE id = :user_id", {"user_id": user_id}
            )

            # Commit all deletions
            await self.db.commit()

            logger.info(
                f"[OK] User account deleted: {user_id} (username: {username}, email: {email}) - Reason: {reason}"
            )

            return {
                "success": True,
                "user_id": user_id,
                "username": username,
                "email": email,
                "deletion_timestamp": datetime.now(timezone.utc).isoformat(),
                "reason": reason,
                "message": "User account and all associated data have been permanently deleted",
            }

        except Exception as e:
            logger.error(f"[ERROR] Failed to delete user {user_id}: {e}")
            await self.db.rollback()
            return {"success": False, "error": f"Account deletion failed: {str(e)}"}

    async def anonymize_user_account(
        self, user_id: str, reason: str = "user_request"
    ) -> Dict[str, Any]:
        """
        Anonymize user account (alternative to full deletion)
        Keeps attribution data but removes PII

        Args:
            user_id: User ID to anonymize
            reason: Reason for anonymization

        Returns:
            Success/failure status and anonymization details
        """
        try:
            user = await self.get_user_profile(user_id)
            if not user:
                return {"success": False, "error": "User not found"}

            original_email = user.email
            original_username = user.username

            # Generate anonymous identifiers
            anon_id = f"anon_{secrets.token_hex(8)}"
            anon_email = f"deleted_{secrets.token_hex(8)}@anonymized.local"

            # Update user with anonymized data
            user.email = anon_email
            user.username = anon_id
            user.full_name = "Anonymized User"
            user.status = UserStatus.CLOSED.value
            user.verification_status = VerificationStatus.UNVERIFIED.value
            user.attribution_enabled = False
            user.data_sharing_consent = False
            user.analytics_consent = False
            user.marketing_consent = False
            user.metadata = {
                "anonymized": True,
                "anonymization_date": datetime.now(timezone.utc).isoformat(),
            }

            # Delete sensitive session data
            await self.db.execute(
                "DELETE FROM user_sessions WHERE user_id = :user_id",
                {"user_id": user_id},
            )

            # Delete identity verification data
            await self.db.execute(
                "DELETE FROM identity_verifications WHERE user_id = :user_id",
                {"user_id": user_id},
            )

            await self.db.commit()

            logger.info(
                f"[OK] User account anonymized: {user_id} (was: {original_username}/{original_email}) - Reason: {reason}"
            )

            return {
                "success": True,
                "user_id": user_id,
                "original_username": original_username,
                "original_email": original_email,
                "anonymized_username": anon_id,
                "anonymization_timestamp": datetime.now(timezone.utc).isoformat(),
                "reason": reason,
                "message": "User account has been anonymized. Attribution data preserved but PII removed.",
            }

        except Exception as e:
            logger.error(f"[ERROR] Failed to anonymize user {user_id}: {e}")
            await self.db.rollback()
            return {
                "success": False,
                "error": f"Account anonymization failed: {str(e)}",
            }

    def _validate_payout_details(
        self, method: PayoutMethod, details: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Validate payout method details"""

        errors = []

        if method == PayoutMethod.PAYPAL:
            if "email" not in details:
                errors.append("PayPal email required")
            elif not self.validate_email(details["email"]):
                errors.append("Invalid PayPal email format")

        elif method == PayoutMethod.STRIPE:
            required_fields = ["account_id", "country"]
            for field in required_fields:
                if field not in details:
                    errors.append(f"Stripe {field} required")

        elif method == PayoutMethod.CRYPTO:
            required_fields = ["wallet_address", "currency"]
            for field in required_fields:
                if field not in details:
                    errors.append(f"Crypto {field} required")

        elif method == PayoutMethod.BANK_TRANSFER:
            required_fields = ["account_number", "routing_number", "bank_name"]
            for field in required_fields:
                if field not in details:
                    errors.append(f"Bank {field} required")

        return {"valid": len(errors) == 0, "errors": errors}

    async def get_user_onboarding_status(self, user_id: str) -> Dict[str, Any]:
        """Get user onboarding completion status"""

        if user_id not in self.users:
            return {"success": False, "error": "User not found"}

        user_profile = self.users[user_id]

        # Check completion status
        steps = {
            "email_verified": user_profile.status != UserStatus.PENDING,
            "identity_verified": user_profile.verification_status
            == VerificationStatus.VERIFIED,
            "payout_configured": user_profile.payout_method is not None,
            "privacy_consent": user_profile.data_sharing_consent,
            "attribution_enabled": user_profile.attribution_enabled,
        }

        completed_steps = sum(steps.values())
        total_steps = len(steps)
        completion_percentage = (completed_steps / total_steps) * 100

        return {
            "success": True,
            "user_id": user_id,
            "completion_percentage": completion_percentage,
            "completed_steps": completed_steps,
            "total_steps": total_steps,
            "steps": steps,
            "next_actions": self._get_next_onboarding_actions(steps),
        }

    def _get_next_onboarding_actions(self, steps: Dict[str, bool]) -> List[str]:
        """Get next recommended onboarding actions"""

        actions = []

        if not steps["email_verified"]:
            actions.append("Verify your email address")

        if not steps["identity_verified"]:
            actions.append("Complete identity verification")

        if not steps["payout_configured"]:
            actions.append("Set up payout method")

        if not steps["privacy_consent"]:
            actions.append("Review and accept privacy settings")

        if not steps["attribution_enabled"]:
            actions.append("Enable attribution tracking")

        if not actions:
            actions.append("Onboarding complete! Start using AI platforms.")

        return actions

    async def get_user_statistics(self, user_id: str) -> Dict[str, Any]:
        """Get user statistics and analytics"""

        result = await self.db.execute(
            select(UserModel)
            .where(UserModel.id == user_id)
            .options(selectinload(UserModel.payout_methods))
        )
        user = result.scalars().first()

        if not user:
            return {"success": False, "error": "User not found"}

        # Get the default payout method if it exists
        default_payout_method = next(
            (pm for pm in user.payout_methods if pm.is_default), None
        )

        # Calculate statistics
        stats = {
            "total_earnings": float(user.total_earnings),
            "total_attributions": user.total_attributions,
            "average_confidence": user.average_confidence,
            "days_since_joining": (datetime.now(timezone.utc) - user.created_at).days,
            "verification_status": user.verification_status,
            "payout_method": default_payout_method.method
            if default_payout_method
            else None,
            "attribution_enabled": user.attribution_enabled,
            "uba_participation": user.uba_participation,
        }

        return {"success": True, "user_id": user_id, "statistics": stats}


# Factory function for easy instantiation
def create_user_service() -> UserService:
    """Create a user service instance"""
    from ..database.connection import get_database_manager

    db_manager = get_database_manager()
    return UserService(db_manager)


# Example usage and testing
if __name__ == "__main__":

    async def demo_user_service():
        """Demonstrate the user service"""

        service = create_user_service()

        # Register a new user
        print(" Registering new user...")
        result = await service.register_user(
            email="alice@example.com",
            username="alice123",
            password="SecurePass123!",
            full_name="Alice Johnson",
        )
        print(f"Registration result: {result}")

        if result["success"]:
            user_id = result["user_id"]

            # Check onboarding status
            print("\n Checking onboarding status...")
            status = await service.get_user_onboarding_status(user_id)
            print(f"Onboarding status: {status}")

            # Start identity verification
            print("\n🆔 Starting identity verification...")
            verification_result = await service.start_identity_verification(
                user_id=user_id,
                verification_type="id_document",
                document_type="passport",
                document_country="US",
            )
            print(f"Verification result: {verification_result}")

            # Complete verification (simulate approval)
            if verification_result["success"]:
                verification_id = verification_result["verification_id"]
                completion_result = await service.complete_verification(
                    verification_id=verification_id, approved=True
                )
                print(f"Verification completion: {completion_result}")

            # Set up payout method
            print("\n Setting up payout method...")
            payout_result = await service.setup_payout_method(
                user_id=user_id,
                payout_method=PayoutMethod.PAYPAL,
                payout_details={"email": "alice@example.com"},
            )
            print(f"Payout setup result: {payout_result}")

            # Login user
            print("\n Logging in user...")
            login_result = await service.login_user(
                email="alice@example.com",
                password="SecurePass123!",
                ip_address="127.0.0.1",
                user_agent="Demo Client",
            )
            print(f"Login result: {login_result}")

            # Get final onboarding status
            print("\n[OK] Final onboarding status...")
            final_status = await service.get_user_onboarding_status(user_id)
            print(f"Final status: {final_status}")

            # Get user statistics
            print("\n User statistics...")
            stats = await service.get_user_statistics(user_id)
            print(f"Statistics: {stats}")

    asyncio.run(demo_user_service())
