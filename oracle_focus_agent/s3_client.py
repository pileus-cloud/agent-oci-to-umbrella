"""
AWS S3 client for uploading files.
"""

from typing import IO, Dict, Any, Optional
import boto3
from botocore.exceptions import ClientError
from .logger import get_logger


logger = get_logger("s3_client")


class S3Client:
    """AWS S3 client for uploading FOCUS files."""

    def __init__(self, config):
        """
        Initialize S3 client.

        Args:
            config: Configuration object with S3 settings
        """
        self.config = config
        self.bucket_name = config.s3.get_bucket_name()
        self.prefix = config.s3.get_prefix()

        # Create S3 client
        if config.s3.access_key_id and config.s3.secret_access_key:
            # Use credentials from config (not recommended)
            logger.warning("Using S3 credentials from config file (not recommended)")
            self.s3_client = boto3.client(
                's3',
                region_name=config.s3.region,
                aws_access_key_id=config.s3.access_key_id,
                aws_secret_access_key=config.s3.secret_access_key
            )
        else:
            # Use AWS credential chain (recommended)
            logger.info("Using AWS credential chain for S3 authentication")
            self.s3_client = boto3.client(
                's3',
                region_name=config.s3.region
            )

        logger.info(f"Initialized S3 client for bucket: {self.bucket_name}, prefix: {self.prefix}")

    def get_full_key(self, key: str) -> str:
        """
        Get full S3 key including prefix.

        Args:
            key: Base key (filename)

        Returns:
            Full S3 key with prefix
        """
        if self.prefix:
            # Remove leading/trailing slashes and join
            prefix = self.prefix.strip("/")
            return f"{prefix}/{key}"
        return key

    def upload_stream(self, key: str, source_stream: IO, size: int) -> bool:
        """
        Upload a file from a stream to S3.

        Args:
            key: S3 key (filename without prefix)
            source_stream: File-like object to read from
            size: Total size of the file in bytes

        Returns:
            True if upload successful, False otherwise

        Raises:
            Exception: If upload fails
        """
        full_key = self.get_full_key(key)
        logger.info(f"Uploading to S3: s3://{self.bucket_name}/{full_key} ({self._format_size(size)})")

        if self.config.advanced.dry_run:
            logger.info("DRY RUN: Would upload file")
            return True

        try:
            # Use upload_fileobj for streaming upload
            self.s3_client.upload_fileobj(
                source_stream,
                self.bucket_name,
                full_key,
                ExtraArgs={
                    'ContentType': 'application/gzip',
                }
            )

            logger.info(f"Successfully uploaded to S3: {full_key}")
            return True

        except ClientError as e:
            logger.error(f"Failed to upload to S3: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error during S3 upload: {e}")
            raise

    def object_exists(self, key: str) -> bool:
        """
        Check if an object exists in S3.

        Args:
            key: S3 key (filename without prefix)

        Returns:
            True if object exists, False otherwise
        """
        full_key = self.get_full_key(key)

        try:
            self.s3_client.head_object(Bucket=self.bucket_name, Key=full_key)
            return True
        except ClientError as e:
            if e.response['Error']['Code'] == '404':
                return False
            # Re-raise other errors
            logger.error(f"Error checking if object exists: {e}")
            raise

    def get_object_metadata(self, key: str) -> Optional[Dict[str, Any]]:
        """
        Get metadata for an S3 object.

        Args:
            key: S3 key (filename without prefix)

        Returns:
            Dictionary of metadata, or None if object doesn't exist
        """
        full_key = self.get_full_key(key)

        try:
            response = self.s3_client.head_object(Bucket=self.bucket_name, Key=full_key)
            return {
                "size": response.get("ContentLength", 0),
                "etag": response.get("ETag", "").strip('"'),
                "last_modified": response.get("LastModified"),
                "content_type": response.get("ContentType", ""),
            }
        except ClientError as e:
            if e.response['Error']['Code'] == '404':
                return None
            logger.error(f"Error getting object metadata: {e}")
            raise

    def test_connectivity(self) -> bool:
        """
        Test S3 connectivity and permissions.

        Returns:
            True if connection successful, False otherwise
        """
        try:
            # Test by uploading a small test object (tests PutObject permission)
            import io
            from datetime import datetime

            test_key = self.get_full_key(f"_test_connectivity_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}.txt")
            test_content = b"S3 connectivity test"
            test_stream = io.BytesIO(test_content)

            self.s3_client.upload_fileobj(
                test_stream,
                self.bucket_name,
                test_key
            )

            # Clean up test file
            try:
                self.s3_client.delete_object(Bucket=self.bucket_name, Key=test_key)
            except Exception:
                pass  # Ignore cleanup errors

            logger.info("S3 connectivity test successful")
            return True

        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == '404':
                logger.error(f"S3 bucket not found: {self.bucket_name}")
            elif error_code == '403':
                logger.error(f"Access denied to S3 bucket: {self.bucket_name}")
            else:
                logger.error(f"S3 connectivity test failed: {e}")
            return False

        except Exception as e:
            logger.error(f"S3 connectivity test failed: {e}")
            return False

    @staticmethod
    def _format_size(size_bytes: int) -> str:
        """Format size in bytes to human-readable string."""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.2f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.2f} TB"
