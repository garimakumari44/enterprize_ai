from __future__ import annotations

from typing import Any

from sqlalchemy import Index, Text, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column
from pgvector.sqlalchemy import Vector

from app.db.database import Base


class DocumentChunkVector(Base):
    __tablename__ = "document_chunk_vectors"

    id: Mapped[str] = mapped_column(
        Text,
        primary_key=True,
        nullable=False,
    )

    content: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    embedding: Mapped[list[float]] = mapped_column(
        Vector(384),
        nullable=False,
    )

    metadata_: Mapped[dict[str, Any]] = mapped_column(
        "metadata",
        JSONB,
        nullable=False,
        server_default=text("'{}'::jsonb"),
    )

    __table_args__ = (
        Index(
            "document_chunk_vectors_embedding_idx",
            "embedding",
            postgresql_using="hnsw",
            postgresql_ops={
                "embedding": "vector_cosine_ops",
            },
        ),
    )