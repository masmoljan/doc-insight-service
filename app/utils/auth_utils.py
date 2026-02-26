from datetime import datetime, timedelta, timezone
from uuid import UUID

import jwt
from passlib.context import CryptContext
from app.config import app_config
from app.utils.app_error import AppError, AppErrorType

JWT_SECRET = app_config.jwt_secret
JWT_EXPIRES_MINUTES = app_config.jwt_expires_minutes

pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, password_hash: str) -> bool:
    return pwd_context.verify(plain_password, password_hash)


def create_access_token(user_id: UUID) -> str:
    if not JWT_SECRET:
        raise AppError(AppErrorType.JWT_SECRET_MISSING)

    now = datetime.now(timezone.utc)
    payload = {
        "user_id": str(user_id),
        "iat": now,
        "exp": now + timedelta(minutes=JWT_EXPIRES_MINUTES),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm="HS256")
