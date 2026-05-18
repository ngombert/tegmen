# Story 2.2 : Fail-Fast sur Recette Inexistante

## Metadata

- **Status:** done
- **Epic:** 2 — Consultation Détaillée d'une Recette
- **Story ID:** 2.2
- **Story Key:** `2-2-fail-fast-sur-recette-inexistante`
- **Created:** 2026-05-02
- **Sprint Status File:** `_bmad-output/implementation-artifacts/sprint-status-agent-gourmet.yaml`

---

## User Story

**As a** Maestro (API Gateway),
**I want** recevoir une erreur structurée immédiate si l'identifiant de recette demandé n'existe pas,
**So that** je puisse informer la famille sans halluciner ni patienter inutilement.

---

## Acceptance Criteria

**AC1 — Erreur Structurée Domain-Specific (FR9)**
> **Given** un identifiant de recette inexistant (ex: `recipe_id="999"`)
> **When** Maestro envoie une requête `get_recipe_details`
> **Then** Gourmet lève une `A2ARPCError` avec le code `RECIPE_NOT_FOUND = -32010`
> **And** l'erreur contient un message explicite en français : "Recette non trouvée"
> **And** l'erreur inclut le `recipe_id` invalide dans le champ `data`

**AC2 — Suppression des Patterns Obsolètes**
> **And** aucun endpoint ne doit retourner un dictionnaire de type `{"error": "..."}`. Les erreurs doivent systématiquement être des levées d'exceptions `A2ARPCError`.

**AC3 — Validation Pydantic pour Type Invalide**
> **And** un `recipe_id` de type invalide (ex: integer au lieu de string) doit être rejeté par la validation Pydantic avec un code `INVALID_PARAMS` (-32602) avant même d'interroger le service.

**AC4 — Conformité JSON-RPC**
> **And** un test vérifie que la réponse reçue par le client est une `JsonRpcResponse` avec un champ `error` structuré et aucun champ `result`.

---

## Tasks / Subtasks

- [x] Task 1 : Audit et Nettoyage (AC: #2)
  - [x] Vérifier qu'aucune fonction ne retourne manuellement `{"error": ...}`.
  - [x] S'assurer que `RecipeService` lève bien `A2ARPCError` pour tous les cas d'erreur métier.

- [x] Task 2 : Validation de la structure d'erreur (AC: #1, #4)
  - [x] Vérifier que `handle_get_recipe_details` dans `a2a.py` propage correctement l'exception du service.
  - [x] S'assurer que le champ `data` de l'erreur contient bien les informations de contexte requises.

- [x] Task 3 : Tests de Robustesse Error-Handling (AC: #1, #3, #4)
  - [x] Ajouter/Vérifier `test_a2a_get_recipe_details_not_found` : valide le code `-32010` et le contenu du `data`.
  - [x] Ajouter/Vérifier `test_a2a_get_recipe_details_invalid_type` : valide le code `-32602`.
  - [x] Valider que le format de réponse JSON-RPC est strictement respecté en cas d'erreur (pas de fuite technique dans `message`).

### Review Findings
- [x] [Review][Patch] Uncaught ValidationError in `handle_message_send` [a2a.py:78]
- [x] [Review][Patch] Unhandled empty message parts [a2a.py:60-72]
- [x] [Review][Patch] Missing generic exception guard in handler [a2a.py:32-51]
- [x] [Review][Patch] Minimal docstrings for new schemas [recipe.py]

---

## Developer Context

### Architecture Compliance
- Utilisation de `src/common/exceptions.py` pour tous les codes d'erreur.
- Respect du standard JSON-RPC 2.0 pour la structure des erreurs.

### Technical Stack
- **Python 3.13+**
- **Pydantic v2 (Strict)**
- **A2A SDK**

### Previous Story Intelligence
- La Story 2.1 a déjà mis en place les schémas `RecipeDetailRequest` et `RecipeDetailResponse`.
- La logique de base est présente dans `RecipeService.get_recipe_details` et `a2a.py`. Cette story sert de validation finale et de verrouillage du comportement Fail-Fast.

---

## Project Context Reference
- [Architecture Decision Document](file:///home/ngombert/projects/tegmen/_bmad-output/planning-artifacts/architecture.md)
- [PRD Agent Gourmet](file:///home/ngombert/projects/tegmen/_bmad-output/planning-artifacts/prd_agent_gourmet.md)
- [Project Context](file:///home/ngombert/projects/tegmen/_bmad-output/project-context.md)

## Status Update
- **Completion Note:** Fail-Fast behavior formalized. Handlers now use `A2ARPCError` consistently. Old dictionary-based error returns removed. Tests verify structured error response with domain codes.
- **Target File:** `src/agent_gourmet/app/api/routers/a2a.py`
- **Target File:** `src/agent_gourmet/app/services/recipe_service.py`

## File List
- `src/agent_gourmet/app/api/routers/a2a.py` (Modified)
- `tests/agent_gourmet/test_gourmet_a2a.py` (Modified)

## Dev Agent Record
### Implementation Plan
1. Audit handlers for manual error dictionary returns.
2. Replace manual error returns with `A2ARPCError` in `message/send` handler.
3. Update integration tests to verify the presence of `data` in `RECIPE_NOT_FOUND` errors.
4. Run full test suite to ensure JSON-RPC compliance for all error cases.

### Debug Log
- Audit confirmed that `tools.py` was already removed and `RecipeService` was already using `A2ARPCError`.
- Updated `handle_message_send` to raise `A2ARPCError` for missing params instead of returning a dictionnaire.
- Integration tests now explicitly check for `-32010` (domain code) and `-32602` (standard code).
