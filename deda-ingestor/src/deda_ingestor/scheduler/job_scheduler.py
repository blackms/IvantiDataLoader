"""Scheduler for running product synchronization jobs."""
import signal
from datetime import datetime
from typing import Optional

import structlog
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger
from dependency_injector.wiring import inject, Provide

from ..config.settings import SchedulerConfig
from ..container import Container
from ..core.product_service import ProductService

logger = structlog.get_logger(__name__)


class JobScheduler:
    """Scheduler for managing product synchronization jobs."""

    def __init__(
        self,
        config: SchedulerConfig,
        product_service: ProductService,
    ):
        """
        Initialize the job scheduler.

        Args:
            config: Scheduler configuration
            product_service: Product service for synchronization
        """
        self.config = config
        self.product_service = product_service
        self.scheduler = BlockingScheduler(timezone=config.timezone)
        self._setup_signal_handlers()

    def _setup_signal_handlers(self) -> None:
        """Setup signal handlers for graceful shutdown."""
        def shutdown(signum, frame):
            logger.info("Received shutdown signal", signal=signum)
            self.stop()

        signal.signal(signal.SIGINT, shutdown)
        signal.signal(signal.SIGTERM, shutdown)

    def _parse_schedule_time(self) -> tuple[int, int]:
        """
        Parse schedule time from configuration.

        Returns:
            tuple[int, int]: Hour and minute for scheduling

        Raises:
            ValueError: If schedule time format is invalid
        """
        try:
            schedule_dt = datetime.strptime(self.config.schedule_time, "%H:%M")
            return schedule_dt.hour, schedule_dt.minute
        except ValueError as e:
            logger.error(
                "Invalid schedule time format",
                schedule_time=self.config.schedule_time,
                error=str(e)
            )
            raise ValueError(
                f"Invalid schedule time format: {self.config.schedule_time}. "
                "Expected format: HH:MM"
            ) from e

    def _sync_products(self) -> None:
        """Execute product synchronization job."""
        logger.info("Starting scheduled product synchronization")
        
        try:
            sync_result = self.product_service.process_messages()
            
            logger.info(
                "Scheduled synchronization completed",
                total_processed=sync_result.total_processed,
                successful=sync_result.successful_syncs,
                failed=sync_result.failed_syncs,
                skipped=sync_result.skipped_syncs,
                duration_seconds=sync_result.duration_seconds,
                success_rate=f"{sync_result.success_rate:.2f}%"
            )

        except Exception as e:
            logger.exception(
                "Error during scheduled synchronization",
                error=str(e)
            )

    def start(self) -> None:
        """Start the scheduler."""
        try:
            hour, minute = self._parse_schedule_time()
            
            # Schedule the job to run daily at the configured time
            self.scheduler.add_job(
                self._sync_products,
                CronTrigger(
                    hour=hour,
                    minute=minute,
                    timezone=self.config.timezone
                ),
                name="product_sync",
                id="product_sync_job",
                replace_existing=True,
                max_instances=1,  # Ensure only one instance runs at a time
            )

            logger.info(
                "Scheduler started",
                schedule_time=f"{hour:02d}:{minute:02d}",
                timezone=self.config.timezone
            )

            # Start the scheduler
            self.scheduler.start()

        except (KeyboardInterrupt, SystemExit):
            self.stop()
        except Exception as e:
            logger.exception("Error starting scheduler", error=str(e))
            raise

    def stop(self) -> None:
        """Stop the scheduler."""
        logger.info("Stopping scheduler")
        self.scheduler.shutdown()

    def run_now(self) -> None:
        """Run the synchronization job immediately."""
        logger.info("Running product synchronization immediately")
        self._sync_products()


@inject
def create_scheduler(
    config: SchedulerConfig = Provide[Container.scheduler_config],
    product_service: ProductService = Provide[Container.product_service],
) -> JobScheduler:
    """
    Create and configure a job scheduler instance.

    Args:
        config: Scheduler configuration
        product_service: Product service instance

    Returns:
        JobScheduler: Configured scheduler instance
    """
    return JobScheduler(config, product_service)