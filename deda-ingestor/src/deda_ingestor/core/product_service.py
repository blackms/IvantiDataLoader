"""Core service for handling product synchronization."""
import json
import logging
from typing import Optional

import structlog

from ..adapters.product_adapter import ProductAdapter
from ..core.models import Product, SyncResult
from ..repositories.base import MessageQueueRepository, ProductRepository

logger = structlog.get_logger(__name__)


class ProductService:
    """Service for handling product synchronization between RabbitMQ and Ivanti."""

    def __init__(
        self,
        message_queue: MessageQueueRepository,
        product_repository: ProductRepository,
        max_retries: int = 3
    ):
        """
        Initialize ProductService.

        Args:
            message_queue: Repository for message queue operations
            product_repository: Repository for product operations
            max_retries: Maximum number of retries for failed operations
        """
        self.message_queue = message_queue
        self.product_repository = product_repository
        self.max_retries = max_retries
        self.sync_result = SyncResult()

    def process_messages(self) -> SyncResult:
        """
        Process messages from the queue and sync with Ivanti.

        Returns:
            SyncResult: Results of the synchronization process
        """
        logger.info("Starting product synchronization")

        try:
            # Process messages from queue
            for message, delivery_tag in self.message_queue.consume_messages():
                try:
                    success = self._process_single_message(message)
                    if success:
                        self.message_queue.acknowledge_message(delivery_tag)
                    else:
                        # If processing failed, reject and don't requeue
                        self.message_queue.reject_message(delivery_tag, requeue=False)
                except Exception as e:
                    logger.exception(
                        "Error processing message",
                        error=str(e),
                        delivery_tag=delivery_tag
                    )
                    self.message_queue.reject_message(delivery_tag, requeue=False)
                    self.sync_result.record_failure(
                        str(delivery_tag),
                        f"Processing error: {str(e)}"
                    )

        except Exception as e:
            logger.exception("Fatal error during message processing", error=str(e))
            raise

        finally:
            self.sync_result.complete()
            self._log_sync_results()

        return self.sync_result

    def _process_single_message(self, message: dict) -> bool:
        """
        Process a single message from the queue.

        Args:
            message: The message to process

        Returns:
            bool: True if processing was successful, False otherwise
        """
        try:
            # Convert message to domain model
            product = ProductAdapter.from_rabbitmq_message(message)
            
            # Check if product already exists
            existing_product = self.product_repository.get_product(product.product_id)
            
            if existing_product:
                success = self._update_product(product)
            else:
                success = self._create_product(product)
            
            return success

        except ValueError as e:
            logger.error(
                "Invalid message format",
                error=str(e),
                message=json.dumps(message)
            )
            self.sync_result.record_failure(
                message.get("productId", "unknown"),
                f"Invalid message format: {str(e)}"
            )
            return False

        except Exception as e:
            logger.exception(
                "Error processing product",
                error=str(e),
                product_id=message.get("productId", "unknown")
            )
            self.sync_result.record_failure(
                message.get("productId", "unknown"),
                f"Processing error: {str(e)}"
            )
            return False

    def _create_product(self, product: Product) -> bool:
        """
        Create a new product in Ivanti.

        Args:
            product: The product to create

        Returns:
            bool: True if creation was successful, False otherwise
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
                self.sync_result.record_failure(
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
            self.sync_result.record_failure(
                product.product_id,
                f"Creation error: {str(e)}"
            )
            return False

    def _update_product(self, product: Product) -> bool:
        """
        Update an existing product in Ivanti.

        Args:
            product: The product to update

        Returns:
            bool: True if update was successful, False otherwise
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
                self.sync_result.record_failure(
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
            self.sync_result.record_failure(
                product.product_id,
                f"Update error: {str(e)}"
            )
            return False

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
                "Synchronization errors",
                errors=self.sync_result.errors
            )