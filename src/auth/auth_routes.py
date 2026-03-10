"""
Authentication Routes
FastAPI routes for user authentication, registration, and token management
"""

import logging
from datetime import datetime, timezone
from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials
from pydantic import BaseModel, EmailStr, field_validator
from sqlalchemy.orm import Session

from ..api.dependencies import get_db
from ..models.user import UserModel
from .auth_middleware import check_rate_limit, get_current_user, security
from .jwt_manager import (
    create_access_token,
    create_refresh_token,
    hash_password,
    jwt_manager,
    verify_password,
)

logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/api/v1/auth", tags=["authentication"])


# Pydantic models for request/response
class UserRegistration(BaseModel):
    email: EmailStr
    username: str
    password: str
    full_name: str

    @field_validator("username")
    @classmethod
    def validate_username(cls, v):
        if len(v) < 3:
            raise ValueError("Username must be at least 3 characters long")
        if not v.isalnum():
            raise ValueError("Username must contain only alphanumeric characters")
        return v

    @field_validator("password")
    @classmethod
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters long")
        if not any(c.isupper() for c in v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not any(c.islower() for c in v):
            raise ValueError("Password must contain at least one lowercase letter")
        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain at least one digit")
        return v


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    user_id: str
    username: str


class RefreshTokenRequest(BaseModel):
    refresh_token: str


class PasswordResetRequest(BaseModel):
    email: EmailStr


class PasswordResetConfirm(BaseModel):
    token: str
    new_password: str

    @field_validator("new_password")
    @classmethod
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters long")
        if not any(c.isupper() for c in v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not any(c.islower() for c in v):
            raise ValueError("Password must contain at least one lowercase letter")
        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain at least one digit")
        return v


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str

    @field_validator("new_password")
    @classmethod
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters long")
        return v


# Authentication routes
@router.post("/register", response_model=TokenResponse)
async def register_user(
    request: Request, user_data: UserRegistration, db: Session = Depends(get_db)
):
    """Register a new user"""
    try:
        # Check rate limit
        check_rate_limit(request, user_data.email)

        # Check if user already exists
        existing_user = (
            db.query(UserModel)
            .filter(
                (UserModel.email == user_data.email)
                | (UserModel.username == user_data.username)
            )
            .first()
        )

        if existing_user:
            if existing_user.email == user_data.email:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Email already registered",
                )
            else:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Username already taken",
                )

        # Hash password
        hashed_password = hash_password(user_data.password)

        # Create new user
        new_user = UserModel(
            email=user_data.email,
            username=user_data.username,
            full_name=user_data.full_name,
            hashed_password=hashed_password,
        )

        db.add(new_user)
        db.commit()
        db.refresh(new_user)

        logger.info(f"New user registered: {new_user.email}")

        # Generate tokens
        access_token, expires_in = create_access_token(user_id=str(new_user.id))
        refresh_token = create_refresh_token(user_id=str(new_user.id))

        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=expires_in,
            user_id=str(new_user.id),
            username=new_user.username,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"User registration error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="User registration failed",
        )


@router.post("/login", response_model=TokenResponse)
async def login_user(
    request: Request, login_data: UserLogin, db: Session = Depends(get_db)
):
    """Authenticate user and return tokens"""
    try:
        # Check rate limit
        check_rate_limit(request, login_data.email)

        # Find user
        user = db.query(UserModel).filter(UserModel.email == login_data.email).first()

        if not user or not verify_password(login_data.password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials",
            )

        # Check user status
        if user.status != "active":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User account is not active",
            )

        # Update last login time
        user.last_login = datetime.now(timezone.utc)
        db.commit()
        db.refresh(user)

        logger.info(f"User logged in: {user.email}")

        # Generate tokens
        access_token, expires_in = create_access_token(user_id=str(user.id))
        refresh_token = create_refresh_token(user_id=str(user.id))

        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=expires_in,
            user_id=str(user.id),
            username=user.username,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Login failed",
        )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    request: Request, refresh_data: RefreshTokenRequest, db: Session = Depends(get_db)
):
    """Refresh access token using refresh token"""
    try:
        # Verify refresh token
        payload = jwt_manager.verify_token(refresh_data.refresh_token)
        if payload["type"] != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token type"
            )

        user_id = payload["sub"]

        # Find user
        user = db.query(UserModel).filter(UserModel.id == user_id).first()

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
            )

        # Check user status
        if user.status != "active":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User account is not active",
            )

        # Generate new tokens
        access_token, expires_in = create_access_token(user_id=str(user.id))
        new_refresh_token = create_refresh_token(user_id=str(user.id))

        return TokenResponse(
            access_token=access_token,
            refresh_token=new_refresh_token,
            expires_in=expires_in,
            user_id=str(user.id),
            username=user.username,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Token refresh error: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token"
        )


@router.post("/logout")
async def logout_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """Logout user and revoke tokens"""
    try:
        token = credentials.credentials
        jwt_manager.revoke_token(token)
        logger.info(f"User logged out: {current_user['username']}")
        return {"message": "Logout successful"}

    except Exception as e:
        logger.error(f"Logout error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Logout failed"
        )


