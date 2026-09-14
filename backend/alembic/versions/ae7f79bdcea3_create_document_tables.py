"""
create document tables

Revision ID: ae7f79bdcea3
Revises: 005f97529df2
Create Date: 2026-08-13 11:42:46.366529

Creates the document storage and processing infrastructure.

Tables:
    folders
    tags
    documents
    document_versions
    document_chunks
    document_tags
    processing_jobs
    processing_steps
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# ---------------------------------------------------------------------------
# Revision identifiers
# ---------------------------------------------------------------------------

revision: str = "ae7f79bdcea3"
down_revision: Union[str, Sequence[str], None] = "005f97529df2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# ============================================================================
# UPGRADE
# ============================================================================


def upgrade() -> None:
    """
    Create document storage and processing tables.

    Dependency order:

        folders
        tags

        documents
            |
            v
        document_versions
            |
            +--> document_chunks
            |
            +--> processing_jobs
                    |
                    v
              processing_steps

        documents <--> document_versions
            circular FK completed after both tables exist

    The existing users table is intentionally untouched.
    """

    # ========================================================================
    # FOLDERS
    # ========================================================================

    op.create_table(
        "folders",

        sa.Column(
            "id",
            sa.UUID(),
            nullable=False,
        ),

        sa.Column(
            "name",
            sa.String(length=255),
            nullable=False,
        ),

        sa.Column(
            "description",
            sa.Text(),
            nullable=True,
        ),

        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),

        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),

        sa.PrimaryKeyConstraint("id"),
    )

    op.create_index(
        op.f("ix_folders_name"),
        "folders",
        ["name"],
        unique=False,
    )

    # ========================================================================
    # TAGS
    # ========================================================================

    op.create_table(
        "tags",

        sa.Column(
            "id",
            sa.UUID(),
            nullable=False,
        ),

        sa.Column(
            "name",
            sa.String(length=100),
            nullable=False,
        ),

        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),

        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),

        sa.PrimaryKeyConstraint("id"),
    )

    op.create_index(
        op.f("ix_tags_name"),
        "tags",
        ["name"],
        unique=True,
    )

    # ========================================================================
    # DOCUMENTS
    # ========================================================================
    #
    # current_version_id intentionally has NO FK here.
    #
    # document_versions.document_id -> documents.id
    #
    # The reverse FK:
    #
    # documents.current_version_id -> document_versions.id
    #
    # is added after document_versions exists.
    # ========================================================================

    op.create_table(
        "documents",

        sa.Column(
            "id",
            sa.UUID(),
            nullable=False,
        ),

        sa.Column(
            "name",
            sa.String(length=500),
            nullable=False,
        ),

        sa.Column(
            "description",
            sa.Text(),
            nullable=True,
        ),

        sa.Column(
            "document_type",
            sa.String(length=100),
            nullable=True,
        ),

        sa.Column(
            "status",
            sa.String(length=50),
            server_default="active",
            nullable=False,
        ),

        sa.Column(
            "current_version_id",
            sa.UUID(),
            nullable=True,
        ),

        sa.Column(
            "metadata",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'{}'::jsonb"),
            nullable=False,
        ),

        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),

        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),

        sa.PrimaryKeyConstraint("id"),
    )

    op.create_index(
        op.f("ix_documents_status"),
        "documents",
        ["status"],
        unique=False,
    )

    # ========================================================================
    # DOCUMENT VERSIONS
    # ========================================================================

    op.create_table(
        "document_versions",

        sa.Column(
            "id",
            sa.UUID(),
            nullable=False,
        ),

        sa.Column(
            "document_id",
            sa.UUID(),
            nullable=False,
        ),

        sa.Column(
            "version_number",
            sa.Integer(),
            nullable=False,
        ),

        # --------------------------------------------------------------------
        # Original file
        # --------------------------------------------------------------------

        sa.Column(
            "original_filename",
            sa.String(length=1000),
            nullable=False,
        ),

        sa.Column(
            "mime_type",
            sa.String(length=255),
            nullable=True,
        ),

        sa.Column(
            "file_size",
            sa.BigInteger(),
            nullable=True,
        ),

        sa.Column(
            "checksum",
            sa.String(length=128),
            nullable=True,
        ),

        # --------------------------------------------------------------------
        # Object storage
        # --------------------------------------------------------------------

        # IMPORTANT:
        # Must match DocumentVersion.storage_provider
        # default="minio"
        sa.Column(
            "storage_provider",
            sa.String(length=100),
            server_default="minio",
            nullable=False,
        ),

        # IMPORTANT:
        # Must match DocumentVersion.object_storage_bucket
        # nullable=False
        sa.Column(
            "object_storage_bucket",
            sa.String(length=255),
            nullable=False,
        ),

        sa.Column(
            "object_storage_key",
            sa.String(length=2000),
            nullable=False,
        ),

        # --------------------------------------------------------------------
        # Processing state
        # --------------------------------------------------------------------

        sa.Column(
            "status",
            sa.String(length=50),
            server_default="uploaded",
            nullable=False,
        ),

        sa.Column(
            "error_message",
            sa.Text(),
            nullable=True,
        ),

        # --------------------------------------------------------------------
        # Extracted metadata
        # --------------------------------------------------------------------

        sa.Column(
            "page_count",
            sa.Integer(),
            nullable=True,
        ),

        sa.Column(
            "detected_language",
            sa.String(length=50),
            nullable=True,
        ),

        sa.Column(
            "metadata",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'{}'::jsonb"),
            nullable=False,
        ),

        # --------------------------------------------------------------------
        # Timestamps
        # --------------------------------------------------------------------

        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),

        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),

        # --------------------------------------------------------------------
        # Foreign keys
        # --------------------------------------------------------------------

        sa.ForeignKeyConstraint(
            ["document_id"],
            ["documents.id"],
            ondelete="CASCADE",
        ),

        sa.PrimaryKeyConstraint("id"),

        sa.UniqueConstraint(
            "document_id",
            "version_number",
            name="uq_document_version_number",
        ),
    )

    # ------------------------------------------------------------------------
    # Indexes
    # ------------------------------------------------------------------------

    op.create_index(
        op.f("ix_document_versions_checksum"),
        "document_versions",
        ["checksum"],
        unique=False,
    )

    op.create_index(
        op.f("ix_document_versions_document_id"),
        "document_versions",
        ["document_id"],
        unique=False,
    )

    op.create_index(
        op.f("ix_document_versions_status"),
        "document_versions",
        ["status"],
        unique=False,
    )

    # ========================================================================
    # COMPLETE DOCUMENT <-> VERSION RELATIONSHIP
    # ========================================================================

    op.create_foreign_key(
        "fk_documents_current_version_id",
        "documents",
        "document_versions",
        ["current_version_id"],
        ["id"],
        ondelete="SET NULL",
    )

    # ========================================================================
    # DOCUMENT CHUNKS
    # ========================================================================

    op.create_table(
        "document_chunks",

        sa.Column(
            "id",
            sa.UUID(),
            nullable=False,
        ),

        sa.Column(
            "document_version_id",
            sa.UUID(),
            nullable=False,
        ),

        sa.Column(
            "chunk_index",
            sa.Integer(),
            nullable=False,
        ),

        sa.Column(
            "parent_chunk_id",
            sa.UUID(),
            nullable=True,
        ),

        sa.Column(
            "chunk_type",
            sa.String(length=100),
            server_default="text",
            nullable=False,
        ),

        sa.Column(
            "content",
            sa.Text(),
            nullable=False,
        ),

        sa.Column(
            "normalized_content",
            sa.Text(),
            nullable=True,
        ),

        sa.Column(
            "token_count",
            sa.Integer(),
            nullable=True,
        ),

        sa.Column(
            "character_count",
            sa.Integer(),
            nullable=True,
        ),

        sa.Column(
            "page_start",
            sa.Integer(),
            nullable=True,
        ),

        sa.Column(
            "page_end",
            sa.Integer(),
            nullable=True,
        ),

        sa.Column(
            "section_title",
            sa.String(length=1000),
            nullable=True,
        ),

        sa.Column(
            "section_path",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
        ),

        sa.Column(
            "metadata",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'{}'::jsonb"),
            nullable=False,
        ),

        sa.Column(
            "entities",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
        ),

        sa.Column(
            "keywords",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
        ),

        sa.Column(
            "embedding_status",
            sa.String(length=50),
            server_default="pending",
            nullable=False,
        ),

        sa.Column(
            "embedding_model",
            sa.String(length=255),
            nullable=True,
        ),

        sa.Column(
            "embedding_dimensions",
            sa.Integer(),
            nullable=True,
        ),

        sa.Column(
            "indexed",
            sa.Boolean(),
            server_default=sa.text("false"),
            nullable=False,
        ),

        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),

        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),

        sa.ForeignKeyConstraint(
            ["document_version_id"],
            ["document_versions.id"],
            ondelete="CASCADE",
        ),

        sa.ForeignKeyConstraint(
            ["parent_chunk_id"],
            ["document_chunks.id"],
            ondelete="SET NULL",
        ),

        sa.PrimaryKeyConstraint("id"),
    )

    # ------------------------------------------------------------------------
    # Chunk indexes
    # ------------------------------------------------------------------------

    op.create_index(
        op.f("ix_document_chunks_chunk_type"),
        "document_chunks",
        ["chunk_type"],
        unique=False,
    )

    op.create_index(
        op.f("ix_document_chunks_document_version_id"),
        "document_chunks",
        ["document_version_id"],
        unique=False,
    )

    op.create_index(
        op.f("ix_document_chunks_embedding_status"),
        "document_chunks",
        ["embedding_status"],
        unique=False,
    )

    op.create_index(
        op.f("ix_document_chunks_indexed"),
        "document_chunks",
        ["indexed"],
        unique=False,
    )

    op.create_index(
        op.f("ix_document_chunks_parent_chunk_id"),
        "document_chunks",
        ["parent_chunk_id"],
        unique=False,
    )

    # ========================================================================
    # DOCUMENT TAGS
    # ========================================================================

    op.create_table(
        "document_tags",

        sa.Column(
            "document_id",
            sa.UUID(),
            nullable=False,
        ),

        sa.Column(
            "tag_id",
            sa.UUID(),
            nullable=False,
        ),

        sa.ForeignKeyConstraint(
            ["document_id"],
            ["documents.id"],
            ondelete="CASCADE",
        ),

        sa.ForeignKeyConstraint(
            ["tag_id"],
            ["tags.id"],
            ondelete="CASCADE",
        ),

        sa.PrimaryKeyConstraint(
            "document_id",
            "tag_id",
        ),
    )

    # ========================================================================
    # PROCESSING JOBS
    # ========================================================================

    op.create_table(
        "processing_jobs",

        sa.Column(
            "id",
            sa.UUID(),
            nullable=False,
        ),

        sa.Column(
            "document_version_id",
            sa.UUID(),
            nullable=False,
        ),

        # --------------------------------------------------------------------
        # Job identity
        # --------------------------------------------------------------------

        sa.Column(
            "job_type",
            sa.String(length=100),
            server_default="document_processing",
            nullable=False,
        ),

        sa.Column(
            "status",
            sa.String(length=50),
            server_default="queued",
            nullable=False,
        ),

        # --------------------------------------------------------------------
        # Execution control
        # --------------------------------------------------------------------

        sa.Column(
            "priority",
            sa.Integer(),
            server_default="0",
            nullable=False,
        ),

        sa.Column(
            "attempt_count",
            sa.Integer(),
            server_default="0",
            nullable=False,
        ),

        sa.Column(
            "max_attempts",
            sa.Integer(),
            server_default="3",
            nullable=False,
        ),

        sa.Column(
            "worker_id",
            sa.String(length=255),
            nullable=True,
        ),

        # --------------------------------------------------------------------
        # Progress
        # --------------------------------------------------------------------

        sa.Column(
            "current_step",
            sa.String(length=100),
            nullable=True,
        ),

        sa.Column(
            "progress",
            sa.Integer(),
            server_default="0",
            nullable=False,
        ),

        # --------------------------------------------------------------------
        # Errors
        # --------------------------------------------------------------------

        sa.Column(
            "error_code",
            sa.String(length=100),
            nullable=True,
        ),

        sa.Column(
            "error_message",
            sa.Text(),
            nullable=True,
        ),

        # --------------------------------------------------------------------
        # Configuration
        # --------------------------------------------------------------------

        sa.Column(
            "config",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'{}'::jsonb"),
            nullable=False,
        ),

        # --------------------------------------------------------------------
        # Result
        # --------------------------------------------------------------------

        sa.Column(
            "result",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'{}'::jsonb"),
            nullable=False,
        ),

        # --------------------------------------------------------------------
        # Timestamps
        # --------------------------------------------------------------------

        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),

        sa.Column(
            "started_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),

        sa.Column(
            "completed_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),

        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),

        sa.ForeignKeyConstraint(
            ["document_version_id"],
            ["document_versions.id"],
            ondelete="CASCADE",
        ),

        sa.PrimaryKeyConstraint("id"),
    )

    # ------------------------------------------------------------------------
    # Processing job indexes
    # ------------------------------------------------------------------------

    op.create_index(
        op.f("ix_processing_jobs_document_version_id"),
        "processing_jobs",
        ["document_version_id"],
        unique=False,
    )

    op.create_index(
        op.f("ix_processing_jobs_job_type"),
        "processing_jobs",
        ["job_type"],
        unique=False,
    )

    op.create_index(
        op.f("ix_processing_jobs_status"),
        "processing_jobs",
        ["status"],
        unique=False,
    )

    # ========================================================================
    # PROCESSING STEPS
    # ========================================================================

    op.create_table(
        "processing_steps",

        sa.Column(
            "id",
            sa.UUID(),
            nullable=False,
        ),

        sa.Column(
            "processing_job_id",
            sa.UUID(),
            nullable=False,
        ),

        # --------------------------------------------------------------------
        # Step identity
        # --------------------------------------------------------------------

        sa.Column(
            "name",
            sa.String(length=100),
            nullable=False,
        ),

        sa.Column(
            "step_order",
            sa.Integer(),
            nullable=False,
        ),

        sa.Column(
            "status",
            sa.String(length=50),
            server_default="pending",
            nullable=False,
        ),

        # --------------------------------------------------------------------
        # Provider
        # --------------------------------------------------------------------

        sa.Column(
            "provider",
            sa.String(length=100),
            nullable=True,
        ),

        sa.Column(
            "provider_operation",
            sa.String(length=255),
            nullable=True,
        ),

        # --------------------------------------------------------------------
        # Execution
        # --------------------------------------------------------------------

        sa.Column(
            "attempt_count",
            sa.Integer(),
            server_default="0",
            nullable=False,
        ),

        sa.Column(
            "duration_ms",
            sa.Integer(),
            nullable=True,
        ),

        # --------------------------------------------------------------------
        # Metadata
        # --------------------------------------------------------------------

        sa.Column(
            "input_metadata",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'{}'::jsonb"),
            nullable=False,
        ),

        sa.Column(
            "output_metadata",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'{}'::jsonb"),
            nullable=False,
        ),

        # --------------------------------------------------------------------
        # Errors
        # --------------------------------------------------------------------

        sa.Column(
            "error_code",
            sa.String(length=100),
            nullable=True,
        ),

        sa.Column(
            "error_message",
            sa.Text(),
            nullable=True,
        ),

        # --------------------------------------------------------------------
        # Timestamps
        # --------------------------------------------------------------------

        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),

        sa.Column(
            "started_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),

        sa.Column(
            "completed_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),

        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),

        sa.ForeignKeyConstraint(
            ["processing_job_id"],
            ["processing_jobs.id"],
            ondelete="CASCADE",
        ),

        sa.PrimaryKeyConstraint("id"),
    )

    # ------------------------------------------------------------------------
    # Processing step indexes
    # ------------------------------------------------------------------------

    op.create_index(
        op.f("ix_processing_steps_name"),
        "processing_steps",
        ["name"],
        unique=False,
    )

    op.create_index(
        op.f("ix_processing_steps_processing_job_id"),
        "processing_steps",
        ["processing_job_id"],
        unique=False,
    )

    op.create_index(
        op.f("ix_processing_steps_status"),
        "processing_steps",
        ["status"],
        unique=False,
    )


# ============================================================================
# DOWNGRADE
# ============================================================================


def downgrade() -> None:
    """
    Remove all document-related tables.

    The users table is intentionally NOT touched.
    """

    # ========================================================================
    # PROCESSING STEPS
    # ========================================================================

    op.drop_index(
        op.f("ix_processing_steps_status"),
        table_name="processing_steps",
    )

    op.drop_index(
        op.f("ix_processing_steps_processing_job_id"),
        table_name="processing_steps",
    )

    op.drop_index(
        op.f("ix_processing_steps_name"),
        table_name="processing_steps",
    )

    op.drop_table("processing_steps")

    # ========================================================================
    # PROCESSING JOBS
    # ========================================================================

    op.drop_index(
        op.f("ix_processing_jobs_status"),
        table_name="processing_jobs",
    )

    op.drop_index(
        op.f("ix_processing_jobs_job_type"),
        table_name="processing_jobs",
    )

    op.drop_index(
        op.f("ix_processing_jobs_document_version_id"),
        table_name="processing_jobs",
    )

    op.drop_table("processing_jobs")

    # ========================================================================
    # DOCUMENT TAGS
    # ========================================================================

    op.drop_table("document_tags")

    # ========================================================================
    # DOCUMENT CHUNKS
    # ========================================================================

    op.drop_index(
        op.f("ix_document_chunks_parent_chunk_id"),
        table_name="document_chunks",
    )

    op.drop_index(
        op.f("ix_document_chunks_indexed"),
        table_name="document_chunks",
    )

    op.drop_index(
        op.f("ix_document_chunks_embedding_status"),
        table_name="document_chunks",
    )

    op.drop_index(
        op.f("ix_document_chunks_document_version_id"),
        table_name="document_chunks",
    )

    op.drop_index(
        op.f("ix_document_chunks_chunk_type"),
        table_name="document_chunks",
    )

    op.drop_table("document_chunks")

    # ========================================================================
    # DOCUMENT CURRENT VERSION FK
    # ========================================================================

    op.drop_constraint(
        "fk_documents_current_version_id",
        "documents",
        type_="foreignkey",
    )

    # ========================================================================
    # DOCUMENT VERSIONS
    # ========================================================================

    op.drop_index(
        op.f("ix_document_versions_status"),
        table_name="document_versions",
    )

    op.drop_index(
        op.f("ix_document_versions_document_id"),
        table_name="document_versions",
    )

    op.drop_index(
        op.f("ix_document_versions_checksum"),
        table_name="document_versions",
    )

    op.drop_table("document_versions")

    # ========================================================================
    # DOCUMENTS
    # ========================================================================

    op.drop_index(
        op.f("ix_documents_status"),
        table_name="documents",
    )

    op.drop_table("documents")

    # ========================================================================
    # TAGS
    # ========================================================================

    op.drop_index(
        op.f("ix_tags_name"),
        table_name="tags",
    )

    op.drop_table("tags")

    # ========================================================================
    # FOLDERS
    # ========================================================================

    op.drop_index(
        op.f("ix_folders_name"),
        table_name="folders",
    )

    op.drop_table("folders")