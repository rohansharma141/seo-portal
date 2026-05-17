"""Application configuration — reads every environment variable in Section 10
of the build doc.

Design rule (Section 6 of the build doc): every integration credential defaults
to an empty string so the portal starts and runs fully on mock data when keys
are absent. Setting a key later activates the real integration with no code
change. pydantic-settings matches env vars to field names case-insensitively,
so the field `database_url` is populated from `DATABASE_URL`.
"""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ── Database ────────────────────────────────────────────────────────
    supabase_url: str = ""
    supabase_key: str = ""
    database_url: str = ""

    # ── Authentication ──────────────────────────────────────────────────
    jwt_secret: str = "dev-insecure-change-me-min-32-characters-long"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 1440

    # ── External integrations (placeholders — empty value = mock mode) ──
    firecrawl_api_key: str = ""
    gsc_credentials_path: str = ""
    gsc_site_url: str = ""
    anthropic_api_key: str = ""

    # ── Notifications ───────────────────────────────────────────────────
    resend_api_key: str = ""
    resend_from_email: str = "seo@kedar.estate"
    notification_email: str = "rohan@kedar.estate"

    # ── Rate limiting ───────────────────────────────────────────────────
    upstash_redis_url: str = ""
    upstash_redis_token: str = ""

    # ── App config ──────────────────────────────────────────────────────
    environment: str = "development"
    app_url: str = "http://localhost:8000"
    frontend_url: str = "http://localhost:3000"
    api_token_prefix: str = "pse_"
    log_level: str = "INFO"

    # Fixed app metadata (not env-driven)
    app_name: str = "Prithvi SEO Portal"
    app_version: str = "1.0.0"

    @property
    def is_production(self) -> bool:
        return self.environment.lower() == "production"

    # Booleans the rest of the app uses to choose real integration vs mock.
    @property
    def firecrawl_enabled(self) -> bool:
        return bool(self.firecrawl_api_key)

    @property
    def gsc_enabled(self) -> bool:
        return bool(self.gsc_credentials_path)

    @property
    def anthropic_enabled(self) -> bool:
        return bool(self.anthropic_api_key)

    @property
    def resend_enabled(self) -> bool:
        return bool(self.resend_api_key)

    @property
    def rate_limit_redis_enabled(self) -> bool:
        return bool(self.upstash_redis_url and self.upstash_redis_token)


@lru_cache
def get_settings() -> Settings:
    """Cached singleton. Use this (or the `settings` export) everywhere."""
    return Settings()


settings = get_settings()
