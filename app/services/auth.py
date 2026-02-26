from uuid import UUID

import jwt
from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.utils import AppError, AppErrorType
from app.config import app_config

security = HTTPBearer(auto_error=False)
CREDS_DEPENDENCY = Depends(security)


def get_current_user_id(
    creds: HTTPAuthorizationCredentials | None = CREDS_DEPENDENCY,
) -> UUID | None:
    if not creds or not creds.credentials:
        return None

    if not app_config.jwt_secret:
        raise AppError(AppErrorType.JWT_SECRET_MISSING)

    try:
        payload = jwt.decode(
            creds.credentials,
            app_config.jwt_secret,
            algorithms=["HS256"],
        )
        user_id = payload.get("user_id")
        if not user_id:
            raise AppError(AppErrorType.TOKEN_MISSING_USER_ID)
        return UUID(user_id)
    except jwt.PyJWTError as error:
        raise AppError(AppErrorType.TOKEN_INVALID) from error