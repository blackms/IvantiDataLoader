"""Domain models for the application."""
from datetime import datetime, UTC
from decimal import Decimal
from typing import List, Optional

from pydantic import BaseModel, Field, validator


class ProductElement(BaseModel):
    """Product element model."""
    length: int = Field(alias="Lenght")
    product_element: str = Field(alias="Procuct Element")
    type: str = Field(alias="Type")
    startup_days: int = Field(alias="GG Startup")
    resource_unit: str = Field(alias="RU")
    resource_unit_qty: int = Field(alias="RU Qty")
    resource_unit_measure: str = Field(alias="RU Unit of measure")
    quantity_min: int = Field(alias="Q.ty min")
    quantity_max: int = Field(alias="Q.ty MAX")
    max_discount_percentage: Decimal = Field(alias="%Sconto MAX")
    startup_cost: Decimal = Field(alias="Startup Costo")
    startup_margin: Decimal = Field(alias="Startup Margine")
    startup_price: Decimal = Field(alias="Startup Prezzo")
    monthly_fee_cost: Decimal = Field(alias="Canone Costo Mese")
    monthly_fee_margin: Decimal = Field(alias="Canone Margine")
    monthly_fee_price: Decimal = Field(alias="Canone Prezzo Mese")
    extended_description: str = Field(alias="Extended Description")
    profit_center: str = Field(alias="Profit Center Prevalente")
    status: str = Field(alias="Status")
    notes: Optional[str] = Field(alias="Note", default=None)
    object_reference: Optional[str] = Field(alias="Object", default=None)

    @validator("status")
    def validate_status(cls, v: str) -> str:
        """Validate status field."""
        valid_statuses = {"Active", "Inactive", "Draft"}
        if v not in valid_statuses:
            raise ValueError(f"Invalid status. Must be one of: {valid_statuses}")
        return v

    def to_ivanti_element(self) -> dict:
        """Convert to Ivanti API format."""
        return {
            "name": self.product_element,
            "type": self.type,
            "startup_days": self.startup_days,
            "resource_unit": self.resource_unit,
            "resource_unit_qty": self.resource_unit_qty,
            "resource_unit_measure": self.resource_unit_measure,
            "quantity_min": self.quantity_min,
            "quantity_max": self.quantity_max,
            "max_discount_percentage": float(self.max_discount_percentage),
            "startup_cost": float(self.startup_cost),
            "startup_margin": float(self.startup_margin),
            "startup_price": float(self.startup_price),
            "monthly_fee_cost": float(self.monthly_fee_cost),
            "monthly_fee_margin": float(self.monthly_fee_margin),
            "monthly_fee_price": float(self.monthly_fee_price),
            "extended_description": self.extended_description,
            "profit_center": self.profit_center,
            "status": self.status,
            "notes": self.notes,
            "object_reference": self.object_reference
        }


class Product(BaseModel):
    """Product model."""
    product_id: str
    product_name: str
    product_elements: List[ProductElement]
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: Optional[datetime] = None

    @validator("product_id")
    def validate_product_id(cls, v: str) -> str:
        """Validate product ID field."""
        if not v.strip():
            raise ValueError("Product ID cannot be empty")
        return v

    @validator("product_name")
    def validate_product_name(cls, v: str) -> str:
        """Validate product name field."""
        if not v.strip():
            raise ValueError("Product name cannot be empty")
        return v

    def to_ivanti_request(self) -> dict:
        """Convert to Ivanti API request format."""
        return {
            "id": self.product_id,
            "name": self.product_name,
            "elements": [
                element.to_ivanti_element()
                for element in self.product_elements
            ],
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }

    @classmethod
    def from_ivanti_response(cls, data: dict) -> "Product":
        """Create from Ivanti API response."""
        elements = []
        for element_data in data.get("elements", []):
            element = {
                "Lenght": element_data.get("length", 0),
                "Procuct Element": element_data["name"],
                "Type": element_data["type"],
                "GG Startup": element_data["startup_days"],
                "RU": element_data["resource_unit"],
                "RU Qty": element_data["resource_unit_qty"],
                "RU Unit of measure": element_data["resource_unit_measure"],
                "Q.ty min": element_data["quantity_min"],
                "Q.ty MAX": element_data["quantity_max"],
                "%Sconto MAX": element_data["max_discount_percentage"],
                "Startup Costo": element_data["startup_cost"],
                "Startup Margine": element_data["startup_margin"],
                "Startup Prezzo": element_data["startup_price"],
                "Canone Costo Mese": element_data["monthly_fee_cost"],
                "Canone Margine": element_data["monthly_fee_margin"],
                "Canone Prezzo Mese": element_data["monthly_fee_price"],
                "Extended Description": element_data["extended_description"],
                "Profit Center Prevalente": element_data["profit_center"],
                "Status": element_data["status"],
                "Note": element_data.get("notes"),
                "Object": element_data.get("object_reference")
            }
            elements.append(ProductElement(**element))

        created_at = datetime.fromisoformat(
            data["created_at"].replace("Z", "+00:00")
        )
        updated_at = None
        if data.get("updated_at"):
            updated_at = datetime.fromisoformat(
                data["updated_at"].replace("Z", "+00:00")
            )

        return cls(
            product_id=data["id"],
            product_name=data["name"],
            product_elements=elements,
            created_at=created_at,
            updated_at=updated_at
        )


class IvantiProductElement(BaseModel):
    """Ivanti product element model."""
    id: str
    name: str
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


class IvantiProduct(BaseModel):
    """Ivanti product model."""
    id: str
    name: str
    elements: List[IvantiProductElement]
    created_at: datetime
    updated_at: Optional[datetime] = None


class SyncResult(BaseModel):
    """Synchronization result model."""
    total_processed: int = 0
    successful_syncs: int = 0
    failed_syncs: int = 0
    skipped_syncs: int = 0
    errors: dict = Field(default_factory=dict)
    start_time: datetime = Field(default_factory=lambda: datetime.now(UTC))
    end_time: Optional[datetime] = None