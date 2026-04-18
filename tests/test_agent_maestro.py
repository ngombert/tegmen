from unittest.mock import patch, AsyncMock, MagicMock

# Mock semantic_router components to avoid loading heavy models during unit tests
# We must do this before importing the app
with (
    patch("src.agent_maestro.router.HuggingFaceEncoder"),
    patch("src.agent_maestro.router.SemanticRouter") as MockRouter,
):
    # Setup mock router to be callable
    mock_router_instance = MagicMock()
    MockRouter.return_value = mock_router_instance
    # When router(message) is called, it returns a result object with a .name attribute
    mock_route_result = MagicMock()
    mock_route_result.name = "gourmet"
    mock_router_instance.return_value = mock_route_result

    from src.agent_maestro.main import app

from fastapi.testclient import TestClient

client = TestClient(app)


def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200


@patch("src.agent_maestro.main.classify_intent")
def test_chat_routing_gourmet(mock_classify):
    mock_classify.return_value = "gourmet"

    # Mock specific internal logic depending on mode
    # Test Monolith mode (default) logic
    # We mock get_agent and Runner/session_service to avoid complex local agent setup
    with (
        patch("src.agent_maestro.main.MICROSERVICES_MODE", False),
        patch("src.agent_maestro.agents.get_agent") as mock_get_agent,
    ):
        mock_agent = MagicMock()
        mock_agent.name = "agent_gourmet"
        mock_get_agent.return_value = mock_agent

        response = client.post("/chat", json={"message": "Je veux des pâtes"})

        assert response.status_code == 200
        data = response.json()
        assert data["agent"] == "agent_gourmet"
        assert data["route"] == "gourmet"
        assert "réessayer" in data["message"]


@patch("src.agent_maestro.main.classify_intent")
@patch("src.agent_maestro.main.call_remote_agent")
def test_chat_microservices_gourmet(mock_call_remote, mock_classify):
    mock_classify.return_value = "gourmet"
    mock_call_remote.return_value = "Remote pasta recipe"

    # Set MICROSERVICES_MODE to True
    with patch("src.agent_maestro.main.MICROSERVICES_MODE", True):
        response = client.post("/chat", json={"message": "Je veux des pâtes"})

        assert response.status_code == 200
        data = response.json()
        assert data["agent"] == "agent_gourmet"
        assert data["route"] == "gourmet"
        assert data["message"] == "Remote pasta recipe"
        mock_call_remote.assert_called_once()


@patch("src.agent_maestro.main.classify_intent")
def test_chat_unknown_intent(mock_classify):
    mock_classify.return_value = "unknown"

    with (
        patch("src.agent_maestro.main.MICROSERVICES_MODE", False),
        patch("src.agent_maestro.agents.get_agent") as mock_get_agent,
    ):
        mock_agent = MagicMock()
        mock_agent.name = "agent_unknown"
        mock_get_agent.return_value = mock_agent

        response = client.post("/chat", json={"message": "blabla"})

        assert response.status_code == 200
        data = response.json()
        assert data["route"] == "unknown"
        assert "réessayer" in data["message"]


def test_routes_list():
    response = client.get("/routes")
    assert response.status_code == 200
    data = response.json()
    assert "routes" in data
    assert len(data["routes"]) >= 4
