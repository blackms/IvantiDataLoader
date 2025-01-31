"""Base classes for the data loader framework."""
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Dict, Generic, List, Optional, TypeVar

from pydantic import BaseModel, Field


class DataSourceConfig(BaseModel):
    """Configuration for a data source."""
    type: str
    name: str
    config: Dict[str, Any] = Field(default_factory=dict)


class MappingConfig(BaseModel):
    """Configuration for field mappings."""
    source_field: str
    target_field: str
    transform: Optional[str] = None
    default_value: Optional[Any] = None


class LoaderConfig(BaseModel):
    """Configuration for the data loader."""
    source: DataSourceConfig
    mappings: List[MappingConfig]
    target: Dict[str, Any] = Field(default_factory=dict)


T = TypeVar('T')
U = TypeVar('U')


class DataReader(ABC, Generic[T]):
    """Abstract base class for data readers."""

    def __init__(self, config: DataSourceConfig):
        """Initialize the reader with configuration."""
        self.config = config

    @abstractmethod
    def read(self) -> List[T]:
        """Read data from the source."""
        pass

    @abstractmethod
    def validate(self, data: T) -> bool:
        """Validate the data format."""
        pass


class DataTransformer(ABC, Generic[T, U]):
    """Abstract base class for data transformers."""

    def __init__(self, config: List[MappingConfig]):
        """Initialize the transformer with mapping configuration."""
        self.config = config

    @abstractmethod
    def transform(self, data: T) -> U:
        """Transform data from source format to target format."""
        pass


class DataLoader(ABC, Generic[U]):
    """Abstract base class for data loaders."""

    def __init__(self, config: Dict[str, Any]):
        """Initialize the loader with configuration."""
        self.config = config

    @abstractmethod
    def load(self, data: U) -> bool:
        """Load data into the target system."""
        pass


class LoadResult(BaseModel):
    """Result of a data load operation."""
    total_records: int = 0
    successful_loads: int = 0
    failed_loads: int = 0
    skipped_loads: int = 0
    errors: Dict[str, str] = Field(default_factory=dict)
    start_time: datetime = Field(default_factory=datetime.now)
    end_time: Optional[datetime] = None

    def record_success(self) -> None:
        """Record a successful load."""
        self.total_records += 1
        self.successful_loads += 1

    def record_failure(self, identifier: str, error: str) -> None:
        """Record a failed load."""
        self.total_records += 1
        self.failed_loads += 1
        self.errors[identifier] = error

    def record_skip(self) -> None:
        """Record a skipped load."""
        self.total_records += 1
        self.skipped_loads += 1

    def complete(self) -> None:
        """Mark the load operation as complete."""
        self.end_time = datetime.now()

    @property
    def duration_seconds(self) -> float:
        """Get the duration of the load operation in seconds."""
        if not self.end_time:
            return 0
        return (self.end_time - self.start_time).total_seconds()

    @property
    def success_rate(self) -> float:
        """Get the success rate as a percentage."""
        if self.total_records == 0:
            return 0
        return (self.successful_loads / self.total_records) * 100