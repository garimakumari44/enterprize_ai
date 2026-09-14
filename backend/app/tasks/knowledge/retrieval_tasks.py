"""
Knowledge Retrieval Celery Tasks
"""

from celery import shared_task

from app.db.session import SessionLocal
from app.knowledge.services.search_service    import SearchService


@shared_task(name="knowledge.semantic_search")
def semantic_search(
    query: str,
    collection_id: str,
    top_k: int = 10,
):
    """
    Perform semantic vector search.
    """

    db = SessionLocal()

    try:
        service = SearchService(db)

        results = service.semantic_search(
            query=query,
            collection_id=collection_id,
            top_k=top_k,
        )

        return {
            "query": query,
            "results": results,
        }

    finally:
        db.close()


@shared_task(name="knowledge.hybrid_search")
def hybrid_search(
    query: str,
    collection_id: str,
    top_k: int = 10,
):
    """
    Run hybrid search
    (vector + keyword).
    """

    db = SessionLocal()

    try:
        service = SearchService(db)

        results = service.hybrid_search(
            query=query,
            collection_id=collection_id,
            top_k=top_k,
        )

        return {
            "query": query,
            "results": results,
        }

    finally:
        db.close()