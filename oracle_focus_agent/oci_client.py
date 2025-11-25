"""
Oracle Cloud Infrastructure Object Storage client.
"""

import os
from typing import List, Dict, Any, IO
from datetime import datetime
import oci
from .logger import get_logger


logger = get_logger("oci_client")


class ObjectInfo:
    """Information about an OCI object."""

    def __init__(self, name: str, size: int, time_created: datetime):
        self.name = name
        self.size = size
        self.time_created = time_created

    def __repr__(self):
        return f"ObjectInfo(name={self.name}, size={self.size}, time_created={self.time_created})"


class OCIClient:
    """Oracle Cloud Infrastructure Object Storage client."""

    def __init__(self, config):
        """
        Initialize OCI client.

        Args:
            config: Configuration object with OCI settings
        """
        self.config = config
        self.namespace = config.oci.namespace
        self.bucket = config.oci.bucket

        # Load OCI configuration from file
        config_file = os.path.expanduser(config.oci.config_file)
        try:
            self.oci_config = oci.config.from_file(
                file_location=config_file,
                profile_name=config.oci.profile
            )
            logger.info(f"Loaded OCI config from {config_file} [{config.oci.profile}]")
        except Exception as e:
            logger.error(f"Failed to load OCI config: {e}")
            raise

        # Create Object Storage client
        try:
            self.client = oci.object_storage.ObjectStorageClient(self.oci_config)
            logger.info(f"Initialized OCI client for namespace: {self.namespace}, bucket: {self.bucket}")
        except Exception as e:
            logger.error(f"Failed to create OCI client: {e}")
            raise

    def list_objects(self, prefix: str) -> List[ObjectInfo]:
        """
        List all objects under a given prefix with pagination.

        Args:
            prefix: Object prefix to filter by

        Returns:
            List of ObjectInfo instances

        Raises:
            Exception: If listing fails
        """
        logger.debug(f"Listing objects with prefix: {prefix}")

        all_objects = []
        next_start_with = None

        try:
            while True:
                response = self.client.list_objects(
                    namespace_name=self.namespace,
                    bucket_name=self.bucket,
                    prefix=prefix,
                    start=next_start_with,
                    fields="name,timeCreated,size"
                )

                objects = response.data.objects
                for obj in objects:
                    # Only include .csv.gz files
                    if obj.name.lower().endswith(".csv.gz"):
                        all_objects.append(ObjectInfo(
                            name=obj.name,
                            size=obj.size,
                            time_created=obj.time_created
                        ))

                next_start_with = response.data.next_start_with
                if not next_start_with:
                    break

            logger.info(f"Found {len(all_objects)} .csv.gz files under prefix: {prefix}")
            return all_objects

        except Exception as e:
            logger.error(f"Failed to list objects: {e}")
            raise

    def download_stream(self, object_name: str, target_stream: IO) -> int:
        """
        Download an object and stream it to a target.

        Args:
            object_name: Full object name in OCI
            target_stream: File-like object to write to

        Returns:
            Number of bytes downloaded

        Raises:
            Exception: If download fails
        """
        logger.debug(f"Downloading object: {object_name}")

        try:
            response = self.client.get_object(
                namespace_name=self.namespace,
                bucket_name=self.bucket,
                object_name=object_name
            )

            bytes_downloaded = 0
            chunk_size = self.config.advanced.chunk_size_bytes

            for chunk in response.data.raw.stream(chunk_size, decode_content=False):
                target_stream.write(chunk)
                bytes_downloaded += len(chunk)

            logger.debug(f"Downloaded {bytes_downloaded} bytes from {object_name}")
            return bytes_downloaded

        except Exception as e:
            logger.error(f"Failed to download object {object_name}: {e}")
            raise

    def get_object_metadata(self, object_name: str) -> Dict[str, Any]:
        """
        Get metadata for an object.

        Args:
            object_name: Full object name in OCI

        Returns:
            Dictionary of metadata

        Raises:
            Exception: If getting metadata fails
        """
        try:
            response = self.client.head_object(
                namespace_name=self.namespace,
                bucket_name=self.bucket,
                object_name=object_name
            )

            return {
                "size": int(response.headers.get("content-length", 0)),
                "etag": response.headers.get("etag", ""),
                "last_modified": response.headers.get("last-modified", ""),
                "content_type": response.headers.get("content-type", ""),
            }

        except Exception as e:
            logger.error(f"Failed to get metadata for {object_name}: {e}")
            raise

    def test_connectivity(self) -> bool:
        """
        Test OCI connectivity and permissions.

        Returns:
            True if connection successful, False otherwise
        """
        try:
            # Try to list objects with empty prefix (just test connectivity)
            response = self.client.list_objects(
                namespace_name=self.namespace,
                bucket_name=self.bucket,
                prefix="",
                limit=1
            )
            logger.info("OCI connectivity test successful")
            return True

        except Exception as e:
            logger.error(f"OCI connectivity test failed: {e}")
            return False
