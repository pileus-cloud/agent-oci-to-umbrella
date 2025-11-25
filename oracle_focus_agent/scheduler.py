"""
Scheduler for periodic sync operations.
"""

import time
import signal
from .logger import get_logger


logger = get_logger("scheduler")


class Scheduler:
    """Schedules periodic sync operations."""

    def __init__(self, interval_seconds: int, orchestrator):
        """
        Initialize scheduler.

        Args:
            interval_seconds: Seconds between sync operations
            orchestrator: Transfer orchestrator instance
        """
        self.interval_seconds = interval_seconds
        self.orchestrator = orchestrator
        self.should_stop = False

        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGTERM, self._handle_signal)
        signal.signal(signal.SIGINT, self._handle_signal)

    def _handle_signal(self, signum, frame):
        """Handle shutdown signals."""
        sig_name = signal.Signals(signum).name
        logger.info(f"Received {sig_name}, initiating graceful shutdown...")
        self.should_stop = True

    def run_forever(self):
        """
        Run scheduler loop forever until stopped.

        Performs sync operations at configured intervals.
        """
        logger.info(f"Scheduler started (interval: {self.interval_seconds}s)")

        while not self.should_stop:
            try:
                # Perform sync
                logger.info(f"Triggering sync operation")
                stats = self.orchestrator.sync()

                if stats.files_failed > 0:
                    logger.warning(f"Sync completed with {stats.files_failed} failures")
                else:
                    logger.info("Sync completed successfully")

            except Exception as e:
                logger.error(f"Sync operation failed with exception: {e}", exc_info=True)

            # Sleep until next interval (check for shutdown every second)
            logger.info(f"Next sync in {self.interval_seconds} seconds")

            for _ in range(self.interval_seconds):
                if self.should_stop:
                    break
                time.sleep(1)

        logger.info("Scheduler stopped")

    def stop(self):
        """Stop the scheduler."""
        logger.info("Stopping scheduler...")
        self.should_stop = True
