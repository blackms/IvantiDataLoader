"""Field mapping transformer plugin."""
from typing import Any, Callable, Dict, List, Optional

from pydantic import BaseModel, Field

from ...core.base import DataTransformer, MappingConfig
from ...core.exceptions import TransformerError
from ..registry import PluginRegistry


class FieldTransform:
    """Collection of field transformation functions."""

    @staticmethod
    def to_string(value: Any) -> str:
        """Convert value to string."""
        return str(value) if value is not None else ""

    @staticmethod
    def to_int(value: Any) -> Optional[int]:
        """Convert value to integer."""
        try:
            return int(float(value)) if value is not None else None
        except (ValueError, TypeError):
            return None

    @staticmethod
    def to_float(value: Any) -> Optional[float]:
        """Convert value to float."""
        try:
            return float(value) if value is not None else None
        except (ValueError, TypeError):
            return None

    @staticmethod
    def to_bool(value: Any) -> Optional[bool]:
        """Convert value to boolean."""
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            return value.lower() in ('true', 'yes', '1', 'on')
        if isinstance(value, (int, float)):
            return bool(value)
        return None

    @staticmethod
    def strip(value: Any) -> str:
        """Strip whitespace from string value."""
        return str(value).strip() if value is not None else ""

    @staticmethod
    def upper(value: Any) -> str:
        """Convert value to uppercase."""
        return str(value).upper() if value is not None else ""

    @staticmethod
    def lower(value: Any) -> str:
        """Convert value to lowercase."""
        return str(value).lower() if value is not None else ""


class FieldMapperConfig(BaseModel):
    """Configuration for field mapper."""
    mappings: List[MappingConfig] = Field(
        ...,
        description="List of field mappings"
    )
    ignore_missing: bool = Field(
        default=False,
        description="Ignore missing source fields"
    )
    include_unmapped: bool = Field(
        default=False,
        description="Include fields not in mapping"
    )


@PluginRegistry.register_transformer("field_mapper")
class FieldMapper(DataTransformer[Dict[str, Any], Dict[str, Any]]):
    """Transformer plugin for mapping fields between formats."""

    def __init__(self, config: FieldMapperConfig):
        """
        Initialize field mapper.

        Args:
            config: Transformer configuration
        """
        super().__init__(config.mappings)
        self.ignore_missing = config.ignore_missing
        self.include_unmapped = config.include_unmapped
        self._transform_functions: Dict[str, Callable] = {
            'string': FieldTransform.to_string,
            'int': FieldTransform.to_int,
            'float': FieldTransform.to_float,
            'bool': FieldTransform.to_bool,
            'strip': FieldTransform.strip,
            'upper': FieldTransform.upper,
            'lower': FieldTransform.lower
        }

    def _apply_transform(
        self,
        value: Any,
        transform: Optional[str]
    ) -> Any:
        """
        Apply transformation to value.

        Args:
            value: Value to transform
            transform: Name of transform to apply

        Returns:
            Any: Transformed value

        Raises:
            TransformerError: If transform not found
        """
        if not transform:
            return value

        # Handle multiple transforms (e.g., "strip|upper")
        transforms = transform.split('|')
        result = value

        for t in transforms:
            t = t.strip()
            if t not in self._transform_functions:
                raise TransformerError(f"Transform not found: {t}")
            result = self._transform_functions[t](result)

        return result

    def transform(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Transform data using field mappings.

        Args:
            data: Source data dictionary

        Returns:
            Dict[str, Any]: Transformed data dictionary

        Raises:
            TransformerError: If transformation fails
        """
        try:
            result = {}

            # Apply mappings
            for mapping in self.config:
                source_value = data.get(mapping.source_field)

                # Handle missing source fields
                if source_value is None:
                    if self.ignore_missing:
                        continue
                    if mapping.default_value is not None:
                        source_value = mapping.default_value
                    else:
                        raise TransformerError(
                            f"Missing required field: {mapping.source_field}"
                        )

                # Apply transformation
                try:
                    transformed_value = self._apply_transform(
                        source_value,
                        mapping.transform
                    )
                    result[mapping.target_field] = transformed_value
                except Exception as e:
                    raise TransformerError(
                        f"Transform failed for field {mapping.source_field}: {str(e)}"
                    ) from e

            # Include unmapped fields if configured
            if self.include_unmapped:
                mapped_sources = {m.source_field for m in self.config}
                unmapped = {
                    k: v for k, v in data.items()
                    if k not in mapped_sources
                }
                result.update(unmapped)

            return result

        except Exception as e:
            if isinstance(e, TransformerError):
                raise
            raise TransformerError(f"Transformation failed: {str(e)}") from e

    def register_transform(
        self,
        name: str,
        func: Callable[[Any], Any]
    ) -> None:
        """
        Register a custom transformation function.

        Args:
            name: Name of the transform
            func: Transform function

        Raises:
            TransformerError: If transform already exists
        """
        if name in self._transform_functions:
            raise TransformerError(f"Transform already exists: {name}")
        self._transform_functions[name] = func