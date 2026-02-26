"""create documents table

Revision ID: 7293f3328338
Revises: 8a386e7eb6e9
Create Date: 2026-02-19 15:45:33.303943

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = '7293f3328338'
down_revision: Union[str, Sequence[str], None] = '8a386e7eb6e9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "Documents",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.Column(
            "metadata",
            postgresql.JSONB,
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
        sa.Column("session_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.CheckConstraint(
            "(session_id IS NOT NULL AND user_id IS NULL) OR "
            "(session_id IS NULL AND user_id IS NOT NULL)",
            name="documents_session_or_user_id_check",
        ),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table("Documents")
