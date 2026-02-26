from datetime import UTC, datetime
from uuid import UUID, uuid4

from pgvector.sqlalchemy import Vector
from sqlalchemy import Column, DateTime, ForeignKey, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlmodel import Field, SQLModel


class EmbeddedDocument(SQLModel, table=True):
    __tablename__ = "EmbeddedDocuments"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        sa_column=Column(
            DateTime(timezone=True), server_default=func.now(), nullable=False
        ),
    )
    content: str = Field(sa_column=Column(Text, nullable=False))
    metadata_: dict = Field(
        default_factory=dict,
        sa_column=Column(JSONB, name="metadata", nullable=False),
    )
    document_id: UUID = Field(
        sa_column=Column(
            PG_UUID(as_uuid=True),
            ForeignKey("Documents.id", ondelete="CASCADE"),
            name="documentId",
            nullable=False,
            index=True,
        ),
    )
    embedding: list[float] | None = Field(default=None, sa_column=Column(Vector(1536)))
