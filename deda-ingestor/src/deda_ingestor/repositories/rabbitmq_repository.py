"""RabbitMQ repository implementation."""
import json
from contextlib import contextmanager
from typing import Any, Generator, Optional

import pika
from pika.adapters.blocking_connection import BlockingChannel
from pika.credentials import PlainCredentials
from pika.exceptions import (
    AMQPConnectionError,
    AMQPChannelError,
    StreamLostError
)

from ..config.settings import RabbitMQConfig
from ..core.exceptions import (
    ConnectionError,
    MessageProcessingError,
    RetryableConnectionError
)
from ..utils.logging import get_logger
from ..utils.retry import RetryConfig
from .base import MessageQueueRepository

logger = get_logger()


class RabbitMQRepository(MessageQueueRepository):
    """Repository for interacting with RabbitMQ."""

    def __init__(
        self,
        config: RabbitMQConfig,
        retry_config: Optional[RetryConfig] = None
    ):
        """
        Initialize RabbitMQ repository.

        Args:
            config: RabbitMQ configuration
            retry_config: Retry configuration
        """
        super().__init__(retry_config)
        self.config = config
        self._connection: Optional[pika.BlockingConnection] = None
        self._channel: Optional[BlockingChannel] = None

    def connect(self) -> None:
        """
        Establish connection to RabbitMQ.

        Raises:
            RetryableConnectionError: If connection fails temporarily
            ConnectionError: If connection fails permanently
        """
        if self.is_connected():
            return

        try:
            logger.info(
                "Connecting to RabbitMQ",
                host=self.config.host,
                port=self.config.port
            )

            credentials = PlainCredentials(
                username=self.config.username,
                password=self.config.password
            )
            
            parameters = pika.ConnectionParameters(
                host=self.config.host,
                port=self.config.port,
                credentials=credentials,
                heartbeat=600,
                connection_attempts=3,
                retry_delay=5,
                client_properties={
                    'connection_name': 'deda_ingestor',
                    'product': 'Deda Ingestor',
                    'version': '0.1.0'
                }
            )

            self._connection = pika.BlockingConnection(parameters)
            self._channel = self._connection.channel()

            self._setup_queues()
            logger.info("Successfully connected to RabbitMQ")

        except AMQPConnectionError as e:
            raise RetryableConnectionError(
                f"Failed to connect to RabbitMQ: {str(e)}",
                details={
                    "host": self.config.host,
                    "port": self.config.port
                }
            ) from e
        except Exception as e:
            raise ConnectionError(
                f"Unexpected error connecting to RabbitMQ: {str(e)}"
            ) from e

    def _setup_queues(self) -> None:
        """
        Set up required queues and exchanges.

        Raises:
            MessageProcessingError: If queue setup fails
        """
        try:
            # Declare main queue
            self._channel.queue_declare(
                queue=self.config.queue,
                durable=True,
                arguments={
                    'x-message-ttl': 86400000,  # 24 hours
                    'x-dead-letter-exchange': '',
                    'x-dead-letter-routing-key': f"{self.config.queue}_dlq"
                }
            )

            # Declare Dead Letter Queue (DLQ)
            self._channel.queue_declare(
                queue=f"{self.config.queue}_dlq",
                durable=True
            )

            logger.debug("Queues set up successfully")

        except Exception as e:
            raise MessageProcessingError(
                f"Failed to set up queues: {str(e)}"
            ) from e

    def disconnect(self) -> None:
        """Close the RabbitMQ connection."""
        if self._connection and not self._connection.is_closed:
            logger.info("Closing RabbitMQ connection")
            try:
                self._connection.close()
            except Exception as e:
                logger.warning(f"Error closing connection: {str(e)}")
            finally:
                self._connection = None
                self._channel = None

    def is_connected(self) -> bool:
        """
        Check if connection is active.

        Returns:
            bool: True if connected
        """
        return (
            self._connection is not None
            and not self._connection.is_closed
            and self._channel is not None
            and not self._channel.is_closed
        )

    def reconnect(self) -> None:
        """
        Re-establish connection.

        Raises:
            RetryableConnectionError: If reconnection fails
        """
        logger.info("Attempting to reconnect to RabbitMQ")
        self.disconnect()
        self.connect()

    @contextmanager
    def _ensure_connection(self):
        """
        Context manager to ensure connection is active.

        Raises:
            RetryableConnectionError: If connection cannot be established
        """
        if not self.is_connected():
            self.connect()
        try:
            yield
        except (AMQPConnectionError, StreamLostError) as e:
            logger.warning("Lost connection to RabbitMQ, attempting to reconnect")
            self.reconnect()
            raise RetryableConnectionError(
                "Lost connection to RabbitMQ",
                details={"error": str(e)}
            ) from e

    def consume_messages(self) -> Generator[tuple[Any, int], None, None]:
        """
        Consume messages from the queue.

        Yields:
            tuple[Any, int]: Tuple of (message content, delivery tag)

        Raises:
            ConnectionError: If connection fails
            MessageProcessingError: If message processing fails
        """
        with self._ensure_connection():
            try:
                self._channel.basic_qos(prefetch_count=1)
                
                for method_frame, properties, body in self._channel.consume(
                    queue=self.config.queue,
                    auto_ack=False
                ):
                    if not method_frame:
                        continue

                    try:
                        message = json.loads(body.decode('utf-8'))
                        logger.debug(
                            "Received message",
                            delivery_tag=method_frame.delivery_tag
                        )
                        yield message, method_frame.delivery_tag

                    except json.JSONDecodeError as e:
                        logger.error(
                            "Invalid JSON in message",
                            error=str(e),
                            body=body.decode('utf-8', errors='replace')
                        )
                        self.reject_message(method_frame.delivery_tag, requeue=False)
                        continue

            except AMQPChannelError as e:
                raise MessageProcessingError(
                    f"Channel error while consuming messages: {str(e)}"
                ) from e
            except Exception as e:
                raise MessageProcessingError(
                    f"Unexpected error while consuming messages: {str(e)}"
                ) from e

    def acknowledge_message(self, delivery_tag: int) -> None:
        """
        Acknowledge message processing.

        Args:
            delivery_tag: Message delivery tag

        Raises:
            ConnectionError: If connection fails
            MessageProcessingError: If acknowledgment fails
        """
        with self._ensure_connection():
            try:
                self._channel.basic_ack(delivery_tag)
                logger.debug("Acknowledged message", delivery_tag=delivery_tag)
            except Exception as e:
                raise MessageProcessingError(
                    f"Failed to acknowledge message: {str(e)}",
                    details={"delivery_tag": delivery_tag}
                ) from e

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
        with self._ensure_connection():
            try:
                self._channel.basic_reject(delivery_tag, requeue=requeue)
                logger.debug(
                    "Rejected message",
                    delivery_tag=delivery_tag,
                    requeue=requeue
                )
            except Exception as e:
                raise MessageProcessingError(
                    f"Failed to reject message: {str(e)}",
                    details={
                        "delivery_tag": delivery_tag,
                        "requeue": requeue
                    }
                ) from e

    def health_check(self) -> bool:
        """
        Check repository health.

        Returns:
            bool: True if repository is healthy
        """
        try:
            if not self.is_connected():
                self.connect()
            return True
        except Exception as e:
            logger.error("Health check failed", error=str(e))
            return False

    def __enter__(self) -> 'RabbitMQRepository':
        """Context manager entry."""
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Context manager exit."""
        self.disconnect()