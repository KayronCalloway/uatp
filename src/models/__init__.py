"""UATP Models package.

Imports models together to ensure SQLAlchemy relationships are resolved correctly.
"""

from .capsule import CapsuleModel
from .user import UserModel

__all__ = ["UserModel", "CapsuleModel"]
