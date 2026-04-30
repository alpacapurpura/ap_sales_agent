"""Campaigns API dependency factories.

AsyncSession DI: builds a per-request async session backed by the
application async engine (asyncpg driver). Services are constructed here
to keep routers thin (validate → service → map exception pattern).
"""

from __future__ import annotations

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from src.core.config import settings

# ── Async engine (asyncpg) ────────────────────────────────────────────────────
# Build a postgresql+asyncpg URL from the sync settings URL.
_async_url = settings.database_url.replace("postgresql://", "postgresql+asyncpg://", 1)

_async_engine = create_async_engine(
    _async_url,
    pool_pre_ping=True,
    pool_recycle=300,
)

_AsyncSessionLocal: async_sessionmaker[AsyncSession] = async_sessionmaker(
    _async_engine,
    expire_on_commit=False,
    class_=AsyncSession,
)


async def get_campaigns_async_session() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency: yields a per-request AsyncSession.

    Commits on success, rolls back on exception.
    """
    async with _AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
