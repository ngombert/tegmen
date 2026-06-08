import pytest
from common.exceptions import A2ARPCError

@pytest.mark.asyncio
async def test_homework_list_success(client):
    """Test successful homework list retrieval."""
    rpc_request = {
        "jsonrpc": "2.0",
        "method": "homework/list",
        "params": {
            "context": {"family_id": "fam-123"}
        },
        "id": "1"
    }
    
    response = await client.post("/a2a/SendMessage", json=rpc_request)
    assert response.status_code == 200
    
    data = response.json()
    assert "result" in data
    assert "homeworks" in data["result"]
    assert data["result"]["total_count"] == 2
    assert data["result"]["homeworks"][0]["subject"] == "Mathématiques"

@pytest.mark.asyncio
async def test_homework_list_missing_family_id(client):
    """Test homework list without family_id."""
    rpc_request = {
        "jsonrpc": "2.0",
        "method": "homework/list",
        "params": {},
        "id": "2"
    }
    
    response = await client.post("/a2a/SendMessage", json=rpc_request)
    assert response.status_code == 200
    
    data = response.json()
    assert "error" in data
    assert data["error"]["code"] == -32602 # INVALID_PARAMS
    assert "family_id" in data["error"]["message"]

@pytest.mark.asyncio
async def test_homework_add_success(client):
    """Test successful homework addition."""
    rpc_request = {
        "jsonrpc": "2.0",
        "method": "homework/add",
        "params": {
            "context": {"family_id": "fam-456"},
            "subject": "Histoire",
            "task": "Apprendre la leçon sur la Révolution",
            "due_date": "Mardi"
        },
        "id": "3"
    }
    
    response = await client.post("/a2a/SendMessage", json=rpc_request)
    assert response.status_code == 200
    
    data = response.json()
    assert "result" in data
    assert data["result"]["subject"] == "Histoire"
    assert data["result"]["family_id"] == "fam-456"
    
    # Verify it was added
    list_request = {
        "jsonrpc": "2.0",
        "method": "homework/list",
        "params": {
            "context": {"family_id": "fam-456"}
        },
        "id": "4"
    }
    list_response = await client.post("/a2a/SendMessage", json=list_request)
    list_data = list_response.json()
    assert list_data["result"]["total_count"] == 1
    assert list_data["result"]["homeworks"][0]["subject"] == "Histoire"

@pytest.mark.asyncio
async def test_homework_add_invalid_params(client):
    """Test homework addition with missing fields."""
    rpc_request = {
        "jsonrpc": "2.0",
        "method": "homework/add",
        "params": {
            "context": {"family_id": "fam-123"},
            "subject": "Physique"
            # Missing task and due_date
        },
        "id": "5"
    }
    
    response = await client.post("/a2a/SendMessage", json=rpc_request)
    assert response.status_code == 200
    
    data = response.json()
    assert "error" in data
    assert data["error"]["code"] == -32602 # INVALID_PARAMS
