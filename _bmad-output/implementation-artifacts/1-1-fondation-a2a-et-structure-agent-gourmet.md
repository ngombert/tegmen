# Story 1.1: Fondation A2A et Structure Agent Gourmet

Status: in-progress

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a développeur Tegmen,
I want que l'Agent Gourmet soit restructuré selon l'architecture standardisée et que le serveur A2A dispatch correctement les requêtes,
So that les futurs endpoints Gourmet soient opérationnels de bout en bout via le protocole A2A.

## Acceptance Criteria

1. **Structure `app/`** : Le module `agent_gourmet/` est réorganisé en `app/schemas/`, `app/services/`, `app/api/` avec des imports fonctionnels. Les fichiers historiques (`tools.py`, `agent.py`) sont migrés vers la nouvelle arborescence.
2. **Pydantic Strict** : Tous les modèles Pydantic utilisent `ConfigDict(strict=True)` et le typage Python 3.13+ (`list`, `dict`, `X | None` — interdiction de `typing.List`, `typing.Optional`).
3. **Correction `a2a_server.py`** : `common/a2a_server.py` dispatch la méthode `message/send` vers les handlers enregistrés par Gourmet (correction rétro-compatible — Maestro ne doit pas casser).
4. **Correction `a2a_client.py`** : `common/a2a_client.py` accepte un paramètre optionnel `context: RequestContext | None = None` dans `send_message()` et `call_remote_agent()` pour la propagation du contexte (rétro-compatible — le paramètre est optionnel avec défaut `None`).
5. **Test A2A** : Un test d'intégration A2A automatisé (`pytest-asyncio`, sans réseau) valide le flux requête JSON-RPC → `A2AServer.handle_request` → handler Gourmet → réponse structurée.
6. **Régression zéro** : Les 84 tests existants passent sans régression.
7. **FR15 — Agent Card** : L'endpoint `/a2a/AgentCard` retourne les métadonnées enrichies de l'agent (skills avec description exhaustive, version, URL).
8. **FR16 — Rejet validation** : Une requête JSON-RPC mal formée est rejetée avec une erreur Pydantic structurée (`JsonRpcResponse` avec `JsonRpcError`).

## Tasks / Subtasks

