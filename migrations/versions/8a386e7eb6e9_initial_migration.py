"""initial migration

Revision ID: 8a386e7eb6e9
Revises:
Create Date: 2026-02-19 15:39:58.230549

"""

from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = "8a386e7eb6e9"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")
    op.execute('CREATE EXTENSION IF NOT EXISTS "pgcrypto"')


def downgrade() -> None:
    """Downgrade schema."""
    op.execute('DROP EXTENSION IF EXISTS "pgcrypto"')
    op.execute("DROP EXTENSION IF EXISTS vector")
