import pytest
import jwt
from unittest.mock import patch, AsyncMock
from httpx import AsyncClient, ASGITransport
from agent_maestro.main import app, UNKNOWN_RESPONSE
from common.config import config


def get_auth_headers():
    token = jwt.encode(
        {"family_id": "test-family", "user_id": "user-parent-1"},
        config.JWT_SECRET,
        algorithm=config.JWT_ALGORITHM
    )
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.asyncio
@patch("agent_maestro.main.classify_intent", return_value=("unknown", 0.05))
async def test_gateway_routing_success(mock_classify):
    """Test JSON-RPC routing: unknown intent returns a graceful fallback."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        payload = {
            "jsonrpc": "2.0",
            "method": "route_message",
            "params": {"message": "Hello specialized agent"},
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
    assert data["result"]["route"] == "unknown"
    assert data["result"]["agent"] == "maestro"


@pytest.mark.asyncio
@patch("agent_maestro.main.classify_intent", return_value=("chitchat", 0.9))
async def test_gateway_routing_chitchat(mock_classify):
    """Test JSON-RPC routing: chitchat intent returns a local personality response."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        payload = {
            "jsonrpc": "2.0",
            "method": "route_message",
            "params": {"message": "Salut"},
            "id": "req-chitchat"
        }
        response = await ac.post(
            "/api/v1/routing",
            json=payload,
            headers=get_auth_headers()
        )

    assert response.status_code == 200
    data = response.json()
    assert data["result"]["route"] == "chitchat"
    assert data["result"]["agent"] == "maestro"
    assert len(data["result"]["message"]) > 0


@pytest.mark.asyncio
@patch("agent_maestro.main.call_remote_agent", new_callable=AsyncMock, return_value="Voici une recette de poulet !")
@patch("agent_maestro.main.classify_intent", return_value=("gourmet", 0.9))
async def test_gateway_routing_dispatches_to_remote_agent(mock_classify, mock_call):
    """Test JSON-RPC routing: real intent dispatches to specialized agent."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        payload = {
            "jsonrpc": "2.0",
            "method": "route_message",
            "params": {"message": "Que cuisiner ce soir ?"},
            "id": "req-gourmet"
        }
        response = await ac.post(
            "/api/v1/routing",
            json=payload,
            headers=get_auth_headers()
        )

    assert response.status_code == 200
    data = response.json()
    assert data["result"]["route"] == "gourmet"
    assert data["result"]["agent"] == "agent_gourmet"
    assert data["result"]["message"] == "Voici une recette de poulet !"
    mock_call.assert_called_once()


@pytest.mark.asyncio
@patch("agent_maestro.main.call_remote_agent", new_callable=AsyncMock, side_effect=ConnectionError("Timeout"))
@patch("agent_maestro.main.classify_intent", return_value=("gourmet", 0.9))
async def test_gateway_routing_agent_error_returns_json_rpc_error(mock_classify, mock_call):
    """Test JSON-RPC routing: agent error returns a JSON-RPC error response (not 500 HTTP)."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        payload = {
            "jsonrpc": "2.0",
            "method": "route_message",
            "params": {"message": "Que cuisiner ce soir ?"},
            "id": "req-error"
        }
        response = await ac.post(
            "/api/v1/routing",
            json=payload,
            headers=get_auth_headers()
        )

    assert response.status_code == 200  # JSON-RPC errors are still HTTP 200
    data = response.json()
    assert "error" in data
    assert data["error"]["code"] == -32603
    assert "indisponible" in data["error"]["message"]


@pytest.mark.asyncio
@patch("agent_maestro.main.classify_intent", return_value=("gourmet", 0.2))
async def test_gateway_routing_clarification(mock_classify):
    """Test JSON-RPC routing: ambiguous intent returns a clarification request."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        payload = {
            "jsonrpc": "2.0",
            "method": "route_message",
            "params": {"message": "Pâtes ?"},
            "id": "req-clarify"
        }
        response = await ac.post(
            "/api/v1/routing",
            json=payload,
            headers=get_auth_headers()
        )

    assert response.status_code == 200
    data = response.json()
    assert data["result"]["route"] == "gourmet"
    assert data["result"]["agent"] == "maestro"
    # Match using a safer substring
    assert "pas s\xfbr de bien comprendre" in data["result"]["message"].lower()


@pytest.mark.asyncio
async def test_gateway_routing_invalid_payload():
    """Test routing request with invalid JSON-RPC payload (missing method)."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        payload = {"jsonrpc": "2.0", "params": {}, "id": "req-2"}
        response = await ac.post(
            "/api/v1/routing",
            json=payload,
            headers=get_auth_headers()
        )

    assert response.status_code == 422
