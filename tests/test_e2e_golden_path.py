import pytest
import httpx
import asyncio
import os
import uuid

# Configuration des URLs (utilisant localhost pour le test hors-container)
MAESTRO_URL = os.getenv("MAESTRO_URL", "http://localhost:8000")
GOURMET_URL = os.getenv("GOURMET_URL", "http://localhost:8001")

@pytest.fixture
async def auth_headers():
    """Obtains a JWT token for testing."""
    async with httpx.AsyncClient() as client:
        # Get token for mock parent user
        response = await client.get(f"{MAESTRO_URL}/dev/token/user-parent-1")
        if response.status_code != 200:
            pytest.fail(f"Impossible d'obtenir un token de test: {response.text}")
        
        token = response.json()["access_token"]
        return {"Authorization": f"Bearer {token}"}

@pytest.mark.asyncio
async def test_e2e_gourmet_search_flow(auth_headers):
    """
    Scénario Golden Path:
    1. L'utilisateur demande une recette via le Gateway (Maestro).
    2. Maestro classifie l'intention comme 'gourmet'.
    3. Maestro appelle Gourmet via A2A (message/send).
    4. Gourmet répond avec une structure 'Message' valide.
    5. Maestro renvoie la réponse au client.
    """
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        # 1. Vérification de la disponibilité des services
        try:
            health = await client.get(f"{MAESTRO_URL}/health")
            assert health.status_code == 200, "Maestro doit être disponible"
        except Exception as e:
            pytest.fail(f"Maestro non joignable sur {MAESTRO_URL}: {e}")

        # 2. Envoi d'une requête de recherche (Format JSON-RPC utilisé par le Frontend)
        payload = {
            "jsonrpc": "2.0",
            "method": "message/send",
            "params": {
                "message": "Je cherche une recette de pâtes carbonara",
                "debug": True
            },
            "id": str(uuid.uuid4())
        }

        print(f"\n[E2E] Envoi de la requête à Maestro: {payload['params']['message']}")
        
        response = await client.post(f"{MAESTRO_URL}/api/v1/routing", json=payload, headers=auth_headers)
        
        # 3. Validation de la réponse technique
        assert response.status_code == 200, f"Erreur HTTP: {response.status_code}"
        data = response.json()
        
        assert "result" in data, f"Erreur JSON-RPC: {data.get('error')}"
        result = data["result"]
        
        # 4. Validation de la logique métier (Routing)
        assert result["route"] == "gourmet", f"Mauvais routage: {result['route']}"
        assert result["agent"] == "agent_gourmet"
        
        # 5. Validation du contenu (Preuve que Gourmet a travaillé)
        message_text = result["message"].lower()
        assert "carbonara" in message_text or "trouvé" in message_text, "La réponse ne semble pas pertinente"
        
        print(f"[E2E] Succès ! Agent utilisé: {result['agent']}, Message: {result['message'][:50]}...")

@pytest.mark.asyncio
async def test_e2e_error_handling_invalid_route(auth_headers):
    """Vérifie que Maestro gère correctement les intentions inconnues."""
    async with httpx.AsyncClient(timeout=10.0) as client:
        payload = {
            "jsonrpc": "2.0",
            "method": "message/send",
            "params": {
                "message": "Quel est le sens de la vie ?",
            },
            "id": "test-error"
        }
        
        response = await client.post(f"{MAESTRO_URL}/api/v1/routing", json=payload, headers=auth_headers)
        data = response.json()
        
        # Maestro doit répondre avec un fallback ou un agent par défaut, pas une erreur 500
        assert response.status_code == 200
        assert "result" in data
