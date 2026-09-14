"""
Filesystem Service

Business layer for filesystem integration.
"""

from typing import Dict, Any

from .filesystem_client import FilesystemClient



class FilesystemService:
    """
    Service layer used by workflow nodes.
    """

    def __init__(
        self,
        client: FilesystemClient
    ):
        self.client = client



    def read(
        self,
        file_path: str
    ) -> Dict[str, Any]:

        content = self.client.read_file(
            file_path
        )


        return {
            "success": True,
            "path": file_path,
            "content": content
        }



    def write(
        self,
        file_path: str,
        content: str
    ) -> Dict[str, Any]:

        saved_path = self.client.write_file(
            file_path,
            content
        )


        return {
            "success": True,
            "path": saved_path
        }



    def delete(
        self,
        file_path: str
    ) -> Dict[str, Any]:

        self.client.delete_file(
            file_path
        )


        return {
            "success": True,
            "deleted": file_path
        }



    def list(
        self,
        directory: str = "."
    ) -> Dict[str, Any]:

        files = self.client.list_files(
            directory
        )


        return {
            "success": True,
            "files": files
        }



    def exists(
        self,
        file_path: str
    ) -> Dict[str, Any]:

        result = self.client.exists(
            file_path
        )


        return {
            "success": True,
            "exists": result
        }



    def metadata(
        self,
        file_path: str
    ) -> Dict[str, Any]:

        size = self.client.get_file_size(
            file_path
        )


        return {
            "success": True,
            "size": size,
            "path": file_path
        }