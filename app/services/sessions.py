from datetime import UTC, datetime, timedelta
from uuid import UUID

from sqlmodel import Session as SQLModelSession, select

from app.config import app_config
from app.database import engine
from app.models import Session as SessionModel


def create_session() -> SessionModel:
    expires_at = datetime.now(UTC) + timedelta(
        minutes=app_config.session_expires_minutes
    )
    with SQLModelSession(engine) as session:
        record = SessionModel(expires_at=expires_at)
        session.add(record)
        session.commit()
        session.refresh(record)
        return record


def get_session(session_id: UUID) -> SessionModel | None:
    with SQLModelSession(engine) as session:
        statement = select(SessionModel).where(SessionModel.id == session_id)
        return session.exec(statement).first()


def is_session_expired(record: SessionModel) -> bool:
    return record.expires_at <= datetime.now(UTC)
