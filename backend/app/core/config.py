from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    BOOKFLIX_DB_URL: str = "sqlite:///./bookflix.db"
    BOOKFLIX_REDIS_URL: str = "redis://localhost:6379/0"
    BOOKFLIX_STORAGE_DIR: str = "./storage"
    BOOKFLIX_TTS_VOICE: str = "pt-BR-FranciscaNeural"
    BOOKFLIX_TTS_RATE: str = "+0%"
    BOOKFLIX_CHUNK_TARGET: int = 900
    BOOKFLIX_CHUNK_MIN: int = 400
    BOOKFLIX_CACHE_TTL_SECONDS: int = 86400
    BOOKFLIX_ALLOW_ORIGINS: str = "*"
    BOOKFLIX_PIPER_BIN: str | None = None
    BOOKFLIX_PIPER_MODEL: str | None = None

    @property
    def storage_path(self) -> Path:
        return Path(self.BOOKFLIX_STORAGE_DIR)


@lru_cache
def get_settings() -> Settings:
    return Settings()
