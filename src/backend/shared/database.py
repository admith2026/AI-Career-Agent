"""Async database session management."""

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from shared.config import BaseServiceSettings

_settings = BaseServiceSettings()
engine = create_async_engine(_settings.database_url, pool_size=10, max_overflow=20)
async_session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def get_db() -> AsyncSession:  # type: ignore[misc]
    """FastAPI dependency that yields an async DB session."""
    async with async_session_factory() as session:
        try:
            yield session
        finally:
            await session.close()


async def get_db_session():
    """Standalone async generator for use outside FastAPI dependency injection."""
    async with async_session_factory() as session:
        try:
            yield session
        finally:
            await session.close()
