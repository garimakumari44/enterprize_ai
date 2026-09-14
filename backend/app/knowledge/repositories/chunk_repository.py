from __future__ import annotations

from typing import List, Optional

from sqlalchemy.orm import Session

from app.db.models.chunk import Chunk


class ChunkRepository:
    """
    Database access for document chunks.
    """

    def __init__(self, db: Session):
        self.db = db

    def create(self, chunk: Chunk) -> Chunk:
        self.db.add(chunk)
        self.db.commit()
        self.db.refresh(chunk)
        return chunk

    def get(self, chunk_id: int) -> Optional[Chunk]:
        return (
            self.db.query(Chunk)
            .filter(Chunk.id == chunk_id)
            .first()
        )

    def get_by_document(self, document_id: int) -> List[Chunk]:
        return (
            self.db.query(Chunk)
            .filter(Chunk.document_id == document_id)
            .all()
        )

    def list(self, skip: int = 0, limit: int = 100):
        return (
            self.db.query(Chunk)
            .offset(skip)
            .limit(limit)
            .all()
        )

    def delete(self, chunk_id: int) -> bool:
        chunk = self.get(chunk_id)

        if not chunk:
            return False

        self.db.delete(chunk)
        self.db.commit()

        return True