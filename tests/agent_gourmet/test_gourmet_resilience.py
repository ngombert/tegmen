"""
Tests de résilience pour l'Agent Gourmet — Story 3.1.

Couvre :
- AC1 : Timeout via asyncio.wait_for quand la persistance dépasse 3000ms
- AC2 : Chaos delay via GOURMET_ARTIFICIAL_DELAY_MS
- AC3 : Démarrage à froid < 3s (lifespan)
- AC4 : 5 requêtes concurrentes sans blocage (asyncio.gather)
- AC5 : Configuration externalisée (settings)
- Intégration A2A : réponse JSON-RPC avec code -32000 en cas de timeout
"""

import asyncio
import time

import pytest
from fastapi.testclient import TestClient

from agent_gourmet.app.schemas.recipe import SearchRequest
from agent_gourmet.app.services.recipe_service import RecipeService
from agent_gourmet.main import app
from common.exceptions import A2ARPCError


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def service() -> RecipeService:
    return RecipeService()


@pytest.fixture
def client():
    return TestClient(app)


# ---------------------------------------------------------------------------
# Task 3 — Tests de Timeout (AC1, AC2)
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_timeout_triggers_error(service: RecipeService, monkeypatch) -> None:
    """AC1+AC2 : Un délai artificiel > timeout doit lever A2ARPCError(TIMEOUT)."""
    import common.config as cfg

    monkeypatch.setattr(cfg.config, "GOURMET_ARTIFICIAL_DELAY_MS", 4000)
    monkeypatch.setattr(cfg.config, "GOURMET_PERSISTENCE_TIMEOUT_MS", 100)

    with pytest.raises(A2ARPCError) as exc:
        await service.search_recipes(SearchRequest(query=""))

    assert exc.value.code == A2ARPCError.TIMEOUT
    assert exc.value.data == {"timeout_ms": 100}
    assert "persistance" in exc.value.message.lower()


@pytest.mark.asyncio
async def test_timeout_under_threshold(service: RecipeService, monkeypatch) -> None:
    """AC2 : Un délai artificiel < timeout ne doit PAS déclencher d'erreur."""
    import common.config as cfg

    monkeypatch.setattr(cfg.config, "GOURMET_ARTIFICIAL_DELAY_MS", 50)
    monkeypatch.setattr(cfg.config, "GOURMET_PERSISTENCE_TIMEOUT_MS", 3000)

    response = await service.search_recipes(SearchRequest(query=""))
    assert response.total_count == 4


@pytest.mark.asyncio
async def test_timeout_respects_config_timing(service: RecipeService, monkeypatch) -> None:
    """AC1 : Le timeout se déclenche en moins de timeout_ms + 500ms (marge de tolérance CI)."""
    import common.config as cfg

    timeout_ms = 200
    monkeypatch.setattr(cfg.config, "GOURMET_ARTIFICIAL_DELAY_MS", 5000)
    monkeypatch.setattr(cfg.config, "GOURMET_PERSISTENCE_TIMEOUT_MS", timeout_ms)

    start = time.monotonic()
    with pytest.raises(A2ARPCError) as exc:
        await service.search_recipes(SearchRequest(query=""))
    elapsed_ms = (time.monotonic() - start) * 1000

    assert exc.value.code == A2ARPCError.TIMEOUT
    # Doit se déclencher en moins de timeout_ms + 500ms (marge CI)
    assert elapsed_ms < timeout_ms + 500, f"Timeout trop lent : {elapsed_ms:.0f}ms"


@pytest.mark.asyncio
async def test_timeout_on_get_recipe_details(service: RecipeService, monkeypatch) -> None:
    """AC1 : get_recipe_details est aussi protégé par le timeout."""
    import common.config as cfg

    monkeypatch.setattr(cfg.config, "GOURMET_ARTIFICIAL_DELAY_MS", 4000)
    monkeypatch.setattr(cfg.config, "GOURMET_PERSISTENCE_TIMEOUT_MS", 100)

    with pytest.raises(A2ARPCError) as exc:
        await service.get_recipe_details("1")

    assert exc.value.code == A2ARPCError.TIMEOUT


