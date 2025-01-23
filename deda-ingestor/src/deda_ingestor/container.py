"""Dependency injection container configuration."""
from dependency_injector import containers, providers
from dependency_injector.providers import Configuration, Singleton

from .config.settings import (
    AppConfig,
    RabbitMQConfig,
    IvantiConfig,
    LogConfig,
    SchedulerConfig
)
from .core.product_service import ProductService
from .repositories.rabbitmq_repository import RabbitMQRepository
from .repositories.ivanti_repository import IvantiRepository


class Container(containers.DeclarativeContainer):
    """Dependency injection container."""

    # Configuration
    config = providers.Singleton(AppConfig)

    # Logging configuration provider
    log_config = providers.Singleton(
        LogConfig,
        level=config.provided.log.level,
        directory=config.provided.log.directory,
        app_log_file=config.provided.log.app_log_file,
        error_log_file=config.provided.log.error_log_file,
        sync_report_file=config.provided.log.sync_report_file,
    )

    # RabbitMQ configuration and repository
    rabbitmq_config = providers.Singleton(
        RabbitMQConfig,
        host=config.provided.rabbitmq.host,
        port=config.provided.rabbitmq.port,
        username=config.provided.rabbitmq.username,
        password=config.provided.rabbitmq.password,
        queue=config.provided.rabbitmq.queue,
        connection_retry_count=config.provided.rabbitmq.connection_retry_count,
        connection_retry_delay=config.provided.rabbitmq.connection_retry_delay,
    )

    rabbitmq_repository = providers.Singleton(
        RabbitMQRepository,
        config=rabbitmq_config,
    )

    # Ivanti configuration and repository
    ivanti_config = providers.Singleton(
        IvantiConfig,
        api_url=config.provided.ivanti.api_url,
        api_key=config.provided.ivanti.api_key,
        client_id=config.provided.ivanti.client_id,
        client_secret=config.provided.ivanti.client_secret,
        token_url=config.provided.ivanti.token_url,
        request_timeout=config.provided.ivanti.request_timeout,
        max_retries=config.provided.ivanti.max_retries,
        retry_delay=config.provided.ivanti.retry_delay,
    )

    ivanti_repository = providers.Singleton(
        IvantiRepository,
        config=ivanti_config,
    )

    # Scheduler configuration
    scheduler_config = providers.Singleton(
        SchedulerConfig,
        schedule_time=config.provided.scheduler.schedule_time,
        timezone=config.provided.scheduler.timezone,
    )

    # Core service
    product_service = providers.Singleton(
        ProductService,
        message_queue=rabbitmq_repository,
        product_repository=ivanti_repository,
        max_retries=config.provided.ivanti.max_retries,
    )


# Create and configure container instance
container = Container()

# Wire the container (this enables dependency injection in FastAPI routes if we add them later)
container.wire(modules=[
    "deda_ingestor.core.product_service",
    "deda_ingestor.repositories.rabbitmq_repository",
    "deda_ingestor.repositories.ivanti_repository",
])