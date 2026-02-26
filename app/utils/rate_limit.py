import jwt
from fastapi import Request
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.config import app_config
from app.utils.auth_utils import JWT_SECRET

def get_user_id_from_request(request: Request) -> str | None:
    auth_header = request.headers.get("authorization")
    if not auth_header:
        return None

    scheme, _, token = auth_header.partition(" ")
    if scheme.lower() != "bearer" or not token:
        return None

    if not JWT_SECRET:
        return None

    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
    except jwt.PyJWTError:
        return None

    user_id = payload.get("user_id")
    if not user_id:
        return None

    return str(user_id)


def rate_limit_key(request: Request) -> str:
    user_id = get_user_id_from_request(request)
    if user_id:
        return f"user:{user_id}"

    ip_address = get_remote_address(request)
    return f"ip:{ip_address}"


limiter = Limiter(
    key_func=rate_limit_key,
    storage_uri=app_config.rate_limit_redis_url,
    default_limits=[app_config.rate_limit_default],
    enabled=True,
)
