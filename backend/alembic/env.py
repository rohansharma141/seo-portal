"""Alembic environment — async engine, wired to the model metadata.

Reads the DB URL from settings.database_url (Section 10). When that is unset
(placeholder mode) a harmless local URL is used so offline SQL generation
(`alembic upgrade head --sql`) still works for verification without a DB.
"""

import asyncio
import os
import sys
from logging.config import fileConfig

from alembic import context
from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

# Make the backend package importable when alembic runs from backend/.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import settings  # noqa: E402
from models import Base  # noqa: E402  (registers every table on Base.metadata)

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata

# Fallback only used for offline SQL preview when DATABASE_URL is unconfigured.
_FALLBACK_URL = "postgresql+asyncpg://user:pass@localhost:5432/seo_portal"


def _async_url() -> str:
    return settings.database_url or _FALLBACK_URL


def run_migrations_offline() -> None:
    """Emit SQL without connecting (used by `--sql` and for verification)."""
    url = _async_url().replace("+asyncpg", "")  # sync dialect for offline
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def _do_run_migrations(connection: Connection) -> None:
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        compare_type=True,
    )
    with context.begin_transaction():
        context.run_migrations()


async def run_migrations_online() -> None:
    section = config.get_section(config.config_ini_section) or {}
    section["sqlalchemy.url"] = _async_url()
    connectable = async_engine_from_config(
        section, prefix="sqlalchemy.", poolclass=pool.NullPool
    )
    async with connectable.connect() as connection:
        await connection.run_sync(_do_run_migrations)
    await connectable.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    asyncio.run(run_migrations_online())
