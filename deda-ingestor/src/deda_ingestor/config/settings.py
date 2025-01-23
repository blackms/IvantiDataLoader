"""Configuration settings for the Deda Ingestor application."""
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()


@dataclass
class RabbitMQConfig:
    """RabbitMQ connection configuration."""
    host: str = os.getenv("RABBITMQ_HOST", "localhost")
    port: int = int(os.getenv("RABBITMQ_PORT", "5672"))
    username: str = os.getenv("RABBITMQ_USER", "guest")
    password: str = os.getenv("RABBITMQ_PASSWORD", "guest")
    queue: str = os.getenv("RABBITMQ_QUEUE", "products_queue")
    connection_retry_count: int = int(os.getenv("RABBITMQ_RETRY_COUNT", "3"))
    connection_retry_delay: int = int(os.getenv("RABBITMQ_RETRY_DELAY", "5"))


@dataclass
class IvantiConfig:
    """Ivanti API configuration."""
    api_url: str = os.getenv("IVANTI_API_URL", "")
    api_key: str = os.getenv("IVANTI_API_KEY", "")
    client_id: str = os.getenv("IVANTI_CLIENT_ID", "")
    client_secret: str = os.getenv("IVANTI_CLIENT_SECRET", "")
    token_url: str = os.getenv("IVANTI_TOKEN_URL", "")
    request_timeout: int = int(os.getenv("IVANTI_REQUEST_TIMEOUT", "30"))
    max_retries: int = int(os.getenv("IVANTI_MAX_RETRIES", "3"))
    retry_delay: int = int(os.getenv("IVANTI_RETRY_DELAY", "5"))


@dataclass
class LogConfig:
    """Logging configuration."""
    level: str = os.getenv("LOG_LEVEL", "INFO")
    directory: Path = field(
        default_factory=lambda: Path(os.getenv("LOG_DIR", "logs"))
    )
    app_log_file: str = "app.log"
    error_log_file: str = "error.log"
    sync_report_file: str = "sync_report.log"


@dataclass
class SchedulerConfig:
    """Scheduler configuration."""
    schedule_time: str = os.getenv("SCHEDULE_TIME", "02:00")
    timezone: str = os.getenv("TIMEZONE", "UTC")


@dataclass
class AppConfig:
    """Main application configuration."""
    rabbitmq: RabbitMQConfig = field(default_factory=RabbitMQConfig)
    ivanti: IvantiConfig = field(default_factory=IvantiConfig)
    log: LogConfig = field(default_factory=LogConfig)
    scheduler: SchedulerConfig = field(default_factory=SchedulerConfig)
    environment: str = os.getenv("ENVIRONMENT", "development")
    debug: bool = os.getenv("DEBUG", "false").lower() == "true"

    def __post_init__(self):
        """Validate configuration and create necessary directories."""
        if self.environment != "test":
            self._validate_config()
        self._create_directories()

    def _validate_config(self) -> None:
        """Validate required configuration values."""
        if not self.ivanti.api_url:
            raise ValueError("IVANTI_API_URL must be set")
        if not self.ivanti.api_key:
            raise ValueError("IVANTI_API_KEY must be set")
        if not self.ivanti.client_id or not self.ivanti.client_secret:
            raise ValueError("IVANTI_CLIENT_ID and IVANTI_CLIENT_SECRET must be set")

    def _create_directories(self) -> None:
        """Create necessary directories if they don't exist."""
        if self.environment != "test":
            self.log.directory.mkdir(parents=True, exist_ok=True)


# Set test environment for pytest
if "PYTEST_CURRENT_TEST" in os.environ:
    os.environ["ENVIRONMENT"] = "test"

# Create global config instance
config = AppConfig()