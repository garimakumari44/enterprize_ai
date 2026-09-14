"""add auth fields to user model

Revision ID: 005f97529df2
Revises: 6f053d5f53ef
Create Date: 2026-07-31 18:56:48.138989
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "005f97529df2"
down_revision: Union[str, Sequence[str], None] = "6f053d5f53ef"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""

    op.add_column(
        "users",
        sa.Column(
            "is_verified",
            sa.Boolean(),
            server_default=sa.false(),
            nullable=False,
        ),
    )

    op.add_column(
        "users",
        sa.Column(
            "refresh_token_version",
            sa.Integer(),
            server_default="0",
            nullable=False,
        ),
    )

    op.add_column(
        "users",
        sa.Column(
            "last_login_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
    )


def downgrade() -> None:
    """Downgrade schema."""

    op.drop_column("users", "last_login_at")
    op.drop_column("users", "refresh_token_version")
    op.drop_column("users", "is_verified")