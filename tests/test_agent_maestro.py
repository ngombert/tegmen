import jwt
from unittest.mock import patch, AsyncMock, MagicMock
from common.config import config

# Mock semantic_router components to avoid loading heavy models during unit tests
# We must do this before importing the app
with (
    patch("agent_maestro.router.HuggingFaceEncoder"),
    patch("agent_maestro.router.SemanticRouter") as MockRouter,
):
    # Setup mock router to be callable
    mock_router_instance = MagicMock()
    MockRouter.return_value = mock_router_instance
    # When router(message) is called, it returns a result object with a .name attribute
    mock_route_result = MagicMock()
    mock_route_result.name = "gourmet"
    mock_router_instance.return_value = mock_route_result

    from agent_maestro.main import app

from fastapi.testclient import TestClient

client = TestClient(app)

def get_auth_headers():
    token = jwt.encode(
        {"family_id": "test-family", "user_id": "test-user"},
        config.JWT_SECRET,
        algorithm=config.JWT_ALGORITHM
    )
    return {"Authorization": f"Bearer {token}"}


def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200


@patch("agent_maestro.main.classify_intent")
@patch("agent_maestro.main.call_remote_agent")
def test_chat_routing_gourmet(mock_call_remote, mock_classify):
    mock_classify.return_value = "gourmet"
    mock_call_remote.return_value = "Mocked gourmet response"

    response = client.post(
        "/chat", 
        json={"message": "Je veux des pâtes"},
        headers=get_auth_headers()
    )

    assert response.status_code == 200
    data = response.json()
    assert data["agent"] == "agent_gourmet"
    assert data["route"] == "gourmet"
    assert data["message"] == "Mocked gourmet response"


@patch("agent_maestro.main.classify_intent")
@patch("agent_maestro.main.call_remote_agent")
def test_chat_remote_error(mock_call_remote, mock_classify):
    mock_classify.return_value = "gourmet"
    mock_call_remote.side_effect = Exception("Remote failure")

    response = client.post(
        "/chat", 
        json={"message": "Je veux des pâtes"},
        headers=get_auth_headers()
    )

    assert response.status_code == 500
    assert "Remote failure" in response.json()["detail"]


@patch("agent_maestro.main.classify_intent")
def test_chat_unknown_intent(mock_classify):
    mock_classify.return_value = "unknown"

    response = client.post(
        "/chat", 
        json={"message": "blabla"},
        headers=get_auth_headers()
    )

    assert response.status_code == 200
    data = response.json()
    assert data["route"] == "unknown"
    assert "réessayer" in data["message"]


def test_chat_unauthorized():
    response = client.post("/chat", json={"message": "No token"})
    assert response.status_code == 401
    assert "Authentification requise" in response.json()["detail"]


def test_routes_list():
    response = client.get("/routes")
    assert response.status_code == 200
    data = response.json()
    assert "agents" in data
    assert len(data["agents"]) >= 3
