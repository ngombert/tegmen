import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from agent_acadomie.main import app

@pytest_asyncio.fixture
async def client():
    """Async client fixture for testing the Acadomie agent."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
