from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

from loguru import logger
from pydantic import BaseModel, Field

from app.redis_client import RedisClient

CONFIG_REDIS_KEY = "admin:system_config"
PROVIDER_HEALTH_REDIS_KEY = "admin:provider_health"


class AuthConfig(BaseModel):
    require_email_verification: bool = True
    trial_hours: int = Field(default=24 * 30, ge=24, le=24 * 365)


class NotificationConfig(BaseModel):
    enable_telegram_alerts: bool = True
    enable_email_alerts: bool = False


class SMTPConfig(BaseModel):
    enabled: bool = False
    host: str = ""
    port: int = Field(default=587, ge=1, le=65535)
    username: str = ""
    password: str = ""
    from_email: str = ""
    from_name: str = "PulseSignal Pro"
    use_tls: bool = True
    use_ssl: bool = False


class IntegrationConfig(BaseModel):
    telegram_bot_token: str = ""
    telegram_vip_channel_id: str = ""
    binance_api_key: str = ""
    binance_api_secret: str = ""
    twelvedata_api_key: str = ""
    stripe_secret_key: str = ""
    stripe_webhook_secret: str = ""
    stripe_monthly_price_id: str = ""
    stripe_yearly_price_id: str = ""
    stripe_lifetime_price_id: str = ""
    # Crypto payment wallet addresses (shown to users on payment page)
    crypto_wallet_bep20: str = ""   # USDT BEP-20 (BSC)
    crypto_wallet_trc20: str = ""   # USDT TRC-20 (Tron)
    crypto_wallet_btc: str = ""     # Bitcoin
    crypto_wallet_eth: str = ""     # Ethereum / USDT ERC-20


class SystemConfig(BaseModel):
    scanner_interval_minutes: int = Field(default=10, ge=1, le=1440)
    min_signal_confidence: int = Field(default=75, ge=0, le=100)
    scanner_timeframes: list[str] = Field(
        default_factory=lambda: ["15m", "1H", "4H"]
    )
    enable_crypto_scan: bool = True
    enable_forex_scan: bool = True
    maintenance_mode: bool = False
    scanner_enabled: bool = True
    max_signals_per_scan: int = Field(default=50, ge=1, le=5000)
    per_symbol_daily_signal_limit: int = Field(default=2, ge=0, le=100)
    global_daily_signal_limit: int = Field(default=25, ge=0, le=10000)
    repeated_signal_cooldown_minutes: int = Field(default=180, ge=0, le=10080)
    ict_weight: float = Field(default=1.0, ge=0.0, le=5.0)
    trend_weight: float = Field(default=1.0, ge=0.0, le=5.0)
    momentum_weight: float = Field(default=1.0, ge=0.0, le=5.0)
    auth: AuthConfig = Field(default_factory=AuthConfig)
    notifications: NotificationConfig = Field(default_factory=NotificationConfig)
    smtp: SMTPConfig = Field(default_factory=SMTPConfig)
    integrations: IntegrationConfig = Field(default_factory=IntegrationConfig)


class ProviderHealth(BaseModel):
    status: str = "unknown"  # unknown | healthy | issue
    message: str = "Not checked yet."
    checked_at: datetime | None = None
    details: dict[str, Any] = Field(default_factory=dict)


class ProviderHealthState(BaseModel):
    smtp: ProviderHealth = Field(default_factory=ProviderHealth)
    telegram: ProviderHealth = Field(default_factory=ProviderHealth)


def _coerce_legacy_weight(value: Any, default: float) -> float:
    try:
        num = float(value)
    except (TypeError, ValueError):
        return default
    # Old UI used 0..100 percentage sliders; map to 0..5 multiplier.
    if num > 5:
        num = num / 20.0
    return max(0.0, min(5.0, num))


def _normalize_raw_config(raw: dict[str, Any]) -> dict[str, Any]:
    data = dict(raw)
    allowed_timeframes = {"5m", "15m", "1H", "4H", "1D"}

    # Backward compatibility with legacy config keys used by the first admin UI.
    if "min_confidence_threshold" in data and "min_signal_confidence" not in data:
        data["min_signal_confidence"] = data.get("min_confidence_threshold")
    if "volume_weight" in data and "trend_weight" not in data:
        data["trend_weight"] = data.get("volume_weight")

    try:
        data["min_signal_confidence"] = max(
            75,
            int(data.get("min_signal_confidence", 75) or 75),
        )
    except Exception:
        data["min_signal_confidence"] = 75

    data["ict_weight"] = _coerce_legacy_weight(data.get("ict_weight", 1.0), 1.0)
    data["trend_weight"] = _coerce_legacy_weight(data.get("trend_weight", 1.0), 1.0)
    data["momentum_weight"] = _coerce_legacy_weight(
        data.get("momentum_weight", 1.0), 1.0
    )

    raw_timeframes = data.get("scanner_timeframes")
    if not isinstance(raw_timeframes, list):
        raw_timeframes = ["15m", "1H", "4H"]
    cleaned_timeframes = []
    for tf in raw_timeframes:
        value = str(tf or "").strip()
        if value in allowed_timeframes and value not in cleaned_timeframes:
            cleaned_timeframes.append(value)
    data["scanner_timeframes"] = cleaned_timeframes or ["15m", "1H", "4H"]

    return data


