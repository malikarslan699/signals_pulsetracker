from __future__ import annotations

import json
from typing import Any, List, Optional

from loguru import logger
from pydantic import BaseModel, Field

from app.redis_client import RedisClient

PACKAGES_REDIS_KEY = "admin:packages_config"


# ---------------------------------------------------------------------------
# Feature flags per package
# ---------------------------------------------------------------------------
class PackageFeatureFlags(BaseModel):
    # Signal access
    realtime_signals: bool = True
    signal_history: bool = True
    history_days: int = Field(default=30, ge=0)
    # Market access
    crypto_access: bool = True
    forex_access: bool = True
    # Premium features
    telegram_alerts: bool = False
    advanced_analytics: bool = False
    advanced_indicator_breakdown: bool = False
    export_data: bool = False
    api_access: bool = False
    # Limits (0 = unlimited)
    max_alerts: int = Field(default=0, ge=0)
    max_watchlist: int = Field(default=20, ge=0)
    max_signals_per_day: int = Field(default=50, ge=0)
    websocket_connections: int = Field(default=0, ge=0)


# ---------------------------------------------------------------------------
# Package definition
# ---------------------------------------------------------------------------
class PackageDefinition(BaseModel):
    slug: str
    name: str
    price: float = Field(default=0.0, ge=0)
    duration_days: Optional[int] = None  # None = never expires (lifetime)
    duration_label: str = ""             # display: "/ month", "/ year", "one-time"
    is_active: bool = True
    sort_order: int = 0
    description: str = ""
    badge_text: str = ""
    badge_color: str = "#6B7280"
    features: PackageFeatureFlags = Field(default_factory=PackageFeatureFlags)


# ---------------------------------------------------------------------------
# Container for all packages
# ---------------------------------------------------------------------------
class PackagesConfig(BaseModel):
    packages: List[PackageDefinition] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Default packages
# ---------------------------------------------------------------------------
def _default_packages() -> PackagesConfig:
    return PackagesConfig(packages=[
        PackageDefinition(
            slug="trial",
            name="Trial",
            price=0.0,
            duration_days=30,
            duration_label="30 days",
            is_active=True,
            sort_order=1,
            description="Get started with limited access",
            badge_text="",
            badge_color="#6B7280",
            features=PackageFeatureFlags(
                realtime_signals=False,
                signal_history=True,
                history_days=7,
                crypto_access=True,
                forex_access=False,
                telegram_alerts=False,
                advanced_analytics=False,
                advanced_indicator_breakdown=False,
                export_data=False,
                api_access=False,
                max_alerts=0,
                max_watchlist=10,
                max_signals_per_day=20,
                websocket_connections=0,
            ),
        ),
        PackageDefinition(
            slug="monthly",
            name="Monthly Pro",
            price=29.0,
            duration_days=30,
            duration_label="/ month",
            is_active=True,
            sort_order=2,
            description="Full access for active traders",
            badge_text="Most Popular",
            badge_color="#8B5CF6",
            features=PackageFeatureFlags(
                realtime_signals=True,
                signal_history=True,
                history_days=90,
                crypto_access=True,
                forex_access=True,
                telegram_alerts=True,
                advanced_analytics=True,
                advanced_indicator_breakdown=True,
                export_data=True,
                api_access=True,
                max_alerts=10,
                max_watchlist=100,
                max_signals_per_day=0,
                websocket_connections=3,
            ),
        ),
        PackageDefinition(
            slug="yearly",
            name="Yearly Pro",
            price=199.0,
            duration_days=365,
            duration_label="/ year",
            is_active=True,
            sort_order=3,
            description="Best deal for serious traders",
            badge_text="Save 43%",
            badge_color="#10B981",
            features=PackageFeatureFlags(
                realtime_signals=True,
                signal_history=True,
                history_days=180,
                crypto_access=True,
                forex_access=True,
                telegram_alerts=True,
                advanced_analytics=True,
                advanced_indicator_breakdown=True,
                export_data=True,
                api_access=True,
                max_alerts=20,
                max_watchlist=250,
                max_signals_per_day=0,
                websocket_connections=5,
            ),
        ),
        PackageDefinition(
            slug="lifetime",
            name="Lifetime Pro",
            price=299.0,
            duration_days=None,
            duration_label="one-time",
            is_active=True,
            sort_order=4,
            description="Unlimited forever — no recurring fees",
            badge_text="Best Value",
            badge_color="#F59E0B",
            features=PackageFeatureFlags(
                realtime_signals=True,
                signal_history=True,
                history_days=365,
                crypto_access=True,
                forex_access=True,
                telegram_alerts=True,
                advanced_analytics=True,
                advanced_indicator_breakdown=True,
                export_data=True,
                api_access=True,
                max_alerts=0,
                max_watchlist=0,
                max_signals_per_day=0,
                websocket_connections=10,
            ),
        ),
    ])


