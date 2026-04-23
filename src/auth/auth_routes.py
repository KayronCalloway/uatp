"""
Authentication Routes
FastAPI routes for user authentication, registration, and token management

SECURITY: This module supports HTTP-only cookie authentication for enhanced
XSS protection. Tokens are stored in HTTP-only, Secure, SameSite cookies
instead of being returned in response bodies for client-side storage.
"""

import logging
import os
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from fastapi.security import HTTPAuthorizationCredentials
from pydantic import BaseModel, EmailStr, field_validator
from sqlalchemy.orm import Session

from ..api.dependencies import get_db
from ..models.user import UserModel
from .auth_middleware import (
    check_rate_limit,
    get_current_user,
    security,
    security_optional,
)
from .jwt_manager import (
    create_access_token,
    create_refresh_token,
    hash_password,
    jwt_manager,
    verify_password,
)

# Cookie configuration
COOKIE_SECURE = os.getenv("ENVIRONMENT", "development") in (
    "production",
    "prod",
    "staging",
)
COOKIE_SAMESITE = "lax"  # "strict" breaks OAuth redirects, "lax" is good default
COOKIE_HTTPONLY = True
COOKIE_MAX_AGE_ACCESS = 15 * 60  # 15 minutes
COOKIE_MAX_AGE_REFRESH = 7 * 24 * 60 * 60  # 7 days

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


# Cookie helper functions
def set_auth_cookies(response: Response, access_token: str, refresh_token: str) -> None:
    """
    Set HTTP-only authentication cookies.

    SECURITY: These cookies are:
    - HttpOnly: Not accessible via JavaScript (XSS protection)
    - Secure: Only sent over HTTPS in production
    - SameSite=Lax: CSRF protection while allowing navigation
    """
    response.set_cookie(
        key="access_token",
        value=access_token,
        max_age=COOKIE_MAX_AGE_ACCESS,
        httponly=COOKIE_HTTPONLY,
        secure=COOKIE_SECURE,
        samesite=COOKIE_SAMESITE,
        path="/",
    )
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        max_age=COOKIE_MAX_AGE_REFRESH,
        httponly=COOKIE_HTTPONLY,
        secure=COOKIE_SECURE,
        samesite=COOKIE_SAMESITE,
        path="/api/v1/auth",  # Only sent to auth endpoints
    )


def clear_auth_cookies(response: Response) -> None:
    """Clear authentication cookies on logout."""
    response.delete_cookie(key="access_token", path="/")
    response.delete_cookie(key="refresh_token", path="/api/v1/auth")


# CSRF Token endpoint
@router.get("/csrf-token")
async def get_csrf_token(request: Request, response: Response):
    """
    Get a CSRF token for use in subsequent mutation requests.

    SECURITY: This endpoint issues CSRF tokens that must be included in the
    X-CSRF-Token header for all non-safe (POST, PUT, DELETE) requests when
    using cookie-based authentication.

    The token is returned in the response body and also set as a non-HTTP-only
    cookie for the double-submit pattern.
    """
    from ..security.csrf_protection import csrf_protection
    from .auth_middleware import get_current_user_optional

    # Get current user if authenticated (for session binding)
    # IMPORTANT: Must use user_id for consistency with login/register issuance
    # and csrf_middleware validation (which checks request.state.user.get("user_id"))
    current_user = get_current_user_optional(request)
    session_id = str(current_user.get("user_id", ""))[:32] if current_user else None
    token = csrf_protection.generate_token(session_id=session_id)

    # Set as cookie for double-submit pattern (NOT HTTP-only so JS can read it)
    response.set_cookie(
        key="csrf_token",
        value=token,
        max_age=3600,  # 1 hour
        httponly=False,  # Must be readable by JavaScript
        secure=COOKIE_SECURE,
        samesite=COOKIE_SAMESITE,
        path="/",
    )

    return {"csrf_token": token, "expires_in": 3600}


