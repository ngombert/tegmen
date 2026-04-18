import pytest
import jwt
from httpx import AsyncClient, ASGITransport
from agent_maestro.main import app
from common.config import config

def get_auth_headers():
    token = jwt.encode(
        {"family_id": "test-family", "user_id": "test-user"},
        config.JWT_SECRET,
        algorithm=config.JWT_ALGORITHM
    )
    return {"Authorization": f"Bearer {token}"}

@pytest.mark.asyncio
async def test_gateway_routing_success():
    """Test successful JSON-RPC routing request."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        payload = {
            "jsonrpc": "2.0",
            "method": "route_message",
            "params": {
                "message": "Hello specialized agent",
                "context": {
                    "family_id": "fam-1",
                    "user_id": "user-1",
                    "correlation_id": "corr-1",
                    "language": "fr"
                }
            },
            "id": "req-1"
        }
        response = await ac.post(
            "/api/v1/routing", 
            json=payload,
            headers=get_auth_headers()
        )
    
    assert response.status_code == 200
    data = response.json()
    assert data["jsonrpc"] == "2.0"
    assert "result" in data
    assert data["id"] == "req-1"
    assert "Mock Gateway" in data["result"]["message"]

@pytest.mark.asyncio
async def test_gateway_routing_invalid_payload():
    """Test routing request with invalid JSON-RPC payload (missing method)."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # Missing 'method' field
        payload = {
            "jsonrpc": "2.0",
            "params": {},
            "id": "req-2"
        }
        response = await ac.post(
            "/api/v1/routing", 
            json=payload,
            headers=get_auth_headers()
        )
    
    # FastAPI returns 422 Unprocessable Entity for Pydantic validation errors by default
    assert response.status_code == 422
    # In Story 4.2, we will implement a global exception handler to return 
    # a proper JSON-RPC error even for validation failures.
