from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


_BACKEND_DIR = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=str(_BACKEND_DIR / ".env"), extra="ignore")

    data_provider: str = "yahoo"
    cache_ttl_seconds: int = 86400
    cache_dir: str = ".cache"
    default_start: str = "2025-04-01"
    default_end: str = "2026-03-31"
    timezone: str = "Asia/Kolkata"
    nifty_ticker: str = "^NSEI"
    cors_origins: str = "*"


settings = Settings()
