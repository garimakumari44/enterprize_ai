# app/integrations/google_drive/drive_client.py

from typing import Optional, List, Dict, Any
import io

from google.oauth2.credentials import Credentials
from google.oauth2.service_account import Credentials as ServiceAccountCredentials

from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload, MediaIoBaseDownload


class GoogleDriveClient:
    """
    Low-level Google Drive API client.

    Handles:
    - Authentication
    - API initialization
    - Raw Drive operations
    """


    SCOPES = [
        "https://www.googleapis.com/auth/drive"
    ]


    def __init__(
        self,
        credentials: Dict[str, Any],
    ):
        """
        credentials:
        {
            "type": "service_account",
            "file": "service_account.json"
        }

        OR

        {
            "type": "oauth",
            "token": "...",
            "refresh_token": "..."
        }
        """

        self.credentials = self._load_credentials(credentials)

        self.client = build(
            "drive",
            "v3",
            credentials=self.credentials
        )


    # -----------------------------------
    # Authentication
    # -----------------------------------

    def _load_credentials(
        self,
        credentials: Dict[str, Any]
    ):

        auth_type = credentials.get("type")


        if auth_type == "service_account":

            return ServiceAccountCredentials.from_service_account_file(
                credentials["file"],
                scopes=self.SCOPES
            )


        elif auth_type == "oauth":

            return Credentials(
                token=credentials["token"],
                refresh_token=credentials.get(
                    "refresh_token"
                ),
                token_uri="https://oauth2.googleapis.com/token",
                client_id=credentials["client_id"],
                client_secret=credentials["client_secret"],
                scopes=self.SCOPES
            )


        raise ValueError(
            "Unsupported Google Drive authentication type"
        )


    # -----------------------------------
    # Files
    # -----------------------------------

    def list_files(
        self,
        query: Optional[str] = None,
        limit: int = 10
    ) -> List[Dict]:


        response = (
            self.client
            .files()
            .list(
                q=query,
                pageSize=limit,
                fields="files(id,name,mimeType,size)"
            )
            .execute()
        )


        return response.get(
            "files",
            []
        )


    def get_file(
        self,
        file_id: str
    ) -> Dict:


        response = (
            self.client
            .files()
            .get(
                fileId=file_id,
                fields="*"
            )
            .execute()
        )


        return response



    def download_file(
        self,
        file_id: str
    ) -> bytes:


        request = (
            self.client
            .files()
            .get_media(
                fileId=file_id
            )
        )


        buffer = io.BytesIO()

        downloader = MediaIoBaseDownload(
            buffer,
            request
        )


        done = False

        while not done:

            _, done = downloader.next_chunk()


        return buffer.getvalue()



    def upload_file(
        self,
        name: str,
        content: bytes,
        mime_type: str
    ) -> Dict:


        file_metadata = {
            "name": name
        }


        media = MediaIoBaseUpload(
            io.BytesIO(content),
            mimetype=mime_type
        )


        response = (
            self.client
            .files()
            .create(
                body=file_metadata,
                media_body=media,
                fields="id,name"
            )
            .execute()
        )


        return response



    def delete_file(
        self,
        file_id: str
    ) -> bool:


        self.client.files().delete(
            fileId=file_id
        ).execute()


        return True