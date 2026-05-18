# Story 2.1 : Extraction Complète d'une Recette

## Metadata

- **Status:** done
- **Epic:** 2 — Consultation Détaillée d'une Recette
- **Story ID:** 2.1
- **Story Key:** `2-1-extraction-complete-d-une-recette`
- **Created:** 2026-05-02
- **Sprint Status File:** `_bmad-output/implementation-artifacts/sprint-status-agent-gourmet.yaml`

---

## User Story

**As a** famille utilisant Tegmen,
**I want** pouvoir consulter les détails complets d'une recette (métadonnées, ingrédients, instructions),
**So that** je puisse suivre la recette pas-à-pas pour préparer le repas.

---

## Acceptance Criteria

**AC1 — Extraction des Métadonnées (FR7)**
> **Given** un identifiant de recette existant dans la base
> **When** Maestro envoie une requête `get_recipe_details` avec le `recipe_id`
> **Then** Gourmet retourne un objet contenant : `name`, `tags`, `prep_time`, `servings`, `difficulty`
> **And** les types sont strictement respectés (Pydantic `strict=True`)

**AC2 — Liste des Ingrédients Quantifiée (FR8)**
> **And** la réponse inclut le champ `ingredients` qui est une liste d'objets possédant : `name`, `quantity`, `unit`
> **And** `quantity` et `unit` peuvent être nuls si non applicables

**AC3 — Instructions Pas-à-Pas (FR10)**
> **And** la réponse inclut le champ `steps` qui est une liste ordonnée de chaînes de caractères (instructions séquentielles)

**AC4 — Validation de Requête et Réponse (NFR-INT-1)**
> **And** la requête est validée par un schéma `RecipeDetailRequest` (contenant `recipe_id: str`)
> **And** la réponse est validée par un schéma `RecipeDetailResponse`
> **And** un `recipe_id` de type invalide (ex: integer au lieu de string) est rejeté avec une erreur `INVALID_PARAMS` (-32602)

---

## Tasks / Subtasks

- [x] Task 1 : Mise à jour des Schémas Pydantic (AC: #4)
  - [x] Créer `RecipeDetailRequest` dans `src/agent_gourmet/app/schemas/recipe.py` avec `recipe_id: str`
  - [x] Créer `RecipeDetailResponse` dans `src/agent_gourmet/app/schemas/recipe.py` (encapsulant `RecipeDetail`)
  - [x] S'assurer que `ConfigDict(strict=True)` est appliqué partout

- [x] Task 2 : Mise à jour du Handler A2A (AC: #1, #2, #3, #4)
  - [x] Modifier `handle_get_recipe_details` dans `src/agent_gourmet/app/api/routers/a2a.py`
  - [x] Utiliser `RecipeDetailRequest` pour valider les paramètres entrants
  - [x] Utiliser `RecipeDetailResponse` (ou `RecipeDetail`) pour valider la sortie avant `model_dump()`

- [x] Task 3 : Tests Unitaires et d'Intégration (AC: #4)
  - [x] Ajouter un test vérifiant que `get_recipe_details` avec un ID non-string (ex: `123`) est rejeté par la validation Pydantic
  - [x] Vérifier que la réponse JSON-RPC contient bien tous les champs requis par le schéma complet
  - [x] Valider le flux complet via `test_gourmet_a2a.py`

### Review Findings
- [x] [Review][Patch] Uncaught ValidationError in `handle_message_send` [a2a.py:78]
- [x] [Review][Patch] Unhandled empty message parts [a2a.py:60-72]
- [x] [Review][Patch] Missing generic exception guard in handler [a2a.py:32-51]
- [x] [Review][Patch] Minimal docstrings for new schemas [recipe.py]

---

## Developer Context

### Architecture Compliance
- Les schémas doivent rester dans `src/agent_gourmet/app/schemas/`.
- La logique métier est déjà partiellement présente dans `RecipeService.get_recipe_details`.
- Le handler A2A est dans `src/agent_gourmet/app/api/routers/a2a.py`.

### Technical Stack
- **Python 3.13+**
- **FastAPI**
- **Pydantic v2 (Strict)**
- **A2A Protocol** (JSON-RPC)

### Previous Story Intelligence
- Les patterns de Story 1.1 à 1.3 ont établi l'usage de `A2ARPCError` pour les erreurs métier.
- L'asynchronisme (`async def`) est obligatoire pour tous les services et handlers.
- Le mock `RECIPES_DB` dans `recipe_service.py` contient déjà des données riches avec ingrédients et étapes.

### Git Intelligence
- Le projet suit les Conventional Commits.
- Les tests utilisent `pytest-asyncio`.

---

## Project Context Reference
- [Architecture Decision Document](file:///home/ngombert/projects/tegmen/_bmad-output/planning-artifacts/architecture.md)
- [PRD Agent Gourmet](file:///home/ngombert/projects/tegmen/_bmad-output/planning-artifacts/prd_agent_gourmet.md)
- [Project Context](file:///home/ngombert/projects/tegmen/_bmad-output/project-context.md)

## Status Update
- **Completion Note:** Implementation complete. Added RecipeDetailRequest/Response schemas and updated the A2A handler for strict validation. All tests passing.
- **Target File:** `src/agent_gourmet/app/api/routers/a2a.py`
- **Target File:** `src/agent_gourmet/app/schemas/recipe.py`

## File List
- `src/agent_gourmet/app/api/routers/a2a.py` (Modified)
- `src/agent_gourmet/app/schemas/recipe.py` (Modified)
- `tests/agent_gourmet/test_gourmet_schemas.py` (Modified)
- `tests/agent_gourmet/test_gourmet_a2a.py` (Modified)

## Dev Agent Record
### Implementation Plan
1. Add `RecipeDetailRequest` and `RecipeDetailResponse` to `schemas/recipe.py`.
2. Update `a2a.py` handler to use these schemas for validation.
3. Update tests to cover strict type validation and nested response structure.

### Debug Log
- Encountered `KeyError: 'id'` in tests after nesting the response in `RecipeDetailResponse`. Fixed by updating test assertions to look for `recipe` key.
- OpenTelemetry logs were overwhelming test output. Disabled via `OTEL_ENABLED=false` for test runs.
