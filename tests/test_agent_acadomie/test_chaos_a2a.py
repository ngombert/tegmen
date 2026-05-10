import pytest
import asyncio
import time
from unittest.mock import patch, AsyncMock
from litellm.exceptions import RateLimitError, APIConnectionError

@pytest.mark.asyncio
@patch("litellm.acompletion")
async def test_chaos_llm_rate_limit(mock_acompletion, client):
    """Test resilience against LLM RateLimitError."""
    # Simulating a rate limit error directly from LiteLLM
    response_mock = AsyncMock()
    response_mock.status_code = 429
    request_mock = AsyncMock()
    mock_acompletion.side_effect = RateLimitError("Too Many Requests", response_mock, request_mock)
    
    rpc_request = {
        "jsonrpc": "2.0",
        "method": "organization/advice",
        "params": {
            "student_id": "student-1",
            "context": {"family_id": "fam-123"}
        },
        "id": "chaos-1"
    }
    
    response = await client.post("/a2a/SendMessage", json=rpc_request)
    assert response.status_code == 200
    
    data = response.json()
    assert "error" in data
    # internal error code expected for unexpected LLM failures
    assert data["error"]["code"] == -32603 # INTERNAL_ERROR
    assert "Erreur lors de la génération du conseil" in data["error"]["message"]

@pytest.mark.asyncio
@patch("litellm.acompletion")
async def test_chaos_llm_api_connection_error(mock_acompletion, client):
    """Test resilience against LLM APIConnectionError."""
    # Simulating a connection error
    mock_acompletion.side_effect = APIConnectionError("Connection Failed", llm_provider="openai", model="gpt-4")
    
    rpc_request = {
        "jsonrpc": "2.0",
        "method": "organization/advice",
        "params": {
            "student_id": "student-1",
            "context": {"family_id": "fam-123"}
        },
        "id": "chaos-2"
    }
    
    response = await client.post("/a2a/SendMessage", json=rpc_request)
    assert response.status_code == 200
    
    data = response.json()
    assert "error" in data
    assert data["error"]["code"] == -32603 # INTERNAL_ERROR

@pytest.mark.asyncio
async def test_chaos_concurrency(client):
    """Test that the server processes concurrent requests asynchronously without blocking."""
    rpc_request = {
        "jsonrpc": "2.0",
        "method": "calendar/list",
        "params": {
            "context": {"family_id": "fam-123"}
        },
        "id": "concurrent"
    }
    
    num_requests = 10
    start_time = time.time()
    
    # Send 10 concurrent requests
    tasks = [client.post("/a2a/SendMessage", json=rpc_request) for _ in range(num_requests)]
    responses = await asyncio.gather(*tasks)
    
    end_time = time.time()
    total_time = end_time - start_time
    
    # Verify all responses succeeded
    for response in responses:
        assert response.status_code == 200
        data = response.json()
        assert "result" in data
        assert "events" in data["result"]
        
    # In an asynchronous system with a 0.01s mock delay in CalendarService,
    # 10 requests should complete in just over 0.01s, not 0.1s.
    # We assert that the total time is significantly less than linear time.
    assert total_time < 0.2  # Should be very fast
