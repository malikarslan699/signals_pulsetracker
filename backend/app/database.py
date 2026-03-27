from __future__ import annotations

from typing import AsyncGenerator

import httpx
from loguru import logger
from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from app.config import get_settings

settings = get_settings()

_FALLBACK_CRYPTO_PAIRS = [
    "BTCUSDT",
    "ETHUSDT",
    "BNBUSDT",
    "SOLUSDT",
    "XRPUSDT",
    "ADAUSDT",
    "DOGEUSDT",
    "AVAXUSDT",
    "DOTUSDT",
    "LINKUSDT",
]

_DEFAULT_FOREX_PAIRS = [
    "XAUUSD",
    "XAGUSD",
    "USOIL",
    "EURUSD",
    "GBPUSD",
    "USDJPY",
    "USDCHF",
    "AUDUSD",
    "USDCAD",
    "NZDUSD",
    "EURGBP",
    "EURJPY",
    "GBPJPY",
    "AUDJPY",
    "CADJPY",
    "CHFJPY",
    "US100",
    "US500",
    "US30",
    "DE40",
    "UK100",
    "JP225",
]

# ---------------------------------------------------------------------------
# Engine
# ---------------------------------------------------------------------------
engine: AsyncEngine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.is_development,
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,
    pool_recycle=3600,
    connect_args={
        "server_settings": {
            "application_name": "pulsesignal_backend",
        }
    },
)

# ---------------------------------------------------------------------------
# Session factory
# ---------------------------------------------------------------------------
AsyncSessionFactory: async_sessionmaker[AsyncSession] = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
    autocommit=False,
)


# ---------------------------------------------------------------------------
# Declarative Base
# ---------------------------------------------------------------------------
class Base(DeclarativeBase):
    pass


# ---------------------------------------------------------------------------
# Dependencies
# ---------------------------------------------------------------------------
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency that provides a database session per request."""
    async with AsyncSessionFactory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


# ---------------------------------------------------------------------------
# Lifecycle helpers
# ---------------------------------------------------------------------------
async def create_tables() -> None:
    """Create all tables defined in Base.metadata (development / testing only)."""
    # Import all models so their metadata is registered
    import app.models  # noqa: F401

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        # Backward-compatible hotfix: older deployments created users.telegram_chat_id
        # as INTEGER, which overflows for many Telegram chat IDs.
        result = await conn.execute(
            text(
                """
                SELECT data_type
                FROM information_schema.columns
                WHERE table_schema = 'public'
                  AND table_name = 'users'
                  AND column_name = 'telegram_chat_id'
                """
            )
        )
        data_type = result.scalar_one_or_none()
        if data_type == "integer":
            await conn.execute(
                text(
                    """
                    ALTER TABLE public.users
                    ALTER COLUMN telegram_chat_id TYPE BIGINT
                    USING telegram_chat_id::bigint
                    """
                )
            )
            logger.info("Migrated users.telegram_chat_id from INTEGER to BIGINT.")

        await _seed_pairs_if_empty(conn)
    logger.info("Database tables created successfully.")


async def _seed_pairs_if_empty(conn) -> None:
    """Seed default pairs on fresh deployments."""
    count_result = await conn.execute(text("SELECT COUNT(*) FROM pairs"))
    existing = int(count_result.scalar_one() or 0)
    if existing >= 50:
        return

    rows: list[tuple[str, str, str, str, str]] = []

    # Prefer live Binance futures symbol list.
    try:
        async with httpx.AsyncClient(timeout=8) as client:
            response = await client.get("https://fapi.binance.com/fapi/v1/exchangeInfo")
            response.raise_for_status()
            payload = response.json()

        for item in payload.get("symbols", []):
            if (
                item.get("status") == "TRADING"
                and item.get("contractType") == "PERPETUAL"
                and item.get("quoteAsset") == "USDT"
            ):
                symbol = str(item.get("symbol", "")).upper()
                base_asset = str(item.get("baseAsset", "")).upper()
                quote_asset = str(item.get("quoteAsset", "USDT")).upper()
                if symbol and base_asset and quote_asset:
                    rows.append((symbol, "crypto", "binance", base_asset, quote_asset))
    except Exception as exc:
        logger.warning(f"Could not fetch Binance exchange symbols for seed: {exc}")

    if not rows:
        for symbol in _FALLBACK_CRYPTO_PAIRS:
            rows.append((symbol, "crypto", "binance", symbol.replace("USDT", ""), "USDT"))

    for symbol in _DEFAULT_FOREX_PAIRS:
        if symbol.isalpha() and len(symbol) >= 6:
            base_asset = symbol[:-3]
            quote_asset = symbol[-3:]
        else:
            base_asset = symbol
            quote_asset = "USD"
        rows.append((symbol, "forex", "otc", base_asset, quote_asset))

    inserted = 0
    for symbol, market, exchange, base_asset, quote_asset in rows:
        await conn.execute(
            text(
                """
                INSERT INTO pairs (
                    id, symbol, market, exchange, base_asset, quote_asset,
                    is_active, precision_price, precision_qty, min_qty
                ) VALUES (
                    uuid_generate_v4(), :symbol, :market, :exchange, :base_asset, :quote_asset,
                    true, 8, 3, 0.001
                )
                ON CONFLICT (symbol) DO NOTHING
                """
            ),
            {
                "symbol": symbol,
                "market": market,
                "exchange": exchange,
                "base_asset": base_asset,
                "quote_asset": quote_asset,
            },
        )
        inserted += 1

    logger.info(f"Pair seed completed (candidates={len(rows)}, inserted_attempts={inserted}).")


async def drop_tables() -> None:
    """Drop all tables (testing / reset purposes)."""
    import app.models  # noqa: F401

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    logger.warning("All database tables dropped.")


async def check_db_health() -> bool:
    """Return True if the database is reachable, False otherwise."""
    try:
        async with AsyncSessionFactory() as session:
            await session.execute(text("SELECT 1"))
        return True
    except Exception as exc:
        logger.error(f"Database health check failed: {exc}")
        return False
