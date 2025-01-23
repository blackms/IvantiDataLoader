"""Base interfaces for adapters."""
from abc import ABC, abstractmethod
from typing import Any, Dict, Generic, Optional, TypeVar

from ..core.exceptions import AdapterError

# Generic type variables for input and output types
InputT = TypeVar("InputT")
OutputT = TypeVar("OutputT")


class DataAdapter(Generic[InputT, OutputT], ABC):
    """Base interface for data adapters."""

    @abstractmethod
    def adapt(self, data: InputT) -> OutputT:
        """
        Convert input data to output format.

        Args:
            data: Input data to convert

        Returns:
            OutputT: Converted data

        Raises:
            AdapterError: If conversion fails
        """
        pass


class ValidationMixin:
    """Mixin for data validation functionality."""

    def validate_required_fields(
        self,
        data: Dict[str, Any],
        required_fields: list[str],
        context: str = ""
    ) -> None:
        """
        Validate that all required fields are present and not empty.

        Args:
            data: Data to validate
            required_fields: List of required field names
            context: Context string for error messages

        Raises:
            AdapterError: If validation fails
        """
        missing_fields = []
        empty_fields = []

        for field in required_fields:
            if field not in data:
                missing_fields.append(field)
            elif not str(data[field]).strip():
                empty_fields.append(field)

        errors = []
        if missing_fields:
            errors.append(f"Missing required fields: {', '.join(missing_fields)}")
        if empty_fields:
            errors.append(f"Empty required fields: {', '.join(empty_fields)}")

        if errors:
            context_str = f" in {context}" if context else ""
            raise AdapterError(
                f"Validation failed{context_str}: {'; '.join(errors)}",
                details={
                    "missing_fields": missing_fields,
                    "empty_fields": empty_fields,
                    "context": context
                }
            )


class TransformationMixin:
    """Mixin for data transformation functionality."""

    def safe_get(
        self,
        data: Dict[str, Any],
        key: str,
        default: Any = None,
        transform: Optional[callable] = None
    ) -> Any:
        """
        Safely get a value from a dictionary with optional transformation.

        Args:
            data: Dictionary to get value from
            key: Key to get
            default: Default value if key not found
            transform: Optional transformation function

        Returns:
            Any: Retrieved and optionally transformed value
        """
        value = data.get(key, default)
        if value is not None and transform is not None:
            try:
                return transform(value)
            except Exception as e:
                raise AdapterError(
                    f"Failed to transform value for key '{key}': {str(e)}",
                    details={
                        "key": key,
                        "value": value,
                        "transform": transform.__name__
                    }
                )
        return value


class ErrorHandlingMixin:
    """Mixin for error handling functionality."""

    def handle_adapter_error(
        self,
        error: Exception,
        context: str,
        details: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Handle adapter errors consistently.

        Args:
            error: Original error
            context: Error context
            details: Additional error details

        Raises:
            AdapterError: Wrapped error with context
        """
        error_details = {
            "original_error": str(error),
            "error_type": type(error).__name__,
            "context": context
        }
        if details:
            error_details.update(details)

        raise AdapterError(
            f"Adapter error in {context}: {str(error)}",
            details=error_details
        ) from error


class BaseAdapter(
    DataAdapter[InputT, OutputT],
    ValidationMixin,
    TransformationMixin,
    ErrorHandlingMixin
):
    """
    Base adapter class combining validation, transformation, and error handling.
    
    This class provides a foundation for implementing adapters with common
    functionality for data validation, transformation, and error handling.
    """

    def adapt(self, data: InputT) -> OutputT:
        """
        Template method for data adaptation.

        Args:
            data: Input data to adapt

        Returns:
            OutputT: Adapted data

        Raises:
            AdapterError: If adaptation fails
        """
        try:
            # Validate input data
            self.validate_input(data)
            
            # Transform data
            transformed_data = self.transform_data(data)
            
            # Validate output data
            self.validate_output(transformed_data)
            
            return transformed_data
            
        except Exception as e:
            self.handle_adapter_error(
                e,
                context=f"adapting {type(data).__name__}",
                details={"input_type": type(data).__name__}
            )

    @abstractmethod
    def validate_input(self, data: InputT) -> None:
        """
        Validate input data.

        Args:
            data: Input data to validate

        Raises:
            AdapterError: If validation fails
        """
        pass

    @abstractmethod
    def transform_data(self, data: InputT) -> OutputT:
        """
        Transform input data to output format.

        Args:
            data: Input data to transform

        Returns:
            OutputT: Transformed data

        Raises:
            AdapterError: If transformation fails
        """
        pass

    @abstractmethod
    def validate_output(self, data: OutputT) -> None:
        """
        Validate output data.

        Args:
            data: Output data to validate

        Raises:
            AdapterError: If validation fails
        """
        pass