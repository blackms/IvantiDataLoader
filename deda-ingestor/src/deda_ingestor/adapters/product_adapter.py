"""Adapter for transforming product data between different formats."""
from datetime import datetime
from decimal import Decimal, InvalidOperation
from typing import Any, Dict, List, Optional, Union
from uuid import uuid4

from loguru import logger

from ..core.exceptions import AdapterError
from ..core.models import (
    Product,
    ProductElement,
    IvantiProduct,
    IvantiProductElement
)
from .base import BaseAdapter


class ProductAdapter(BaseAdapter[Dict[str, Any], Product]):
    """Adapter for transforming product data between RabbitMQ and domain models."""

    REQUIRED_PRODUCT_FIELDS = ["productId", "productName", "productElements"]
    REQUIRED_ELEMENT_FIELDS = [
        "Lenght",
        "Procuct Element",
        "Type",
        "GG Startup",
        "RU",
        "RU Qty",
        "RU Unit of measure",
        "Q.ty min",
        "Q.ty MAX",
        "%Sconto MAX",
        "Startup Costo",
        "Startup Margine",
        "Startup Prezzo",
        "Canone Costo Mese",
        "Canone Margine",
        "Canone Prezzo Mese",
        "Extended Description",
        "Profit Center Prevalente",
        "Status"
    ]

    def validate_input(self, data: Dict[str, Any]) -> None:
        """
        Validate input data from RabbitMQ.

        Args:
            data: Raw data from RabbitMQ

        Raises:
            AdapterError: If validation fails
        """
        # Validate required product fields
        self.validate_required_fields(
            data,
            self.REQUIRED_PRODUCT_FIELDS,
            "product data"
        )

        # Validate product elements
        elements = data.get("productElements", [])
        if not isinstance(elements, list):
            raise AdapterError(
                "Product elements must be a list",
                details={"received_type": type(elements).__name__}
            )

        # Validate each element
        for i, element in enumerate(elements):
            try:
                self.validate_required_fields(
                    element,
                    self.REQUIRED_ELEMENT_FIELDS,
                    f"product element {i+1}"
                )
            except AdapterError as e:
                raise AdapterError(
                    f"Invalid product element at index {i}",
                    details={
                        "element_index": i,
                        "validation_errors": e.details
                    }
                ) from e

    def transform_data(self, data: Dict[str, Any]) -> Product:
        """
        Transform RabbitMQ message to Product domain model.

        Args:
            data: Raw data from RabbitMQ

        Returns:
            Product: Domain model instance

        Raises:
            AdapterError: If transformation fails
        """
        try:
            # Transform product elements
            product_elements = []
            for i, element_data in enumerate(data.get("productElements", [])):
                try:
                    element = self._transform_product_element(element_data)
                    product_elements.append(element)
                except Exception as e:
                    raise AdapterError(
                        f"Failed to transform product element at index {i}",
                        details={
                            "element_index": i,
                            "element_data": element_data,
                            "error": str(e)
                        }
                    ) from e

            # Create product instance
            return Product(
                product_id=str(data["productId"]),
                product_name=str(data["productName"]),
                product_elements=product_elements,
                created_at=datetime.utcnow()
            )

        except Exception as e:
            if not isinstance(e, AdapterError):
                raise AdapterError(
                    "Failed to transform product data",
                    details={"error": str(e)}
                ) from e
            raise

    def validate_output(self, data: Product) -> None:
        """
        Validate transformed product data.

        Args:
            data: Transformed product data

        Raises:
            AdapterError: If validation fails
        """
        if not data.product_elements:
            raise AdapterError(
                "Product must have at least one element",
                details={"product_id": data.product_id}
            )

    def _transform_product_element(self, data: Dict[str, Any]) -> ProductElement:
        """
        Transform raw element data to ProductElement.

        Args:
            data: Raw element data

        Returns:
            ProductElement: Transformed element

        Raises:
            AdapterError: If transformation fails
        """
        try:
            # Convert numeric values to Decimal
            numeric_fields = {
                "%Sconto MAX": "max_discount_percentage",
                "Startup Costo": "startup_cost",
                "Startup Margine": "startup_margin",
                "Startup Prezzo": "startup_price",
                "Canone Costo Mese": "monthly_fee_cost",
                "Canone Margine": "monthly_fee_margin",
                "Canone Prezzo Mese": "monthly_fee_price"
            }

            for source_field, _ in numeric_fields.items():
                try:
                    data[source_field] = Decimal(str(data.get(source_field, 0)))
                except (InvalidOperation, TypeError) as e:
                    raise AdapterError(
                        f"Invalid numeric value for {source_field}",
                        details={
                            "field": source_field,
                            "value": data.get(source_field),
                            "error": str(e)
                        }
                    ) from e

            return ProductElement(**data)

        except Exception as e:
            if not isinstance(e, AdapterError):
                raise AdapterError(
                    "Failed to transform product element",
                    details={"error": str(e)}
                ) from e
            raise

    @classmethod
    def to_ivanti_product(cls, product: Product) -> IvantiProduct:
        """
        Convert a Product domain model to an IvantiProduct for API operations.

        Args:
            product: Product domain model instance

        Returns:
            IvantiProduct: Model formatted for Ivanti API

        Raises:
            AdapterError: If conversion fails
        """
        try:
            ivanti_elements = []
            
            for element in product.product_elements:
                try:
                    ivanti_element = cls._to_ivanti_element(element)
                    ivanti_elements.append(ivanti_element)
                except Exception as e:
                    raise AdapterError(
                        f"Failed to convert element: {element.product_element}",
                        details={
                            "element_id": element.product_element,
                            "error": str(e)
                        }
                    ) from e

            return IvantiProduct(
                product_id=product.product_id,
                product_name=product.product_name,
                elements=ivanti_elements,
                created_at=product.created_at,
                updated_at=product.updated_at
            )

        except Exception as e:
            if not isinstance(e, AdapterError):
                raise AdapterError(
                    f"Failed to convert product {product.product_id} to Ivanti format",
                    details={"error": str(e)}
                ) from e
            raise

    @staticmethod
    def _to_ivanti_element(element: ProductElement) -> IvantiProductElement:
        """
        Convert ProductElement to IvantiProductElement.

        Args:
            element: Product element to convert

        Returns:
            IvantiProductElement: Converted element

        Raises:
            AdapterError: If conversion fails
        """
        try:
            return IvantiProductElement(
                id=str(uuid4()),
                product_element=element.product_element,
                type=element.type,
                startup_days=element.startup_days,
                resource_unit=element.resource_unit,
                resource_unit_qty=element.resource_unit_qty,
                resource_unit_measure=element.resource_unit_measure,
                quantity_min=element.quantity_min,
                quantity_max=element.quantity_max,
                max_discount_percentage=float(element.max_discount_percentage),
                startup_cost=float(element.startup_cost),
                startup_margin=float(element.startup_margin),
                startup_price=float(element.startup_price),
                monthly_fee_cost=float(element.monthly_fee_cost),
                monthly_fee_margin=float(element.monthly_fee_margin),
                monthly_fee_price=float(element.monthly_fee_price),
                extended_description=element.extended_description,
                profit_center=element.profit_center,
                status=element.status,
                notes=element.notes,
                object_reference=element.object_reference
            )
        except Exception as e:
            raise AdapterError(
                "Failed to convert element to Ivanti format",
                details={"error": str(e)}
            ) from e

    @classmethod
    def from_ivanti_response(
        cls,
        response_data: Dict[str, Any]
    ) -> Optional[Product]:
        """
        Convert Ivanti API response data to a Product domain model.

        Args:
            response_data: Dictionary containing product data from Ivanti API

        Returns:
            Optional[Product]: Domain model instance if conversion successful

        Raises:
            AdapterError: If conversion fails
        """
        try:
            # Extract base fields
            product_id = str(response_data.get("id", ""))
            product_name = str(response_data.get("name", ""))

            # Extract dates
            created_at = None
            updated_at = None
            if created_str := response_data.get("created_at"):
                created_at = datetime.fromisoformat(
                    created_str.replace("Z", "+00:00")
                )
            if updated_str := response_data.get("updated_at"):
                updated_at = datetime.fromisoformat(
                    updated_str.replace("Z", "+00:00")
                )

            # Convert elements
            product_elements = []
            for element_data in response_data.get("elements", []):
                try:
                    element_data = cls._transform_ivanti_element(element_data)
                    product_elements.append(ProductElement(**element_data))
                except Exception as e:
                    logger.warning(
                        f"Failed to convert Ivanti element: {str(e)}",
                        element_data=element_data
                    )
                    continue

            if not product_elements:
                logger.warning(
                    "No valid elements found in Ivanti response",
                    product_id=product_id
                )
                return None

            return Product(
                product_id=product_id,
                product_name=product_name,
                product_elements=product_elements,
                created_at=created_at or datetime.utcnow(),
                updated_at=updated_at
            )

        except Exception as e:
            raise AdapterError(
                "Failed to convert Ivanti response to Product",
                details={"error": str(e)}
            ) from e

    @staticmethod
    def _transform_ivanti_element(data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Transform Ivanti element data to format expected by ProductElement.

        Args:
            data: Raw Ivanti element data

        Returns:
            Dict[str, Any]: Transformed element data

        Raises:
            AdapterError: If transformation fails
        """
        try:
            return {
                "Lenght": data.get("length", 0),
                "Procuct Element": data.get("name", ""),
                "Type": data.get("type", ""),
                "GG Startup": data.get("startup_days", 0),
                "RU": data.get("resource_unit", ""),
                "RU Qty": data.get("resource_unit_qty", 0),
                "RU Unit of measure": data.get("resource_unit_measure", ""),
                "Q.ty min": data.get("quantity_min", 0),
                "Q.ty MAX": data.get("quantity_max", 0),
                "%Sconto MAX": Decimal(str(data.get("max_discount_percentage", 0))),
                "Startup Costo": Decimal(str(data.get("startup_cost", 0))),
                "Startup Margine": Decimal(str(data.get("startup_margin", 0))),
                "Startup Prezzo": Decimal(str(data.get("startup_price", 0))),
                "Canone Costo Mese": Decimal(str(data.get("monthly_fee_cost", 0))),
                "Canone Margine": Decimal(str(data.get("monthly_fee_margin", 0))),
                "Canone Prezzo Mese": Decimal(str(data.get("monthly_fee_price", 0))),
                "Extended Description": data.get("extended_description", ""),
                "Profit Center Prevalente": data.get("profit_center", ""),
                "Status": data.get("status", "Active"),
                "Note": data.get("notes"),
                "Object": data.get("object_reference")
            }
        except Exception as e:
            raise AdapterError(
                "Failed to transform Ivanti element data",
                details={"error": str(e)}
            ) from e