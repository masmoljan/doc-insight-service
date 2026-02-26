from collections.abc import Callable

import structlog
from fastapi import Request
from starlette.responses import Response

logger = structlog.get_logger(__name__)


async def log_requests(
    request: Request,
    call_next: Callable[[Request], Response],
) -> Response:
    try:
        response = await call_next(request)
    except Exception:
        logger.exception(
            "request_failed",
            method=request.method,
            path=request.url.path,
        )
        raise
    status = response.status_code
    if status >= 500:
        log_method = logger.error
    elif status >= 400:
        log_method = logger.warning
    else:
        log_method = logger.info
    log_method(
        "request",
        method=request.method,
        path=request.url.path,
        status=status,
    )
    return response
