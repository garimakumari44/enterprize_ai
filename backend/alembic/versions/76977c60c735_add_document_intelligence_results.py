"""add document intelligence results

Revision ID: 76977c60c735
Revises: 0420581c8743
Create Date: 2026-08-23 09:47:30.344127

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "76977c60c735"
down_revision: Union[str, Sequence[str], None] = "0420581c8743"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create the persisted document intelligence result table."""

    op.create_table(
        "document_intelligence_results",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("processing_id", sa.UUID(), nullable=False),
        sa.Column("document_id", sa.UUID(), nullable=False),
        sa.Column("document_version_id", sa.UUID(), nullable=False),
        sa.Column("document_type", sa.String(length=100), nullable=True),
        sa.Column("confidence", sa.Float(), nullable=True),
        sa.Column("structured_data", sa.JSON(), nullable=False),
        sa.Column("validation_results", sa.JSON(), nullable=False),
        sa.Column("artifacts", sa.JSON(), nullable=False),
        sa.Column("knowledge", sa.JSON(), nullable=False),
        sa.Column("raw_text", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["processing_id"],
            ["processing_jobs.id"],
            ondelete="CASCADE",
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
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("processing_id"),
    )

    op.create_index(
        "ix_document_intelligence_results_document_id",
        "document_intelligence_results",
        ["document_id"],
        unique=False,
    )

    op.create_index(
        "ix_document_intelligence_results_document_version_id",
        "document_intelligence_results",
        ["document_version_id"],
        unique=False,
    )

    op.create_index(
        "ix_document_intelligence_results_processing_id",
        "document_intelligence_results",
        ["processing_id"],
        unique=False,
    )


def downgrade() -> None:
    """Remove the persisted document intelligence result table."""

    op.drop_index(
        "ix_document_intelligence_results_processing_id",
        table_name="document_intelligence_results",
    )

    op.drop_index(
        "ix_document_intelligence_results_document_version_id",
        table_name="document_intelligence_results",
    )

    op.drop_index(
        "ix_document_intelligence_results_document_id",
        table_name="document_intelligence_results",
    )

    op.drop_table("document_intelligence_results")