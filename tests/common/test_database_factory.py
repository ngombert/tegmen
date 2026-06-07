import pytest
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker
from common.database import create_async_engine_for_agent, create_session_factory


def test_create_async_engine():
    url = "sqlite+aiosqlite:///:memory:"
    engine = create_async_engine_for_agent(url, debug=True)
    assert isinstance(engine, AsyncEngine)
    assert str(engine.url) == url


def test_create_session_factory():
    url = "sqlite+aiosqlite:///:memory:"
    engine = create_async_engine_for_agent(url)
    factory = create_session_factory(engine)
    assert isinstance(factory, async_sessionmaker)
    session = factory()
    assert isinstance(session, AsyncSession)
