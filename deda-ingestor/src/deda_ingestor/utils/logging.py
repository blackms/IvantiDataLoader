"""Logging configuration using loguru."""
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional, Union

from loguru import logger

from ..config.settings import LogConfig


def configure_logging(config: LogConfig) -> None:
    """
    Configure loguru logger with appropriate sinks and formats.

    Args:
        config: Logging configuration
    """
    # Remove default handler
    logger.remove()

    # Add console handler with custom format
    logger.add(
        sys.stderr,
        format=_get_console_format(),
        level=config.level,
        backtrace=True,
        diagnose=True,
    )

    # Add file handler for general logs
    logger.add(
        config.directory / config.app_log_file,
        format=_get_file_format(),
        level=config.level,
        rotation="10 MB",
        retention="30 days",
        compression="gz",
        serialize=True,
        backtrace=True,
        diagnose=True,
    )

    # Add file handler for error logs
    logger.add(
        config.directory / config.error_log_file,
        format=_get_file_format(),
        level="ERROR",
        rotation="10 MB",
        retention="60 days",
        compression="gz",
        serialize=True,
        backtrace=True,
        diagnose=True,
    )

    # Add file handler for sync reports
    logger.add(
        config.directory / config.sync_report_file,
        format=_get_report_format(),
        level="INFO",
        filter=_is_sync_report,
        rotation="1 day",
        retention="90 days",
        compression="gz",
        serialize=True,
    )


def _get_console_format() -> str:
    """Get format string for console output."""
    return (
        "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
        "<level>{level: <8}</level> | "
        "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
        "<level>{message}</level>"
    )


def _get_file_format() -> str:
    """Get format string for file output."""
    return (
        "{time:YYYY-MM-DD HH:mm:ss} | "
        "{level: <8} | "
        "process:{process} | "
        "thread:{thread} | "
        "{name}:{function}:{line} | "
        "{message}"
    )


def _get_report_format() -> str:
    """Get format string for sync reports."""
    return "{message}"


def _is_sync_report(record: Dict[str, Any]) -> bool:
    """
    Filter for sync report messages.

    Args:
        record: Log record

    Returns:
        bool: True if record is a sync report
    """
    return record["extra"].get("report_type") == "sync"


def init_logging(config: LogConfig) -> None:
    """
    Initialize logging configuration.

    Args:
        config: Logging configuration
    """
    configure_logging(config)


def get_logger():
    """Get configured logger instance."""
    return logger


def log_exception(
    exc: Exception,
    context: Dict[str, Any] = None,
    level: str = "ERROR"
) -> None:
    """
    Log an exception with context.

    Args:
        exc: Exception to log
        context: Additional context information
        level: Log level
    """
    context = context or {}
    logger.opt(exception=True).log(
        level,
        "Exception occurred: {exc}",
        exc=str(exc),
        **context
    )


def log_sync_report(report_data: Dict[str, Any]) -> None:
    """
    Log synchronization report.

    Args:
        report_data: Report data to log
    """
    report_data["timestamp"] = datetime.utcnow().isoformat()
    logger.bind(report_type="sync").info(report_data)


def format_error_context(
    error: Union[Exception, str],
    context: Dict[str, Any] = None
) -> Dict[str, Any]:
    """
    Format error context for logging.

    Args:
        error: Error to format
        context: Additional context information

    Returns:
        Dict[str, Any]: Formatted error context
    """
    error_context = {
        "error_type": type(error).__name__ if isinstance(error, Exception) else "str",
        "error_message": str(error),
        "timestamp": datetime.utcnow().isoformat()
    }

    if context:
        error_context.update(context)

    if isinstance(error, Exception) and hasattr(error, "__dict__"):
        error_context.update({
            k: v for k, v in error.__dict__.items()
            if not k.startswith("_") and isinstance(v, (str, int, float, bool, dict, list))
        })

    return error_context


# Initialize logger with default configuration for tests
if "pytest" in sys.modules:
    init_logging(LogConfig(
        level="DEBUG",
        directory=Path("tests/logs"),
        app_log_file="test_app.log",
        error_log_file="test_error.log",
        sync_report_file="test_sync_report.log"
    ))