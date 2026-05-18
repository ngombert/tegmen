# Story 1.2 : Recherche de Recettes Basique

## Metadata

- **Status:** ready-for-dev
- **Epic:** 1 — Recherche et Découverte de Recettes
- **Story ID:** 1.2
- **Story Key:** `1-2-recherche-de-recettes-basique`
- **Created:** 2026-05-02
- **Sprint Status File:** `_bmad-output/implementation-artifacts/sprint-status-agent-gourmet.yaml`

---

## User Story

**As a** famille utilisant Tegmen,
**I want** pouvoir chercher des recettes par mots-clés ou ingrédients,
**So that** je puisse trouver des idées de repas rapidement.

---

## Acceptance Criteria

**AC1 — Recherche fonctionnelle (FR1)**
> **Given** une base de recettes en mémoire (mock `RECIPES_DB`)
> **When** Maestro envoie une requête `search_recipes` avec un mot-clé
> **Then** Gourmet retourne une liste de recettes correspondantes avec les champs `id`, `name`, `tags`, `prep_time`
> **And** la recherche fonctionne à la fois par **nom de recette** (ex: "carbonara") et par **nom d'ingrédient** (ex: "pecorino")

**AC2 — Réponse typage Pydantic strict (NFR-INT-1)**
> **And** le retour est un objet `SearchResponse` (Pydantic strict) avec les champs `results: list[RecipeBase]` et `total_count: int`

**AC3 — Aucun résultat (FR6)**
> **When** aucune recette ne correspond à la requête
> **Then** la réponse est un payload structuré explicite : `{"results": [], "total_count": 0}`
> **And** aucune exception n'est levée

**AC4 — Tests zéro réseau**
> **And** les scénarios nominaux et d'absence de résultats sont couverts par des tests `pytest-asyncio` sans aucun I/O réseau

---

## ⚠️ Contexte Critique : Travail déjà effectué en Story 1.1

> [!IMPORTANT]
> La fondation de la Story 1.2 a été **partiellement implémentée** lors de la Story 1.1 pour établir le squelette fonctionnel de l'agent. Le développeur **NE DOIT PAS réimplémenter** ce qui existe déjà.

**Ce qui est DÉJÀ implémenté (ne pas toucher) :**
- `src/agent_gourmet/app/schemas/recipe.py` : `SearchRequest`, `SearchResponse`, `RecipeBase` avec `ConfigDict(strict=True)` ✅
- `src/agent_gourmet/app/services/recipe_service.py` : `RecipeService.search_recipes(request: SearchRequest) -> SearchResponse` ✅
- `src/agent_gourmet/app/api/routers/a2a.py` : handler `handle_search_recipes` enregistré sous la méthode JSON-RPC `search_recipes` ✅
- `src/agent_gourmet/RECIPES_DB` : 4 recettes de démonstration avec ingrédients structurés ✅

**Ce qu'il RESTE à faire pour valider les ACs :**
1. **Vérifier** que la recherche par ingrédient est bien fonctionnelle dans `recipe_service.py`
2. **Compléter** les tests existants (`tests/agent_gourmet/test_gourmet_service.py`) avec les cas manquants (recherche par ingrédient, zéro résultat)
3. **Ajouter** un test d'intégration A2A pour le retour `total_count: 0` via `test_gourmet_a2a.py`

---

## Tasks / Subtasks

