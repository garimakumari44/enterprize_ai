from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.documents.document import Document


class SearchService:
    """
    Search documents.

    Later this can be replaced by:
    - Elasticsearch
    - OpenSearch
    - Vector Search
    """

    def __init__(self, db: Session):
        self.db = db

    def by_filename(self, keyword: str):
        stmt = select(Document).where(
            Document.filename.ilike(f"%{keyword}%")
        )

        return self.db.scalars(stmt).all()

    def by_content_type(self, content_type: str):
        stmt = select(Document).where(
            Document.mime_type == content_type
        )

        return self.db.scalars(stmt).all()

    def by_folder(self, folder_id):
        stmt = select(Document).where(
            Document.folder_id == folder_id
        )

        return self.db.scalars(stmt).all()

    def all(self):
        stmt = select(Document)

        return self.db.scalars(stmt).all()