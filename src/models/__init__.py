"""UATP Models package.

Imports models together to ensure SQLAlchemy relationships are resolved correctly.
"""

from .capsule import CapsuleModel
from .user import UserModel
from .user_management import IdentityVerificationModel, UserSessionModel

__all__ = [
    "UserModel",
    "CapsuleModel",
    "UserSessionModel",
    "IdentityVerificationModel",
]
