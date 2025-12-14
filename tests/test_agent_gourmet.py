import pytest
from unittest.mock import patch
from fastapi.testclient import TestClient
from src.agent_gourmet.agent import get_agent
# We import app inside test to allow mocking dependencies if needed,
# but for main.py simply importing it might trigger side effects (setup_logger, wrappers).
# Ideally key dependencies should be patched before import or designed to be testable.
# Here we will try to test the result of the module import.


def test_get_agent():
    agent = get_agent()
    assert agent.name == "agent_gourmet"
    assert len(agent.tools) == 2


@patch("src.agent_gourmet.main.create_a2a_app")
def test_main_app_structure(mock_create_a2a):
    # Mock the A2A app creation to avoid complex starlette structures during import if possible,
    # but since main.py executes at import time, we might be too late to patch if we import inside test.
    # However, standard practice is often to import at top level.
    # If side effects are heavy, we patch sys.modules or use helpers.
    # The main.py here is simple enough.

    from src.agent_gourmet.main import app

    client = TestClient(app)
    # The A2A app is mounted at root / which usually handles JSONRPC or specific routes.
    # Accessing /docs should be valid for FastAPI
    response = client.get("/docs")
    assert response.status_code == 200
    assert "Agent Gourmet" in response.text


@pytest.mark.asyncio
async def test_lifespan():
    # Test lifespan manually
    from src.agent_gourmet.main import app, lifespan

    # Check if context manager yields
    async with lifespan(app):
        pass
    # If no error, pass. Could verify logs if logger was mocked.
