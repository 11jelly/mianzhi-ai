from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import get_settings

settings = get_settings()

engine = (
    create_async_engine(settings.database_url, pool_pre_ping=True)
    if settings.database_url
    else None
)

async_session_factory = (
    async_sessionmaker(engine, expire_on_commit=False)
    if engine is not None
    else None
)


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    if async_session_factory is None:
        msg = "DATABASE_URL is not configured."
        raise RuntimeError(msg)

    async with async_session_factory() as session:
        yield session
