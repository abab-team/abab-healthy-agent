class FamilyError(Exception):
    """Base family service error."""


class FamilyNotFoundError(FamilyError):
    """Raised when a family cannot be found."""


class FamilyMemberNotFoundError(FamilyError):
    """Raised when a family member cannot be found."""


class FamilyMemberAlreadyExistsError(FamilyError):
    """Raised when a user is already a member of a family."""


class MemberReferenceNotFoundError(FamilyError):
    """Raised when a family member reference cannot be resolved."""


class MemberReferenceAmbiguousError(FamilyError):
    """Raised when a family member reference matches multiple members."""