- [x] Task 1 : Vérifier et compléter la logique de `recipe_service.py` (AC: #1, #2)
  - [x] Vérifier que `search_recipes()` cherche bien dans `ing.name.lower()` pour la recherche par ingrédient
  - [x] Vérifier que le retour `SearchResponse(results=[], total_count=0)` est correct quand aucun résultat

- [x] Task 2 : Compléter les tests de service (AC: #1, #3, #4)
  - [x] Ajouter `test_search_recipes_by_ingredient()` : chercher "pecorino" → retourne Carbonara
  - [x] Ajouter `test_search_recipes_empty_result()` : chercher "xyzzy" → retourne `{results: [], total_count: 0}`
  - [x] Ajouter `test_search_recipes_combined()` : chercher par tag + query → résultat filtré correct

- [x] Task 3 : Compléter les tests d'intégration A2A (AC: #2, #3, #4)
  - [x] Ajouter `test_a2a_search_empty_result()` : appel JSON-RPC `search_recipes` avec query introuvable → `result.total_count == 0`
  - [x] Ajouter `test_a2a_search_by_ingredient()` : appel JSON-RPC `search_recipes` avec query ingrédient → `result.total_count >= 1`
  - [x] Ajouter `test_a2a_search_invalid_params()` : params invalides (ex: `query: 123`) → `error` dans la réponse JSON-RPC (validation Pydantic strict)

- [x] Task 4 : Validation finale
  - [x] Exécuter `OTEL_ENABLED=false PYTHONPATH=src uv run pytest tests/agent_gourmet/`
  - [x] Exécuter `OTEL_ENABLED=false PYTHONPATH=src uv run pytest` (suite complète — zéro régression)

---

## Dev Notes

### Stack Technique

- Python 3.13+ strict (`X | None`, `list[X]`, jamais `Optional`, `List`)
- FastAPI + Pydantic v2 avec `ConfigDict(strict=True)`
- `pytest-asyncio` en mode `asyncio_mode="auto"` (configuré dans `pyproject.toml`)
- Tests avec `starlette.testclient.TestClient` pour les tests d'intégration A2A

### Chemins des fichiers clés

| Fichier | Rôle |
|---------|------|
| `src/agent_gourmet/app/schemas/recipe.py` | Schémas Pydantic `SearchRequest`, `SearchResponse`, `RecipeBase` |
| `src/agent_gourmet/app/services/recipe_service.py` | Logique métier `RecipeService.search_recipes()` |
| `src/agent_gourmet/app/api/routers/a2a.py` | Handler `handle_search_recipes`, dict `GOURMET_METHODS` |
| `src/agent_gourmet/main.py` | App FastAPI, mount du serveur A2A |
| `tests/agent_gourmet/test_gourmet_service.py` | Tests du service async |
| `tests/agent_gourmet/test_gourmet_a2a.py` | Tests d'intégration A2A via `TestClient` |
| `tests/agent_gourmet/test_gourmet_schemas.py` | Tests des schémas Pydantic |

### Patterns établis en Story 1.1

**Test de service (asyncio) :**
```python
@pytest.mark.asyncio
async def test_search_recipes_by_ingredient(service):
    request = SearchRequest(query="pecorino")
    response = await service.search_recipes(request)
    assert response.total_count >= 1
    assert any("carbonara" in r.name.lower() for r in response.results)
```

**Test d'intégration A2A (TestClient) :**
```python
def test_a2a_search_empty_result(client):
    payload = {
        "jsonrpc": "2.0",
        "method": "search_recipes",
        "params": {"query": "xyzzy_introuvable"},
        "id": "test-empty"
    }
    response = client.post("/a2a/SendMessage", json=payload)
    data = response.json()
    assert data["result"]["total_count"] == 0
    assert data["result"]["results"] == []
```

**Test paramètres invalides (strict Pydantic) :**
```python
def test_a2a_search_invalid_params(client):
    payload = {
        "jsonrpc": "2.0",
        "method": "search_recipes",
        "params": {"query": 123},  # doit échouer : strict=True sur SearchRequest
        "id": "test-invalid"
    }
    response = client.post("/a2a/SendMessage", json=payload)
    data = response.json()
    # Doit retourner une erreur (validation Pydantic) et non un résultat
    assert "error" in data or data.get("result") is None
```

### Lancer les tests

```bash
# Tests du module Gourmet uniquement
OTEL_ENABLED=false PYTHONPATH=src uv run pytest tests/agent_gourmet/ -v

# Suite complète (anti-régression)
OTEL_ENABLED=false PYTHONPATH=src uv run pytest
```

> [!NOTE]
> La variable `OTEL_ENABLED=false` est requise en CI pour éviter les erreurs de connexion OpenTelemetry lors des tests.

### Note sur RECIPES_DB

La base de données mock contient 4 recettes : Pâtes Carbonara (id=1), Poulet Rôti (id=2), Salade César (id=3), Ratatouille (id=4). La recherche par ingrédient fonctionne sur `ing.name.lower()`. La migration vers une vraie base de données est **hors scope MVP** (voir NFR-PERF-1 qui s'adressera en Story 1.3 ou Epic 3).
