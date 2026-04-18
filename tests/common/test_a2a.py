import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from src.common.a2a_client import call_remote_agent
from src.common.a2a_server import create_a2a_app
from src.common.schemas import JsonRpcRequest, JsonRpcResponse


# A2A Client Tests
@pytest.mark.asyncio
@patch("src.common.a2a_client.httpx.AsyncClient")
async def test_call_remote_agent_success(mock_client_cls):
    # Setup mock parsed response
    mock_response_obj = MagicMock()
    # Explicitly remove 'error' attribute so hasattr returns False
    del mock_response_obj.root.error

    # Configure result structure
    mock_response_obj.root.result.parts = [MagicMock()]
    mock_response_obj.root.result.parts[0].root.text = "Hello from agent"

    # Setup mock instance
    mock_client_instance = mock_client_cls.return_value
    mock_client_instance.aclose = AsyncMock()

    # Setup A2AClient mock inside RemoteAgentClient
    with patch("src.common.a2a_client.A2AClient") as MockA2AClient:
        mock_a2a_instance = MockA2AClient.return_value
        mock_a2a_instance.send_message = AsyncMock(return_value=mock_response_obj)

        # Test valid route
        response = await call_remote_agent("gourmet", "Hello")
        assert response == "Hello from agent"


@pytest.mark.asyncio
async def test_call_remote_agent_not_found():
    response = await call_remote_agent("invalid_route", "Hello")
    assert "non trouvé" in response


# A2A Server Tests
def test_create_a2a_app():
    mock_agent = MagicMock()
    app = create_a2a_app(
        agent=mock_agent,
        agent_name="test_agent",
        agent_description="Test Description",
        skills=[],
        public_url="http://test",
    )
    assert app is not None
    # Verify it has routes
    assert hasattr(app, "router")
    # Verify routes exist (FastAPI uses .routes on the app object)
    assert len(app.routes) > 0


# test_adk_executor_execute removed as ADKAgentExecutor is deprecated/removed in Lean version.
