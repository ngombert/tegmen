import pytest
from fastapi.testclient import TestClient
from agent_maestro.main import app, FALLBACK_RESPONSES, get_request_context, warmup
from common.agent_registry import agent_registry
from common.schemas import RequestContext
import httpx

client = TestClient(app)

def override_get_request_context():
    return RequestContext(
        family_id="test_family",
        user_id="test_user",
        user_name="Test User",
        role="parent",
        correlation_id="test-correlation",
        preferences={},
        restrictions=[]
    )

app.dependency_overrides[get_request_context] = override_get_request_context

@pytest.mark.asyncio
async def test_maestro_graceful_timeout(httpx_mock):
    """
    Vérifie que Maestro retourne un message convivial en cas de timeout d'un agent.
    """
    # 1. Configurer un agent qui va timeout
    agent_name = "gourmet"
    agent_url = "http://localhost:8001"
    # On fournit des utterances pour que le routeur sémantique le reconnaisse
    agent_registry.register_agent(
        agent_name, 
        agent_url, 
        utterances=["Qu'est-ce qu'on mange ce soir ?", "recette de cuisine"]
    )
    warmup() # Re-init router with new utterances
    
    # 2. Mocker le timeout du transport A2A
    httpx_mock.add_exception(httpx.TimeoutException("Slow agent"), url=f"{agent_url}/a2a/SendMessage")
    
    # 3. Appeler Maestro (on simule une requête qui route vers gourmet)
    # Note: On utilise l'endpoint A2A de Maestro pour tester le routage
    payload = {
        "jsonrpc": "2.0",
        "method": "SendMessage",
        "params": {"message": "Qu'est-ce qu'on mange ce soir ?"}, # Route vers gourmet
        "id": "test-id-123"
    }
    
    # On doit mocker l'authentification si nécessaire, 
    # mais ici on va juste vérifier la réponse si on arrive au dispatch
    # Comme TestClient est synchrone, on utilise app.post directement
    response = client.post("/api/v1/routing", json=payload, headers={"Authorization": "Bearer fake-token"})
    
    # 4. Vérifier la réponse
    assert response.status_code == 200
    data = response.json()
    assert "result" in data
    assert data["result"]["message"] in FALLBACK_RESPONSES
    assert data["result"]["agent"] == "maestro"
    assert data["id"] == "test-id-123"
