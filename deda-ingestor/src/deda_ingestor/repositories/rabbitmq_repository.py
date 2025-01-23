"""RabbitMQ repository implementation."""
import json
from typing import Any, Generator, Optional

import pika
from pika.adapters.blocking_connection import BlockingChannel
from pika.credentials import PlainCredentials
from pika.spec import Basic, BasicProperties
from tenacity import retry, stop_after_attempt, wait_exponential

from ..config.settings import RabbitMQConfig
from ..core.models import Product
from .base import MessageQueueRepository


class RabbitMQRepository(MessageQueueRepository):
    """Repository for interacting with RabbitMQ."""

    def __init__(self, config: RabbitMQConfig):
        """
        Initialize RabbitMQ repository.

        Args:
            config: RabbitMQ configuration
        """
        self.config = config
        self._connection: Optional[pika.BlockingConnection] = None
        self._channel: Optional[BlockingChannel] = None

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10)
    )
    def connect(self) -> None:
        """
        Establish connection to RabbitMQ.

        Raises:
            pika.exceptions.AMQPConnectionError: If connection fails
        """
        if self._connection and not self._connection.is_closed:
            return

        # Create connection parameters
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
            # Set client properties for better identification in management UI
            client_properties={
                'connection_name': 'deda_ingestor',
                'product': 'Deda Ingestor',
                'version': '0.1.0'
            }
        )

        # Establish connection
        self._connection = pika.BlockingConnection(parameters)
        self._channel = self._connection.channel()

        # Declare queue (ensure it exists)
        self._channel.queue_declare(
            queue=self.config.queue,
            durable=True,  # Survive broker restarts
            arguments={
                'x-message-ttl': 86400000,  # 24 hours in milliseconds
                'x-dead-letter-exchange': '',
                'x-dead-letter-routing-key': f"{self.config.queue}_dlq"
            }
        )

        # Declare Dead Letter Queue (DLQ)
        self._channel.queue_declare(
            queue=f"{self.config.queue}_dlq",
            durable=True
        )

    def disconnect(self) -> None:
        """Close the RabbitMQ connection."""
        if self._connection and not self._connection.is_closed:
            self._connection.close()
        self._connection = None
        self._channel = None

    def consume_messages(self) -> Generator[tuple[Any, int], None, None]:
        """
        Consume messages from the queue.

        Yields:
            tuple[Any, int]: Tuple of (message content, delivery tag)

        Raises:
            ValueError: If not connected to RabbitMQ
            json.JSONDecodeError: If message is not valid JSON
        """
        if not self._channel:
            raise ValueError("Not connected to RabbitMQ")

        # Set QoS (prefetch count)
        self._channel.basic_qos(prefetch_count=1)

        # Start consuming messages
        for method_frame, properties, body in self._channel.consume(
            queue=self.config.queue,
            auto_ack=False
        ):
            if not method_frame:
                continue

            try:
                # Parse message body
                message = json.loads(body.decode('utf-8'))
                yield message, method_frame.delivery_tag
            except json.JSONDecodeError:
                # Reject malformed messages
                self.reject_message(method_frame.delivery_tag, requeue=False)
                continue

    def acknowledge_message(self, delivery_tag: int) -> None:
        """
        Acknowledge message processing.

        Args:
            delivery_tag: The delivery tag of the message to acknowledge

        Raises:
            ValueError: If not connected to RabbitMQ
        """
        if not self._channel:
            raise ValueError("Not connected to RabbitMQ")
        
        self._channel.basic_ack(delivery_tag)

    def reject_message(self, delivery_tag: int, requeue: bool = False) -> None:
        """
        Reject message processing.

        Args:
            delivery_tag: The delivery tag of the message to reject
            requeue: Whether to requeue the message

        Raises:
            ValueError: If not connected to RabbitMQ
        """
        if not self._channel:
            raise ValueError("Not connected to RabbitMQ")
        
        self._channel.basic_reject(delivery_tag, requeue=requeue)

    def __enter__(self) -> 'RabbitMQRepository':
        """Context manager entry."""
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Context manager exit."""
        self.disconnect()