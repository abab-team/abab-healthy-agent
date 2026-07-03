class IdentityError(Exception):
    """Base identity service error."""


class UserNotFoundError(IdentityError):
    """Raised when a user cannot be found."""


class UserAlreadyExistsError(IdentityError):
    """Raised when email or phone is already used by another user."""


class UserContactRequiredError(IdentityError):
    """Raised when creating a user without email or phone."""
