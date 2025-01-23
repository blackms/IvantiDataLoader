"""Base repository interface."""
from abc import ABC, abstractmethod
from typing import Any, Dict, Generic, List, Optional, TypeVar

from ..core.models import Product, SyncResult

T = TypeVar("T")


class BaseRepository(ABC, Generic[T]):
    """Base repository interface."""

    @abstractmethod
    def connect(self) -> None:
        """
        Connect to the repository.

        Raises:
            ConnectionError: If connection fails
        """
        pass

    @abstractmethod
    def close(self) -> None:
        """Close repository connections."""
        pass

    @abstractmethod
    def get_product(self, product_id: str) -> Optional[Product]:
        """
        Get product by ID.

        Args:
            product_id: Product ID

        Returns:
            Optional[Product]: Product if found, None otherwise
        """
        pass

    @abstractmethod
    def create_product(self, product: Product) -> bool:
        """
        Create new product.

        Args:
            product: Product to create

        Returns:
            bool: True if successful
        """
        pass

    @abstractmethod
    def update_product(self, product: Product) -> bool:
        """
        Update existing product.

        Args:
            product: Product to update

        Returns:
            bool: True if successful
        """
        pass

    @abstractmethod
    def batch_process_products(
        self,
        products: List[Product],
        operation: str = "create"
    ) -> SyncResult:
        """
        Process multiple products in batch.

        Args:
            products: List of products to process
            operation: Operation to perform ("create" or "update")

        Returns:
            SyncResult: Batch processing result
        """
        pass