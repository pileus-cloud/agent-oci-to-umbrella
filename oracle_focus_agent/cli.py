"""
Command-line interface for Oracle FOCUS Agent.
"""

import sys
import argparse
from .config import Config
from .logger import setup_logging, get_logger
from .oci_client import OCIClient
from .s3_client import S3Client
from .state import StateManager
from .orchestrator import TransferOrchestrator
from .scheduler import Scheduler
from .daemon import DaemonManager


def main():
    """Main entry point for CLI."""
    parser = argparse.ArgumentParser(
        description="Oracle FOCUS to Umbrella BYOD Transfer Agent",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Commands:
  start   Start daemon in background
  stop    Stop running daemon
  run     Run in foreground (Ctrl+C to stop)
  test    Test configuration and connectivity
  sync    Perform one-time sync and exit
  status  Check daemon status

Examples:
  oracle-focus-agent test --config config.yaml
  oracle-focus-agent run --config config.yaml
  oracle-focus-agent start --config config.yaml
  oracle-focus-agent stop
  oracle-focus-agent sync --config config.yaml
  oracle-focus-agent sync --config config.yaml --force  # Force re-transfer all files
        """
    )

    parser.add_argument(
        "command",
        choices=["start", "stop", "run", "test", "sync", "status"],
        help="Command to execute"
    )

    parser.add_argument(
        "--config",
        "-c",
        default="config.yaml",
        help="Path to configuration file (default: config.yaml)"
    )

    parser.add_argument(
        "--force",
        "-f",
        action="store_true",
        help="Force re-transfer all files, ignoring state (useful when files are updated)"
    )

    args = parser.parse_args()

    # Commands that don't need config
    if args.command in ["stop", "status"]:
        return execute_daemon_command(args.command)

    # Load and validate configuration
    try:
        config = Config.load(args.config)
        errors = config.validate()

        if errors:
            print("Configuration errors:")
            for error in errors:
                print(f"  - {error}")
            return 2

    except FileNotFoundError as e:
        print(f"Error: {e}")
        return 2
    except Exception as e:
        print(f"Failed to load configuration: {e}")
        return 2

    # Setup logging
    logger = setup_logging(config)

    # Execute command
    try:
        if args.command == "test":
            return execute_test(config, logger)
        elif args.command == "sync":
            return execute_sync(config, logger, args.force)
        elif args.command == "run":
            return execute_run(config, logger)
        elif args.command == "start":
            return execute_start(config, logger, args.config)
        else:
            logger.error(f"Unknown command: {args.command}")
            return 1

    except KeyboardInterrupt:
        logger.info("Interrupted by user")
        return 0
    except Exception as e:
        logger.error(f"Command failed: {e}", exc_info=True)
        return 1


def execute_test(config, logger) -> int:
    """
    Test configuration and connectivity.

    Returns:
        Exit code (0 for success)
    """
    logger.info("Testing configuration and connectivity...")

    print("\nConfiguration Test")
    print("=" * 70)

    # Test OCI configuration
    print(f"✓ OCI config file: {config.oci.config_file} [{config.oci.profile}]")
    print(f"✓ OCI namespace: {config.oci.namespace}")
    print(f"✓ OCI bucket: {config.oci.bucket}")

    try:
        oci_client = OCIClient(config)
        if oci_client.test_connectivity():
            print("✓ OCI connectivity: OK")
        else:
            print("✗ OCI connectivity: FAILED")
            return 3
    except Exception as e:
        print(f"✗ OCI connectivity: FAILED - {e}")
        return 3

    # Test S3 configuration
    print(f"✓ S3 bucket path: {config.s3.bucket_path}")
    print(f"✓ S3 region: {config.s3.region}")

    try:
        s3_client = S3Client(config)
        if s3_client.test_connectivity():
            print("✓ S3 connectivity: OK")
        else:
            print("✗ S3 connectivity: FAILED")
            return 3
    except Exception as e:
        print(f"✗ S3 connectivity: FAILED - {e}")
        return 3

    # Test state file
    try:
        state_manager = StateManager(config)
        stats = state_manager.get_stats()
        print(f"✓ State file: {config.state.file}")
        print(f"  - Tracked files: {stats['total_files']}")
    except Exception as e:
        print(f"✗ State file: FAILED - {e}")
        return 1

    print("\n✓ All tests passed!")
    print("=" * 70)

    return 0


def execute_sync(config, logger, force: bool = False) -> int:
    """
    Perform one-time sync and exit.

    Args:
        config: Configuration object
        logger: Logger instance
        force: If True, re-transfer all files ignoring state

    Returns:
        Exit code (0 for success)
    """
    if force:
        logger.info("Performing one-time sync (FORCED - ignoring state)...")
    else:
        logger.info("Performing one-time sync...")

    try:
        # Initialize components
        oci_client = OCIClient(config)
        s3_client = S3Client(config)
        state_manager = StateManager(config)
        orchestrator = TransferOrchestrator(config, oci_client, s3_client, state_manager)

        # Perform sync with force flag
        stats = orchestrator.sync(force=force)

        # Return non-zero if any failures
        if stats.files_failed > 0:
            logger.warning(f"Sync completed with {stats.files_failed} failures")
            return 1

        logger.info("Sync completed successfully")
        return 0

    except Exception as e:
        logger.error(f"Sync failed: {e}", exc_info=True)
        return 1


def execute_run(config, logger) -> int:
    """
    Run in foreground (for testing/debugging).

    Returns:
        Exit code (0 for success)
    """
    logger.info("Starting agent in foreground mode (Ctrl+C to stop)")

    try:
        # Initialize components
        oci_client = OCIClient(config)
        s3_client = S3Client(config)
        state_manager = StateManager(config)
        orchestrator = TransferOrchestrator(config, oci_client, s3_client, state_manager)

        # Create and run scheduler
        scheduler = Scheduler(config.agent.poll_interval, orchestrator)
        scheduler.run_forever()

        return 0

    except KeyboardInterrupt:
        logger.info("Stopped by user")
        return 0
    except Exception as e:
        logger.error(f"Run failed: {e}", exc_info=True)
        return 1


def execute_start(config, logger, config_path: str) -> int:
    """
    Start daemon in background.

    Returns:
        Exit code (0 for success)
    """
    daemon = DaemonManager()

    if daemon.is_running():
        pid = daemon.get_pid()
        print(f"Error: Daemon already running with PID {pid}")
        return 4

    print("Starting daemon in background...")

    def daemon_main():
        """Main function for daemon mode."""
        # Re-initialize logger for daemon (file output only)
        daemon_logger = setup_logging(config)
        daemon_logger.info("Daemon started")

        try:
            # Initialize components
            oci_client = OCIClient(config)
            s3_client = S3Client(config)
            state_manager = StateManager(config)
            orchestrator = TransferOrchestrator(config, oci_client, s3_client, state_manager)

            # Create and run scheduler
            scheduler = Scheduler(config.agent.poll_interval, orchestrator)
            scheduler.run_forever()

        except Exception as e:
            daemon_logger.error(f"Daemon failed: {e}", exc_info=True)
            sys.exit(1)

    success = daemon.start(daemon_main)
    return 0 if success else 1


def execute_daemon_command(command: str) -> int:
    """
    Execute daemon-only commands (stop, status).

    Returns:
        Exit code (0 for success)
    """
    daemon = DaemonManager()

    if command == "stop":
        success = daemon.stop()
        return 0 if success else 5

    elif command == "status":
        status = daemon.status()
        print(status["message"])
        return 0 if status["running"] else 5

    return 1


if __name__ == "__main__":
    sys.exit(main())
