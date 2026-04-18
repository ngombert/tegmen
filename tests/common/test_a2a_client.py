import pytest
import httpx
from common.a2a_client import RemoteAgentClient

@pytest.mark.asyncio
async def test_remote_agent_client_timeout(httpx_mock):
    """Test that client uses correct timeout."""
    client = RemoteAgentClient("http://agent-test")
    assert client.client.timeout.connect == 5.0
    assert client.client.timeout.read == 5.0
    await client.close()

@pytest.mark.asyncio
async def test_remote_agent_client_injection():
    """Test that httpx_client is injectable."""
    mock_client = httpx.AsyncClient()
    client = RemoteAgentClient("http://agent-test", httpx_client=mock_client)
    assert client.client is mock_client
    # No need to close mock_client here if it's managed externally, 
    # but RemoteAgentClient.close() would close it.
    await client.close()

@pytest.mark.asyncio
async def test_remote_agent_client_send_message_success(httpx_mock):
    """Test successful message sending."""
    httpx_mock.add_response(
        url="http://agent-test",
        json={
            "jsonrpc": "2.0",
            "result": {
                "messageId": "msg-123",
                "role": "agent",
                "parts": [{"text": "Hello, I am Agent Test"}]
            },
            "id": "123"
        }
    )
    
    client = RemoteAgentClient("http://agent-test")
    response = await client.send_message("Hi", context_id="ctx-1")
    assert response == "Hello, I am Agent Test"
    await client.close()
