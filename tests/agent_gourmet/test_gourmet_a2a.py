import pytest
from fastapi.testclient import TestClient
from agent_gourmet.main import app
from unittest.mock import patch, AsyncMock

@pytest.fixture
def client():
    return TestClient(app)

def test_a2a_agent_card(client):
    response = client.get("/a2a/AgentCard")
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "agent_gourmet"
    assert "search_recipes" in str(data["skills"])

@patch("agent_gourmet.app.api.routers.a2a.LLMService.generate_response", new_callable=AsyncMock)
def test_a2a_send_message_search(mock_generate, client):
    # Test message/send using LLM
    mock_generate.return_value = "Voici une délicieuse recette de carbonara."
    
    payload = {
        "jsonrpc": "2.0",
        "method": "message/send",
        "params": {
            "message": {
                "role": "user",
                "parts": [{"text": "recette carbonara"}]
            },
            "contextId": "test-context-id"
        },
        "id": "1"
    }
    response = client.post("/a2a/SendMessage", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "result" in data
    # Check new A2A structured response
    assert data["result"]["role"] == "agent"
    assert "messageId" in data["result"]
    assert data["result"]["contextId"] == "test-context-id"
    assert "carbonara" in data["result"]["parts"][0]["text"].lower()

@patch("agent_gourmet.app.api.routers.a2a.LLMService.generate_response", new_callable=AsyncMock)
def test_a2a_send_message_error(mock_generate, client):
    # Test message/send when LLM fails
    mock_generate.side_effect = Exception("LLM failure")
    
    payload = {
        "jsonrpc": "2.0",
        "method": "message/send",
        "params": {
            "message": {
                "role": "user",
                "parts": [{"text": "recette carbonara"}]
            },
            "contextId": "test-context-id"
        },
        "id": "1"
    }
    response = client.post("/a2a/SendMessage", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "result" in data
    assert "difficulté" in data["result"]["parts"][0]["text"]

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

def test_a2a_get_recipe_details_success(client):
    payload = {
        "jsonrpc": "2.0",
        "method": "get_recipe_details",
        "params": {"recipe_id": "1"},
        "id": "test-detail-ok"
    }
    response = client.post("/a2a/SendMessage", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "result" in data
    recipe = data["result"]["recipe"]
    assert recipe["id"] == "1"
    assert recipe["name"] == "Pâtes Carbonara"
    assert "tags" in recipe
    assert "prep_time" in recipe
    assert "servings" in recipe
    assert "difficulty" in recipe
    assert "ingredients" in recipe
    assert len(recipe["ingredients"]) > 0
    assert "steps" in recipe
    assert len(recipe["steps"]) > 0

def test_a2a_get_recipe_details_not_found(client):
    payload = {
        "jsonrpc": "2.0",
        "method": "get_recipe_details",
        "params": {"recipe_id": "999"},
        "id": "test-detail-404"
    }
    response = client.post("/a2a/SendMessage", json=payload)
    data = response.json()
    assert "error" in data
    assert data["error"]["code"] == -32010 # RECIPE_NOT_FOUND
    assert data["error"]["data"]["recipe_id"] == "999"

def test_a2a_get_recipe_details_invalid_type(client):
    payload = {
        "jsonrpc": "2.0",
        "method": "get_recipe_details",
        "params": {"recipe_id": 123}, # Should fail (strict str)
        "id": "test-detail-type"
    }
    response = client.post("/a2a/SendMessage", json=payload)
    data = response.json()
    assert "error" in data
    assert data["error"]["code"] == -32602 # INVALID_PARAMS
