from __future__ import annotations

from typing import List, Optional

from sqlalchemy.orm import Session

from app.db.models.embedding import Embedding


class EmbeddingRepository:
    """
    Database operations for embeddings.
    """

    def __init__(self, db: Session):
        self.db = db

    def create(self, embedding: Embedding) -> Embedding:
        self.db.add(embedding)
        self.db.commit()
        self.db.refresh(embedding)
        return embedding

    def get(self, embedding_id: int) -> Optional[Embedding]:
        return (
            self.db.query(Embedding)
            .filter(Embedding.id == embedding_id)
            .first()
        )

    def get_by_chunk(self, chunk_id: int):
        return (
            self.db.query(Embedding)
            .filter(Embedding.chunk_id == chunk_id)
            .first()
        )

    def list(self) -> List[Embedding]:
        return self.db.query(Embedding).all()

    def delete(self, embedding_id: int):
        embedding = self.get(embedding_id)

        if embedding:
            self.db.delete(embedding)
            self.db.commit()