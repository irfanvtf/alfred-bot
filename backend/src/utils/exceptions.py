"""
Custom exceptions for the Alfred Bot application.
"""


class AlfredBotError(Exception):
    """Base exception class for all Alfred Bot errors."""

    pass


class TextProcessingError(AlfredBotError):
    """Exception raised when text processing operations fail."""

    pass


class ConfigurationError(AlfredBotError):
    """Exception raised when there are configuration issues."""

    pass


class APIError(AlfredBotError):
    """Exception raised when API calls fail."""

    pass


class ValidationError(AlfredBotError):
    """Exception raised when input validation fails."""

    pass


class DatabaseError(AlfredBotError):
    """Exception raised when database operations fail."""

    pass
