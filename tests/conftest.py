import pytest
from agent_maestro.main import app

@pytest.fixture(autouse=True)
def clear_overrides():
    """Clear FastAPI dependency overrides after each test."""
    yield
    app.dependency_overrides.clear()


@pytest.fixture(autouse=True)
async def setup_db():
    import agent_maestro.app.db.session as maestro_db_session
    from sqlalchemy.ext.asyncio import create_async_engine
    from sqlalchemy.pool import NullPool
    from common.database import create_session_factory

    # Dispose the old one
    await maestro_db_session.engine.dispose()

    # Create a new engine with NullPool for the current test loop
    new_engine = create_async_engine(
        maestro_db_session.DATABASE_URL,
        poolclass=NullPool
    )
    maestro_db_session.engine = new_engine
    new_factory = create_session_factory(new_engine)
    maestro_db_session.async_session_factory = new_factory

    from agent_maestro.main import session_store
    session_store.session_factory = new_factory

    yield

    # Clean up
    await new_engine.dispose()

