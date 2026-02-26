"""add delete cascade to embedded documents

Revision ID: e3b3c9a4f6d1
Revises: 0b9f972e43ee
Create Date: 2026-02-23 10:15:00.000000

"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = "e3b3c9a4f6d1"
down_revision: Union[str, Sequence[str], None] = "0b9f972e43ee"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.drop_constraint(
        "EmbeddedDocuments_documentId_fkey",
        "EmbeddedDocuments",
        type_="foreignkey",
    )
    op.create_foreign_key(
        "EmbeddedDocuments_documentId_fkey",
        "EmbeddedDocuments",
        "Documents",
        ["documentId"],
        ["id"],
        ondelete="CASCADE",
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_constraint(
        "EmbeddedDocuments_documentId_fkey",
        "EmbeddedDocuments",
        type_="foreignkey",
    )
    op.create_foreign_key(
        "EmbeddedDocuments_documentId_fkey",
        "EmbeddedDocuments",
        "Documents",
        ["documentId"],
        ["id"],
    )
