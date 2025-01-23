"""Pytest configuration and fixtures."""
import os
from pathlib import Path

# Set test environment first
os.environ["ENVIRONMENT"] = "test"

# Configure test paths
TEST_DIR = Path(__file__).parent
FIXTURES_DIR = TEST_DIR / "fixtures"
LOG_DIR = TEST_DIR / "logs"

# Create test directories
FIXTURES_DIR.mkdir(exist_ok=True)
LOG_DIR.mkdir(exist_ok=True)

# Configure test environment variables before any imports
os.environ.update({
    "ENVIRONMENT": "test",
    "IVANTI_API_URL": "https://ivanti-test-api.example.com",
    "IVANTI_API_KEY": "test-api-key",
    "IVANTI_CLIENT_ID": "test-client-id",
    "IVANTI_CLIENT_SECRET": "test-client-secret",
    "IVANTI_TOKEN_URL": "https://ivanti-test-api.example.com/oauth/token",
    "LOG_DIR": str(LOG_DIR),
    "LOG_LEVEL": "DEBUG",
    "RABBITMQ_HOST": "localhost",
    "RABBITMQ_PORT": "5672",
    "RABBITMQ_USER": "guest",
    "RABBITMQ_PASSWORD": "guest",
    "RABBITMQ_QUEUE": "test_queue"
})

# Import after environment setup
import pytest
from loguru import logger

from deda_ingestor.config.settings import LogConfig
from deda_ingestor.utils.logging import init_logging


@pytest.fixture(scope="session", autouse=True)
def setup_logging():
    """Initialize logging for tests."""
    # Configure logging
    log_config = LogConfig(
        level="DEBUG",
        directory=LOG_DIR,
        app_log_file="test_app.log",
        error_log_file="test_error.log",
        sync_report_file="test_sync_report.log"
    )
    
    # Remove default logger
    logger.remove()
    
    # Initialize logging
    init_logging(log_config)
    
    yield
    
    # Cleanup logs after all tests
    logger.remove()


@pytest.fixture(autouse=True)
def cleanup_logs():
    """Clean up log files after each test."""
    yield
    
    # Clean up log files
    if LOG_DIR.exists():
        for log_file in LOG_DIR.glob("*.log"):
            try:
                log_file.unlink()
            except FileNotFoundError:
                pass


@pytest.fixture(autouse=True)
def mock_datetime(monkeypatch):
    """Mock datetime to return a fixed value."""
    import datetime
    from datetime import UTC
    
    class MockDateTime:
        @classmethod
        def now(cls, tz=None):
            return datetime.datetime(2024, 1, 23, 12, 0, tzinfo=UTC)
        
        @classmethod
        def utcnow(cls):
            return cls.now(UTC)
    
    monkeypatch.setattr(datetime, 'datetime', MockDateTime)


@pytest.fixture(autouse=True)
def mock_uuid(monkeypatch):
    """Mock UUID to return predictable values."""
    import uuid
    
    class MockUUID:
        _next_id = 1
        
        @classmethod
        def uuid4(cls):
            uuid_str = f"00000000-0000-0000-0000-{cls._next_id:012d}"
            cls._next_id += 1
            return uuid.UUID(uuid_str)
    
    monkeypatch.setattr(uuid, 'uuid4', MockUUID.uuid4)