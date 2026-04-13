class DomainError(Exception):
    """Base exception for domain errors."""

    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(self.message)


class NotFoundError(DomainError):
    """Raised when an entity is not found."""


class ValidationError(DomainError):
    """Raised when validation fails."""


class AuthenticationError(DomainError):
    """Raised when authentication fails."""


class AuthorizationError(DomainError):
    """Raised when authorization fails."""


class ConflictError(DomainError):
    """Raised when there is a conflict (e.g. duplicate resource)."""
