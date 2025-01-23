"""Base repository interfaces."""
from abc import ABC, abstractmethod
from typing import Any, Generator, Optional, Protocol

from ..core.models import Product, SyncResult


class MessageQueue(Protocol):
    """Protocol for message queue operations."""
    def connect(self) -> None:
        """Establish connection to the message queue."""
        ...

    def disconnect(self) -> None:
        """Close the connection to the message queue."""
        ...

    def get_message(self) -> Optional[Any]:
        """Get a message from the queue."""
        ...

    def acknowledge(self, delivery_tag: int) -> None:
        """Acknowledge message processing."""
        ...

    def reject(self, delivery_tag: int, requeue: bool = False) -> None:
        """Reject message processing."""
        ...


class ProductRepository(ABC):
    """Abstract base class for product repositories."""

    @abstractmethod
    def get_product(self, product_id: str) -> Optional[Product]:
        """
        Retrieve a product by its ID.

        Args:
            product_id: The unique identifier of the product

        Returns:
            Optional[Product]: The product if found, None otherwise
        """
        pass

    @abstractmethod
    def create_product(self, product: Product) -> bool:
        """
        Create a new product.

        Args:
            product: The product to create

        Returns:
            bool: True if creation successful, False otherwise
        """
        pass

    @abstractmethod
    def update_product(self, product: Product) -> bool:
        """
        Update an existing product.

        Args:
            product: The product to update

        Returns:
            bool: True if update successful, False otherwise
        """
        pass

    @abstractmethod
    def delete_product(self, product_id: str) -> bool:
        """
        Delete a product by its ID.

        Args:
            product_id: The unique identifier of the product to delete

        Returns:
            bool: True if deletion successful, False otherwise
        """
        pass


class MessageQueueRepository(ABC):
    """Abstract base class for message queue repositories."""

    @abstractmethod
    def connect(self) -> None:
        """Establish connection to the message queue."""
        pass

    @abstractmethod
    def disconnect(self) -> None:
        """Close the connection to the message queue."""
        pass

    @abstractmethod
    def consume_messages(self) -> Generator[tuple[Any, int], None, None]:
        """
        Consume messages from the queue.

        Yields:
            tuple[Any, int]: Tuple of (message content, delivery tag)
        """
        pass

    @abstractmethod
    def acknowledge_message(self, delivery_tag: int) -> None:
        """
        Acknowledge message processing.

        Args:
            delivery_tag: The delivery tag of the message to acknowledge
        """
        pass

    @abstractmethod
    def reject_message(self, delivery_tag: int, requeue: bool = False) -> None:
        """
        Reject message processing.

        Args:
            delivery_tag: The delivery tag of the message to reject
            requeue: Whether to requeue the message
        """
        pass