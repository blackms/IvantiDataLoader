"""Main entry point for the Deda Ingestor application."""
import argparse
import signal
import sys
from pathlib import Path
from typing import NoReturn, Optional

from dependency_injector.wiring import inject, Provide
from loguru import logger

from .config.settings import config
from .container import Container
from .core.exceptions import DedaIngestorError
from .scheduler.job_scheduler import create_scheduler
from .utils.logging import get_logger

logger = get_logger()


def parse_args() -> argparse.Namespace:
    """
    Parse command line arguments.

    Returns:
        argparse.Namespace: Parsed arguments
    """
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
    parser.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        default=None,
        help="Override the logging level"
    )
    return parser.parse_args()


class Application:
    """Main application class."""

    def __init__(self):
        """Initialize application."""
        self._setup_signal_handlers()
        self.running = True

    def _setup_signal_handlers(self) -> None:
        """Setup signal handlers for graceful shutdown."""
        def handle_shutdown(signum: int, frame) -> None:
            """
            Handle shutdown signals.

            Args:
                signum: Signal number
                frame: Current stack frame
            """
            signal_name = signal.Signals(signum).name
            logger.info(f"Received {signal_name} signal, initiating shutdown")
            self.running = False

        # Register signal handlers
        signal.signal(signal.SIGINT, handle_shutdown)
        signal.signal(signal.SIGTERM, handle_shutdown)

    @inject
    def run(
        self,
        args: argparse.Namespace,
        container: Container = Provide[Container]
    ) -> Optional[int]:
        """
        Run the application.

        Args:
            args: Command line arguments
            container: Dependency injection container

        Returns:
            Optional[int]: Exit code (0 for success, non-zero for error)
        """
        try:
            # Override log level if specified
            if args.log_level:
                config.log.level = args.log_level

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
                
                # Keep running until shutdown signal
                while self.running:
                    signal.pause()
                
                logger.info("Shutting down scheduler")
                scheduler.stop()
                return 0

        except DedaIngestorError as e:
            logger.error(
                "Application error",
                error=str(e),
                details=e.details if hasattr(e, 'details') else None
            )
            return 1
        except Exception as e:
            logger.exception("Unexpected error occurred")
            return 1
        finally:
            self._cleanup()

    def _cleanup(self) -> None:
        """Perform cleanup operations."""
        logger.info("Performing cleanup")
        try:
            # Add any cleanup operations here
            pass
        except Exception as e:
            logger.error(f"Error during cleanup: {str(e)}")


def main() -> NoReturn:
    """
    Main application entry point.

    This function will never return normally, it will always exit
    via sys.exit() with an appropriate status code.
    """
    try:
        # Create and run application
        app = Application()
        exit_code = app.run(parse_args())
        sys.exit(exit_code or 0)

    except Exception as e:
        logger.exception("Fatal error occurred")
        sys.exit(1)


if __name__ == "__main__":
    main()