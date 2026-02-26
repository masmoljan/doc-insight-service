from sqlmodel import Session, create_engine

from app.config import app_config

engine = create_engine(app_config.database_url)


def get_session():
    with Session(engine) as session:
        yield session
