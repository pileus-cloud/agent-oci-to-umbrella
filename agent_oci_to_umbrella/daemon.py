"""
Daemon management for background operation.
"""

import os
import sys
import atexit
import time
from typing import Optional, Dict, Any
from .logger import get_logger


logger = get_logger("daemon")


class DaemonManager:
    """Manages daemon lifecycle using PID files."""

    def __init__(self, pid_file: str = "/tmp/oracle-focus-agent.pid"):
        """
        Initialize daemon manager.

        Args:
            pid_file: Path to PID file
        """
        self.pid_file = pid_file

    def start(self, target_func):
        """
        Start daemon in background.

        Args:
            target_func: Function to run in daemon mode

        Returns:
            True if started successfully, False otherwise
        """
        # Check if already running
        if self.is_running():
            pid = self.get_pid()
            logger.error(f"Daemon already running with PID {pid}")
            return False

        logger.info("Starting daemon in background")

        try:
            # Fork first child
            pid = os.fork()
            if pid > 0:
                # Parent process - wait a moment and check if daemon started
                time.sleep(1)
                if self.is_running():
                    daemon_pid = self.get_pid()
                    logger.info(f"Daemon started successfully with PID {daemon_pid}")
                    return True
                else:
                    logger.error("Daemon failed to start")
                    return False

        except OSError as e:
            logger.error(f"Fork failed: {e}")
            return False

        # First child - decouple from parent
        os.chdir("/")
        os.setsid()
        os.umask(0)

        # Fork second child
        try:
            pid = os.fork()
            if pid > 0:
                # Exit first child
                sys.exit(0)
        except OSError as e:
            logger.error(f"Second fork failed: {e}")
            sys.exit(1)

        # Second child - this is the daemon
        # Redirect standard file descriptors
        sys.stdout.flush()
        sys.stderr.flush()

        with open(os.devnull, 'r') as devnull_r:
            os.dup2(devnull_r.fileno(), sys.stdin.fileno())

        with open(os.devnull, 'a+') as devnull_w:
            os.dup2(devnull_w.fileno(), sys.stdout.fileno())
            os.dup2(devnull_w.fileno(), sys.stderr.fileno())

        # Write PID file
        atexit.register(self._delete_pid_file)
        self._write_pid_file()

        # Run the target function
        try:
            target_func()
        except Exception as e:
            logger.error(f"Daemon execution failed: {e}", exc_info=True)
            sys.exit(1)

        sys.exit(0)

    def stop(self) -> bool:
        """
        Stop running daemon.

        Returns:
            True if stopped successfully, False otherwise
        """
        pid = self.get_pid()

        if not pid:
            logger.error("Daemon is not running")
            return False

        logger.info(f"Stopping daemon (PID {pid})")

        try:
            # Send SIGTERM
            os.kill(pid, 15)  # SIGTERM

            # Wait for process to exit (up to 30 seconds)
            for _ in range(30):
                try:
                    os.kill(pid, 0)  # Check if process exists
                    time.sleep(1)
                except OSError:
                    # Process no longer exists
                    break

            # Check if process is still running
            try:
                os.kill(pid, 0)
                logger.warning(f"Process {pid} did not stop gracefully, sending SIGKILL")
                os.kill(pid, 9)  # SIGKILL
                time.sleep(1)
            except OSError:
                pass

            # Remove PID file
            if os.path.exists(self.pid_file):
                os.remove(self.pid_file)

            logger.info("Daemon stopped successfully")
            return True

        except OSError as e:
            logger.error(f"Failed to stop daemon: {e}")
            return False

    def status(self) -> Dict[str, Any]:
        """
        Get daemon status.

        Returns:
            Dictionary with status information
        """
        pid = self.get_pid()

        if not pid:
            return {
                "running": False,
                "pid": None,
                "message": "Daemon is not running"
            }

        # Check if process actually exists
        try:
            os.kill(pid, 0)
            return {
                "running": True,
                "pid": pid,
                "message": f"Daemon is running with PID {pid}"
            }
        except OSError:
            # PID file exists but process doesn't
            return {
                "running": False,
                "pid": None,
                "message": "Daemon PID file exists but process is not running (stale PID file)"
            }

    def is_running(self) -> bool:
        """
        Check if daemon is running.

        Returns:
            True if running, False otherwise
        """
        pid = self.get_pid()
        if not pid:
            return False

        try:
            os.kill(pid, 0)
            return True
        except OSError:
            return False

    def get_pid(self) -> Optional[int]:
        """
        Get PID from PID file.

        Returns:
            PID if file exists and is valid, None otherwise
        """
        if not os.path.exists(self.pid_file):
            return None

        try:
            with open(self.pid_file, 'r') as f:
                pid = int(f.read().strip())
            return pid
        except (ValueError, IOError):
            return None

    def _write_pid_file(self):
        """Write current process PID to file."""
        pid = os.getpid()
        with open(self.pid_file, 'w') as f:
            f.write(str(pid))
        os.chmod(self.pid_file, 0o644)
        logger.debug(f"Wrote PID {pid} to {self.pid_file}")

    def _delete_pid_file(self):
        """Delete PID file."""
        if os.path.exists(self.pid_file):
            os.remove(self.pid_file)
            logger.debug(f"Deleted PID file {self.pid_file}")
