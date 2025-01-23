"""Base repository interfaces and abstract classes."""
from abc import ABC, abstractmethod
from typing import Any, Generator, Optional, Protocol, TypeVar

from ..core.exceptions import (
    ConnectionError,
    RetryableError,
    MessageProcessingError
)
from ..core.models import Product, SyncResult
from ..utils.logging import get_logger
from ..utils.retry import retry_with_backoff, RetryConfig

logger = get_logger()

T = TypeVar("T")


class ConnectionManager(Protocol):
    """Protocol for connection management."""

    def connect(self) -> None:
        """Establish connection."""
        ...

    def disconnect(self) -> None:
        """Close connection."""
        ...

    def is_connected(self) -> bool:
        """Check if connection is active."""
        ...

    def reconnect(self) -> None:
        """Re-establish connection."""
        ...


class Repository(ABC):
    """Base repository interface."""

    @abstractmethod
    def health_check(self) -> bool:
        """
        Check repository health.

        Returns:
            bool: True if repository is healthy
        """
        pass


class MessageQueue(Protocol):
    """Protocol for message queue operations."""

    def get_message(self) -> Optional[Any]:
        """
        Get a message from the queue.

        Returns:
            Optional[Any]: Message if available, None otherwise
        """
        ...

    def acknowledge(self, delivery_tag: int) -> None:
        """
        Acknowledge message processing.

        Args:
            delivery_tag: Message delivery tag
        """
        ...

    def reject(self, delivery_tag: int, requeue: bool = False) -> None:
        """
        Reject message processing.

        Args:
            delivery_tag: Message delivery tag
            requeue: Whether to requeue the message
        """
        ...


class MessageQueueRepository(Repository, ConnectionManager):
    """Abstract base class for message queue repositories."""

    def __init__(self, retry_config: Optional[RetryConfig] = None):
        """
        Initialize repository.

        Args:
            retry_config: Retry configuration
        """
        self.retry_config = retry_config or RetryConfig()

    @retry_with_backoff(
        retryable_exceptions=RetryableError,
        config=RetryConfig(max_attempts=3)
    )
    @abstractmethod
    def consume_messages(self) -> Generator[tuple[Any, int], None, None]:
        """
        Consume messages from the queue.

        Yields:
            tuple[Any, int]: Tuple of (message content, delivery tag)

        Raises:
            ConnectionError: If connection fails
            MessageProcessingError: If message processing fails
        """
        pass

    @retry_with_backoff(
        retryable_exceptions=RetryableError,
        config=RetryConfig(max_attempts=3)
    )
    @abstractmethod
    def acknowledge_message(self, delivery_tag: int) -> None:
        """
        Acknowledge message processing.

        Args:
            delivery_tag: Message delivery tag

        Raises:
            ConnectionError: If connection fails
            MessageProcessingError: If acknowledgment fails
        """
        pass

    @retry_with_backoff(
        retryable_exceptions=RetryableError,
        config=RetryConfig(max_attempts=3)
    )
    @abstractmethod
    def reject_message(self, delivery_tag: int, requeue: bool = False) -> None:
        """
        Reject message processing.

        Args:
            delivery_tag: Message delivery tag
            requeue: Whether to requeue the message

        Raises:
            ConnectionError: If connection fails
            MessageProcessingError: If rejection fails
        """
        pass


class ProductRepository(Repository, ConnectionManager):
    """Abstract base class for product repositories."""

    def __init__(self, retry_config: Optional[RetryConfig] = None):
        """
        Initialize repository.

        Args:
            retry_config: Retry configuration
        """
        self.retry_config = retry_config or RetryConfig()

    @retry_with_backoff(
        retryable_exceptions=RetryableError,
        config=RetryConfig(max_attempts=3)
    )
    @abstractmethod
    def get_product(self, product_id: str) -> Optional[Product]:
        """
        Retrieve a product by its ID.

        Args:
            product_id: Product ID

        Returns:
            Optional[Product]: Product if found, None otherwise

        Raises:
            ConnectionError: If connection fails
            MessageProcessingError: If retrieval fails
        """
        pass

    @retry_with_backoff(
        retryable_exceptions=RetryableError,
        config=RetryConfig(max_attempts=3)
    )
    @abstractmethod
    def create_product(self, product: Product) -> bool:
        """
        Create a new product.

        Args:
            product: Product to create

        Returns:
            bool: True if creation successful

        Raises:
            ConnectionError: If connection fails
            MessageProcessingError: If creation fails
        """
        pass

    @retry_with_backoff(
        retryable_exceptions=RetryableError,
        config=RetryConfig(max_attempts=3)
    )
    @abstractmethod
    def update_product(self, product: Product) -> bool:
        """
        Update an existing product.

        Args:
            product: Product to update

        Returns:
            bool: True if update successful

        Raises:
            ConnectionError: If connection fails
            MessageProcessingError: If update fails
        """
        pass

    @retry_with_backoff(
        retryable_exceptions=RetryableError,
        config=RetryConfig(max_attempts=3)
    )
    @abstractmethod
    def delete_product(self, product_id: str) -> bool:
        """
        Delete a product.

        Args:
            product_id: Product ID

        Returns:
            bool: True if deletion successful

        Raises:
            ConnectionError: If connection fails
            MessageProcessingError: If deletion fails
        """
        pass

    @abstractmethod
    def batch_process_products(
        self,
        products: list[Product],
        operation: str
    ) -> SyncResult:
        """
        Process multiple products in batch.

        Args:
            products: List of products to process
            operation: Operation to perform ('create' or 'update')

        Returns:
            SyncResult: Results of the batch operation

        Raises:
            ConnectionError: If connection fails
            MessageProcessingError: If processing fails
        """
        pass