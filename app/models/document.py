from datetime import UTC, datetime
from uuid import UUID, uuid4

from sqlalchemy import CheckConstraint, Column, DateTime, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlmodel import Field, SQLModel


class Document(SQLModel, table=True):
    __tablename__ = "Documents"
    __table_args__ = (
        CheckConstraint(
            "(session_id IS NOT NULL AND user_id IS NULL) OR "
            "(session_id IS NULL AND user_id IS NOT NULL)",
            name="documents_session_or_user_id_check",
        ),
    )

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        sa_column=Column(
            DateTime(timezone=True),
            server_default=func.now(),
            nullable=False,
        ),
    )
    metadata_: dict = Field(
        default_factory=dict,
        sa_column=Column(JSONB, name="metadata", nullable=False),
    )
    session_id: UUID | None = Field(
        default=None,
        sa_column=Column(PG_UUID(as_uuid=True), nullable=True, index=True),
    )
    user_id: UUID | None = Field(
        default=None,
        sa_column=Column(PG_UUID(as_uuid=True), nullable=True, index=True),
    )
