"""
S3 Client

Low-level AWS S3 API wrapper.
"""

from typing import Dict, Any, Optional, BinaryIO

import aioboto3
from botocore.exceptions import ClientError


class S3Client:
    """
    Async AWS S3 client wrapper.
    """

    def __init__(
        self,
        access_key: str,
        secret_key: str,
        region: str,
    ):

        self.access_key = access_key
        self.secret_key = secret_key
        self.region = region


        self.session = aioboto3.Session()



    def _client(self):
        """
        Create S3 client.
        """

        return self.session.client(
            "s3",
            aws_access_key_id=self.access_key,
            aws_secret_access_key=self.secret_key,
            region_name=self.region,
        )



    async def upload_file(
        self,
        bucket: str,
        key: str,
        file_path: str,
    ) -> Dict[str, Any]:
        """
        Upload file to S3.
        """

        try:

            async with self._client() as client:

                await client.upload_file(
                    file_path,
                    bucket,
                    key
                )


            return {
                "success": True,
                "bucket": bucket,
                "key": key
            }


        except ClientError as e:

            raise Exception(
                f"S3 upload failed: {e}"
            )



    async def upload_bytes(
        self,
        bucket: str,
        key: str,
        data: bytes,
    ):

        """
        Upload binary data.
        """

        try:

            async with self._client() as client:

                await client.put_object(
                    Bucket=bucket,
                    Key=key,
                    Body=data
                )


            return {
                "success": True,
                "key": key
            }


        except ClientError as e:

            raise Exception(
                f"S3 upload failed: {e}"
            )



    async def download_file(
        self,
        bucket: str,
        key: str,
        destination: str,
    ):

        """
        Download S3 object.
        """

        try:

            async with self._client() as client:

                await client.download_file(
                    bucket,
                    key,
                    destination
                )


            return {
                "success": True,
                "path": destination
            }


        except ClientError as e:

            raise Exception(
                f"S3 download failed: {e}"
            )



    async def get_object(
        self,
        bucket: str,
        key: str,
    ):

        """
        Read object content.
        """

        try:

            async with self._client() as client:

                response = await client.get_object(
                    Bucket=bucket,
                    Key=key
                )

                body = await response["Body"].read()


                return body


        except ClientError as e:

            raise Exception(
                f"S3 read failed: {e}"
            )



    async def delete_object(
        self,
        bucket: str,
        key: str,
    ):

        """
        Delete object.
        """

        try:

            async with self._client() as client:

                await client.delete_object(
                    Bucket=bucket,
                    Key=key
                )


            return {
                "success": True,
                "deleted": key
            }


        except ClientError as e:

            raise Exception(
                f"S3 delete failed: {e}"
            )



    async def list_objects(
        self,
        bucket: str,
        prefix: Optional[str] = None
    ):

        """
        List objects inside bucket.
        """

        try:

            async with self._client() as client:


                params = {
                    "Bucket": bucket
                }


                if prefix:
                    params["Prefix"] = prefix



                response = await client.list_objects_v2(
                    **params
                )


                return response.get(
                    "Contents",
                    []
                )


        except ClientError as e:

            raise Exception(
                f"S3 listing failed: {e}"
            )



    async def generate_presigned_url(
        self,
        bucket: str,
        key: str,
        expires: int = 3600
    ):

        """
        Generate temporary download URL.
        """

        try:

            async with self._client() as client:

                url = await client.generate_presigned_url(
                    "get_object",
                    Params={
                        "Bucket": bucket,
                        "Key": key,
                    },
                    ExpiresIn=expires
                )


                return url


        except ClientError as e:

            raise Exception(
                f"S3 URL generation failed: {e}"
            )