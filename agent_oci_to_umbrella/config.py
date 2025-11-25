"""
Configuration management for Oracle FOCUS Agent.
"""

import os
from typing import Dict, List, Any, Optional
import yaml


class Config:
    """Configuration loader and validator."""

    def __init__(self, config_dict: Dict[str, Any]):
        """Initialize configuration from dictionary."""
        self.raw = config_dict

        # OCI Configuration
        self.oci = OCIConfig(config_dict.get("oci", {}))

        # S3 Configuration
        self.s3 = S3Config(config_dict.get("s3", {}))

        # Agent Configuration
        self.agent = AgentConfig(config_dict.get("agent", {}))

        # Retry Configuration
        self.retry = RetryConfig(config_dict.get("retry", {}))

        # Logging Configuration
        self.logging = LoggingConfig(config_dict.get("logging", {}))

        # State Configuration
        self.state = StateConfig(config_dict.get("state", {}))

        # Naming Configuration
        self.naming = NamingConfig(config_dict.get("naming", {}))

        # Advanced Configuration
        self.advanced = AdvancedConfig(config_dict.get("advanced", {}))

    @staticmethod
    def load(config_path: str) -> 'Config':
        """
        Load configuration from YAML file.

        Args:
            config_path: Path to YAML configuration file

        Returns:
            Config object

        Raises:
            FileNotFoundError: If config file doesn't exist
            yaml.YAMLError: If config file is invalid YAML
        """
        # Expand user home directory
        config_path = os.path.expanduser(config_path)

        if not os.path.exists(config_path):
            raise FileNotFoundError(f"Configuration file not found: {config_path}")

        with open(config_path, 'r') as f:
            config_dict = yaml.safe_load(f)

        if not config_dict:
            raise ValueError(f"Configuration file is empty: {config_path}")

        return Config(config_dict)

    def validate(self) -> List[str]:
        """
        Validate configuration and return list of errors.

        Returns:
            List of error messages (empty if valid)
        """
        errors = []

        # Validate OCI configuration
        if not self.oci.namespace:
            errors.append("OCI namespace is required")

        if not self.oci.bucket:
            errors.append("OCI bucket is required")

        if not self.oci.bucket.startswith("ocid1.tenancy."):
            errors.append("OCI bucket must be a valid tenancy OCID starting with 'ocid1.tenancy.'")

        # Validate S3 configuration
        if not self.s3.bucket_path:
            errors.append("S3 bucket_path is required")

        if not self.s3.bucket_path.startswith("s3://"):
            errors.append("S3 bucket_path must start with 's3://'")

        # Validate agent configuration
        if self.agent.poll_interval < 60:
            errors.append("poll_interval must be at least 60 seconds")

        if self.agent.lookback_days < 0:
            errors.append("lookback_days must be >= 0")

        if self.agent.max_concurrent_transfers < 1:
            errors.append("max_concurrent_transfers must be at least 1")

        # Validate retry configuration
        if self.retry.max_retries < 0:
            errors.append("max_retries must be >= 0")

        # Validate advanced configuration
        if self.advanced.max_file_size_gb < 1:
            errors.append("max_file_size_gb must be at least 1")

        if self.advanced.chunk_size_bytes < 1024:
            errors.append("chunk_size_bytes must be at least 1024 bytes")

        return errors


class OCIConfig:
    """OCI-specific configuration."""

    def __init__(self, config: Dict[str, Any]):
        self.config_file = config.get("config_file", "~/.oci/config")
        self.profile = config.get("profile", "DEFAULT")
        self.namespace = config.get("namespace", "bling")
        self.bucket = config.get("bucket", "")
        self.prefix = config.get("prefix", "FOCUS Reports/")


class S3Config:
    """S3-specific configuration."""

    def __init__(self, config: Dict[str, Any]):
        self.bucket_path = config.get("bucket_path", "")
        self.region = config.get("region", "us-east-1")
        self.access_key_id = config.get("access_key_id", "")
        self.secret_access_key = config.get("secret_access_key", "")

    def get_bucket_name(self) -> str:
        """Extract bucket name from s3://bucket/path format."""
        if not self.bucket_path.startswith("s3://"):
            return ""

        parts = self.bucket_path[5:].split("/")
        return parts[0] if parts else ""

    def get_prefix(self) -> str:
        """Extract prefix from s3://bucket/path format."""
        if not self.bucket_path.startswith("s3://"):
            return ""

        parts = self.bucket_path[5:].split("/", 1)
        return parts[1] if len(parts) > 1 else ""


class AgentConfig:
    """Agent operation configuration."""

    def __init__(self, config: Dict[str, Any]):
        self.poll_interval = config.get("poll_interval", 600)
        self.lookback_days = config.get("lookback_days", 0)
        self.max_concurrent_transfers = config.get("max_concurrent_transfers", 3)
        self.daemon_mode = config.get("daemon_mode", True)


class RetryConfig:
    """Retry strategy configuration."""

    def __init__(self, config: Dict[str, Any]):
        self.max_retries = config.get("max_retries", 3)
        self.initial_delay = config.get("initial_delay", 5)
        self.backoff_multiplier = config.get("backoff_multiplier", 2)
        self.max_delay = config.get("max_delay", 300)


class LoggingConfig:
    """Logging configuration."""

    def __init__(self, config: Dict[str, Any]):
        self.level = config.get("level", "INFO")
        self.file = config.get("file", "")
        self.max_size_mb = config.get("max_size_mb", 100)
        self.backup_count = config.get("backup_count", 5)
        self.format = config.get("format", "%(asctime)s - %(name)s - %(levelname)s - %(message)s")


class StateConfig:
    """State management configuration."""

    def __init__(self, config: Dict[str, Any]):
        self.file = config.get("file", "./state/state.json")
        self.retention_days = config.get("retention_days", 30)


class NamingConfig:
    """File naming configuration."""

    def __init__(self, config: Dict[str, Any]):
        self.date_format = config.get("date_format", "%Y-%m-%d")
        self.separator = config.get("separator", "_")


class AdvancedConfig:
    """Advanced settings configuration."""

    def __init__(self, config: Dict[str, Any]):
        self.validate_file_size = config.get("validate_file_size", True)
        self.max_file_size_gb = config.get("max_file_size_gb", 5)
        self.chunk_size_bytes = config.get("chunk_size_bytes", 8388608)  # 8MB
        self.validate_checksum = config.get("validate_checksum", True)
        self.dry_run = config.get("dry_run", False)
