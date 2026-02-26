from contextlib import asynccontextmanager
from pathlib import Path

import structlog
from alembic import command
from alembic.config import Config
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app.middleware import log_requests
from app.routes import ask, auth, health, upload
from app.utils.app_error import AppError
from app.utils.logging import configure_logging
from app.utils.rate_limit import limiter

configure_logging()
logger = structlog.get_logger(__name__)


def run_migrations() -> None:
    alembic_cfg = Config(str(Path(__file__).resolve().parent / "alembic.ini"))
    command.upgrade(alembic_cfg, "head")


@asynccontextmanager
async def lifespan(_: FastAPI):
    run_migrations()
    yield


app = FastAPI(lifespan=lifespan)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.middleware("http")(log_requests)


@app.exception_handler(AppError)
async def handle_app_error(request: Request, exc: AppError) -> JSONResponse:
    return JSONResponse(status_code=exc.http_status_code, content=exc.body)


app.include_router(health.router)
app.include_router(upload.router)
app.include_router(ask.router)
app.include_router(auth.router)
