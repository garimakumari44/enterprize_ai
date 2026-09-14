"""
S3 Service

High-level S3 operations
used by workflow nodes.
"""

from typing import Any, Dict


from .s3_client import S3Client



class S3Service:
    """
    S3 business service.
    """

    def __init__(
        self,
        config: Dict[str, Any]
    ):

        self.bucket = config["bucket"]


        self.client = S3Client(
            access_key=config["access_key"],
            secret_key=config["secret_key"],
            region=config.get(
                "region",
                "us-east-1"
            )
        )



    async def upload(
        self,
        file_path: str,
        key: str
    ):

        """
        Upload workflow file.
        """

        return await self.client.upload_file(
            bucket=self.bucket,
            key=key,
            file_path=file_path
        )



    async def upload_content(
        self,
        content: bytes,
        filename: str
    ):

        """
        Upload generated AI output.
        """

        return await self.client.upload_bytes(
            bucket=self.bucket,
            key=filename,
            data=content
        )



    async def download(
        self,
        key: str,
        destination: str
    ):

        """
        Download file for workflow processing.
        """

        return await self.client.download_file(
            bucket=self.bucket,
            key=key,
            destination=destination
        )



    async def read(
        self,
        key: str
    ):

        """
        Read file content.
        """

        return await self.client.get_object(
            bucket=self.bucket,
            key=key
        )



    async def delete(
        self,
        key: str
    ):

        return await self.client.delete_object(
            bucket=self.bucket,
            key=key
        )



    async def list_files(
        self,
        prefix: str = None
    ):

        return await self.client.list_objects(
            bucket=self.bucket,
            prefix=prefix
        )



    async def get_download_url(
        self,
        key: str,
        expires: int = 3600
    ):

        return await self.client.generate_presigned_url(
            bucket=self.bucket,
            key=key,
            expires=expires
        )