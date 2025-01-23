"""Adapter for transforming product data between different formats."""
from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional
from uuid import uuid4

from ..core.models import (
    Product,
    ProductElement,
    IvantiProduct,
    IvantiProductElement
)


class ProductAdapter:
    """Adapter for transforming product data between different formats."""

    @staticmethod
    def from_rabbitmq_message(message: Dict[str, Any]) -> Product:
        """
        Convert a RabbitMQ message to a Product domain model.

        Args:
            message: Dictionary containing product data from RabbitMQ

        Returns:
            Product: Domain model instance

        Raises:
            ValueError: If required fields are missing or invalid
        """
        # Extract base product data
        product_id = str(message.get("productId", ""))
        product_name = str(message.get("productName", ""))

        # Extract and transform product elements
        product_elements_data = message.get("productElements", [])
        product_elements = []

        for element_data in product_elements_data:
            try:
                # Convert numeric values to Decimal for precision
                element_data = {
                    **element_data,
                    "%Sconto MAX": Decimal(str(element_data.get("%Sconto MAX", 0))),
                    "Startup Costo": Decimal(str(element_data.get("Startup Costo", 0))),
                    "Startup Margine": Decimal(str(element_data.get("Startup Margine", 0))),
                    "Startup Prezzo": Decimal(str(element_data.get("Startup Prezzo", 0))),
                    "Canone Costo Mese": Decimal(str(element_data.get("Canone Costo Mese", 0))),
                    "Canone Margine": Decimal(str(element_data.get("Canone Margine", 0))),
                    "Canone Prezzo Mese": Decimal(str(element_data.get("Canone Prezzo Mese", 0)))
                }
                product_elements.append(ProductElement(**element_data))
            except (ValueError, TypeError) as e:
                raise ValueError(f"Invalid product element data: {str(e)}")

        return Product(
            product_id=product_id,
            product_name=product_name,
            product_elements=product_elements,
            created_at=datetime.utcnow()
        )

    @staticmethod
    def to_ivanti_product(product: Product) -> IvantiProduct:
        """
        Convert a Product domain model to an IvantiProduct for API operations.

        Args:
            product: Product domain model instance

        Returns:
            IvantiProduct: Model formatted for Ivanti API
        """
        ivanti_elements = []
        
        for element in product.product_elements:
            ivanti_element = IvantiProductElement(
                id=str(uuid4()),  # Generate unique ID for new elements
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
            ivanti_elements.append(ivanti_element)

        return IvantiProduct(
            product_id=product.product_id,
            product_name=product.product_name,
            elements=ivanti_elements,
            created_at=product.created_at,
            updated_at=product.updated_at
        )

    @staticmethod
    def from_ivanti_response(response_data: Dict[str, Any]) -> Optional[Product]:
        """
        Convert Ivanti API response data to a Product domain model.

        Args:
            response_data: Dictionary containing product data from Ivanti API

        Returns:
            Optional[Product]: Domain model instance if conversion successful, None otherwise
        """
        try:
            # Extract base fields
            product_id = str(response_data.get("id", ""))
            product_name = str(response_data.get("name", ""))

            # Extract dates
            created_at = None
            updated_at = None
            if created_str := response_data.get("created_at"):
                created_at = datetime.fromisoformat(created_str.replace("Z", "+00:00"))
            if updated_str := response_data.get("updated_at"):
                updated_at = datetime.fromisoformat(updated_str.replace("Z", "+00:00"))

            # Convert elements
            product_elements = []
            for element_data in response_data.get("elements", []):
                try:
                    element_data = {
                        "Lenght": element_data.get("length", 0),
                        "Procuct Element": element_data.get("name", ""),
                        "Type": element_data.get("type", ""),
                        "GG Startup": element_data.get("startup_days", 0),
                        "RU": element_data.get("resource_unit", ""),
                        "RU Qty": element_data.get("resource_unit_qty", 0),
                        "RU Unit of measure": element_data.get("resource_unit_measure", ""),
                        "Q.ty min": element_data.get("quantity_min", 0),
                        "Q.ty MAX": element_data.get("quantity_max", 0),
                        "%Sconto MAX": Decimal(str(element_data.get("max_discount_percentage", 0))),
                        "Startup Costo": Decimal(str(element_data.get("startup_cost", 0))),
                        "Startup Margine": Decimal(str(element_data.get("startup_margin", 0))),
                        "Startup Prezzo": Decimal(str(element_data.get("startup_price", 0))),
                        "Canone Costo Mese": Decimal(str(element_data.get("monthly_fee_cost", 0))),
                        "Canone Margine": Decimal(str(element_data.get("monthly_fee_margin", 0))),
                        "Canone Prezzo Mese": Decimal(str(element_data.get("monthly_fee_price", 0))),
                        "Extended Description": element_data.get("extended_description", ""),
                        "Profit Center Prevalente": element_data.get("profit_center", ""),
                        "Status": element_data.get("status", "Active"),
                        "Note": element_data.get("notes"),
                        "Object": element_data.get("object_reference")
                    }
                    product_elements.append(ProductElement(**element_data))
                except (ValueError, TypeError) as e:
                    raise ValueError(f"Invalid element data from Ivanti: {str(e)}")

            return Product(
                product_id=product_id,
                product_name=product_name,
                product_elements=product_elements,
                created_at=created_at or datetime.utcnow(),
                updated_at=updated_at
            )

        except (ValueError, KeyError, TypeError) as e:
            # Log error and return None if conversion fails
            return None