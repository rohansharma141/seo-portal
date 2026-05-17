"""Database setup — async SQLAlchemy 2.0 engine + Supabase client.

The engine is created lazily so the API can start with `uvicorn main:app
--reload` even when `DATABASE_URL` is an unconfigured placeholder (the build
doc requires the portal to boot and serve /health without any credentials).
The first request that actually needs the database raises a clear error if it
is still unconfigured.

Models (Step 2, Section 4) subclass `Base`. Request handlers depend on
`get_db` for an `AsyncSession`.
"""

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from config import settings


class Base(DeclarativeBase):
    """Declarative base for all ORM models."""


_engine: AsyncEngine | None = None
_sessionmaker: async_sessionmaker[AsyncSession] | None = None


def _normalise_db_url(url: str) -> str:
    """Force the asyncpg driver. Supabase/Postgres connection strings are
    commonly handed out as `postgresql://` or `postgres://`; SQLAlchemy's
    async engine needs the `postgresql+asyncpg://` form."""
    if url.startswith("postgresql+asyncpg://"):
        return url
    if url.startswith("postgresql://"):
        return url.replace("postgresql://", "postgresql+asyncpg://", 1)
    if url.startswith("postgres://"):
        return url.replace("postgres://", "postgresql+asyncpg://", 1)
    return url


def get_engine() -> AsyncEngine:
    global _engine, _sessionmaker
    if _engine is None:
        if not settings.database_url:
            raise RuntimeError(
                "DATABASE_URL is not configured. The API starts without it, "
                "but any database-backed endpoint will fail until it is set. "
                "See backend/.env.example (Section 10 of the build doc)."
            )
        _engine = create_async_engine(
            _normalise_db_url(settings.database_url),
            echo=settings.log_level.upper() == "DEBUG",
            pool_pre_ping=True,
        )
        _sessionmaker = async_sessionmaker(
            _engine, class_=AsyncSession, expire_on_commit=False
        )
    return _engine


def get_sessionmaker() -> async_sessionmaker[AsyncSession]:
    if _sessionmaker is None:
        get_engine()
    assert _sessionmaker is not None
    return _sessionmaker


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency yielding a scoped async session."""
    sessionmaker = get_sessionmaker()
    async with sessionmaker() as session:
        yield session


# ── Supabase client ─────────────────────────────────────────────────────
# Direct DB access goes through SQLAlchemy above. The Supabase client is for
# Supabase Auth / Storage (Section 2 tech stack). Imported lazily so a missing
# `supabase` package or missing keys never blocks server start.
_supabase = None


def get_supabase():
    global _supabase
    if _supabase is None:
        if not (settings.supabase_url and settings.supabase_key):
            raise RuntimeError(
                "SUPABASE_URL / SUPABASE_KEY not configured. "
                "See backend/.env.example (Section 10 of the build doc)."
            )
        from supabase import create_client

        _supabase = create_client(settings.supabase_url, settings.supabase_key)
    return _supabase