- [x] Task 1 : Créer la structure de dossiers `app/` dans `agent_gourmet/` (AC: #1)
  - [x] Créer `src/agent_gourmet/app/__init__.py`
  - [x] Créer `src/agent_gourmet/app/schemas/__init__.py`
  - [x] Créer `src/agent_gourmet/app/services/__init__.py`
  - [x] Créer `src/agent_gourmet/app/api/__init__.py`
  - [x] Créer `src/agent_gourmet/app/api/routers/__init__.py`

- [x] Task 2 : Migrer les schémas Pydantic dans `app/schemas/` (AC: #1, #2)
  - [x] Créer `src/agent_gourmet/app/schemas/recipe.py` — Modèles Pydantic stricts pour les recettes
  - [x] Définir `RecipeBase` avec `ConfigDict(strict=True)` : `id: str`, `name: str`, `tags: list[str]`, `prep_time: int`
  - [x] Définir `Ingredient` : `name: str`, `quantity: str | None = None`, `unit: str | None = None`
  - [x] Définir `RecipeDetail(RecipeBase)` : `ingredients: list[Ingredient]`, `steps: list[str]`, `servings: int | None = None`, `difficulty: str | None = None`
  - [x] Définir `SearchRequest` avec `ConfigDict(strict=True)` : `query: str = ""`, `tag: str | None = None`
  - [x] Définir `SearchResponse` avec `ConfigDict(strict=True)` : `results: list[RecipeBase]`, `total_count: int`

- [x] Task 3 : Migrer la logique métier dans `app/services/` (AC: #1, #2)
  - [x] Créer `src/agent_gourmet/app/services/recipe_service.py`
  - [x] Migrer `RECIPES_DB` depuis `tools.py` — enrichir chaque recette avec `servings`, `difficulty` et des `Ingredient` structurés
  - [x] Convertir `search_recipes()` en `async def search_recipes(request: SearchRequest) -> SearchResponse`
  - [x] Convertir `get_recipe_details()` en `async def get_recipe_details(recipe_id: str) -> RecipeDetail`
  - [x] Lever `A2ARPCError(code=RECIPE_NOT_FOUND, ...)` au lieu de retourner `{"error": "..."}` — définir `RECIPE_NOT_FOUND = -32010` dans `common/exceptions.py`

- [x] Task 4 : Enregistrer les handlers A2A dans le routeur (AC: #1, #3, #5)
  - [x] Créer `src/agent_gourmet/app/api/routers/a2a.py`
  - [x] Enregistrer les méthodes `search_recipes` et `get_recipe_details` sur l'instance `A2AServer`
  - [x] Chaque handler doit extraire les paramètres du `dict params` → valider via le schéma Pydantic → appeler le service → retourner le résultat sérialisé

- [x] Task 5 : Mettre à jour `main.py` (AC: #1, #7, #8)
  - [x] Refactoriser `main.py` pour importer depuis `app/` au lieu de `tools.py` / `agent.py`
  - [x] Enregistrer les handlers du routeur A2A sur l'`A2AServer`
  - [x] Enrichir les métadonnées de skill dans l'Agent Card avec des docstrings exhaustives (FR15)
  - [x] Supprimer l'import et la dépendance à `google.adk` / `LlmAgent` (le module Gourmet devient Lean)

- [x] Task 6 : Corriger `common/a2a_server.py` — dispatch `message/send` (AC: #3)
  - [x] Ajouter la méthode `message/send` dans le dispatch du `A2AServer` (actuellement seul l'endpoint POST existe mais aucun handler agent n'est connecté)
  - [x] Vérifier que la correction est rétro-compatible (Maestro continue de fonctionner)
  - [x] Le handler `message/send` doit extraire le texte du message, identifier la méthode métier, et dispatcher

- [x] Task 7 : Corriger `common/a2a_client.py` — propagation `RequestContext` (AC: #4)
  - [x] Ajouter le paramètre `context: RequestContext | None = None` à `RemoteAgentClient.send_message()`
  - [x] Ajouter le paramètre `context: RequestContext | None = None` à `call_remote_agent()`
  - [x] Si `context` est fourni, l'inclure dans les `params` de la requête JSON-RPC
  - [x] Vérifier que les appels existants de Maestro (sans `context`) continuent de fonctionner

- [x] Task 8 : Ajouter le code d'erreur domaine dans `common/exceptions.py` (AC: #2)
  - [x] Ajouter `RECIPE_NOT_FOUND = -32010` à `A2ARPCError`

- [x] Task 9 : Mettre à jour `agent_gourmet/__init__.py` (AC: #1)
  - [x] Adapter les exports pour la nouvelle structure (supprimer l'import de `agent.py` si supprimé)

- [x] Task 10 : Écrire les tests automatisés (AC: #5, #6, #7, #8)
  - [x] Créer `tests/agent_gourmet/` si absent, avec `__init__.py`
  - [x] Test : `SearchRequest` Pydantic valide et rejette les types invalides
  - [x] Test : `RecipeDetail` Pydantic valide et rejette les types invalides
  - [x] Test : `search_recipes()` retourne un `SearchResponse` structuré
  - [x] Test : `search_recipes()` avec aucun résultat retourne `results: [], total_count: 0` (FR6)
  - [x] Test : `get_recipe_details()` avec un ID valide retourne un `RecipeDetail`
  - [x] Test : `get_recipe_details()` avec un ID inexistant lève `A2ARPCError(RECIPE_NOT_FOUND)`
  - [x] Test : Flux A2A complet — `JsonRpcRequest` → `A2AServer.handle_request()` → handler → `JsonRpcResponse` avec résultat
  - [x] Test : Requête JSON-RPC mal formée → `JsonRpcResponse` avec `JsonRpcError` (FR16)
  - [x] Test : `/a2a/AgentCard` retourne les métadonnées correctes (FR15)
  - [x] Vérifier que les 84 tests existants passent toujours

- [x] Task 11 : Nettoyage (AC: #1)
  - [x] Supprimer `src/agent_gourmet/tools.py` (migré vers `app/services/recipe_service.py`)
  - [x] Supprimer `src/agent_gourmet/agent.py` (dépendance ADK supprimée)
  - [x] Mettre à jour les imports dans les anciens tests (`test_agent_gourmet.py`, `test_agent_gourmet_tools.py`, `test_gourmet_tools.py`) pour pointer vers la nouvelle structure, ou les migrer dans `tests/agent_gourmet/`

## Dev Notes

### Contexte Brownfield Critique

Le module `src/agent_gourmet/` existe déjà avec une structure flat héritée de la phase prototype :

```
src/agent_gourmet/           # ÉTAT ACTUEL (flat, avec ADK)
├── __init__.py              # Exporte agent, get_agent depuis agent.py
├── agent.py                 # LlmAgent ADK (google.adk) — À SUPPRIMER
├── instruction.md           # Prompt LLM — CONSERVER tel quel
├── main.py                  # FastAPI + mount A2A — À REFACTORISER
├── tools.py                 # Fonctions sync, retours dict bruts — À MIGRER
└── Dockerfile               # NE PAS TOUCHER
```

**Structure cible** (conforme à l'architecture) :

```
src/agent_gourmet/
├── __init__.py              # MODIFIER — nouveaux exports
├── instruction.md           # CONSERVER — prompt LLM
├── main.py                  # MODIFIER — imports depuis app/
├── Dockerfile               # NE PAS TOUCHER
└── app/
    ├── __init__.py
    ├── schemas/
    │   ├── __init__.py
    │   └── recipe.py        # NOUVEAU — RecipeBase, RecipeDetail, SearchRequest, SearchResponse, Ingredient
    ├── services/
    │   ├── __init__.py
    │   └── recipe_service.py # NOUVEAU — logique métier async, RECIPES_DB migré
    └── api/
        ├── __init__.py
        └── routers/
            ├── __init__.py
            └── a2a.py       # NOUVEAU — handlers A2A enregistrés sur A2AServer
```

### Problème Critique dans `a2a_server.py` — Dispatch Non Connecté

**BUG IDENTIFIÉ** : Le `A2AServer` dans `common/a2a_server.py` expose un endpoint POST `/a2a/SendMessage` qui appelle `server.handle_request()`, mais **aucun handler métier n'est enregistré** via `server.register_method()`. Le `create_a2a_app()` crée un serveur vide — les agents individuels n'appellent jamais `register_method()`.

**Conséquence** : Toute requête A2A reçue par Gourmet retournera systématiquement `Method 'xxx' not found`.

**Correction** : Le `main.py` de Gourmet doit enregistrer ses handlers sur l'instance `A2AServer` retournée par `create_a2a_app()`. Deux options :
1. Exposer le `server` depuis le retour de `create_a2a_app()` (retourner un tuple `(app, server)`)
2. Ajouter un mécanisme de callback dans `create_a2a_app()` pour enregistrer les méthodes

**Option recommandée** : Modifier `create_a2a_app()` pour accepter un paramètre `methods: dict[str, Callable] | None = None` qui enregistre automatiquement les handlers. Rétro-compatible car optionnel.

### Problème Critique dans `a2a_client.py` — Pas de Propagation du `RequestContext`

**BUG IDENTIFIÉ** : `RemoteAgentClient.send_message()` et `call_remote_agent()` ne transmettent pas le `RequestContext` (family_id, correlation_id, restrictions) aux sous-agents. Maestro construit un `RequestContext` complet mais ne le passe jamais dans les appels A2A.

**Correction** : Ajouter un paramètre optionnel `context: RequestContext | None = None` à `send_message()` et `call_remote_agent()`. Si fourni, le sérialiser dans les `params` du payload JSON-RPC.

### Suppression de la Dépendance ADK dans Gourmet

L'agent Gourmet utilise actuellement `google.adk.agents.LlmAgent` dans `agent.py`. Cette story supprime cette dépendance pour passer à l'approche **Lean** (FastAPI + Pydantic pur) conformément à l'architecture.

**Impact** :
- `agent.py` sera supprimé — plus de `LlmAgent`, `LiteLlm`, `Runner`
- `main.py` ne passera plus `agent` à `create_a2a_app()` — le paramètre existe encore pour compatibilité mais est ignoré
- `instruction.md` est conservé pour référence future mais n'est plus chargé via ADK
- **NE PAS supprimer google-adk de `pyproject.toml`** — Maestro l'utilise encore pour le routage sémantique

### Enrichissement de `RECIPES_DB` pour les Schémas Pydantic

La base mock actuelle utilise des `dict` bruts. La migration vers des schémas Pydantic stricts nécessite d'enrichir chaque recette :

```python
# AVANT (tools.py) — dict brut, pas de typage
{"id": "1", "name": "Pâtes Carbonara", "ingredients": ["pâtes", "oeufs", ...], ...}

# APRÈS (recipe_service.py) — Pydantic strict, Ingredient structuré
RecipeDetail(
    id="1", name="Pâtes Carbonara",
    ingredients=[Ingredient(name="pâtes", quantity="400", unit="g"), ...],
    steps=["Cuire les pâtes", ...],
    tags=["italien", "rapide", "pâtes"],
    prep_time=20, servings=4, difficulty="facile"
)
```

### Code d'Erreur Domaine `RECIPE_NOT_FOUND`

Ajouter dans `common/exceptions.py` :

```python
# Domain-specific error codes (Agent Gourmet)
RECIPE_NOT_FOUND = -32010
```

Ceci remplace le pattern actuel `return {"error": "Recette non trouvée"}` dans `tools.py` par une exception structurée que Maestro peut intercepter via son `A2ARPCError` handler global.

### Pattern d'Enregistrement des Handlers A2A (Nouveau Pattern Projet)

Ce pattern sera établi par cette story et réutilisé par tous les futurs agents :

```python
# Dans main.py de chaque agent
from common.a2a_server import create_a2a_app

a2a_app, a2a_server = create_a2a_app(
    agent_name="agent_gourmet",
    ...
    methods={
        "search_recipes": handle_search_recipes,
        "get_recipe_details": handle_get_recipe_details,
    }
)
```

### Règles Python 3.13+ Obligatoires

- ❌ `typing.Optional[str]` → ✅ `str | None`
- ❌ `typing.List[str]` → ✅ `list[str]`
- ❌ `typing.Dict[str, Any]` → ✅ `dict[str, Any]`
- ❌ `-> None:` manquant → ✅ Toujours annoter le type de retour
- ✅ Tous les modèles Pydantic en `PascalCase` avec suffixe explicite
- ✅ `snake_case` exclusif dans les payloads JSON-RPC (pas d'alias Pydantic)
- ✅ `async def` obligatoire pour toute fonction I/O
- ✅ `ConfigDict(strict=True)` sur tous les modèles Pydantic

### Stack Technique

- Python 3.13+ strict
- FastAPI (version actuelle du lockfile)
- Pydantic v2 (`ConfigDict(strict=True)`)
- `httpx` pour le client async (injectable via paramètre)
- `pytest` + `pytest-asyncio` (`asyncio_mode="auto"`) — zéro I/O réseau en CI
- `uv` comme gestionnaire de packages
- **NE PAS ajouter de dépendance** — tout est déjà dans `pyproject.toml`

### Tests Existants à Adapter

3 fichiers de tests existants testent les anciennes fonctions/imports :

| Fichier | Impact | Action |
|---|---|---|
| `tests/test_agent_gourmet.py` | Importe `agent_gourmet.agent.get_agent` et `agent_gourmet.main` | Migrer vers `tests/agent_gourmet/` — adapter les imports à la nouvelle structure |
| `tests/test_agent_gourmet_tools.py` | Importe `agent_gourmet.tools.search_recipes/get_recipe_details` | Migrer — tester les fonctions async depuis `app.services.recipe_service` |
| `tests/test_gourmet_tools.py` | Duplique probablement `test_agent_gourmet_tools.py` | Supprimer si doublon, sinon migrer |

**Objectif : 84 tests existants + nouveaux tests = tous verts.**

### Anti-Patterns à Éviter

- ❌ **Ne PAS importer directement** des modules agents dans `common/` — le couplage est interdit
- ❌ **Ne PAS utiliser `time.sleep()`** — utiliser `asyncio.sleep()` si nécessaire
- ❌ **Ne PAS masquer les erreurs** avec `except Exception: pass` — toujours lever ou logger
- ❌ **Ne PAS hardcoder les URLs d'agents** — utiliser `agent_registry.get_agent_url()`
- ❌ **Ne PAS modifier `pyproject.toml`** — aucune nouvelle dépendance n'est nécessaire
- ❌ **Ne PAS toucher au `Dockerfile`** de Gourmet
- ❌ **Ne PAS supprimer `google-adk`** de `pyproject.toml` (Maestro l'utilise)

### Fichiers Impactés par `common/` — Vérification Rétro-Compatibilité

| Fichier common modifié | Consommateurs | Risque |
|---|---|---|
| `a2a_server.py` | `agent_gourmet/main.py`, `agent_acadomie/main.py`, `agent_maestro/main.py` (indirectement) | Moyen — paramètre `methods` optionnel |
| `a2a_client.py` | `agent_maestro/main.py` (via `call_remote_agent`) | Faible — paramètre `context` optionnel |
| `exceptions.py` | Tous les agents, tous les tests | Faible — ajout d'une constante |

### Conftest.py Global — Attention

Le `tests/conftest.py` actuel importe `agent_maestro.main.app` et clear les dependency overrides. Si les tests Gourmet sont dans un sous-dossier `tests/agent_gourmet/`, ils peuvent avoir leur propre `conftest.py` sans conflit.

### Project Structure Notes

- Alignement strict avec l'arborescence définie dans `architecture.md#Project Structure`
- `app/api/routers/` pour les endpoints A2A
- `app/schemas/` pour les contrats Pydantic
- `app/services/` pour la logique métier
- Tests dans `tests/agent_gourmet/` (pattern cohérent avec `tests/agent_maestro/`)

### References

- [Source: architecture.md#Project Structure] — Arborescence `src/agent_NAME/app/` imposée
- [Source: architecture.md#Structure Patterns] — `app/api/routers/`, `app/schemas/`, `app/services/`
- [Source: architecture.md#Format Patterns] — Typage Python 3.13+, PascalCase Pydantic, snake_case JSON
- [Source: architecture.md#Process Patterns] — DI obligatoire, A2ARPCError, Fail-Fast
- [Source: architecture.md#Communication Patterns] — correlation_id sur chaque échange
- [Source: epics_agent_gourmet.md#Story 1.1] — Acceptance Criteria originaux
- [Source: epics_agent_gourmet.md#Additional Requirements] — Correction intégration A2A (audit)
- [Source: prd_agent_gourmet.md#Section 3] — Migration asynchrone, Pydantic, Fail-Fast
- [Source: project-context.md#Framework-Specific Rules] — Structure dossiers, Pydantic strict
- [Source: project-context.md#Testing Rules] — Zéro réseau en CI, pytest-asyncio auto
- [Source: 1-1-librairie-commune-a2a-starter-template.md] — Patterns établis pour common/ (Story Maestro 1.1)
- [Source: common/a2a_server.py] — Bug dispatch non connecté identifié
- [Source: common/a2a_client.py] — Bug propagation context identifié

## Dev Agent Record

### Agent Model Used

{{agent_model_name_version}}

### Debug Log References

### Completion Notes List

### File List
