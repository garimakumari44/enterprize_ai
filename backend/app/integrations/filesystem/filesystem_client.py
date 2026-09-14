"""
Filesystem Client

Low-level filesystem operations.
"""

from pathlib import Path
from typing import List, Optional


class FilesystemClient:
    """
    Client responsible for interacting with local filesystem.
    """

    def __init__(self, base_path: Optional[str] = None):
        """
        Args:
            base_path:
                Root directory where operations are allowed.
        """

        self.base_path = Path(base_path).resolve() if base_path else None


    def _resolve_path(self, path: str) -> Path:
        """
        Resolve and validate filesystem path.
        """

        file_path = Path(path)

        if self.base_path:
            file_path = self.base_path / file_path


        file_path = file_path.resolve()


        if self.base_path:
            if not str(file_path).startswith(
                str(self.base_path)
            ):
                raise PermissionError(
                    "Access outside base directory is not allowed"
                )

        return file_path



    def exists(self, path: str) -> bool:
        """
        Check file existence.
        """

        return self._resolve_path(path).exists()



    def read_file(
        self,
        path: str,
        encoding: str = "utf-8"
    ) -> str:
        """
        Read text file.
        """

        file_path = self._resolve_path(path)

        if not file_path.exists():
            raise FileNotFoundError(path)


        return file_path.read_text(
            encoding=encoding
        )



    def write_file(
        self,
        path: str,
        content: str,
        encoding: str = "utf-8"
    ) -> str:
        """
        Write content to file.
        """

        file_path = self._resolve_path(path)


        file_path.parent.mkdir(
            parents=True,
            exist_ok=True
        )


        file_path.write_text(
            content,
            encoding=encoding
        )


        return str(file_path)



    def append_file(
        self,
        path: str,
        content: str,
        encoding: str = "utf-8"
    ):
        """
        Append content to file.
        """

        file_path = self._resolve_path(path)


        with file_path.open(
            "a",
            encoding=encoding
        ) as file:
            file.write(content)



    def delete_file(
        self,
        path: str
    ):
        """
        Delete file.
        """

        file_path = self._resolve_path(path)


        if file_path.exists():
            file_path.unlink()



    def create_directory(
        self,
        path: str
    ):

        directory = self._resolve_path(path)

        directory.mkdir(
            parents=True,
            exist_ok=True
        )

        return str(directory)



    def list_files(
        self,
        path: str = "."
    ) -> List[str]:
        """
        List files inside directory.
        """

        directory = self._resolve_path(path)


        if not directory.exists():
            raise FileNotFoundError(path)


        return [
            str(item)
            for item in directory.iterdir()
        ]



    def get_file_size(
        self,
        path: str
    ) -> int:
        """
        Return file size in bytes.
        """

        file_path = self._resolve_path(path)

        return file_path.stat().st_size