# ---------------------------------------------------------------------------
# Load / save
# ---------------------------------------------------------------------------
async def load_packages_config(redis: RedisClient) -> PackagesConfig:
    raw = await redis._r.get(PACKAGES_REDIS_KEY)
    if not raw:
        return _default_packages()
    try:
        parsed = json.loads(raw)
        config = PackagesConfig(**parsed)
        # Merge in any missing slugs from defaults so new plans always appear
        defaults = _default_packages()
        existing_slugs = {p.slug for p in config.packages}
        for default_pkg in defaults.packages:
            if default_pkg.slug not in existing_slugs:
                config.packages.append(default_pkg)
        config.packages.sort(key=lambda p: p.sort_order)
        return config
    except Exception as exc:
        logger.warning(f"Invalid packages config in Redis; using defaults: {exc}")
        return _default_packages()


async def save_packages_config(redis: RedisClient, config: PackagesConfig) -> None:
    await redis._r.set(PACKAGES_REDIS_KEY, config.model_dump_json())


def get_package(config: PackagesConfig, slug: str) -> Optional[PackageDefinition]:
    for pkg in config.packages:
        if pkg.slug == slug:
            return pkg
    return None


def packages_to_plans_list(config: PackagesConfig) -> list[dict[str, Any]]:
    """Convert PackagesConfig to the legacy plans list format for /subscriptions/plans."""
    result = []
    for pkg in sorted(config.packages, key=lambda p: p.sort_order):
        if not pkg.is_active:
            continue
        feature_list = _features_to_list(pkg)
        result.append({
            "id": pkg.slug,
            "name": pkg.name,
            "price_usd": pkg.price,
            "duration_days": pkg.duration_days,
            "duration_label": pkg.duration_label,
            "description": pkg.description,
            "badge_text": pkg.badge_text,
            "badge_color": pkg.badge_color,
            "features": feature_list,
            "feature_flags": pkg.features.model_dump(),
        })
    return result


def _features_to_list(pkg: PackageDefinition) -> list[str]:
    f = pkg.features
    items: list[str] = []
    if f.realtime_signals:
        items.append("Real-time signals")
    else:
        items.append("Delayed signals")
    if f.signal_history:
        days = f.history_days if f.history_days > 0 else "unlimited"
        items.append(f"Signal history ({days} days)")
    if f.crypto_access and f.forex_access:
        items.append("Crypto + Forex markets")
    elif f.crypto_access:
        items.append("Crypto market access")
    elif f.forex_access:
        items.append("Forex market access")
    if f.telegram_alerts:
        items.append("Telegram alerts")
    if f.advanced_analytics:
        items.append("Advanced analytics")
    if f.advanced_indicator_breakdown:
        items.append("ICT & indicator breakdown")
    if f.export_data:
        items.append("Data export (CSV)")
    if f.api_access:
        items.append("API access")
    alerts = "Unlimited alerts" if f.max_alerts == 0 else f"Up to {f.max_alerts} alert configs"
    items.append(alerts)
    wl = "Unlimited watchlist" if f.max_watchlist == 0 else f"Up to {f.max_watchlist} pairs"
    items.append(wl)
    if f.websocket_connections > 0:
        items.append(f"Up to {f.websocket_connections} WebSocket connections")
    return items
