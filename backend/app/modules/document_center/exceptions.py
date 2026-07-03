class DocumentCenterError(Exception):
    """Base document center service error."""


class MedicalDocumentNotFoundError(DocumentCenterError):
    """Raised when a medical document cannot be found."""


class DocumentVersionNotFoundError(DocumentCenterError):
    """Raised when a document version cannot be found."""


class InvalidDocumentMetadataError(DocumentCenterError):
    """Raised when document metadata is invalid."""
