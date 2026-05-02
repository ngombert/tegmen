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

def test_a2a_search_empty_result(client):
    payload = {
        "jsonrpc": "2.0",
        "method": "search_recipes",
        "params": {"query": "xyzzy_introuvable"},
        "id": "test-empty"
    }
    response = client.post("/a2a/SendMessage", json=payload)
    data = response.json()
    assert "result" in data
    assert data["result"]["total_count"] == 0
    assert data["result"]["results"] == []

def test_a2a_search_by_ingredient(client):
    payload = {
        "jsonrpc": "2.0",
        "method": "search_recipes",
        "params": {"query": "pecorino"},
        "id": "test-ing"
    }
    response = client.post("/a2a/SendMessage", json=payload)
    data = response.json()
    assert "result" in data
    assert data["result"]["total_count"] >= 1
    assert any("carbonara" in r["name"].lower() for r in data["result"]["results"])

def test_a2a_search_invalid_params(client):
    payload = {
        "jsonrpc": "2.0",
        "method": "search_recipes",
        "params": {"query": 123},  # strict=True on SearchRequest
        "id": "test-invalid"
    }
    response = client.post("/a2a/SendMessage", json=payload)
    data = response.json()
    assert "error" in data
    assert data["error"]["code"] == -32602  # INVALID_PARAMS

def test_a2a_search_complex_filters(client):
    payload = {
        "jsonrpc": "2.0",
        "method": "search_recipes",
        "params": {
            "tags_include": ["italien"],
            "max_prep_time": 30
        },
        "id": "test-complex"
    }
    response = client.post("/a2a/SendMessage", json=payload)
    data = response.json()
    assert data["result"]["total_count"] == 1
    assert data["result"]["results"][0]["name"] == "Pâtes Carbonara"

def test_a2a_search_pagination(client):
    payload = {
        "jsonrpc": "2.0",
        "method": "search_recipes",
        "params": {
            "limit": 1,
            "offset": 1
        },
        "id": "test-pag"
    }
    response = client.post("/a2a/SendMessage", json=payload)
    data = response.json()
    assert data["result"]["total_count"] == 4
    assert len(data["result"]["results"]) == 1
    # First is Carbonara, second (offset 1) is Poulet Rôti
    assert data["result"]["results"][0]["name"] == "Poulet Rôti"
