import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient

from agent_maestro.main import app, session_store, ESCAPE_COMMANDS, ESCAPE_RESPONSE, get_request_context
from common.auth import get_current_identity
from common.schemas import JsonRpcRequest, RequestContext

client = TestClient(app)

@pytest.fixture(autouse=True)
def override_dependencies():
    def override_get_request_context():
        return RequestContext(
            family_id="fam1",
            user_id="user1",
            user_name="Test User",
            role="parent",
            correlation_id="corr-1",
            preferences={},
            restrictions=[]
        )
    
    def override_get_current_identity():
        return {"user_id": "user1", "family_id": "fam1"}
        
    app.dependency_overrides[get_request_context] = override_get_request_context
    app.dependency_overrides[get_current_identity] = override_get_current_identity
    yield
    app.dependency_overrides.clear()

@pytest.mark.asyncio
async def test_escape_commands_intercepted_and_session_cleared():
    session_id = "test_escape_sess"
    
    # 1. Set an active session manually
    await session_store.set(session_id, "agent_gourmet")
    assert await session_store.get(session_id) == "agent_gourmet"
    
    # 2. Send an escape command
    request_data = {
        "jsonrpc": "2.0",
        "method": "message/send",
        "params": {
            "message": "stop",
            "session_id": session_id
        },
        "id": "req-1"
    }
    
    response = client.post("/api/v1/routing", json=request_data)
    
    # 3. Check response
    assert response.status_code == 200
    res_data = response.json()
    assert res_data["result"]["message"] == ESCAPE_RESPONSE
    assert res_data["result"]["route"] == "chitchat"
    
    # 4. Check that session was cleared
    assert await session_store.get(session_id) is None

@pytest.mark.asyncio
async def test_all_escape_commands_recognized():
    for cmd in ESCAPE_COMMANDS:
        request_data = {
            "jsonrpc": "2.0",
            "method": "message/send",
            "params": {
                "message": f"  {cmd.upper()}  ", # test uppercase and spaces
                "session_id": "any_sess"
            },
            "id": "req-1"
        }
        
        response = client.post("/api/v1/routing", json=request_data)
        assert response.status_code == 200
        assert response.json()["result"]["message"] == ESCAPE_RESPONSE