@router.post("/forgot-password")
async def forgot_password(
    request: Request, reset_request: PasswordResetRequest, db: Session = Depends(get_db)
):
    """Request password reset"""
    try:
        # Find user
        user = (
            db.query(UserModel).filter(UserModel.email == reset_request.email).first()
        )

        if not user:
            # To prevent user enumeration, don't reveal if the user exists
            logger.warning(
                f"Password reset requested for non-existent user: {reset_request.email}"
            )
            return {"message": "Password reset email sent if user exists"}

        # Generate password reset token
        reset_token = jwt_manager.create_reset_token(user.email)

        # Send email with reset link via configured email provider
        try:
            import os

            sendgrid_key = os.getenv("SENDGRID_API_KEY")

            if sendgrid_key:
                # Send via SendGrid in production
                from sendgrid import SendGridAPIClient
                from sendgrid.helpers.mail import Mail

                reset_link = f"{os.getenv('FRONTEND_URL', 'https://app.uatp.com')}/reset-password?token={reset_token}"

                message = Mail(
                    from_email=os.getenv("SENDGRID_FROM_EMAIL", "noreply@uatp.com"),
                    to_emails=user.email,
                    subject="Password Reset Request - UATP",
                    html_content=f"""
                        <h2>Password Reset Request</h2>
                        <p>You requested a password reset for your UATP account.</p>
                        <p><a href="{reset_link}">Click here to reset your password</a></p>
                        <p>This link will expire in 1 hour.</p>
                        <p>If you didn't request this, please ignore this email.</p>
                    """,
                )

                sg = SendGridAPIClient(sendgrid_key)
                sg.send(message)
                logger.info(f"Password reset email sent to {user.email}")
            else:
                # Development mode - log the token
                logger.warning(
                    f"No email provider configured. Password reset token: {reset_token}"
                )
                logger.info(
                    "Add SENDGRID_API_KEY to enable email delivery in production"
                )

        except ImportError:
            logger.error("SendGrid library not installed. Run: pip install sendgrid")
            logger.info(f"Password reset token for {user.email}: {reset_token}")
        except Exception as e:
            logger.error(f"Failed to send reset email: {e}")
            logger.info(f"Password reset token for {user.email}: {reset_token}")

        return {"message": "Password reset email sent if user exists"}

    except Exception as e:
        logger.error(f"Password reset request error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Password reset request failed",
        )


@router.post("/reset-password")
async def reset_password(
    request: Request, reset_data: PasswordResetConfirm, db: Session = Depends(get_db)
):
    """Reset password using reset token"""
    try:
        # Verify reset token
        payload = jwt_manager.verify_token(reset_data.token)
        if payload["type"] != "reset":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token type"
            )

        email = payload["sub"]

        # Find user
        user = db.query(UserModel).filter(UserModel.email == email).first()

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
            )

        # Hash new password
        new_password_hash = hash_password(reset_data.new_password)

        # Update user password
        user.hashed_password = new_password_hash
        db.commit()

        logger.info(f"Password reset for: {user.email}")

        return {"message": "Password reset successfully"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Password reset error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Password reset failed",
        )


@router.post("/change-password")
async def change_password(
    request: Request,
    password_data: ChangePasswordRequest,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Change user password"""
    try:
        # Find user
        user = (
            db.query(UserModel).filter(UserModel.id == current_user["user_id"]).first()
        )

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
            )

        # Verify current password
        if not verify_password(password_data.current_password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Current password is incorrect",
            )

        # Hash new password
        new_password_hash = hash_password(password_data.new_password)

        # Update user password
        user.hashed_password = new_password_hash
        db.commit()

        logger.info(f"Password changed for: {user.email}")

        return {"message": "Password changed successfully"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Password change error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Password change failed",
        )


@router.get("/me")
async def get_current_user_info(
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get current user information"""
    try:
        # Find user in database
        user = (
            db.query(UserModel).filter(UserModel.id == current_user["user_id"]).first()
        )

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
            )

        return {
            "user_id": str(user.id),
            "email": user.email,
            "username": user.username,
            "full_name": user.full_name,
            "status": user.status,
            "verification_status": user.verification_status,
            "total_earnings": float(user.total_earnings),
            "total_attributions": user.total_attributions,
            "created_at": user.created_at.isoformat(),
            "last_login": user.last_login.isoformat() if user.last_login else None,
            "scopes": current_user.get("scopes", []),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get user info error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get user information",
        )


@router.get("/verify-token")
async def verify_token_endpoint(
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """Verify token validity"""
    return {
        "valid": True,
        "user_id": current_user["user_id"],
        "username": current_user["username"],
        "scopes": current_user.get("scopes", []),
        "expires_at": current_user.get("exp"),
    }


# Example usage and testing
if __name__ == "__main__":
    print(" Authentication routes module loaded")
    print("Available endpoints:")
    print("  POST /api/v1/auth/register")
    print("  POST /api/v1/auth/login")
    print("  POST /api/v1/auth/refresh")
    print("  POST /api/v1/auth/logout")
    print("  POST /api/v1/auth/forgot-password")
    print("  POST /api/v1/auth/reset-password")
    print("  POST /api/v1/auth/change-password")
    print("  GET /api/v1/auth/me")
    print("  GET /api/v1/auth/verify-token")
