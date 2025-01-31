"""Custom exceptions for the data loader framework."""
from typing import Any, Dict, Optional


class DataLoaderError(Exception):
    """Base exception for data loader errors."""

    def __init__(
        self,
        message: str,
        details: Optional[Dict[str, Any]] = None,
        **kwargs
    ):
        """
        Initialize exception.

        Args:
            message: Error message
            details: Additional error details
            **kwargs: Additional context
        """
        self.message = message
        self.details = details or {}
        self.details.update(kwargs)
        super().__init__(message)


class ConfigurationError(DataLoaderError):
    """Error in configuration."""
    pass


class PluginError(DataLoaderError):
    """Error in plugin operations."""
    pass


class ReaderError(DataLoaderError):
    """Error in data reader operations."""
    pass


class TransformerError(DataLoaderError):
    """Error in data transformer operations."""
    pass


class LoaderError(DataLoaderError):
    """Error in data loader operations."""
    pass


class PipelineError(DataLoaderError):
    """Error in pipeline operations."""
    pass


class ValidationError(DataLoaderError):
    """Error in data validation."""
    pass


class ConnectionError(DataLoaderError):
    """Error in external service connections."""
    pass


class RetryableError(DataLoaderError):
    """Error that can be retried."""
    pass