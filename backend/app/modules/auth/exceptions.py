from __future__ import annotations


class AuthError(Exception):
    """Base exception for authentication flows."""


class AuthConfigurationError(AuthError):
    """Raised when required auth configuration is missing."""


class InvalidCredentialsError(AuthError):
    """Raised for invalid login credentials without disclosing which field failed."""


class InvalidTokenError(AuthError):
    """Raised for invalid, expired, or revoked tokens."""


class AuthUserInactiveError(AuthError):
    """Raised when the authenticated user is not active."""
