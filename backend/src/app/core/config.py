"""Typed application settings loaded from environment variables.

Uses pydantic-settings to provide validated, typed configuration with
sensible development defaults. Access via the cached ``get_settings()`` function.
"""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application configuration.

    All values are read from environment variables (case-insensitive).
    The ``.env`` file at the project root is loaded automatically when present.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # --- Application ---
    app_env: str = "development"
    log_level: str = "INFO"

    # --- Backend server ---
    backend_host: str = "0.0.0.0"
    backend_port: int = 8000

    # --- PostgreSQL ---
    postgres_host: str = "localhost"
    postgres_port: int = 5432
    postgres_db: str = "financial_news"
    postgres_user: str = "postgres"
    postgres_password: str = "postgres"

    # Explicit DATABASE_URL override (set by CI, production, etc.)
    database_url: str | None = None

    # --- Export ---
    export_dir: str = "exports"

    # --- Optional third-party API keys ---
    newsdata_api_key: str | None = None
    gnews_api_key: str | None = None

    # --- Computed properties ---

    @property
    def is_production(self) -> bool:
        return self.app_env == "production"

    @property
    def effective_database_url(self) -> str:
        """Async PostgreSQL connection string for SQLAlchemy + asyncpg.

        If DATABASE_URL is explicitly set (e.g. by CI or production),
        use it directly. Otherwise construct from individual components.
        """
        if self.database_url is not None:
            return self.database_url
        return (
            f"postgresql+asyncpg://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return cached application settings (created once, reused everywhere)."""
    return Settings()
