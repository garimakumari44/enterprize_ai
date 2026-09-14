"""
Knowledge Indexing Celery Tasks
"""

from celery import shared_task

from app.db.session import SessionLocal
from app.knowledge.services.indexing_service import IndexingService


@shared_task(name="knowledge.index_document")
def index_document(document_id: str):
    """
    Index document into
    vector database.
    """

    db = SessionLocal()

    try:
        service = IndexingService(db)

        result = service.index_document(document_id)

        return {
            "status": "success",
            "document_id": document_id,
            "indexed": result,
        }

    finally:
        db.close()


@shared_task(name="knowledge.reindex_collection")
def reindex_collection(collection_id: str):
    """
    Rebuild complete vector index.
    """

    db = SessionLocal()

    try:
        service = IndexingService(db)

        total = service.reindex_collection(collection_id)

        return {
            "status": "success",
            "collection_id": collection_id,
            "documents": total,
        }

    finally:
        db.close()


@shared_task(name="knowledge.delete_document_index")
def delete_document_index(document_id: str):
    """
    Remove document from vector index.
    """

    db = SessionLocal()

    try:
        service = IndexingService(db)

        service.delete_document(document_id)

        return {
            "status": "deleted",
            "document_id": document_id,
        }

    finally:
        db.close()