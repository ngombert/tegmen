import pytest
from fastapi.testclient import TestClient
from agent_maestro.main import app, get_request_context
from common.agent_registry import agent_registry
from common.schemas import RequestContext

client = TestClient(app)

def override_get_request_context_admin():
    return RequestContext(
        family_id="test_family",
        user_id="admin_user",
        user_name="Admin",
        role="parent", # Admin role
        correlation_id="test-correlation",
        preferences={},
        restrictions=[]
    )

def override_get_request_context_user():
    return RequestContext(
        family_id="test_family",
        user_id="child_user",
        user_name="Child",
        role="child", # Non-admin role
        correlation_id="test-correlation",
        preferences={},
        restrictions=[]
    )

@pytest.mark.asyncio
async def test_maestro_trace_admin(httpx_mock):
    """
    Vérifie que l'admin reçoit les infos de debug avec le flag debug: true.
    """
    app.dependency_overrides[get_request_context] = override_get_request_context_admin
    
    payload = {
        "jsonrpc": "2.0",
        "method": "SendMessage",
        "params": {
            "message": "Bonjour Maestro",
            "debug": True
        },
        "id": "trace-id-admin"
    }
    
    response = client.post("/api/v1/routing", json=payload)
    assert response.status_code == 200
    data = response.json()
    
    assert "result" in data
    assert "_debug" in data["result"]
    debug = data["result"]["_debug"]
    assert "routing" in debug
    assert "all_scores" in debug["routing"]
    assert "chitchat" in debug["routing"]["all_scores"]
    assert "thresholds" in debug["routing"]

@pytest.mark.asyncio
async def test_maestro_trace_forbidden_for_user(httpx_mock):
    """
    Vérifie qu'un utilisateur non-admin ne reçoit PAS les infos de debug.
    """
    app.dependency_overrides[get_request_context] = override_get_request_context_user
    
    payload = {
        "jsonrpc": "2.0",
        "method": "SendMessage",
        "params": {
            "message": "Bonjour Maestro",
            "debug": True
        },
        "id": "trace-id-user"
    }
    
    response = client.post("/api/v1/routing", json=payload)
    assert response.status_code == 200
    data = response.json()
    
    assert "result" in data
    assert "_debug" not in data["result"]
