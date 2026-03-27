from __future__ import annotations

import asyncio
import os
import sys
from logging.config import fileConfig
from typing import Optional

from alembic import context
from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

# ---------------------------------------------------------------------------
# Make sure the backend package is importable from here
# ---------------------------------------------------------------------------
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

# ---------------------------------------------------------------------------
# Import all models so their metadata is registered on Base.metadata
# ---------------------------------------------------------------------------
from app.database import Base  # noqa: E402 — must come after sys.path manipulation
import app.models  # noqa: E402, F401  — triggers all model imports

# ---------------------------------------------------------------------------
# Alembic Config
# ---------------------------------------------------------------------------
config = context.config

# Interpret the config file for Python logging.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Set the target metadata for autogenerate support
target_metadata = Base.metadata


# ---------------------------------------------------------------------------
# Helper: resolve the database URL from the environment
# ---------------------------------------------------------------------------
def _get_url() -> str:
    """
    Return the database URL for Alembic async engine.
    Priority:
    1. DATABASE_URL env var
    2. sqlalchemy.url from alembic.ini
    """
    from app.config import get_settings

    settings = get_settings()
    return settings.DATABASE_URL


# ---------------------------------------------------------------------------
# Offline migrations (SQL script mode)
# ---------------------------------------------------------------------------
def run_migrations_offline() -> None:
    """
    Run migrations in 'offline' mode.

    Alembic emits raw SQL statements rather than connecting to the database.
    Useful for generating migration scripts to review before applying.
    """
    url = _get_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
        compare_server_default=True,
    )

    with context.begin_transaction():
        context.run_migrations()


# ---------------------------------------------------------------------------
# Online migrations (async engine)
# ---------------------------------------------------------------------------
def do_run_migrations(connection: Connection) -> None:
    """Execute migrations using an open synchronous connection."""
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        compare_type=True,
        compare_server_default=True,
        # Include schemas if needed — adjust as required
        include_schemas=False,
    )
    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """
    Create an async engine and run migrations inside a connection context.
    Alembic's async support wraps the async engine transparently.
    """
    url = _get_url()

    # Build config dict suitable for async_engine_from_config
    configuration = config.get_section(config.config_ini_section, {})
    configuration["sqlalchemy.url"] = url

    connectable = async_engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode using asyncio."""
    asyncio.run(run_async_migrations())


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
