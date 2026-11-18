"""Asynchronous database engine and session management with SQLAlchemy 2.0."""

from collections.abc import AsyncGenerator
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from src.app.core.config import get_settings

settings = get_settings()

# Engine assíncrona SQLAlchemy 2.0 com driver asyncpg
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    future=True,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
)

# Fábrica de sessões assíncronas
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependência FastAPI que fornece uma sessão assíncrona com rollback automático em falhas."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def close_db_connection() -> None:
    """Encerra graciosamente o pool de conexões com o banco de dados."""
    await engine.dispose()
