"""add processing and review models

Revision ID: b35652cc2a5a
Revises: f76c1ba174b2
Create Date: 2026-09-01 21:13:54.987154

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = "b35652cc2a5a"
down_revision: Union[str, Sequence[str], None] = "f76c1ba174b2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""

    # ------------------------------------------------------------------
    # Extraction results
    # ------------------------------------------------------------------

    op.create_table(
        "extraction_results",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("document_id", sa.UUID(), nullable=False),
        sa.Column("document_version_id", sa.UUID(), nullable=False),
        sa.Column("processing_id", sa.UUID(), nullable=False),
        sa.Column("document_type", sa.String(length=100), nullable=False),
        sa.Column("overall_confidence", sa.Float(), nullable=False),
        sa.Column("raw_text", sa.Text(), nullable=True),
        sa.Column(
            "structured_data",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
        ),
        sa.Column("validation_status", sa.String(length=50), nullable=False),
        sa.Column("extraction_method", sa.String(length=100), nullable=True),
        sa.Column(
            "extraction_metadata",
            postgresql.JSONB(astext_type=sa.Text()),
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
        sa.CheckConstraint(
            """
            overall_confidence >= 0
            AND overall_confidence <= 1
            """,
            name="ck_extraction_results_overall_confidence",
        ),
        sa.ForeignKeyConstraint(
            ["document_id"],
            ["documents.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["document_version_id"],
            ["document_versions.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["processing_id"],
            ["processing_jobs.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_index(
        "ix_extraction_results_document_id",
        "extraction_results",
        ["document_id"],
        unique=False,
    )

    op.create_index(
        "ix_extraction_results_document_type",
        "extraction_results",
        ["document_type"],
        unique=False,
    )

    op.create_index(
        "ix_extraction_results_document_version_id",
        "extraction_results",
        ["document_version_id"],
        unique=False,
    )

    op.create_index(
        "ix_extraction_results_processing_id",
        "extraction_results",
        ["processing_id"],
        unique=False,
    )

    # ------------------------------------------------------------------
    # Extracted fields
    # ------------------------------------------------------------------

    op.create_table(
        "extracted_fields",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("extraction_result_id", sa.UUID(), nullable=False),
        sa.Column("field_name", sa.String(length=255), nullable=False),
        sa.Column(
            "value",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
        ),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column(
            "normalized_value",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
        ),
        sa.Column("source", sa.String(length=100), nullable=True),
        sa.Column("page_number", sa.Integer(), nullable=True),
        sa.Column(
            "bounding_box",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
        ),
        sa.Column(
            "field_metadata",
            postgresql.JSONB(astext_type=sa.Text()),
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
        sa.CheckConstraint(
            """
            confidence >= 0
            AND confidence <= 1
            """,
            name="ck_extracted_fields_confidence",
        ),
        sa.CheckConstraint(
            """
            page_number IS NULL
            OR page_number >= 1
            """,
            name="ck_extracted_fields_page_number",
        ),
        sa.ForeignKeyConstraint(
            ["extraction_result_id"],
            ["extraction_results.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_index(
        "ix_extracted_fields_extraction_result_id",
        "extracted_fields",
        ["extraction_result_id"],
        unique=False,
    )

    op.create_index(
        "ix_extracted_fields_field_name",
        "extracted_fields",
        ["field_name"],
        unique=False,
    )

    # ------------------------------------------------------------------
    # Review records
    # ------------------------------------------------------------------

    op.create_table(
        "review_records",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("intelligence_result_id", sa.UUID(), nullable=False),
        sa.Column("reviewer_id", sa.UUID(), nullable=True),
        sa.Column("reviewer_name", sa.String(length=255), nullable=True),
        sa.Column("reviewer_email", sa.String(length=320), nullable=True),
        sa.Column("status", sa.String(length=50), nullable=False),
        sa.Column("decision", sa.String(length=50), nullable=True),
        sa.Column("comments", sa.Text(), nullable=True),
        sa.Column("reviewer_notes", sa.Text(), nullable=True),
        sa.Column("corrections", sa.JSON(), nullable=True),
        sa.Column("overridden_fields", sa.JSON(), nullable=True),
        sa.Column("review_metadata", sa.JSON(), nullable=True),
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
            ["intelligence_result_id"],
            ["document_intelligence_results.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_index(
        "ix_review_records_created_at",
        "review_records",
        ["created_at"],
        unique=False,
    )

    op.create_index(
        "ix_review_records_intelligence_result_id",
        "review_records",
        ["intelligence_result_id"],
        unique=False,
    )

    op.create_index(
        "ix_review_records_reviewer_id",
        "review_records",
        ["reviewer_id"],
        unique=False,
    )

    op.create_index(
        "ix_review_records_status",
        "review_records",
        ["status"],
        unique=False,
    )

    # ------------------------------------------------------------------
    # Document intelligence result changes
    # ------------------------------------------------------------------

    op.add_column(
        "document_intelligence_results",
        sa.Column(
            "classification_confidence",
            sa.Float(),
            nullable=True,
        ),
    )

    # Preserve existing confidence values before removing the
    # legacy confidence column.
    op.execute(
        """
        UPDATE document_intelligence_results
        SET classification_confidence = confidence
        WHERE confidence IS NOT NULL
        """
    )

    # JSON -> JSONB
    op.alter_column(
        "document_intelligence_results",
        "structured_data",
        existing_type=postgresql.JSON(astext_type=sa.Text()),
        type_=postgresql.JSONB(astext_type=sa.Text()),
        existing_nullable=False,
        postgresql_using="structured_data::jsonb",
    )

    op.alter_column(
        "document_intelligence_results",
        "validation_results",
        existing_type=postgresql.JSON(astext_type=sa.Text()),
        type_=postgresql.JSONB(astext_type=sa.Text()),
        existing_nullable=False,
        postgresql_using="validation_results::jsonb",
    )

    op.alter_column(
        "document_intelligence_results",
        "artifacts",
        existing_type=postgresql.JSON(astext_type=sa.Text()),
        type_=postgresql.JSONB(astext_type=sa.Text()),
        existing_nullable=False,
        postgresql_using="artifacts::jsonb",
    )

    op.alter_column(
        "document_intelligence_results",
        "knowledge",
        existing_type=postgresql.JSON(astext_type=sa.Text()),
        type_=postgresql.JSONB(astext_type=sa.Text()),
        existing_nullable=False,
        postgresql_using="knowledge::jsonb",
    )

    # The processing_id index is no longer part of the model.
    op.drop_index(
        op.f("ix_document_intelligence_results_processing_id"),
        table_name="document_intelligence_results",
    )

    op.create_check_constraint(
        "ck_document_intelligence_classification_confidence",
        "document_intelligence_results",
        """
        classification_confidence IS NULL
        OR (
            classification_confidence >= 0
            AND classification_confidence <= 1
        )
        """,
    )

    # Remove the legacy confidence column only after its values
    # have been copied to classification_confidence.
    op.drop_column(
        "document_intelligence_results",
        "confidence",
    )


def downgrade() -> None:
    """Downgrade schema."""

    # ------------------------------------------------------------------
    # Restore legacy confidence column
    # ------------------------------------------------------------------

    op.add_column(
        "document_intelligence_results",
        sa.Column(
            "confidence",
            sa.DOUBLE_PRECISION(precision=53),
            autoincrement=False,
            nullable=True,
        ),
    )

    op.execute(
        """
        UPDATE document_intelligence_results
        SET confidence = classification_confidence
        WHERE classification_confidence IS NOT NULL
        """
    )

    op.drop_constraint(
        "ck_document_intelligence_classification_confidence",
        "document_intelligence_results",
        type_="check",
    )

    op.create_index(
        op.f("ix_document_intelligence_results_processing_id"),
        "document_intelligence_results",
        ["processing_id"],
        unique=False,
    )

    # JSONB -> JSON
    op.alter_column(
        "document_intelligence_results",
        "knowledge",
        existing_type=postgresql.JSONB(astext_type=sa.Text()),
        type_=postgresql.JSON(astext_type=sa.Text()),
        existing_nullable=False,
        postgresql_using="knowledge::json",
    )

    op.alter_column(
        "document_intelligence_results",
        "artifacts",
        existing_type=postgresql.JSONB(astext_type=sa.Text()),
        type_=postgresql.JSON(astext_type=sa.Text()),
        existing_nullable=False,
        postgresql_using="artifacts::json",
    )

    op.alter_column(
        "document_intelligence_results",
        "validation_results",
        existing_type=postgresql.JSONB(astext_type=sa.Text()),
        type_=postgresql.JSON(astext_type=sa.Text()),
        existing_nullable=False,
        postgresql_using="validation_results::json",
    )

    op.alter_column(
        "document_intelligence_results",
        "structured_data",
        existing_type=postgresql.JSONB(astext_type=sa.Text()),
        type_=postgresql.JSON(astext_type=sa.Text()),
        existing_nullable=False,
        postgresql_using="structured_data::json",
    )

    op.drop_column(
        "document_intelligence_results",
        "classification_confidence",
    )

    # ------------------------------------------------------------------
    # Remove review records
    # ------------------------------------------------------------------

    op.drop_index(
        "ix_review_records_status",
        table_name="review_records",
    )

    op.drop_index(
        "ix_review_records_reviewer_id",
        table_name="review_records",
    )

    op.drop_index(
        "ix_review_records_intelligence_result_id",
        table_name="review_records",
    )

    op.drop_index(
        "ix_review_records_created_at",
        table_name="review_records",
    )

    op.drop_table("review_records")

    # ------------------------------------------------------------------
    # Remove extracted fields
    # ------------------------------------------------------------------

    op.drop_index(
        "ix_extracted_fields_field_name",
        table_name="extracted_fields",
    )

    op.drop_index(
        "ix_extracted_fields_extraction_result_id",
        table_name="extracted_fields",
    )

    op.drop_table("extracted_fields")

    # ------------------------------------------------------------------
    # Remove extraction results
    # ------------------------------------------------------------------

    op.drop_index(
        "ix_extraction_results_processing_id",
        table_name="extraction_results",
    )

    op.drop_index(
        "ix_extraction_results_document_version_id",
        table_name="extraction_results",
    )

    op.drop_index(
        op.f("ix_extraction_results_document_type"),
        table_name="extraction_results",
    )

    op.drop_index(
        "ix_extraction_results_document_id",
        table_name="extraction_results",
    )

    op.drop_table("extraction_results")