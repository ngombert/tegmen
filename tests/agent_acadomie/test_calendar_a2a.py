import pytest

@pytest.mark.asyncio
async def test_calendar_list_success(client):
    """Test successful calendar events retrieval."""
    rpc_request = {
        "jsonrpc": "2.0",
        "method": "calendar/list",
        "params": {
            "context": {"family_id": "fam-123"}
        },
        "id": "1"
    }
    
    response = await client.post("/a2a/SendMessage", json=rpc_request)
    assert response.status_code == 200
    
    data = response.json()
    assert "result" in data
    assert "events" in data["result"]
    assert data["result"]["total_count"] == 2
    assert data["result"]["events"][0]["title"] == "Contrôle de Mathématiques"

@pytest.mark.asyncio
async def test_calendar_list_empty(client):
    """Test calendar events retrieval for a family with no events."""
    rpc_request = {
        "jsonrpc": "2.0",
        "method": "calendar/list",
        "params": {
            "context": {"family_id": "fam-999"}
        },
        "id": "2"
    }
    
    response = await client.post("/a2a/SendMessage", json=rpc_request)
    assert response.status_code == 200
    
    data = response.json()
    assert "result" in data
    assert data["result"]["total_count"] == 0
    assert len(data["result"]["events"]) == 0

@pytest.mark.asyncio
async def test_calendar_list_missing_family_id(client):
    """Test calendar events retrieval without family_id."""
    rpc_request = {
        "jsonrpc": "2.0",
        "method": "calendar/list",
        "params": {},
        "id": "3"
    }
    
    response = await client.post("/a2a/SendMessage", json=rpc_request)
    assert response.status_code == 200
    
    data = response.json()
    assert "error" in data
    assert data["error"]["code"] == -32602 # INVALID_PARAMS
    assert "family_id" in data["error"]["message"]
