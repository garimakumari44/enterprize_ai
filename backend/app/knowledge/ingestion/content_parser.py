from pathlib import Path
from typing import Dict


class ContentParser:
    """
    Parses document content.

    Supports:
    - PDF
    - TXT
    - DOCX (future)
    """


    def parse(self, file_path: str) -> Dict:
        """
        Extract content from document.

        Returns:
            {
                "text": "...",
                "type": "pdf"
            }
        """

        path = Path(file_path)

        if not path.exists():
            raise FileNotFoundError(
                f"Document not found: {file_path}"
            )


        extension = path.suffix.lower()


        if extension == ".txt":
            text = self._parse_txt(path)

        elif extension == ".pdf":
            text = self._parse_pdf(path)

        else:
            raise ValueError(
                f"Unsupported file type {extension}"
            )


        return {
            "text": text,
            "file_type": extension.replace(".", "")
        }



    def _parse_txt(self, path: Path) -> str:

        return path.read_text(
            encoding="utf-8"
        )



    def _parse_pdf(self, path: Path) -> str:
        """
        PDF extraction placeholder.

        Production:
        - PyMuPDF
        - Apache Tika
        - Unstructured.io
        """

        import fitz


        document = fitz.open(path)

        pages = []


        for page in document:
            pages.append(
                page.get_text()
            )


        return "\n".join(pages)