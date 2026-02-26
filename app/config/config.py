from dotenv import load_dotenv
from pydantic_settings import BaseSettings, SettingsConfigDict

load_dotenv()


class AppConfig(BaseSettings):
    database_url: str
    jwt_secret: str
    jwt_expires_minutes: int = 1440
    session_expires_minutes: int = 1440
    openai_api_key: str
    data_encryption_key: str
    redis_password: str | None = None
    rate_limit_redis_url: str = "redis://localhost:6379/0"
    rate_limit_default: str = "120/minute"
    rate_limit_auth_token: str = "5/minute"
    rate_limit_auth_register: str = "3/minute"
    rate_limit_upload: str = "10/minute"
    rate_limit_ask: str = "60/minute"
    embedding_cache_redis_url: str = "redis://localhost:6379/1"
    embedding_cache_doc_ttl_seconds: int = 43200
    upload_max_files: int = 5
    upload_max_file_size_bytes: int = 10 * 1024 * 1024

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

app_config = AppConfig()
