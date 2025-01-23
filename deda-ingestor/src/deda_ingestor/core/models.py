"""Core domain models for the Deda Ingestor application."""
from datetime import datetime
from decimal import Decimal
from typing import Dict, List, Optional

from pydantic import BaseModel, Field, validator


class ProductElement(BaseModel):
    """Model for a product element."""
    length: int = Field(..., alias="Lenght")
    product_element: str = Field(..., alias="Procuct Element")
    type: str = Field(..., alias="Type")
    startup_days: int = Field(..., alias="GG Startup")
    resource_unit: str = Field(..., alias="RU")
    resource_unit_qty: int = Field(..., alias="RU Qty")
    resource_unit_measure: str = Field(..., alias="RU Unit of measure")
    quantity_min: int = Field(..., alias="Q.ty min")
    quantity_max: int = Field(..., alias="Q.ty MAX")
    max_discount_percentage: Decimal = Field(..., alias="%Sconto MAX")
    startup_cost: Decimal = Field(..., alias="Startup Costo")
    startup_margin: Decimal = Field(..., alias="Startup Margine")
    startup_price: Decimal = Field(..., alias="Startup Prezzo")
    monthly_fee_cost: Decimal = Field(..., alias="Canone Costo Mese")
    monthly_fee_margin: Decimal = Field(..., alias="Canone Margine")
    monthly_fee_price: Decimal = Field(..., alias="Canone Prezzo Mese")
    extended_description: str = Field(..., alias="Extended Description")
    profit_center: str = Field(..., alias="Profit Center Prevalente")
    status: str = Field(..., alias="Status")
    notes: Optional[str] = Field(None, alias="Note")
    object_reference: Optional[str] = Field(None, alias="Object")

    class Config:
        """Pydantic model configuration."""
        populate_by_name = True
        json_encoders = {
            Decimal: lambda v: float(v),
        }

    @validator("status")
    def validate_status(cls, v: str) -> str:
        """Validate status field."""
        valid_statuses = {"Active", "Inactive", "Discontinued"}
        if v not in valid_statuses:
            raise ValueError(f"Status must be one of {valid_statuses}")
        return v


class Product(BaseModel):
    """Core product model."""
    product_id: str = Field(..., alias="productId")
    product_name: str = Field(..., alias="productName")
    product_elements: List[ProductElement] = Field(..., alias="productElements")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None

    class Config:
        """Pydantic model configuration."""
        populate_by_name = True
        json_encoders = {
            datetime: lambda v: v.isoformat(),
        }

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


class IvantiProductElement(BaseModel):
    """Ivanti product element model for API interactions."""
    id: str
    name: str = Field(..., alias="product_element")
    type: str
    startup_days: int
    resource_unit: str
    resource_unit_qty: int
    resource_unit_measure: str
    quantity_min: int
    quantity_max: int
    max_discount_percentage: float
    startup_cost: float
    startup_margin: float
    startup_price: float
    monthly_fee_cost: float
    monthly_fee_margin: float
    monthly_fee_price: float
    extended_description: str
    profit_center: str
    status: str
    notes: Optional[str] = None
    object_reference: Optional[str] = None

    class Config:
        """Pydantic model configuration."""
        populate_by_name = True


class IvantiProduct(BaseModel):
    """Ivanti product model for API interactions."""
    id: str = Field(alias="product_id")
    name: str = Field(alias="product_name")
    elements: List[IvantiProductElement]
    status: str = "Active"
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

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