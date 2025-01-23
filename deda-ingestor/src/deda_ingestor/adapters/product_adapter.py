"""Adapter for transforming product data between different formats."""
from datetime import datetime
from typing import Any, Dict, Optional

from ..core.models import Product, ProductAttributes, IvantiProduct


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
        # Extract base attributes
        product_id = str(message.get("productId", ""))
        product_name = str(message.get("productName", ""))

        # Extract and transform product attributes
        raw_attributes = message.get("attributes", {})
        
        # Parse release date if present
        release_date = None
        if raw_date := raw_attributes.get("releaseDate"):
            try:
                release_date = datetime.fromisoformat(raw_date.replace("Z", "+00:00"))
            except (ValueError, TypeError):
                pass

        # Create ProductAttributes instance
        attributes = ProductAttributes(
            category=raw_attributes.get("category"),
            manufacturer=raw_attributes.get("manufacturer"),
            release_date=release_date,
            description=raw_attributes.get("description"),
            version=message.get("version"),  # Version might be at top level
            platform=raw_attributes.get("platform"),
            language=raw_attributes.get("language"),
            license_type=raw_attributes.get("licenseType"),
            # Store any additional attributes
            additional_info={
                k: str(v) for k, v in raw_attributes.items()
                if k not in {
                    "category", "manufacturer", "releaseDate", "description",
                    "platform", "language", "licenseType"
                }
            }
        )

        return Product(
            product_id=product_id,
            product_name=product_name,
            attributes=attributes,
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
        # Extract attributes
        attrs = product.attributes

        # Prepare custom fields
        custom_fields = {
            "platform": attrs.platform or "",
            "language": attrs.language or "",
            "license_type": attrs.license_type or "",
            **attrs.additional_info  # Include any additional attributes
        }

        return IvantiProduct(
            product_id=product.product_id,
            product_name=product.product_name,
            category=attrs.category,
            manufacturer=attrs.manufacturer,
            release_date=attrs.release_date,
            description=attrs.description,
            version=attrs.version,
            status="active" if product.is_active else "inactive",
            custom_fields=custom_fields
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
            if created_str := response_data.get("createdAt"):
                created_at = datetime.fromisoformat(created_str.replace("Z", "+00:00"))
            if updated_str := response_data.get("updatedAt"):
                updated_at = datetime.fromisoformat(updated_str.replace("Z", "+00:00"))

            # Extract custom fields
            custom_fields = response_data.get("customFields", {})
            
            # Create attributes
            attributes = ProductAttributes(
                category=response_data.get("category"),
                manufacturer=response_data.get("manufacturer"),
                release_date=datetime.fromisoformat(response_data.get("releaseDate", "").replace("Z", "+00:00"))
                if response_data.get("releaseDate") else None,
                description=response_data.get("description"),
                version=response_data.get("version"),
                platform=custom_fields.get("platform"),
                language=custom_fields.get("language"),
                license_type=custom_fields.get("license_type"),
                # Store remaining custom fields as additional info
                additional_info={
                    k: v for k, v in custom_fields.items()
                    if k not in {"platform", "language", "license_type"}
                }
            )

            return Product(
                product_id=product_id,
                product_name=product_name,
                attributes=attributes,
                created_at=created_at or datetime.utcnow(),
                updated_at=updated_at,
                is_active=response_data.get("status", "active").lower() == "active"
            )

        except (ValueError, KeyError, TypeError) as e:
            # Log error and return None if conversion fails
            return None