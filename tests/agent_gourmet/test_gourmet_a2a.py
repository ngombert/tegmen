import pytest
from fastapi.testclient import TestClient
from agent_gourmet.main import app

@pytest.fixture
def client():
    return TestClient(app)

def test_a2a_agent_card(client):
    response = client.get("/a2a/AgentCard")
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "agent_gourmet"
    assert "search_recipes" in str(data["skills"])

def test_a2a_send_message_search(client):
    # Test message/send dispatching to search_recipes
    payload = {
        "jsonrpc": "2.0",
        "method": "message/send",
        "params": {
            "message": {
                "role": "user",
                "parts": [{"text": "recette carbonara"}]
            }
        },
        "id": "1"
    }
    response = client.post("/a2a/SendMessage", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "result" in data
    assert "carbonara" in data["result"]["message"].lower()

def test_a2a_direct_search(client):
    # Test direct JSON-RPC call to search_recipes
    payload = {
        "jsonrpc": "2.0",
        "method": "search_recipes",
        "params": {"query": "carbonara"},
        "id": "2"
    }
    response = client.post("/a2a/SendMessage", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "result" in data
    assert data["result"]["total_count"] == 1
