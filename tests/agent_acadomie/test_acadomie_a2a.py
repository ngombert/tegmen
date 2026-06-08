import pytest
from common.schemas import JsonRpcResponse

@pytest.mark.asyncio
async def test_health_check(client):
    """Test the health check endpoint."""
    response = await client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["agent"] == "acadomie"
    assert data["mode"] == "lean"

@pytest.mark.asyncio
async def test_agent_card(client):
    """Test the agent card endpoint."""
    response = await client.get("/a2a/AgentCard")
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "agent_acadomie"
    assert len(data["skills"]) == 4
    
    skill_ids = [s["id"] for s in data["skills"]]
    assert "homework" in skill_ids
    assert "calendar" in skill_ids
    assert "grades" in skill_ids
    assert "organization" in skill_ids

@pytest.mark.asyncio
async def test_send_message_basic(client):
    """Test the /a2a/SendMessage endpoint with a basic message."""
    rpc_request = {
        "jsonrpc": "2.0",
        "method": "message/send",
        "params": {
            "message": {
                "parts": [{"text": "Bonjour"}]
            }
        },
        "id": "1"
    }
    
    response = await client.post("/a2a/SendMessage", json=rpc_request)
    assert response.status_code == 200
    
    data = response.json()
    assert "result" in data
    assert "parts" in data["result"]
    assert any("agent acadomie" in p["text"].lower() for p in data["result"]["parts"])

@pytest.mark.asyncio
async def test_send_message_homework(client):
    """Test the /a2a/SendMessage endpoint with homework keyword."""
    rpc_request = {
        "jsonrpc": "2.0",
        "method": "message/send",
        "params": {
            "message": {
                "parts": [{"text": "Quels sont les devoirs ?"}]
            }
        },
        "id": "2"
    }
    
    response = await client.post("/a2a/SendMessage", json=rpc_request)
    assert response.status_code == 200
    
    data = response.json()
    assert "result" in data
    assert any("devoirs" in p["text"].lower() for p in data["result"]["parts"])

@pytest.mark.asyncio
async def test_method_not_found(client):
    """Test calling a non-existent method."""
    rpc_request = {
        "jsonrpc": "2.0",
        "method": "unknown_method",
        "params": {},
        "id": "3"
    }
    
    response = await client.post("/a2a/SendMessage", json=rpc_request)
    assert response.status_code == 200
    
    data = response.json()
    assert "error" in data
    assert data["error"]["code"] == -32601 # METHOD_NOT_FOUND
