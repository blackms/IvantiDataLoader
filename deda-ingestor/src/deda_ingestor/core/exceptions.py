"""Custom exceptions for the application."""
from typing import Any, Optional


class DedaIngestorError(Exception):
    """Base exception for all application errors."""

    def __init__(self, message: str, details: Optional[Any] = None):
        """
        Initialize the exception.

        Args:
            message: Error message
            details: Additional error details
        """
        self.message = message
        self.details = details
        super().__init__(self.message)


class ValidationError(DedaIngestorError):
    """Raised when data validation fails."""
    pass


class AdapterError(DedaIngestorError):
    """Raised when data adaptation fails."""
    pass


class ConnectionError(DedaIngestorError):
    """Raised when connection to external service fails."""
    pass


class AuthenticationError(DedaIngestorError):
    """Raised when authentication fails."""
    pass


class ConfigurationError(DedaIngestorError):
    """Raised when configuration is invalid."""
    pass


class MessageProcessingError(DedaIngestorError):
    """Raised when message processing fails."""

    def __init__(
        self,
        message: str,
        product_id: Optional[str] = None,
        original_error: Optional[Exception] = None,
        details: Optional[Any] = None
    ):
        """
        Initialize the exception.

        Args:
            message: Error message
            product_id: ID of the product being processed
            original_error: Original exception that caused this error
            details: Additional error details
        """
        self.product_id = product_id
        self.original_error = original_error
        super().__init__(message, details)


class IvantiAPIError(DedaIngestorError):
    """Raised when Ivanti API operations fail."""

    def __init__(
        self,
        message: str,
        status_code: Optional[int] = None,
        response_body: Optional[str] = None,
        details: Optional[Any] = None
    ):
        """
        Initialize the exception.

        Args:
            message: Error message
            status_code: HTTP status code
            response_body: Response body from the API
            details: Additional error details
        """
        self.status_code = status_code
        self.response_body = response_body
        super().__init__(message, details)


class RetryableError(DedaIngestorError):
    """Base class for errors that can be retried."""

    def __init__(
        self,
        message: str,
        retry_count: int = 0,
        max_retries: int = 3,
        details: Optional[Any] = None
    ):
        """
        Initialize the exception.

        Args:
            message: Error message
            retry_count: Current retry attempt number
            max_retries: Maximum number of retries allowed
            details: Additional error details
        """
        self.retry_count = retry_count
        self.max_retries = max_retries
        super().__init__(message, details)

    @property
    def can_retry(self) -> bool:
        """Check if operation can be retried."""
        return self.retry_count < self.max_retries


class RetryableConnectionError(RetryableError, ConnectionError):
    """Raised when a connection error occurs that can be retried."""
    pass


class RetryableAPIError(RetryableError, IvantiAPIError):
    """Raised when an API error occurs that can be retried."""
    pass


class SchedulerError(DedaIngestorError):
    """Raised when scheduler operations fail."""
    pass