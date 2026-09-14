# app/integrations/google_drive/drive_service.py

from typing import Dict, List

from .drive_client import GoogleDriveClient



class GoogleDriveService:
    """
    Google Drive business service.

    Used by:
    - Google Drive Workflow Node
    - Automation Engine
    - Document Intelligence
    """


    def __init__(
        self,
        client: GoogleDriveClient
    ):

        self.client = client



    # -----------------------------------
    # Search
    # -----------------------------------

    def search_documents(
        self,
        keyword: str,
        limit: int = 20
    ) -> List[Dict]:


        query = (
            f"name contains '{keyword}'"
        )


        files = self.client.list_files(
            query=query,
            limit=limit
        )


        return [
            {
                "id": file["id"],
                "name": file["name"],
                "type": file.get(
                    "mimeType"
                )
            }
            for file in files
        ]



    # -----------------------------------
    # Get metadata
    # -----------------------------------

    def get_document(
        self,
        file_id: str
    ) -> Dict:


        file = self.client.get_file(
            file_id
        )


        return {
            "id": file["id"],
            "name": file["name"],
            "mime_type": file.get(
                "mimeType"
            ),
            "size": file.get(
                "size"
            )
        }



    # -----------------------------------
    # Download
    # -----------------------------------

    def download_document(
        self,
        file_id: str
    ) -> Dict:


        metadata = self.client.get_file(
            file_id
        )


        content = self.client.download_file(
            file_id
        )


        return {

            "id": file_id,

            "name": metadata["name"],

            "content": content,

            "mime_type":
                metadata.get(
                    "mimeType"
                )
        }



    # -----------------------------------
    # Upload
    # -----------------------------------

    def upload_document(
        self,
        name: str,
        content: bytes,
        mime_type: str
    ) -> Dict:


        result = self.client.upload_file(
            name=name,
            content=content,
            mime_type=mime_type
        )


        return {

            "file_id": result["id"],

            "name": result["name"],

            "status": "uploaded"
        }



    # -----------------------------------
    # Delete
    # -----------------------------------

    def remove_document(
        self,
        file_id: str
    ) -> Dict:


        self.client.delete_file(
            file_id
        )


        return {

            "file_id": file_id,

            "status": "deleted"
        }