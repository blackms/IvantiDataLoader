"""Core service for handling product synchronization."""
from typing import Optional

from ..adapters.product_adapter import ProductAdapter
from ..core.exceptions import (
    AdapterError,
    ConnectionError,
    MessageProcessingError,
    RetryableError
)
from ..core.models import Product, SyncResult
from ..repositories.base import MessageQueueRepository, ProductRepository
from ..utils.logging import get_logger
from ..utils.retry import RetryConfig, retry_with_backoff

logger = get_logger()


class ProductService:
    """Service for handling product synchronization between RabbitMQ and Ivanti."""

    def __init__(
        self,
        message_queue: MessageQueueRepository,
        product_repository: ProductRepository,
        retry_config: Optional[RetryConfig] = None
    ):
        """
        Initialize ProductService.

        Args:
            message_queue: Repository for message queue operations
            product_repository: Repository for product operations
            retry_config: Retry configuration
        """
        self.message_queue = message_queue
        self.product_repository = product_repository
        self.retry_config = retry_config or RetryConfig()
        self.sync_result = SyncResult()

    def _validate_repositories(self) -> None:
        """
        Validate repository health.

        Raises:
            ConnectionError: If repositories are not healthy
        """
        if not self.message_queue.health_check():
            raise ConnectionError("Message queue repository is not healthy")
        if not self.product_repository.health_check():
            raise ConnectionError("Product repository is not healthy")

    @retry_with_backoff(
        retryable_exceptions=RetryableError,
        config=RetryConfig(max_attempts=3)
    )
    def process_messages(self) -> SyncResult:
        """
        Process messages from the queue and sync with Ivanti.

        Returns:
            SyncResult: Results of the synchronization process

        Raises:
            ConnectionError: If connection to services fails
            MessageProcessingError: If message processing fails
        """
        logger.info("Starting product synchronization")
        self.sync_result = SyncResult()  # Reset sync result

        try:
            self._validate_repositories()
            self._process_message_batch()

        except Exception as e:
            logger.exception("Fatal error during message processing", error=str(e))
            raise

        finally:
            self.sync_result.complete()
            self._log_sync_results()

        return self.sync_result

    def _process_message_batch(self) -> None:
        """
        Process a batch of messages from the queue.

        Raises:
            ConnectionError: If connection fails
            MessageProcessingError: If processing fails
        """
        try:
            for message, delivery_tag in self.message_queue.consume_messages():
                try:
                    success = self._process_single_message(message)
                    if success:
                        self._acknowledge_message(delivery_tag)
                    else:
                        self._reject_message(delivery_tag)

                except Exception as e:
                    logger.exception(
                        "Error processing message",
                        error=str(e),
                        delivery_tag=delivery_tag
                    )
                    self._reject_message(delivery_tag)
                    self._record_processing_error(str(delivery_tag), e)

        except Exception as e:
            raise MessageProcessingError(
                f"Error during batch processing: {str(e)}"
            ) from e

    def _process_single_message(self, message: dict) -> bool:
        """
        Process a single message from the queue.

        Args:
            message: Message to process

        Returns:
            bool: True if processing was successful

        Raises:
            AdapterError: If message conversion fails
            MessageProcessingError: If processing fails
        """
        try:
            # Convert message to domain model
            product = self._convert_message_to_product(message)
            if not product:
                return False

            # Process the product
            return self._process_product(product)

        except Exception as e:
            if not isinstance(e, (AdapterError, MessageProcessingError)):
                raise MessageProcessingError(
                    f"Unexpected error processing message: {str(e)}"
                ) from e
            raise

    def _convert_message_to_product(self, message: dict) -> Optional[Product]:
        """
        Convert message to Product domain model.

        Args:
            message: Message to convert

        Returns:
            Optional[Product]: Converted product or None if conversion fails

        Raises:
            AdapterError: If conversion fails
        """
        try:
            return ProductAdapter.from_rabbitmq_message(message)
        except Exception as e:
            logger.error(
                "Failed to convert message to product",
                error=str(e),
                message=message
            )
            raise AdapterError(
                f"Failed to convert message to product: {str(e)}",
                details={"message": message}
            ) from e

    def _process_product(self, product: Product) -> bool:
        """
        Process a product by creating or updating in Ivanti.

        Args:
            product: Product to process

        Returns:
            bool: True if processing was successful

        Raises:
            MessageProcessingError: If processing fails
        """
        try:
            # Check if product exists
            existing_product = self.product_repository.get_product(
                product.product_id
            )
            
            if existing_product:
                success = self._update_product(product)
            else:
                success = self._create_product(product)
            
            return success

        except Exception as e:
            raise MessageProcessingError(
                f"Failed to process product {product.product_id}: {str(e)}",
                product_id=product.product_id
            ) from e

    def _create_product(self, product: Product) -> bool:
        """
        Create a new product in Ivanti.

        Args:
            product: Product to create

        Returns:
            bool: True if creation was successful
        """
        try:
            if self.product_repository.create_product(product):
                logger.info(
                    "Product created successfully",
                    product_id=product.product_id
                )
                self.sync_result.record_success()
                return True
            else:
                logger.error(
                    "Failed to create product",
                    product_id=product.product_id
                )
                self._record_processing_error(
                    product.product_id,
                    "Failed to create product"
                )
                return False

        except Exception as e:
            logger.exception(
                "Error creating product",
                error=str(e),
                product_id=product.product_id
            )
            self._record_processing_error(
                product.product_id,
                f"Creation error: {str(e)}"
            )
            return False

    def _update_product(self, product: Product) -> bool:
        """
        Update an existing product in Ivanti.

        Args:
            product: Product to update

        Returns:
            bool: True if update was successful
        """
        try:
            if self.product_repository.update_product(product):
                logger.info(
                    "Product updated successfully",
                    product_id=product.product_id
                )
                self.sync_result.record_success()
                return True
            else:
                logger.error(
                    "Failed to update product",
                    product_id=product.product_id
                )
                self._record_processing_error(
                    product.product_id,
                    "Failed to update product"
                )
                return False

        except Exception as e:
            logger.exception(
                "Error updating product",
                error=str(e),
                product_id=product.product_id
            )
            self._record_processing_error(
                product.product_id,
                f"Update error: {str(e)}"
            )
            return False

    def _acknowledge_message(self, delivery_tag: int) -> None:
        """
        Acknowledge message processing.

        Args:
            delivery_tag: Message delivery tag
        """
        try:
            self.message_queue.acknowledge_message(delivery_tag)
        except Exception as e:
            logger.error(
                "Failed to acknowledge message",
                error=str(e),
                delivery_tag=delivery_tag
            )

    def _reject_message(self, delivery_tag: int) -> None:
        """
        Reject message processing.

        Args:
            delivery_tag: Message delivery tag
        """
        try:
            self.message_queue.reject_message(delivery_tag, requeue=False)
        except Exception as e:
            logger.error(
                "Failed to reject message",
                error=str(e),
                delivery_tag=delivery_tag
            )

    def _record_processing_error(
        self,
        identifier: str,
        error: Exception | str
    ) -> None:
        """
        Record a processing error in the sync result.

        Args:
            identifier: Error identifier (product ID or delivery tag)
            error: Error details
        """
        self.sync_result.record_failure(
            identifier,
            str(error) if isinstance(error, Exception) else error
        )

    def _log_sync_results(self) -> None:
        """Log the synchronization results."""
        logger.info(
            "Product synchronization completed",
            total_processed=self.sync_result.total_processed,
            successful=self.sync_result.successful_syncs,
            failed=self.sync_result.failed_syncs,
            skipped=self.sync_result.skipped_syncs,
            duration_seconds=self.sync_result.duration_seconds,
            success_rate=f"{self.sync_result.success_rate:.2f}%"
        )

        if self.sync_result.errors:
            logger.error(
                "Synchronization errors occurred",
                errors=self.sync_result.errors
            )