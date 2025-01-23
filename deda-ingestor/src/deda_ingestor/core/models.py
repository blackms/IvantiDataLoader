"""Core domain models for the Deda Ingestor application."""
from datetime import datetime
from typing import Dict, Optional

from pydantic import BaseModel, Field, validator


class ProductAttributes(BaseModel):
    """Product attributes model."""
    category: Optional[str] = None
    manufacturer: Optional[str] = None
    release_date: Optional[datetime] = None
    description: Optional[str] = None
    size: Optional[str] = None
    version: Optional[str] = None
    license_type: Optional[str] = None
    platform: Optional[str] = None
    language: Optional[str] = None
    additional_info: Dict[str, str] = Field(default_factory=dict)


class Product(BaseModel):
    """Core product model."""
    product_id: str = Field(..., description="Unique identifier for the product")
    product_name: str = Field(..., description="Name of the product")
    attributes: ProductAttributes = Field(default_factory=ProductAttributes)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None
    is_active: bool = True

    @validator("product_id")
    def validate_product_id(cls, v: str) -> str:
        """Validate product_id is not empty."""
        if not v.strip():
            raise ValueError("product_id cannot be empty")
        return v.strip()

    @validator("product_name")
    def validate_product_name(cls, v: str) -> str:
        """Validate product_name is not empty."""
        if not v.strip():
            raise ValueError("product_name cannot be empty")
        return v.strip()


class IvantiProduct(BaseModel):
    """Ivanti product model for API interactions."""
    id: str = Field(alias="product_id")
    name: str = Field(alias="product_name")
    category: Optional[str] = None
    manufacturer: Optional[str] = None
    release_date: Optional[datetime] = None
    description: Optional[str] = None
    version: Optional[str] = None
    status: str = "active"
    custom_fields: Dict[str, str] = Field(default_factory=dict)

    class Config:
        """Pydantic model configuration."""
        populate_by_name = True
        json_encoders = {
            datetime: lambda v: v.isoformat(),
        }


class SyncResult(BaseModel):
    """Model for tracking synchronization results."""
    total_processed: int = 0
    successful_syncs: int = 0
    failed_syncs: int = 0
    skipped_syncs: int = 0
    errors: Dict[str, str] = Field(default_factory=dict)
    start_time: datetime = Field(default_factory=datetime.utcnow)
    end_time: Optional[datetime] = None
    
    def record_success(self) -> None:
        """Record a successful sync."""
        self.successful_syncs += 1
        self.total_processed += 1

    def record_failure(self, product_id: str, error: str) -> None:
        """Record a failed sync."""
        self.failed_syncs += 1
        self.total_processed += 1
        self.errors[product_id] = error

    def record_skip(self) -> None:
        """Record a skipped sync."""
        self.skipped_syncs += 1
        self.total_processed += 1

    def complete(self) -> None:
        """Mark sync as complete."""
        self.end_time = datetime.utcnow()

    @property
    def duration_seconds(self) -> float:
        """Calculate duration in seconds."""
        if not self.end_time:
            return 0.0
        return (self.end_time - self.start_time).total_seconds()

    @property
    def success_rate(self) -> float:
        """Calculate success rate as percentage."""
        if self.total_processed == 0:
            return 0.0
        return (self.successful_syncs / self.total_processed) * 100