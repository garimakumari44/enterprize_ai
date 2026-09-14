"""
Knowledge Embedding Celery Tasks
"""

from celery import shared_task

from app.db.session import SessionLocal
from app.processing.embeddings.service  import EmbeddingService



@shared_task(name="knowledge.generate_document_embeddings")
def generate_document_embeddings(document_id: str):
    """
    Generate embeddings for every chunk
    inside a document.
    """

    db = SessionLocal()

    try:
        service = EmbeddingService(db)

        result = service.generate_document_embeddings(
            document_id=document_id
        )

        return {
            "status": "success",
            "document_id": document_id,
            "chunks": result,
        }

    finally:
        db.close()


@shared_task(name="knowledge.generate_chunk_embedding")
def generate_chunk_embedding(chunk_id: str):
    """
    Generate embedding for a single chunk.
    """

    db = SessionLocal()

    try:
        service = EmbeddingService(db)

        service.generate_chunk_embedding(chunk_id)

        return {
            "status": "success",
            "chunk_id": chunk_id,
        }

    finally:
        db.close()


@shared_task(name="knowledge.regenerate_embeddings")
def regenerate_embeddings(collection_id: str):
    """
    Rebuild embeddings for
    an entire collection.
    """

    db = SessionLocal()

    try:
        service = EmbeddingService(db)

        total = service.regenerate_collection_embeddings(
            collection_id
        )

        return {
            "status": "success",
            "collection_id": collection_id,
            "documents": total,
        }

    finally:
        db.close()