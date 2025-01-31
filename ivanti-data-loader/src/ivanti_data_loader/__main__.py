"""Main entry point for the Ivanti Data Loader application."""
import argparse
import logging
import sys
from pathlib import Path
from typing import NoReturn

from .core.exceptions import DataLoaderError
from .core.pipeline import Pipeline
from .utils.logging import get_logger

logger = get_logger()


def parse_args() -> argparse.Namespace:
    """
    Parse command line arguments.

    Returns:
        argparse.Namespace: Parsed arguments
    """
    parser = argparse.ArgumentParser(
        description="Ivanti Data Loader - Generic data ingestion framework"
    )
    parser.add_argument(
        "--config",
        type=str,
        required=True,
        help="Path to YAML configuration file"
    )
    parser.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        default="INFO",
        help="Set the logging level"
    )
    return parser.parse_args()


def main() -> NoReturn:
    """
    Main application entry point.

    This function will never return normally, it will always exit
    via sys.exit() with an appropriate status code.
    """
    try:
        # Parse arguments
        args = parse_args()

        # Set log level
        logging.getLogger().setLevel(args.log_level)

        # Create and execute pipeline
        logger.info(f"Loading configuration from {args.config}")
        pipeline = Pipeline(config_path=args.config)
        
        result = pipeline.execute()

        # Exit with status based on results
        if result.failed_loads > 0:
            logger.warning(
                "Pipeline completed with errors",
                failed=result.failed_loads,
                success_rate=f"{result.success_rate:.2f}%"
            )
            sys.exit(1)
        else:
            logger.info(
                "Pipeline completed successfully",
                total_records=result.total_records,
                success_rate=f"{result.success_rate:.2f}%"
            )
            sys.exit(0)

    except DataLoaderError as e:
        logger.error(
            "Application error",
            error=str(e),
            details=e.details
        )
        sys.exit(1)
    except Exception as e:
        logger.exception("Unexpected error occurred")
        sys.exit(1)


if __name__ == "__main__":
    main()