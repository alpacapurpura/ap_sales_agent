class DomainError(Exception):
    """Base exception for domain errors."""
    def __init__(self, message: str):
        self.message = message
        super().__init__(self.message)

class NotFoundError(DomainError):
    """Raised when an entity is not found."""
    pass

class ValidationError(DomainError):
    """Raised when validation fails."""
    pass

class AuthenticationError(DomainError):
    """Raised when authentication fails."""
    pass

class AuthorizationError(DomainError):
    """Raised when authorization fails."""
    pass

class ConflictError(DomainError):
    """Raised when there is a conflict (e.g. duplicate resource)."""
    pass
