"""
Logging setup for Oracle FOCUS Agent.
"""

import logging
import os
from logging.handlers import RotatingFileHandler
from typing import Optional


def setup_logging(config, log_name: str = "oracle_focus_agent") -> logging.Logger:
    """
    Configure logging with file rotation and console output.

    Args:
        config: Configuration object with logging settings
        log_name: Name for the logger

    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(log_name)

    # Set log level
    level = getattr(logging, config.logging.level.upper(), logging.INFO)
    logger.setLevel(level)

    # Remove existing handlers
    logger.handlers.clear()

    # Create formatter
    formatter = logging.Formatter(config.logging.format)

    # Console handler (always present)
    console_handler = logging.StreamHandler()
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # File handler (if log file specified)
    if config.logging.file:
        log_file = os.path.expanduser(config.logging.file)

        # Create log directory if it doesn't exist
        log_dir = os.path.dirname(log_file)
        if log_dir and not os.path.exists(log_dir):
            os.makedirs(log_dir, mode=0o755, exist_ok=True)

        # Create rotating file handler
        max_bytes = config.logging.max_size_mb * 1024 * 1024
        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=max_bytes,
            backupCount=config.logging.backup_count
        )
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    # Prevent propagation to root logger
    logger.propagate = False

    return logger


def get_logger(name: Optional[str] = None) -> logging.Logger:
    """
    Get a logger instance.

    Args:
        name: Logger name (defaults to oracle_focus_agent)

    Returns:
        Logger instance
    """
    if name:
        return logging.getLogger(f"oracle_focus_agent.{name}")
    return logging.getLogger("oracle_focus_agent")
