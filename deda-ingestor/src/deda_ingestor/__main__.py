"""Main entry point for the Deda Ingestor application."""
import argparse
import logging.config
import sys
from pathlib import Path
from typing import Optional

import structlog

from .config.settings import config
from .container import container
from .scheduler.job_scheduler import create_scheduler


def configure_logging() -> None:
    """Configure structured logging."""
    logging.config.dictConfig({
        'version': 1,
        'disable_existing_loggers': False,
        'formatters': {
            'json': {
                '()': structlog.stdlib.ProcessorFormatter,
                'processor': structlog.processors.JSONRenderer(),
            },
            'console': {
                '()': structlog.stdlib.ProcessorFormatter,
                'processor': structlog.dev.ConsoleRenderer(),
            },
        },
        'handlers': {
            'console': {
                'class': 'logging.StreamHandler',
                'formatter': 'console',
            },
            'json_file': {
                'class': 'logging.handlers.RotatingFileHandler',
                'filename': Path(config.log.directory) / config.log.app_log_file,
                'maxBytes': 10485760,  # 10MB
                'backupCount': 5,
                'formatter': 'json',
            },
            'error_file': {
                'class': 'logging.handlers.RotatingFileHandler',
                'filename': Path(config.log.directory) / config.log.error_log_file,
                'maxBytes': 10485760,  # 10MB
                'backupCount': 5,
                'formatter': 'json',
                'level': 'ERROR',
            },
        },
        'root': {
            'handlers': ['console', 'json_file', 'error_file'],
            'level': config.log.level,
        },
    })

    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Deda Ingestor - Product synchronization between RabbitMQ and Ivanti"
    )
    parser.add_argument(
        "--run-now",
        action="store_true",
        help="Run the synchronization immediately instead of scheduling"
    )
    parser.add_argument(
        "--config",
        type=str,
        help="Path to custom configuration file"
    )
    return parser.parse_args()


def main() -> Optional[int]:
    """
    Main application entry point.

    Returns:
        Optional[int]: Exit code (0 for success, non-zero for error)
    """
    args = parse_args()

    try:
        # Configure logging
        configure_logging()
        logger = structlog.get_logger(__name__)
        logger.info("Starting Deda Ingestor")

        # Create scheduler
        scheduler = create_scheduler()

        if args.run_now:
            # Run synchronization immediately
            logger.info("Running immediate synchronization")
            scheduler.run_now()
            logger.info("Immediate synchronization completed")
            return 0
        else:
            # Start scheduled operation
            logger.info(
                "Starting scheduled operation",
                schedule_time=config.scheduler.schedule_time,
                timezone=config.scheduler.timezone
            )
            scheduler.start()
            return None  # Scheduler runs indefinitely

    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt, shutting down")
        return 0
    except Exception as e:
        logger.exception("Fatal error", error=str(e))
        return 1


if __name__ == "__main__":
    sys.exit(main())