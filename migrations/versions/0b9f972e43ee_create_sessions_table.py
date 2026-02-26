"""create sessions table

Revision ID: 0b9f972e43ee
Revises: 92782818590c
Create Date: 2026-02-19 15:51:00.436704

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = "0b9f972e43ee"
down_revision: Union[str, Sequence[str], None] = "92782818590c"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "Sessions",
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
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "expires_at > created_at",
            name="sessions_expires_at_check",
        ),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table("Sessions")
