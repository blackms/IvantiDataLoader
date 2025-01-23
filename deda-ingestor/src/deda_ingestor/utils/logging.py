"""Logging configuration using loguru."""
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Union

from loguru import logger

from ..config.settings import LogConfig
from ..core.exceptions import ConfigurationError


class LoggingManager:
    """Manager for configuring and handling logging."""

    def __init__(self, config: LogConfig):
        """
        Initialize logging manager.

        Args:
            config: Logging configuration
        """
        self.config = config
        self._configure_logging()

    def _configure_logging(self) -> None:
        """Configure loguru logger with appropriate sinks and formats."""
        try:
            # Create log directory if it doesn't exist
            log_dir = Path(self.config.directory)
            log_dir.mkdir(parents=True, exist_ok=True)

            # Remove default handler
            logger.remove()

            # Add console handler with custom format
            logger.add(
                sys.stderr,
                format=self._get_console_format(),
                level=self.config.level,
                backtrace=True,
                diagnose=True,
            )

            # Add file handler for general logs
            logger.add(
                log_dir / self.config.app_log_file,
                format=self._get_file_format(),
                level=self.config.level,
                rotation="10 MB",
                retention="30 days",
                compression="gz",
                serialize=True,
                backtrace=True,
                diagnose=True,
            )

            # Add file handler for error logs
            logger.add(
                log_dir / self.config.error_log_file,
                format=self._get_file_format(),
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
                log_dir / self.config.sync_report_file,
                format=self._get_report_format(),
                level="INFO",
                filter=self._is_sync_report,
                rotation="1 day",
                retention="90 days",
                compression="gz",
                serialize=True,
            )

        except Exception as e:
            raise ConfigurationError(f"Failed to configure logging: {str(e)}")

    def _get_console_format(self) -> str:
        """Get format string for console output."""
        return (
            "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
            "<level>{level: <8}</level> | "
            "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
            "<level>{message}</level>"
        )

    def _get_file_format(self) -> str:
        """Get format string for file output."""
        return (
            "{time:YYYY-MM-DD HH:mm:ss} | "
            "{level: <8} | "
            "process:{process} | "
            "thread:{thread} | "
            "{name}:{function}:{line} | "
            "{message}"
        )

    def _get_report_format(self) -> str:
        """Get format string for sync reports."""
        return "{message}"

    def _is_sync_report(self, record: Dict[str, Any]) -> bool:
        """
        Filter for sync report messages.

        Args:
            record: Log record

        Returns:
            bool: True if record is a sync report
        """
        return record["extra"].get("report_type") == "sync"

    @staticmethod
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

    @staticmethod
    def log_sync_report(report_data: Dict[str, Any]) -> None:
        """
        Log synchronization report.

        Args:
            report_data: Report data to log
        """
        report_data["timestamp"] = datetime.utcnow().isoformat()
        logger.bind(report_type="sync").info(report_data)

    @staticmethod
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


# Create global logger instance
log_manager: LoggingManager = None


def init_logging(config: LogConfig) -> None:
    """
    Initialize logging configuration.

    Args:
        config: Logging configuration
    """
    global log_manager
    log_manager = LoggingManager(config)


def get_logger():
    """Get configured logger instance."""
    if log_manager is None:
        raise RuntimeError("Logging not initialized. Call init_logging first.")
    return logger