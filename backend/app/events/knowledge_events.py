"""
Knowledge Domain Events

These events are emitted whenever something important happens
inside the Knowledge subsystem.

Example:
---------
Document Uploaded
        ↓
DocumentIngestedEvent
        ↓
Embedding Worker
        ↓
EmbeddingsGeneratedEvent
        ↓
Indexing Worker
        ↓
DocumentIndexedEvent
        ↓
Search Available
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any
from uuid import UUID, uuid4


# ============================================================
# Base Event
# ============================================================

@dataclass(slots=True)
class KnowledgeEvent:
    """Base class for all knowledge events."""

    event_id: UUID = field(default_factory=uuid4)
    timestamp: datetime = field(default_factory=datetime.utcnow)
    event_type: str = "knowledge.event"

    def to_dict(self) -> dict[str, Any]:
        return {
            "event_id": str(self.event_id),
            "timestamp": self.timestamp.isoformat(),
            "event_type": self.event_type,
        }


# ============================================================
# Collection Events
# ============================================================

@dataclass(slots=True)
class CollectionCreatedEvent(KnowledgeEvent):
    collection_id: UUID = field(default_factory=uuid4)
    organization_id: UUID | None = None
    project_id: UUID | None = None
    name: str = ""

    event_type: str = "knowledge.collection.created"


@dataclass(slots=True)
class CollectionDeletedEvent(KnowledgeEvent):
    collection_id: UUID = field(default_factory=uuid4)

    event_type: str = "knowledge.collection.deleted"


# ============================================================
# Document Events
# ============================================================

@dataclass(slots=True)
class DocumentUploadedEvent(KnowledgeEvent):
    document_id: UUID = field(default_factory=uuid4)
    collection_id: UUID = field(default_factory=uuid4)
    filename: str = ""

    event_type: str = "knowledge.document.uploaded"


@dataclass(slots=True)
class DocumentIngestedEvent(KnowledgeEvent):
    document_id: UUID = field(default_factory=uuid4)
    chunk_count: int = 0

    event_type: str = "knowledge.document.ingested"


@dataclass(slots=True)
class DocumentDeletedEvent(KnowledgeEvent):
    document_id: UUID = field(default_factory=uuid4)

    event_type: str = "knowledge.document.deleted"


# ============================================================
# Chunk Events
# ============================================================

@dataclass(slots=True)
class ChunkCreatedEvent(KnowledgeEvent):
    chunk_id: UUID = field(default_factory=uuid4)
    document_id: UUID = field(default_factory=uuid4)

    event_type: str = "knowledge.chunk.created"


@dataclass(slots=True)
class ChunkDeletedEvent(KnowledgeEvent):
    chunk_id: UUID = field(default_factory=uuid4)

    event_type: str = "knowledge.chunk.deleted"


# ============================================================
# Embedding Events
# ============================================================

@dataclass(slots=True)
class EmbeddingsGeneratedEvent(KnowledgeEvent):
    document_id: UUID = field(default_factory=uuid4)
    embedding_count: int = 0
    model_name: str = ""

    event_type: str = "knowledge.embeddings.generated"


@dataclass(slots=True)
class EmbeddingsDeletedEvent(KnowledgeEvent):
    document_id: UUID = field(default_factory=uuid4)

    event_type: str = "knowledge.embeddings.deleted"


# ============================================================
# Index Events
# ============================================================

@dataclass(slots=True)
class DocumentIndexedEvent(KnowledgeEvent):
    document_id: UUID = field(default_factory=uuid4)
    index_name: str = ""

    event_type: str = "knowledge.document.indexed"


@dataclass(slots=True)
class IndexRebuiltEvent(KnowledgeEvent):
    collection_id: UUID = field(default_factory=uuid4)
    document_count: int = 0

    event_type: str = "knowledge.index.rebuilt"


# ============================================================
# Search Events
# ============================================================

@dataclass(slots=True)
class SearchExecutedEvent(KnowledgeEvent):
    query: str = ""
    result_count: int = 0
    latency_ms: float = 0.0

    event_type: str = "knowledge.search.executed"


# ============================================================
# Knowledge Graph Events
# ============================================================

@dataclass(slots=True)
class GraphUpdatedEvent(KnowledgeEvent):
    collection_id: UUID = field(default_factory=uuid4)
    entities_added: int = 0
    relations_added: int = 0

    event_type: str = "knowledge.graph.updated"


# ============================================================
# Cleanup Events
# ============================================================

@dataclass(slots=True)
class KnowledgeCleanupEvent(KnowledgeEvent):
    deleted_chunks: int = 0
    deleted_embeddings: int = 0

    event_type: str = "knowledge.cleanup.completed"


# ============================================================
# Reindex Events
# ============================================================

@dataclass(slots=True)
class ReindexRequestedEvent(KnowledgeEvent):
    collection_id: UUID = field(default_factory=uuid4)

    event_type: str = "knowledge.reindex.requested"


@dataclass(slots=True)
class ReindexCompletedEvent(KnowledgeEvent):
    collection_id: UUID = field(default_factory=uuid4)
    indexed_documents: int = 0

    event_type: str = "knowledge.reindex.completed"


# ============================================================
# Failure Events
# ============================================================

@dataclass(slots=True)
class KnowledgeErrorEvent(KnowledgeEvent):
    resource_id: UUID | None = None
    operation: str = ""
    error: str = ""

    event_type: str = "knowledge.error"