# Authentication routes
@router.post("/register", response_model=TokenResponse)
async def register_user(
    request: Request,
    response: Response,
    user_data: UserRegistration,
    db: Session = Depends(get_db),
):
    """Register a new user. Sets HTTP-only cookies for secure auth."""
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
        access_token, expires_in = create_access_token(
            user_id=str(new_user.id), email=new_user.email, username=new_user.username
        )
        refresh_token = create_refresh_token(user_id=str(new_user.id))

        # SECURITY: Set HTTP-only cookies for XSS protection
        set_auth_cookies(response, access_token, refresh_token)

        # Issue CSRF token for cookie-based auth
        from ..security.csrf_protection import csrf_protection

        csrf_token = csrf_protection.generate_token(session_id=str(new_user.id)[:32])
        response.set_cookie(
            key="csrf_token",
            value=csrf_token,
            max_age=3600,
            httponly=False,  # Must be readable by JavaScript
            secure=COOKIE_SECURE,
            samesite=COOKIE_SAMESITE,
            path="/",
        )

        # DEPRECATION: Tokens in response body will be removed in v8.0
        # Use HTTP-only cookies (already set above) for secure authentication.
        response.headers["Deprecation"] = "true"
        response.headers["Sunset"] = "2026-09-01"
        response.headers["X-Deprecation-Notice"] = (
            "Token response body deprecated. Use cookie auth instead."
        )

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
    request: Request,
    response: Response,
    login_data: UserLogin,
    db: Session = Depends(get_db),
):
    """
    Authenticate user and return tokens.

    SECURITY: Tokens are set as HTTP-only cookies AND returned in response body.
    - Cookie auth: More secure, automatic, XSS-resistant
    - Body response: Backwards compatible for clients using sessionStorage

    Clients should migrate to cookie-based auth for better security.
    """
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

        # Determine scopes based on user role
        scopes = ["read", "write"]
        if getattr(user, "role", None) == "admin":
            scopes.append("admin")

        # Generate tokens
        access_token, expires_in = create_access_token(
            user_id=str(user.id),
            email=user.email,
            username=user.username,
            scopes=scopes,
        )
        refresh_token = create_refresh_token(user_id=str(user.id))

        # SECURITY: Set HTTP-only cookies for XSS protection
        set_auth_cookies(response, access_token, refresh_token)

        # Issue CSRF token for cookie-based auth
        from ..security.csrf_protection import csrf_protection

        csrf_token = csrf_protection.generate_token(session_id=str(user.id)[:32])
        response.set_cookie(
            key="csrf_token",
            value=csrf_token,
            max_age=3600,
            httponly=False,  # Must be readable by JavaScript
            secure=COOKIE_SECURE,
            samesite=COOKIE_SAMESITE,
            path="/",
        )

        # DEPRECATION: Tokens in response body will be removed in v8.0
        # Use HTTP-only cookies (already set above) for secure authentication.
        # Set deprecation header to warn API consumers
        response.headers["Deprecation"] = "true"
        response.headers["Sunset"] = "2026-09-01"  # 6 months notice
        response.headers["X-Deprecation-Notice"] = (
            "Token response body deprecated. Use cookie auth instead."
        )

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
    request: Request,
    response: Response,
    refresh_data: RefreshTokenRequest = None,
    db: Session = Depends(get_db),
):
    """
    Refresh access token using refresh token.

    Accepts refresh token from:
    1. Request body (refresh_data.refresh_token) - backwards compatible
    2. HTTP-only cookie (refresh_token) - preferred, more secure
    """
    try:
        # Get refresh token from body or cookie
        token = None
        if refresh_data and refresh_data.refresh_token:
            token = refresh_data.refresh_token
        else:
            token = request.cookies.get("refresh_token")

        if not token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Refresh token required",
            )

        # Verify refresh token with correct token type
        payload = jwt_manager.verify_token(token, "refresh")
        if not payload:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired refresh token",
            )

        user_id = payload["sub"]
        import uuid

        if isinstance(user_id, str):
            user_id = uuid.UUID(user_id)

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
        access_token, expires_in = create_access_token(
            user_id=str(user.id), email=user.email, username=user.username
        )
        new_refresh_token = create_refresh_token(user_id=str(user.id))

        # SECURITY: Set HTTP-only cookies for XSS protection
        set_auth_cookies(response, access_token, new_refresh_token)

        # DEPRECATION: Tokens in response body will be removed in v8.0
        response.headers["Deprecation"] = "true"
        response.headers["Sunset"] = "2026-09-01"
        response.headers["X-Deprecation-Notice"] = (
            "Token response body deprecated. Use cookie auth instead."
        )

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
    request: Request,
    response: Response,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security_optional),
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """
    Logout user, revoke tokens, and clear auth cookies.

    SECURITY: Supports both Bearer token and cookie-only authentication.
    Clears HTTP-only cookies to ensure complete logout even if client-side
    code fails to clear sessionStorage.
    """
    try:
        # Revoke the Bearer token if provided
        if credentials and credentials.credentials:
            jwt_manager.revoke_token(credentials.credentials)

        # Also revoke cookie tokens if present
        access_cookie = request.cookies.get("access_token")
        refresh_cookie = request.cookies.get("refresh_token")
        if access_cookie:
            jwt_manager.revoke_token(access_cookie)
        if refresh_cookie:
            jwt_manager.revoke_token(refresh_cookie)

        # SECURITY: Clear auth cookies
        clear_auth_cookies(response)

        logger.info(f"User logged out: {current_user.get('username', 'unknown')}")
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
    import asyncio
    import random
    import time

    # SECURITY: Normalize response timing to prevent user enumeration
    # Track start time to ensure consistent response timing
    start_time = time.monotonic()
    MIN_RESPONSE_TIME = 0.5  # Minimum 500ms response time

    try:
        # Find user
        user = (
            db.query(UserModel).filter(UserModel.email == reset_request.email).first()
        )

        if not user:
            # SECURITY: To prevent user enumeration via timing:
            # 1. Don't reveal if user exists in response
            # 2. Add random delay to mask timing difference
            logger.warning(
                "Password reset requested for non-existent user"  # Don't log email
            )
            # Add jitter matching typical email send time (200-800ms)
            await asyncio.sleep(random.uniform(0.2, 0.8))
            # Ensure minimum response time
            elapsed = time.monotonic() - start_time
            if elapsed < MIN_RESPONSE_TIME:
                await asyncio.sleep(MIN_RESPONSE_TIME - elapsed)
            return {"message": "Password reset email sent if user exists"}

        # Generate password reset token
        reset_token = jwt_manager.generate_password_reset_token(user.email)

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
                # Development mode - NO token logging (security)
                logger.warning(
                    "No email provider configured. Password reset requested but email not sent."
                )
                logger.info(
                    "Add SENDGRID_API_KEY to enable email delivery in production"
                )

        except ImportError:
            logger.error("SendGrid library not installed. Run: pip install sendgrid")
        except Exception as e:
            logger.error(f"Failed to send reset email: {e}")

        # SECURITY: Ensure consistent response timing for enumeration prevention
        elapsed = time.monotonic() - start_time
        if elapsed < MIN_RESPONSE_TIME:
            await asyncio.sleep(MIN_RESPONSE_TIME - elapsed)

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
        # Verify reset token with correct token type
        payload = jwt_manager.verify_token(reset_data.token, "password_reset")
        if not payload:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired reset token",
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