def _seed_from_settings(config: SystemConfig) -> SystemConfig:
    """Back-fill empty credential fields from environment settings so that the
    admin config page is pre-populated on first load."""
    from app.config import get_settings
    s = get_settings()

    # SMTP
    if not config.smtp.host and s.SMTP_HOST:
        config.smtp.host = s.SMTP_HOST
    if not config.smtp.username and s.SMTP_USER:
        config.smtp.username = s.SMTP_USER
    # Replace password if empty OR looks like a masked value (starts with *)
    if s.SMTP_PASS and (not config.smtp.password or config.smtp.password.startswith("*")):
        config.smtp.password = s.SMTP_PASS
    if not config.smtp.from_email and s.FROM_EMAIL:
        config.smtp.from_email = s.FROM_EMAIL
    if not config.smtp.port:
        config.smtp.port = s.SMTP_PORT or 587
    # Auto-enable SMTP if fully configured from env
    if (not config.smtp.enabled
            and config.smtp.host
            and config.smtp.username
            and config.smtp.password
            and config.smtp.from_email):
        config.smtp.enabled = True

    # Telegram
    if s.TELEGRAM_BOT_TOKEN and (not config.integrations.telegram_bot_token or config.integrations.telegram_bot_token.startswith("*")):
        config.integrations.telegram_bot_token = s.TELEGRAM_BOT_TOKEN
    if not config.integrations.telegram_vip_channel_id and s.TELEGRAM_VIP_CHANNEL_ID:
        config.integrations.telegram_vip_channel_id = str(s.TELEGRAM_VIP_CHANNEL_ID)

    return config


async def load_system_config(redis: RedisClient) -> SystemConfig:
    raw = await redis._r.get(CONFIG_REDIS_KEY)
    if not raw:
        return _seed_from_settings(SystemConfig())

    try:
        parsed = json.loads(raw)
    except Exception as exc:
        logger.warning(f"Invalid admin config JSON in Redis; using defaults: {exc}")
        return _seed_from_settings(SystemConfig())

    try:
        normalized = _normalize_raw_config(parsed if isinstance(parsed, dict) else {})
        return _seed_from_settings(SystemConfig(**normalized))
    except Exception as exc:
        logger.warning(f"Invalid admin config shape; using defaults: {exc}")
        return _seed_from_settings(SystemConfig())


async def save_system_config(redis: RedisClient, config: SystemConfig) -> None:
    await redis._r.set(CONFIG_REDIS_KEY, config.model_dump_json())


async def load_provider_health(redis: RedisClient) -> ProviderHealthState:
    raw = await redis._r.get(PROVIDER_HEALTH_REDIS_KEY)
    if not raw:
        return ProviderHealthState()
    try:
        parsed = json.loads(raw)
        return ProviderHealthState(**parsed)
    except Exception as exc:
        logger.warning(f"Invalid provider health state in Redis: {exc}")
        return ProviderHealthState()


async def set_provider_health(
    redis: RedisClient,
    provider: str,
    status: str,
    message: str,
    details: dict[str, Any] | None = None,
) -> ProviderHealthState:
    state = await load_provider_health(redis)
    entry = ProviderHealth(
        status=status,
        message=message,
        checked_at=datetime.now(timezone.utc),
        details=details or {},
    )
    if provider == "smtp":
        state.smtp = entry
    elif provider == "telegram":
        state.telegram = entry

    await redis._r.set(PROVIDER_HEALTH_REDIS_KEY, state.model_dump_json())
    return state


def _mask_secret(value: str) -> str:
    if not value:
        return ""
    if len(value) <= 4:
        return "*" * len(value)
    return "*" * (len(value) - 4) + value[-4:]


def mask_sensitive_config(config: SystemConfig) -> SystemConfig:
    masked = config.model_copy(deep=True)

    masked.smtp.password = _mask_secret(masked.smtp.password)
    masked.integrations.telegram_bot_token = _mask_secret(
        masked.integrations.telegram_bot_token
    )
    masked.integrations.binance_api_key = _mask_secret(
        masked.integrations.binance_api_key
    )
    masked.integrations.binance_api_secret = _mask_secret(
        masked.integrations.binance_api_secret
    )
    masked.integrations.twelvedata_api_key = _mask_secret(
        masked.integrations.twelvedata_api_key
    )
    masked.integrations.stripe_secret_key = _mask_secret(
        masked.integrations.stripe_secret_key
    )
    masked.integrations.stripe_webhook_secret = _mask_secret(
        masked.integrations.stripe_webhook_secret
    )
    return masked
