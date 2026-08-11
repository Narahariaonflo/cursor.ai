"""Domain exceptions."""


class DomainError(Exception):
    """Base exception for domain failures."""


class ValidationError(DomainError):
    """Raised when input breaks a domain invariant."""
