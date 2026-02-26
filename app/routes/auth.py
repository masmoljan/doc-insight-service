from fastapi import APIRouter, Request, status
from pydantic import BaseModel, EmailStr, Field
from sqlmodel import Session, select
from app.config import app_config
from app.database import engine
from app.models import User
from app.utils import (
    AppError,
    AppErrorType,
    create_access_token,
    hash_password,
    limiter,
    verify_password,
)

router = APIRouter(prefix="/auth")


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


@router.post("/register", status_code=status.HTTP_201_CREATED)
@limiter.limit(app_config.rate_limit_auth_register)
def register(request: Request, payload: RegisterRequest):
    email, password = payload.email, payload.password
    with Session(engine) as session:
        existing = session.exec(select(User).where(User.email == email)).first()
        if existing:
            raise AppError(AppErrorType.USER_ALREADY_EXISTS)
        user = User(email=email, password_hash=hash_password(password))
        session.add(user)
        session.commit()
        session.refresh(user)

    token = create_access_token(user.id)
    return {
        "user_id": str(user.id),
        "access_token": token,
        "token_type": "Bearer",
        "expires_in_minutes": app_config.jwt_expires_minutes,
    }


class TokenRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


@router.post("/token", status_code=status.HTTP_200_OK)
@limiter.limit(app_config.rate_limit_auth_token)
def token(request: Request, payload: TokenRequest):
    email, password = payload.email, payload.password
    with Session(engine) as session:
        user = session.exec(select(User).where(User.email == email)).first()
        if not user or not verify_password(password, user.password_hash):
            raise AppError(AppErrorType.INVALID_CREDENTIALS)

    token = create_access_token(user.id)
    return {
        "user_id": str(user.id),
        "access_token": token,
        "token_type": "Bearer",
        "expires_in_minutes": app_config.jwt_expires_minutes,
    }
