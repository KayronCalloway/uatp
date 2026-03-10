"""Custom exceptions for the UATP Capsule Engine.

Provides a hierarchy of exception types to enable more specific error handling.
"""


class UATPEngineError(Exception):
    """Base exception for all UATP Engine errors."""

    pass


class ValidationError(UATPEngineError):
    """Raised when capsule data fails validation checks."""

    pass


class InvalidCapsuleParameterError(ValidationError):
    """Raised when a parameter provided to a capsule creation method is invalid."""

    pass


class CapsuleSigningError(UATPEngineError):
    """Raised when there's an error during capsule signing."""

    pass


class CapsuleLoggingError(UATPEngineError):
    """Raised when there's an error during capsule logging to the chain."""

    pass


class ChainIntegrityError(UATPEngineError):
    """Raised when there's an issue with the integrity of the capsule chain."""

    pass


class CapsuleVerificationError(UATPEngineError):
    """Raised when capsule verification fails."""

    pass


class UATPApiError(Exception):
    """Base exception for all UATP API errors."""

    pass


class InvalidRequestError(UATPApiError):
    """Raised when a request to the API is invalid."""

    pass


class AuthenticationError(UATPApiError):
    """Raised when API authentication fails."""

    pass


class AuthorizationError(UATPApiError):
    """Raised when the authenticated user is not authorized for an action."""

    pass


class RateLimitExceededError(UATPApiError):
    """Raised when a client exceeds the rate limit for API calls."""

    pass
