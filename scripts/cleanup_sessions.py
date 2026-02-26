import logging
import os
import time
from datetime import UTC, datetime

from dotenv import load_dotenv
from sqlalchemy import create_engine, text

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL is required for cleanup")

logging.basicConfig(
    level="INFO",
    format="%(asctime)s %(levelname)s %(message)s",
)
logger = logging.getLogger("cleanup_sessions")

DELETE_DOCUMENTS_SQL = text(
    'DELETE FROM "Documents" WHERE session_id IN ('
    'SELECT id FROM "Sessions" WHERE expires_at <= :now'
    ")"
)
DELETE_SESSIONS_SQL = text('DELETE FROM "Sessions" WHERE expires_at <= :now')
engine = create_engine(DATABASE_URL)


def cleanup_expired_sessions() -> int:
    now = datetime.now(UTC)
    with engine.begin() as connection:
        connection.execute(DELETE_DOCUMENTS_SQL, {"now": now})
        result = connection.execute(DELETE_SESSIONS_SQL, {"now": now})
        return result.rowcount or 0


def main() -> None:
    interval_minutes = int(os.getenv("SESSION_CLEANUP_INTERVAL_MINUTES", "60"))
    interval_seconds = interval_minutes * 60
    logger.info("cleanup started; interval_minutes=%s", interval_minutes)
    while True:
        try:
            deleted_sessions = cleanup_expired_sessions()
            logger.info(
                "cleanup run complete; deleted_sessions=%s", deleted_sessions
            )
        except Exception:
            logger.exception("cleanup run failed")
        time.sleep(interval_seconds)


if __name__ == "__main__":
    main()
