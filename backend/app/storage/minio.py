
"""
app/storage/minio.py

MinIO/S3-compatible implementation of StorageProvider.

The provider owns all concrete boto3/S3 interaction.

Application services should interact with StorageService instead
of using this provider directly.
"""

from __future__ import annotations

from datetime import timezone
from typing import BinaryIO, Mapping, Optional

import boto3
from botocore.client import Config
from botocore.exceptions import BotoCoreError, ClientError

from app.storage.base import StorageProvider
from app.storage.models import ObjectMetadata, UploadResult


class MinIOProvider(StorageProvider):
    """
    MinIO/S3-compatible implementation of StorageProvider.

    This provider works with:
    - Local MinIO
    - Backblaze B2 S3-compatible API
    - Other S3-compatible object storage providers

    Buckets are provisioned outside the application.
    The application only verifies that the configured bucket
    exists and is accessible.
    """

    def __init__(
        self,
        *,
        endpoint_url: str,
        access_key: str,
        secret_key: str,
        bucket: str,
        region: str = "us-east-1",
        secure: bool = False,
    ) -> None:
        """
        Initialize the MinIO/S3-compatible provider.
        """

        # ------------------------------------------------------------------
        # Validate configuration
        # ------------------------------------------------------------------

        if not endpoint_url or not endpoint_url.strip():
            raise ValueError(
                "MINIO_ENDPOINT cannot be empty."
            )

        if not access_key or not access_key.strip():
            raise ValueError(
                "MINIO_ACCESS_KEY cannot be empty."
            )

        if not secret_key or not secret_key.strip():
            raise ValueError(
                "MINIO_SECRET_KEY cannot be empty."
            )

        if not bucket or not bucket.strip():
            raise ValueError(
                "STORAGE_BUCKET cannot be empty."
            )

        # ------------------------------------------------------------------
        # Normalize values
        # ------------------------------------------------------------------

        endpoint_url = endpoint_url.strip().rstrip("/")

        if not endpoint_url.startswith(
            (
                "http://",
                "https://",
            )
        ):
            scheme = "https" if secure else "http"

            endpoint_url = (
                f"{scheme}://{endpoint_url}"
            )

        self.endpoint_url = endpoint_url
        self.region = region
        self.secure = secure
        self.bucket = bucket.strip()

        # ------------------------------------------------------------------
        # Create boto3 S3 client
        # ------------------------------------------------------------------

        self.client = boto3.client(
            "s3",
            endpoint_url=self.endpoint_url,
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            region_name=self.region,
            config=Config(
                signature_version="s3v4",
                s3={
                    "addressing_style": "path",
                },
            ),
        )

    # ======================================================================
    # Bucket
    # ======================================================================

    def ensure_bucket(
        self,
        *,
        bucket: str,
    ) -> None:
        """
        Verify that the specified bucket exists and is accessible.

        Buckets are provisioned outside the application.

        IMPORTANT:
            This method deliberately does NOT create buckets.

        This is important for production S3-compatible providers such as
        Backblaze B2, where the application's credentials may be restricted
        to an existing bucket and may not have bucket-creation permission.
        """

        if not bucket or not bucket.strip():
            raise ValueError(
                "Bucket cannot be empty."
            )

        bucket = bucket.strip()

        try:
            self.client.head_bucket(
                Bucket=bucket,
            )

            # Bucket exists and the credentials can access it.
            return

        except ClientError as exc:
            error = exc.response.get(
                "Error",
                {},
            )

            error_code = str(
                error.get("Code", "")
            )

            # --------------------------------------------------------------
            # Bucket exists but credentials do not have access.
            # --------------------------------------------------------------

            if error_code in {
                "403",
                "AccessDenied",
            }:
                raise RuntimeError(
                    f"Storage bucket '{bucket}' exists but is not "
                    "accessible with the configured credentials."
                ) from exc

            # --------------------------------------------------------------
            # Bucket does not exist.
            # --------------------------------------------------------------

            if error_code in {
                "404",
                "NoSuchBucket",
                "NotFound",
            }:
                raise RuntimeError(
                    f"Storage bucket '{bucket}' does not exist. "
                    "Create the bucket in the storage provider before "
                    "using the application."
                ) from exc

            # --------------------------------------------------------------
            # Any other storage error.
            # --------------------------------------------------------------

            raise RuntimeError(
                f"Unable to access storage bucket '{bucket}'. "
                f"S3 error code: {error_code or 'unknown'}."
            ) from exc

    # ======================================================================
    # Upload
    # ======================================================================

    def upload(
        self,
        *,
        bucket: str,
        key: str,
        file: BinaryIO,
        content_type: Optional[str] = None,
        metadata: Optional[Mapping[str, str]] = None,
    ) -> UploadResult:
        """
        Upload an object to MinIO/S3-compatible storage.
        """

        if not bucket or not bucket.strip():
            raise ValueError(
                "Bucket cannot be empty."
            )

        if not key or not key.strip():
            raise ValueError(
                "Object key cannot be empty."
            )

        bucket = bucket.strip()
        key = key.lstrip("/")

        # ------------------------------------------------------------------
        # Verify bucket exists and is accessible
        # ------------------------------------------------------------------

        self.ensure_bucket(
            bucket=bucket,
        )

        # ------------------------------------------------------------------
        # Build upload arguments
        # ------------------------------------------------------------------

        extra_args: dict[str, object] = {}

        if content_type:
            extra_args["ContentType"] = content_type

        if metadata:
            extra_args["Metadata"] = {
                str(k): str(v)
                for k, v in metadata.items()
            }

        # ------------------------------------------------------------------
        # Upload
        # ------------------------------------------------------------------

        self.client.upload_fileobj(
            Fileobj=file,
            Bucket=bucket,
            Key=key,
            ExtraArgs=extra_args,
        )

        # ------------------------------------------------------------------
        # Retrieve metadata after upload
        #
        # This gives us the actual ETag, size, and content type.
        # ------------------------------------------------------------------

        response = self.client.head_object(
            Bucket=bucket,
            Key=key,
        )

        etag = response.get(
            "ETag"
        )

        if etag:
            etag = etag.strip('"')

        uploaded_at = response.get(
            "LastModified"
        )

        if uploaded_at is not None:
            if uploaded_at.tzinfo is None:
                uploaded_at = uploaded_at.replace(
                    tzinfo=timezone.utc
                )
            else:
                uploaded_at = uploaded_at.astimezone(
                    timezone.utc
                )

        # ------------------------------------------------------------------
        # IMPORTANT:
        #
        # UploadResult does NOT contain "url".
        #
        # Therefore we only return fields defined by UploadResult.
        # ------------------------------------------------------------------

        return UploadResult(
            bucket=bucket,
            key=key,
            etag=etag,
            content_type=response.get(
                "ContentType",
                content_type,
            ),
            size_bytes=response.get(
                "ContentLength"
            ),
            version_id=response.get(
                "VersionId"
            ),
            uploaded_at=uploaded_at,
        )

    # ======================================================================
    # Download
    # ======================================================================

    def download(
        self,
        *,
        bucket: str,
        key: str,
    ) -> bytes:
        """
        Download an object completely into memory.
        """

        if not bucket or not bucket.strip():
            raise ValueError(
                "Bucket cannot be empty."
            )

        if not key or not key.strip():
            raise ValueError(
                "Object key cannot be empty."
            )

        response = self.client.get_object(
            Bucket=bucket.strip(),
            Key=key.lstrip("/"),
        )

        body = response["Body"]

        try:
            return body.read()
        finally:
            body.close()

    # ======================================================================
    # Download Stream
    # ======================================================================

    def download_stream(
        self,
        *,
        bucket: str,
        key: str,
    ) -> BinaryIO:
        """
        Download an object as a readable stream.
        """

        if not bucket or not bucket.strip():
            raise ValueError(
                "Bucket cannot be empty."
            )

        if not key or not key.strip():
            raise ValueError(
                "Object key cannot be empty."
            )

        response = self.client.get_object(
            Bucket=bucket.strip(),
            Key=key.lstrip("/"),
        )

        return response["Body"]

    # ======================================================================
    # Delete
    # ======================================================================

    def delete(
        self,
        *,
        bucket: str,
        key: str,
    ) -> None:
        """
        Delete an object.
        """

        if not bucket or not bucket.strip():
            raise ValueError(
                "Bucket cannot be empty."
            )

        if not key or not key.strip():
            raise ValueError(
                "Object key cannot be empty."
            )

        self.client.delete_object(
            Bucket=bucket.strip(),
            Key=key.lstrip("/"),
        )

    # ======================================================================
    # Exists
    # ======================================================================

    def exists(
        self,
        *,
        bucket: str,
        key: str,
    ) -> bool:
        """
        Check whether an object exists.
        """

        if not bucket or not bucket.strip():
            return False

        if not key or not key.strip():
            return False

        try:
            self.client.head_object(
                Bucket=bucket.strip(),
                Key=key.lstrip("/"),
            )

            return True

        except ClientError as exc:
            error = exc.response.get(
                "Error",
                {},
            )

            error_code = str(
                error.get("Code", "")
            )

            if error_code in {
                "404",
                "NoSuchKey",
                "NotFound",
            }:
                return False

            raise

    # ======================================================================
    # Metadata
    # ======================================================================

    def get_metadata(
        self,
        *,
        bucket: str,
        key: str,
    ) -> ObjectMetadata:
        """
        Retrieve metadata for an object.
        """

        if not bucket or not bucket.strip():
            raise ValueError(
                "Bucket cannot be empty."
            )

        if not key or not key.strip():
            raise ValueError(
                "Object key cannot be empty."
            )

        bucket = bucket.strip()
        key = key.lstrip("/")

        response = self.client.head_object(
            Bucket=bucket,
            Key=key,
        )

        last_modified = response.get(
            "LastModified"
        )

        if last_modified is not None:
            if last_modified.tzinfo is None:
                last_modified = last_modified.replace(
                    tzinfo=timezone.utc
                )
            else:
                last_modified = last_modified.astimezone(
                    timezone.utc
                )

        etag = response.get(
            "ETag"
        )

        if etag:
            etag = etag.strip('"')

        # ------------------------------------------------------------------
        # IMPORTANT:
        #
        # ObjectMetadata expects "size_bytes",
        # not "size".
        # ------------------------------------------------------------------

        return ObjectMetadata(
            bucket=bucket,
            key=key,
            size_bytes=response.get(
                "ContentLength",
                0,
            ),
            content_type=response.get(
                "ContentType",
                "application/octet-stream",
            ),
            etag=etag,
            last_modified=last_modified,
            version_id=response.get(
                "VersionId"
            ),
            metadata={
                str(k): str(v)
                for k, v in response.get(
                    "Metadata",
                    {},
                ).items()
            },
        )

    # ======================================================================
    # Presigned URL
    # ======================================================================

    def generate_presigned_url(
        self,
        *,
        bucket: str,
        key: str,
        expires_in: int = 3600,
    ) -> str:
        """
        Generate a temporary download URL.
        """

        if not bucket or not bucket.strip():
            raise ValueError(
                "Bucket cannot be empty."
            )

        if not key or not key.strip():
            raise ValueError(
                "Object key cannot be empty."
            )

        if expires_in <= 0:
            raise ValueError(
                "expires_in must be greater than zero."
            )

        return self.client.generate_presigned_url(
            ClientMethod="get_object",
            Params={
                "Bucket": bucket.strip(),
                "Key": key.lstrip("/"),
            },
            ExpiresIn=expires_in,
        )

    # ======================================================================
    # Object URL
    # ======================================================================

    def object_url(
        self,
        *,
        key: str,
        bucket: Optional[str] = None,
    ) -> str:
        """
        Build the direct object URL.

        Note:
            This URL is not necessarily publicly accessible.
            For private objects, use generate_presigned_url().
        """

        if not key or not key.strip():
            raise ValueError(
                "Object key cannot be empty."
            )

        bucket_name = (
            bucket.strip()
            if bucket
            else self.bucket
        )

        if not bucket_name:
            raise ValueError(
                "Bucket cannot be empty."
            )

        return (
            f"{self.endpoint_url}/"
            f"{bucket_name}/"
            f"{key.lstrip('/')}"
        )

    # ======================================================================
    # Health Check
    # ======================================================================

    def health_check(self) -> bool:
        """
        Check whether the S3-compatible storage is reachable and the
        configured bucket is accessible.
        """

        try:
            self.client.head_bucket(
                Bucket=self.bucket,
            )

            return True

        except (
            BotoCoreError,
            ClientError,
        ):
            return False

