from datetime import datetime
from pathlib import Path


class MetadataExtractor:
    """
    Extract document metadata.
    """


    def extract(
        self,
        file_path: str,
        extra_metadata: dict | None = None
    ) -> dict:


        path = Path(file_path)


        metadata = {

            "filename":
                path.name,


            "extension":
                path.suffix,


            "size":
                path.stat().st_size,


            "created_at":
                datetime.utcnow(),


        }


        if extra_metadata:
            metadata.update(
                extra_metadata
            )


        return metadata