"""Database module - SQLAlchemy async engine and session factory."""

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine, AsyncEngine
from sqlalchemy.orm import DeclarativeBase

from common.config import config


def create_async_engine_for_agent(database_url: str, debug: bool = False) -> AsyncEngine:
    """Create an async engine for a specific agent."""
    return create_async_engine(
        database_url,
        echo=debug,
        future=True,
    )


def create_session_factory(engine: AsyncEngine) -> async_sessionmaker[AsyncSession]:
    """Create a session factory for a given async engine."""
    return async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )


# Create async engine
engine = create_async_engine_for_agent(config.DATABASE_URL, config.DEBUG)

# Session factory
async_session_factory = create_session_factory(engine)


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy models."""

    pass


async def get_db() -> AsyncSession:
    """Get database session as async context manager."""
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db() -> None:
    """Initialize database - create all tables."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