@pytest.mark.asyncio
async def test_no_delay_by_default(service: RecipeService, monkeypatch) -> None:
    """AC5 : Sans chaos delay, la réponse est immédiate (délai artificiel = 0 par défaut)."""
    import common.config as cfg

    monkeypatch.setattr(cfg.config, "GOURMET_ARTIFICIAL_DELAY_MS", 0)
    monkeypatch.setattr(cfg.config, "GOURMET_PERSISTENCE_TIMEOUT_MS", 3000)

    response = await service.get_recipe_details("1")
    assert response.id == "1"


# ---------------------------------------------------------------------------
# Task 4 — Tests de Concurrence (AC4)
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_concurrent_requests_no_blocking(service: RecipeService, monkeypatch) -> None:
    """AC4 : 5 requêtes concurrentes via asyncio.gather sans blocage."""
    import common.config as cfg

    monkeypatch.setattr(cfg.config, "GOURMET_ARTIFICIAL_DELAY_MS", 0)
    monkeypatch.setattr(cfg.config, "GOURMET_PERSISTENCE_TIMEOUT_MS", 3000)

    requests = [service.search_recipes(SearchRequest(query="")) for _ in range(5)]
    results = await asyncio.gather(*requests)

    assert len(results) == 5
    assert all(r.total_count == 4 for r in results)


@pytest.mark.asyncio
async def test_concurrent_mixed_requests(service: RecipeService, monkeypatch) -> None:
    """AC4 : Mélange de search + get_details en concurrence."""
    import common.config as cfg

    monkeypatch.setattr(cfg.config, "GOURMET_ARTIFICIAL_DELAY_MS", 0)
    monkeypatch.setattr(cfg.config, "GOURMET_PERSISTENCE_TIMEOUT_MS", 3000)

    tasks = [
        service.search_recipes(SearchRequest(query="carbonara")),
        service.get_recipe_details("1"),
        service.search_recipes(SearchRequest(query="poulet")),
        service.get_recipe_details("2"),
        service.search_recipes(SearchRequest(query="")),
    ]
    results = await asyncio.gather(*tasks)
    assert len(results) == 5


# ---------------------------------------------------------------------------
# Task 5 — Test de Démarrage à Froid (AC3)
# ---------------------------------------------------------------------------

def test_cold_start_under_3s() -> None:
    """AC3 : Le lifespan FastAPI démarre en moins de 3 secondes."""
    start = time.monotonic()
    with TestClient(app) as client:
        elapsed = time.monotonic() - start
        assert elapsed < 3.0, f"Démarrage trop lent : {elapsed:.2f}s"
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "ok"


def test_health_after_startup(client) -> None:
    """AC3 : /health retourne ok immédiatement après le démarrage."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["agent"] == "gourmet"


# ---------------------------------------------------------------------------
# Task 6 — Intégration A2A : Timeout comme JsonRpcResponse (AC1)
# ---------------------------------------------------------------------------

def test_a2a_timeout_error_response(monkeypatch) -> None:
    """AC1 : En cas de timeout, l'endpoint A2A retourne une JsonRpcResponse avec error code -32000."""
    import common.config as cfg

    monkeypatch.setattr(cfg.config, "GOURMET_ARTIFICIAL_DELAY_MS", 4000)
    monkeypatch.setattr(cfg.config, "GOURMET_PERSISTENCE_TIMEOUT_MS", 100)

    with TestClient(app) as client:
        payload = {
            "jsonrpc": "2.0",
            "method": "search_recipes",
            "params": {"query": ""},
            "id": "test-timeout-a2a",
        }
        response = client.post("/a2a/SendMessage", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert "error" in data
        assert data["error"]["code"] == A2ARPCError.TIMEOUT  # -32000
        assert data["error"]["data"]["timeout_ms"] == 100


def test_a2a_no_timeout_with_default_config(monkeypatch) -> None:
    """AC5 : Avec config par défaut (pas de chaos delay), les requêtes A2A réussissent."""
    import common.config as cfg

    monkeypatch.setattr(cfg.config, "GOURMET_ARTIFICIAL_DELAY_MS", 0)
    monkeypatch.setattr(cfg.config, "GOURMET_PERSISTENCE_TIMEOUT_MS", 3000)

    with TestClient(app) as client:
        payload = {
            "jsonrpc": "2.0",
            "method": "search_recipes",
            "params": {"query": "carbonara"},
            "id": "test-no-timeout",
        }
        response = client.post("/a2a/SendMessage", json=payload)
        data = response.json()
        assert "result" in data
        assert data["result"]["total_count"] == 1
