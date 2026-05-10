# Story 2.2: Génération de Conseils d'Organisation via Inférence LLM

Status: done

## Story

As a Family Member,
I want the agent to give organizational and revision advice based on my context,
so that I can plan my schoolwork effectively.

## Acceptance Criteria

1. **Given** an incoming A2A request targeting `organization` capabilities **When** Maestro sends a request for advice **Then** the agent validates the input and output using strict Pydantic v2 schemas (`OrganizationRequest`, `OrganizationResponse`).
2. **Given** the validated request **When** the agent processes it **Then** it injects the `litellm` dependency (or equivalent LLM service) to allow easy CI mocking.
3. **Given** the LLM integration **When** preparing the inference **Then** it retrieves the local mock context (current grades and homework) for the given `family_id`/`student_id` to build a safe, localized prompt.
4. **Given** the localized prompt **When** the agent executes the inference **Then** it calls the LLM asynchronously to generate actionable organizational advice.
5. **Given** the generated advice **When** it is ready **Then** it returns the text inside a strictly validated Pydantic response within the timeout limit.

## Tasks / Subtasks

- [ ] **Task 1 — Définir les schémas Pydantic stricts** (AC: #1)
  - [ ] 1.1 Créer `app/schemas/organization.py` pour définir `OrganizationRequest` et `OrganizationResponse`.
  - [ ] 1.2 Mettre à jour `__init__.py` pour exposer ces nouveaux modèles.
- [ ] **Task 2 — Créer le Service LLM avec Inférence Asynchrone** (AC: #2, #4)
  - [ ] 2.1 Créer `app/services/llm_service.py` responsable d'appeler `litellm.acompletion`.
  - [ ] 2.2 S'assurer de la gestion des erreurs LLM et du respect des timeouts définis dans la configuration.
- [ ] **Task 3 — Implémenter la Logique Métier d'Organisation** (AC: #3, #5)
  - [ ] 3.1 Créer `app/services/organization_service.py`.
  - [ ] 3.2 Implémenter la méthode `generate_advice` qui collecte les devoirs (`HomeworkService`) et notes (`GradesService`) pour construire le contexte.
  - [ ] 3.3 Assembler le prompt système et appeler le service LLM.
- [ ] **Task 4 — Intégrer le Handler A2A** (AC: #1)
  - [ ] 4.1 Mettre à jour `app/api/routers/a2a.py` avec la méthode `organization/advice`.
  - [ ] 4.2 Ajouter la méthode à `ACADOMIE_METHODS`.
- [ ] **Task 5 — Ajouter les tests unitaires avec Mocks LLM** (AC: #2)
  - [ ] 5.1 Ajouter `tests/test_agent_acadomie/test_organization_a2a.py`.
  - [ ] 5.2 Mocker `litellm.acompletion` ou le `LLMService` pour simuler une réponse (règle du Zéro I/O réseau).
  - [ ] 5.3 Valider que le contexte (notes/devoirs) est correctement injecté dans l'appel (assertion sur les arguments du mock).

## Dev Notes

- Le modèle par défaut pour cette tâche devrait être configurable (par ex. via `config.LLM_DEFAULT_MODEL`, comme `gpt-4o-mini` ou `claude-3-haiku`).
- Ne pas oublier le mécanisme Fail-Fast : si le LLM met trop de temps à répondre, une erreur `A2ARPCError.TIMEOUT` doit être levée.
