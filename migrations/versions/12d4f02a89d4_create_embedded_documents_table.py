"""create embedded documents table

Revision ID: 12d4f02a89d4
Revises: 7293f3328338
Create Date: 2026-02-19 15:47:17.032021

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from pgvector.sqlalchemy import Vector


# revision identifiers, used by Alembic.
revision: str = "12d4f02a89d4"
down_revision: Union[str, Sequence[str], None] = "7293f3328338"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "EmbeddedDocuments",
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
        sa.Column("content", sa.Text, nullable=False),
        sa.Column(
            "metadata",
            postgresql.JSONB,
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
        sa.Column(
            "documentId",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("Documents.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("embedding", Vector(1536)),
    )
    op.execute(
        'CREATE INDEX IF NOT EXISTS "idx_embedding_cosine" '
        'ON "EmbeddedDocuments" USING hnsw (embedding vector_cosine_ops)'
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index("idx_embedding_cosine", table_name="EmbeddedDocuments")
    op.drop_table("EmbeddedDocuments")
