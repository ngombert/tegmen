import pytest
from agent_maestro.main import app

@pytest.fixture(autouse=True)
def clear_overrides():
    """Clear FastAPI dependency overrides after each test."""
    yield
    app.dependency_overrides.clear()
