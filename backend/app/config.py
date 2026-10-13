from functools import lru_cache

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_env: str = "development"
    database_url: str = (
        "postgresql+psycopg://handoffproof:handoffproof@localhost:5432/handoffproof"
    )
    frontend_origin: str = "http://localhost:5173"
    max_upload_bytes: int = 1_000_000
    # Comma-separated Fernet keys; the first encrypts, all decrypt (rotation).
    connector_encryption_keys: SecretStr | None = None
    # Incremental checkpoints older than this need an explicit full re-read.
    connector_checkpoint_max_age_hours: int = 168

    model_config = SettingsConfigDict(
        env_file=(".env", "../.env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
