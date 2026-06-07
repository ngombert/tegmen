import pytest
import jwt
import os
import asyncio
from unittest.mock import patch, AsyncMock
from httpx import AsyncClient, ASGITransport

from agent_maestro.main import app
from common.config import config
from common.schemas import RequestContext, ContextStackItem, FactSchema, YieldResponse, JsonRpcRequest


def get_auth_headers(role="parent", restrictions=None):
    payload = {
        "family_id": "test-family", 
        "user_id": "user-parent-1",
        "role": role
    }
    token = jwt.encode(
        payload,
        config.JWT_SECRET,
        algorithm=config.JWT_ALGORITHM
    )
    return {"Authorization": f"Bearer {token}"}


# --- Story 2.1: Schema validation tests ---
def test_schemas_phase_2():
    # Test ContextStackItem
    item = ContextStackItem(agent="agent_acadomie", context_data={"last_topic": "math"})
    assert item.agent == "agent_acadomie"
    assert item.context_data == {"last_topic": "math"}

    # Test FactSchema
    fact = FactSchema(content="Léo aime le chocolat", importance_score=0.8, type="soft")
    assert fact.content == "Léo aime le chocolat"
    assert fact.importance_score == 0.8
    assert fact.type == "soft"

    # Test YieldResponse
    y_resp = YieldResponse(message="Je rends la main", context_stack=[item])
    assert y_resp.status == "yield"
    assert len(y_resp.context_stack) == 1

    # Test RequestContext with context_stack (retrocompatibility)
    ctx = RequestContext(
        family_id="fam-1",
        user_id="user-1",
        correlation_id="corr-1",
        context_stack=[item]
    )
    assert ctx.context_stack is not None
    assert ctx.context_stack[0].agent == "agent_acadomie"


# --- Story 2.2: Unitary routing & Manual correction/explicit invocation ---
@pytest.mark.asyncio
@patch("agent_maestro.main.call_remote_agent", new_callable=AsyncMock, return_value="Voici la recette.")
async def test_explicit_routing(mock_call):
    """Test that specifying the agent name in the query forces routing to it."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        payload = {
            "jsonrpc": "2.0",
            "method": "route_message",
            "params": {"message": "Demande à gourmet comment faire des crêpes"},
            "id": "req-explicit"
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
    assert data["result"]["message"] == "Voici la recette."


@pytest.mark.asyncio
async def test_manual_correction_pure():
    """Test that a pure correction message redirects the active session and returns transition msg."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        payload = {
            "jsonrpc": "2.0",
            "method": "route_message",
            "params": {
                "message": "Non, c'était pour gourmet",
                "session_id": "session-123"
            },
            "id": "req-correction"
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
    assert "redirige notre conversation vers l'agent Gourmet" in data["result"]["message"]


# --- Story 2.3: Party Mode and parallel orchestration ---
@pytest.mark.asyncio
@patch("agent_maestro.main.call_remote_agent", new_callable=AsyncMock)
async def test_party_mode_parallel_success(mock_call):
    """Test that Party Mode calls multiple agents in parallel and synthesizes results."""
    # Mock Gourmet and Acadomie responses
    def call_mock(route, *args, **kwargs):
        if route == "gourmet":
            return "Avis Gourmet: manger sain."
        elif route == "acadomie":
            return "Avis Acadomie: réviser avant dîner."
        return "Autre"
    mock_call.side_effect = call_mock

    # Enable mock LLM mode for synthesis
    os.environ["USE_MOCK_LLM"] = "true"

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        payload = {
            "jsonrpc": "2.0",
            "method": "route_message",
            "params": {
                "message": "Party mode: comment gérer la soirée de Léo ?",
            },
            "id": "req-party"
        }
        response = await ac.post(
            "/api/v1/routing",
            json=payload,
            headers=get_auth_headers()
        )

    assert response.status_code == 200
    data = response.json()
    assert data["result"]["route"] == "party"
    assert data["result"]["agent"] == "maestro"
    assert "Avis Gourmet" in data["result"]["message"]
    assert "Avis Acadomie" in data["result"]["message"]


@pytest.mark.asyncio
@patch("agent_maestro.main.call_remote_agent", new_callable=AsyncMock)
async def test_party_mode_graceful_degradation(mock_call):
    """Test that Party Mode functions even if one of the agents fails/timeouts."""
    def call_mock(route, *args, **kwargs):
        if route == "gourmet":
            return "Avis Gourmet: manger sain."
        elif route == "acadomie":
            raise asyncio.TimeoutError("Timeout simulé")
        return "Autre"
    mock_call.side_effect = call_mock

    os.environ["USE_MOCK_LLM"] = "true"

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        payload = {
            "jsonrpc": "2.0",
            "method": "route_message",
            "params": {
                "message": "consulte tout le monde pour Léo",
            },
            "id": "req-party-degraded"
        }
        response = await ac.post(
            "/api/v1/routing",
            json=payload,
            headers=get_auth_headers()
        )

    assert response.status_code == 200
    data = response.json()
    assert data["result"]["route"] == "party"
    assert "Avis Gourmet" in data["result"]["message"]
    assert "Avis Acadomie" not in data["result"]["message"]
