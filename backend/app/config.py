from __future__ import annotations

import secrets
from functools import lru_cache
from typing import Optional

from pydantic import field_validator, computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # -------------------------------------------------------------------------
    # Database
    # -------------------------------------------------------------------------
    DATABASE_URL: str = "postgresql+asyncpg://pulsesignal:password@localhost:5432/pulsesignal_db"

    # -------------------------------------------------------------------------
    # Redis
    # -------------------------------------------------------------------------
    REDIS_URL: str = "redis://localhost:6379/0"

    # -------------------------------------------------------------------------
    # Security / JWT
    # -------------------------------------------------------------------------
    SECRET_KEY: str = secrets.token_hex(32)
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # -------------------------------------------------------------------------
    # Binance API
    # -------------------------------------------------------------------------
    BINANCE_API_KEY: str = ""
    BINANCE_API_SECRET: str = ""
    BINANCE_WS_URL: str = "wss://fstream.binance.com/ws"
    BINANCE_REST_URL: str = "https://fapi.binance.com"

    # -------------------------------------------------------------------------
    # TwelveData API
    # -------------------------------------------------------------------------
    TWELVEDATA_API_KEY: str = ""

    # -------------------------------------------------------------------------
    # Telegram
    # -------------------------------------------------------------------------
    TELEGRAM_BOT_TOKEN: str = ""
    TELEGRAM_VIP_CHANNEL_ID: str = ""

    # -------------------------------------------------------------------------
    # Stripe
    # -------------------------------------------------------------------------
    STRIPE_SECRET_KEY: str = ""
    STRIPE_WEBHOOK_SECRET: str = ""
    STRIPE_MONTHLY_PRICE_ID: str = ""
    STRIPE_LIFETIME_PRICE_ID: str = ""

    # -------------------------------------------------------------------------
    # SMTP Email
    # -------------------------------------------------------------------------
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASS: str = ""
    FROM_EMAIL: str = ""
    ADMIN_EMAIL: str = ""

    # -------------------------------------------------------------------------
    # Application URLs
    # -------------------------------------------------------------------------
    FRONTEND_URL: str = "https://signals.pulsetracker.net"
    BACKEND_URL: str = "https://api.pulsetracker.net"

    # -------------------------------------------------------------------------
    # Environment
    # -------------------------------------------------------------------------
    ENVIRONMENT: str = "production"

    # -------------------------------------------------------------------------
    # Scanner / Engine Settings
    # -------------------------------------------------------------------------
    MIN_SIGNAL_CONFIDENCE: int = 60
    SCANNER_INTERVAL_MINUTES: int = 10
    MAX_CANDLES_CACHE: int = 500

    # -------------------------------------------------------------------------
    # Validators
    # -------------------------------------------------------------------------
    @field_validator("ENVIRONMENT")
    @classmethod
    def validate_environment(cls, v: str) -> str:
        allowed = {"development", "staging", "production"}
        if v not in allowed:
            raise ValueError(f"ENVIRONMENT must be one of: {allowed}")
        return v

    @field_validator("ALGORITHM")
    @classmethod
    def validate_algorithm(cls, v: str) -> str:
        allowed = {"HS256", "HS384", "HS512"}
        if v not in allowed:
            raise ValueError(f"ALGORITHM must be one of: {allowed}")
        return v

    @field_validator("MIN_SIGNAL_CONFIDENCE")
    @classmethod
    def validate_min_confidence(cls, v: int) -> int:
        if not 0 <= v <= 100:
            raise ValueError("MIN_SIGNAL_CONFIDENCE must be between 0 and 100")
        return v

    @field_validator("ACCESS_TOKEN_EXPIRE_MINUTES")
    @classmethod
    def validate_access_token_expiry(cls, v: int) -> int:
        if v < 1:
            raise ValueError("ACCESS_TOKEN_EXPIRE_MINUTES must be at least 1")
        return v

    @field_validator("REFRESH_TOKEN_EXPIRE_DAYS")
    @classmethod
    def validate_refresh_token_expiry(cls, v: int) -> int:
        if v < 1:
            raise ValueError("REFRESH_TOKEN_EXPIRE_DAYS must be at least 1")
        return v

    # -------------------------------------------------------------------------
    # Computed Properties
    # -------------------------------------------------------------------------
    @computed_field
    @property
    def is_production(self) -> bool:
        return self.ENVIRONMENT == "production"

    @computed_field
    @property
    def is_development(self) -> bool:
        return self.ENVIRONMENT == "development"

    @computed_field
    @property
    def access_token_expire_seconds(self) -> int:
        return self.ACCESS_TOKEN_EXPIRE_MINUTES * 60

    @computed_field
    @property
    def refresh_token_expire_seconds(self) -> int:
        return self.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60

    @computed_field
    @property
    def sync_database_url(self) -> str:
        """Synchronous database URL for Alembic migrations."""
        return self.DATABASE_URL.replace(
            "postgresql+asyncpg://", "postgresql+psycopg2://"
        )

    @computed_field
    @property
    def redis_host(self) -> str:
        """Extract Redis host from URL."""
        from urllib.parse import urlparse
        parsed = urlparse(self.REDIS_URL)
        return parsed.hostname or "localhost"

    @computed_field
    @property
    def redis_port(self) -> int:
        """Extract Redis port from URL."""
        from urllib.parse import urlparse
        parsed = urlparse(self.REDIS_URL)
        return parsed.port or 6379

    @computed_field
    @property
    def redis_db(self) -> int:
        """Extract Redis DB index from URL."""
        from urllib.parse import urlparse
        parsed = urlparse(self.REDIS_URL)
        path = parsed.path.lstrip("/")
        return int(path) if path.isdigit() else 0

    @computed_field
    @property
    def redis_password(self) -> Optional[str]:
        """Extract Redis password from URL if present."""
        from urllib.parse import urlparse
        parsed = urlparse(self.REDIS_URL)
        return parsed.password

    @computed_field
    @property
    def allowed_origins(self) -> list[str]:
        """CORS allowed origins derived from FRONTEND_URL."""
        origins = [self.FRONTEND_URL]
        if not self.is_production:
            origins += [
                "http://localhost:3000",
                "http://localhost:5173",
                "http://127.0.0.1:3000",
                "http://127.0.0.1:5173",
            ]
        return origins


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return a cached singleton instance of Settings."""
    return Settings()
