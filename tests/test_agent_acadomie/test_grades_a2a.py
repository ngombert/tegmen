import pytest

@pytest.mark.asyncio
async def test_grades_list_success_parent(client):
    """Test successful grades retrieval by a parent."""
    rpc_request = {
        "jsonrpc": "2.0",
        "method": "grades/list",
        "params": {
            "student_id": "student-1",
            "context": {
                "family_id": "fam-123",
                "user": {"id": "parent-1", "role": "parent"}
            }
        },
        "id": "1"
    }
    
    response = await client.post("/a2a/SendMessage", json=rpc_request)
    assert response.status_code == 200
    
    data = response.json()
    assert "result" in data
    assert "grades" in data["result"]
    assert len(data["result"]["grades"]) == 2
    assert data["result"]["average"] is not None

@pytest.mark.asyncio
async def test_grades_list_success_student(client):
    """Test successful grades retrieval by the matching student."""
    rpc_request = {
        "jsonrpc": "2.0",
        "method": "grades/list",
        "params": {
            "student_id": "student-1",
            "context": {
                "family_id": "fam-123",
                "user": {"id": "student-1", "role": "child"}
            }
        },
        "id": "2"
    }
    
    response = await client.post("/a2a/SendMessage", json=rpc_request)
    assert response.status_code == 200
    
    data = response.json()
    assert "result" in data
    assert len(data["result"]["grades"]) == 2

@pytest.mark.asyncio
async def test_grades_list_forbidden_sibling(client):
    """Test access denied for a sibling trying to read another's grades."""
    rpc_request = {
        "jsonrpc": "2.0",
        "method": "grades/list",
        "params": {
            "student_id": "student-1",
            "context": {
                "family_id": "fam-123",
                "user": {"id": "student-2", "role": "child"}
            }
        },
        "id": "3"
    }
    
    response = await client.post("/a2a/SendMessage", json=rpc_request)
    assert response.status_code == 200
    
    data = response.json()
    assert "error" in data
    assert data["error"]["code"] == -32002 # FORBIDDEN

@pytest.mark.asyncio
async def test_grades_list_missing_identity(client):
    """Test failure when user identity is missing."""
    rpc_request = {
        "jsonrpc": "2.0",
        "method": "grades/list",
        "params": {
            "student_id": "student-1",
            "context": {
                "family_id": "fam-123"
            }
        },
        "id": "4"
    }
    
    response = await client.post("/a2a/SendMessage", json=rpc_request)
    assert response.status_code == 200
    
    data = response.json()
    assert "error" in data
    assert data["error"]["code"] == -32002 # FORBIDDEN
    assert "Identité" in data["error"]["message"]
