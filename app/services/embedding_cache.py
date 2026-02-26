import hashlib
import json
from collections.abc import Iterable

import redis

from app.config import app_config

client: redis.Redis | None = None


def get_client() -> redis.Redis | None:
    global client
    if not app_config.embedding_cache_redis_url:
        return None
    if client is None:
        client = redis.Redis.from_url(app_config.embedding_cache_redis_url)
    return client


def build_doc_chunk_key(text: str) -> str:
    return f"embeddings:doc:{hashlib.sha256(text.encode('utf-8')).hexdigest()}"


def build_query_key(text: str) -> str:
    return (
        f"embeddings:query:{hashlib.sha256(text.encode('utf-8')).hexdigest()}"
    )


def get_embeddings(keys: Iterable[str]) -> list[list[float] | None]:
    key_list = list(keys)
    if not key_list:
        return []

    try:
        redis_client = get_client()
        if redis_client is None:
            return [None] * len(key_list)
        raw_values = redis_client.mget(key_list)
    except Exception:
        return [None] * len(key_list)

    return [json.loads(value) if value else None for value in raw_values]


def set_embedding(
    key: str, embedding: list[float], ttl_seconds: int | None
) -> None:
    payload = json.dumps(embedding, separators=(",", ":")).encode("utf-8")
    try:
        redis_client = get_client()
        if redis_client is None:
            return
        if ttl_seconds and ttl_seconds > 0:
            redis_client.setex(key, ttl_seconds, payload)
        else:
            redis_client.set(key, payload)
    except Exception:
        return
