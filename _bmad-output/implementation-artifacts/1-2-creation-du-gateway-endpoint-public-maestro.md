# Story 1.2: Création du Gateway Endpoint Public Maestro

Status: review

## Story

As a Application Front-end,
I want un endpoint POST public unique exposé par Maestro (`/api/v1/routing`),
So that je puisse envoyer mes requêtes sans exposer les sous-réseaux Docker des autres agents.

## Acceptance Criteria

1. **Given** que le serveur `agent_maestro` est en cours d'exécution
2. **When** je soumets un appel POST valide JSON-RPC à `/api/v1/routing`
3. **Then** l'API FastAPI intercepte la requête sans erreur de type (validation `JsonRpcRequest`)
4. **And** je reçois une réponse asynchrone valide sans blocage CPU (vérifié par tests `pytest-asyncio` sans réseau avec Mock).
5. **And** toute erreur de validation JSON-RPC (mauvais format de requête) retourne une `A2ARPCError` structurée (code -32600).

## Tasks / Subtasks

- [x] Task 1 : Nettoyer `src/agent_maestro/main.py` (Dette Technique)
  - [x] Supprimer les imports `google.adk` et `google.genai` (deprecated dans l'approche Lean).
  - [x] Supprimer la dépendance à `InMemorySessionService` (sera géré différemment plus tard).
- [x] Task 2 : Implémenter le Endpoint de Routage (`/api/v1/routing`)
  - [x] Créer/Mettre à jour `src/agent_maestro/main.py` pour inclure la route `POST /api/v1/routing`.
  - [x] Utiliser `JsonRpcRequest` (de `src.common.schemas`) comme modèle d'entrée.
  - [x] Retourner `JsonRpcResponse` (de `src.common.schemas`) comme modèle de sortie.
  - [x] Implémenter un handler temporaire (mock) qui retourne "Message reçu par Maestro" en attendant le vrai moteur de routage (Story 3.1).
- [x] Task 3 : Mise à jour de la documentation automatique
  - [x] Ajouter docstrings exhaustifs à la nouvelle route pour Swagger (`/docs`).
- [x] Task 4 : Écrire les tests d'intégration (Zéro Réseau)
  - [x] Fichier : `tests/agent_maestro/test_gateway.py`.
  - [x] Tester le succès JSON-RPC (payload valide).
  - [x] Tester l'échec structurel (payload invalide -> erreur -32600).

## Dev Notes

### Standard Public Endpoint
L'arborescence doit respecter la convention FastAPI `src/agent_maestro/main.py` pour l'application racine. L'endpoint public est fixé à `/api/v1/routing` pour suivre le versioning de l'API Tegmen.

### Alignement avec Story 1.1 (Librairie Commune)
- Utiliser impérativement `from src.common.schemas import JsonRpcRequest, JsonRpcResponse`.
- Toute exception de validation doit être levée via `A2ARPCError(INVALID_REQUEST)` ou interceptée par FastAPI pour produire le bon format JSON-RPC.

### Suppression de la Dette ADK
Maestro dans sa version actuelle (`src/agent_maestro/main.py`) est un monolithe legacy mélangeant logique ADK et routage. La story 1.2 marque le début de sa migration vers un rôle de **Gateway pur**.

### Testing Isolation
Utiliser `httpx.AsyncClient(app=app, base_url="http://test")` pour les tests unitaires de route afin de rester in-memory.

## Dev Agent Record

### Agent Model Used
Gemini 2.0 Flash (Antigravity)

### Debug Log References
- [2026-04-18] Story 1.1 verified (23/23 common tests + agents regressions).
- [2026-04-18] Story 1.2 spec created.
- [2026-04-18] Maestro main.py cleaned and /api/v1/routing implemented.
- [2026-04-18] Tests passed: tests/agent_maestro/test_gateway.py.

### Completion Notes List
- ✅ AC #1, #2, #3, #4, #5 satisfied.
- ✅ No ADK dependencies remain in `src/agent_maestro/main.py`.
- ✅ JSON-RPC 2.0 compliant endpoint exposed at `/api/v1/routing`.
- ✅ Auto-documentation Swagger correctly reflects the new routing schema.

### File List
- `src/agent_maestro/main.py` [MODIFY]
- `tests/agent_maestro/test_gateway.py` [NEW]
