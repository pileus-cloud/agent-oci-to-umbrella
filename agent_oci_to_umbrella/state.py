"""
State management for tracking transferred files.
"""

import json
import os
from typing import Dict, Optional
from datetime import datetime, timedelta
from .logger import get_logger


logger = get_logger("state")


class FileState:
    """State information for a transferred file."""

    def __init__(self, data: Dict):
        self.oci_object_name = data.get("oci_object_name", "")
        self.s3_key = data.get("s3_key", "")
        self.size = data.get("size", 0)
        self.time_created = self._parse_datetime(data.get("time_created"))
        self.time_transferred = self._parse_datetime(data.get("time_transferred"))
        self.checksum_md5 = data.get("checksum_md5", "")
        self.duration_seconds = data.get("duration_seconds", 0.0)

    @staticmethod
    def _parse_datetime(dt_str: Optional[str]) -> Optional[datetime]:
        """Parse ISO datetime string."""
        if not dt_str:
            return None
        try:
            return datetime.fromisoformat(dt_str.replace('Z', '+00:00'))
        except Exception:
            return None

    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "oci_object_name": self.oci_object_name,
            "s3_key": self.s3_key,
            "size": self.size,
            "time_created": self.time_created.isoformat() if self.time_created else None,
            "time_transferred": self.time_transferred.isoformat() if self.time_transferred else None,
            "checksum_md5": self.checksum_md5,
            "duration_seconds": self.duration_seconds,
        }


class StateManager:
    """Manages transfer state persistence."""

    def __init__(self, config):
        """
        Initialize state manager.

        Args:
            config: Configuration object with state settings
        """
        self.config = config
        self.state_file = os.path.expanduser(config.state.file)
        self.state: Dict[str, FileState] = {}
        self.last_sync: Optional[datetime] = None

        # Create state directory if it doesn't exist
        state_dir = os.path.dirname(self.state_file)
        if state_dir and not os.path.exists(state_dir):
            os.makedirs(state_dir, mode=0o755, exist_ok=True)
            logger.info(f"Created state directory: {state_dir}")

        # Load existing state
        self.load()

    def load(self):
        """Load state from file."""
        if not os.path.exists(self.state_file):
            logger.info("No existing state file, starting fresh")
            return

        try:
            with open(self.state_file, 'r') as f:
                data = json.load(f)

            self.last_sync = self._parse_datetime(data.get("last_sync"))

            files_data = data.get("files", {})
            self.state = {
                s3_key: FileState(file_data)
                for s3_key, file_data in files_data.items()
            }

            logger.info(f"Loaded state from {self.state_file}: {len(self.state)} files tracked")

        except Exception as e:
            logger.error(f"Failed to load state file: {e}")
            logger.warning("Starting with empty state")
            self.state = {}

    def save(self):
        """Save state to file (atomic write)."""
        try:
            # Prepare data
            data = {
                "version": "1.0",
                "last_sync": datetime.utcnow().isoformat() + 'Z',
                "files": {
                    s3_key: file_state.to_dict()
                    for s3_key, file_state in self.state.items()
                }
            }

            # Write to temporary file
            temp_file = f"{self.state_file}.tmp"
            with open(temp_file, 'w') as f:
                json.dump(data, f, indent=2)

            # Set permissions
            os.chmod(temp_file, 0o600)

            # Atomic rename
            os.replace(temp_file, self.state_file)

            logger.debug(f"Saved state to {self.state_file}")

        except Exception as e:
            logger.error(f"Failed to save state file: {e}")

    def mark_transferred(self, oci_object_name: str, s3_key: str, size: int,
                        time_created: datetime, duration_seconds: float,
                        checksum_md5: str = ""):
        """
        Mark a file as transferred.

        Args:
            oci_object_name: Full OCI object name
            s3_key: S3 key (without prefix)
            size: File size in bytes
            time_created: Time file was created in OCI
            duration_seconds: Transfer duration
            checksum_md5: MD5 checksum (optional)
        """
        file_state = FileState({
            "oci_object_name": oci_object_name,
            "s3_key": s3_key,
            "size": size,
            "time_created": time_created.isoformat() if time_created else None,
            "time_transferred": datetime.utcnow().isoformat() + 'Z',
            "checksum_md5": checksum_md5,
            "duration_seconds": duration_seconds,
        })

        self.state[s3_key] = file_state
        self.save()

        logger.debug(f"Marked as transferred: {s3_key}")

    def is_transferred(self, s3_key: str, size: int, time_created: datetime) -> bool:
        """
        Check if a file has been transferred and is up-to-date.

        Args:
            s3_key: S3 key to check
            size: File size in bytes
            time_created: Time file was created in OCI

        Returns:
            True if file already transferred and unchanged, False otherwise
        """
        if s3_key not in self.state:
            return False

        existing = self.state[s3_key]

        # Size changed - needs re-transfer
        if existing.size != size:
            logger.debug(f"File size changed for {s3_key}: {existing.size} -> {size}")
            return False

        # Time created changed - needs re-transfer
        if existing.time_created and time_created:
            if existing.time_created < time_created:
                logger.debug(f"File updated in OCI: {s3_key}")
                return False

        # File is unchanged
        return True

    def cleanup_old_records(self):
        """Remove old records based on retention policy."""
        if self.config.state.retention_days <= 0:
            return  # Keep forever

        from datetime import timezone
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=self.config.state.retention_days)

        old_keys = []
        for s3_key, file_state in self.state.items():
            if file_state.time_transferred and file_state.time_transferred < cutoff_date:
                old_keys.append(s3_key)

        if old_keys:
            for key in old_keys:
                del self.state[key]

            self.save()
            logger.info(f"Cleaned up {len(old_keys)} old state records")

    def get_stats(self) -> Dict:
        """Get statistics about tracked files."""
        total_size = sum(f.size for f in self.state.values())
        total_files = len(self.state)

        return {
            "total_files": total_files,
            "total_size_bytes": total_size,
            "last_sync": self.last_sync.isoformat() if self.last_sync else None,
        }

    @staticmethod
    def _parse_datetime(dt_str: Optional[str]) -> Optional[datetime]:
        """Parse ISO datetime string."""
        if not dt_str:
            return None
        try:
            return datetime.fromisoformat(dt_str.replace('Z', '+00:00'))
        except Exception:
            return None
