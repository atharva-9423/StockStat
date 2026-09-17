from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    data_provider: str = "investing"
    cache_ttl_seconds: int = 86400
    cache_dir: str = ".cache"
    default_start: str = "2025-04-01"
    default_end: str = "2026-03-31"
    timezone: str = "Asia/Kolkata"
    nifty_ticker: str = "^NSEI"
    cors_origins: str = "*"

    class Meta:
        env_file = ".env"


settings = Settings()
