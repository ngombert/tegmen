# Story 6.2: Adaptation des Timeouts et Résilience A2A

Status: review

## Story

As a System Architect,
I want to adjust the time limits (timeouts) of our asynchronous architecture,
so that it can support the real latency introduced by network calls to LLM providers.

## Acceptance Criteria

1. **Given** the asynchronous A2A architecture **When** internal calls to agents are made **Then** the `asyncio.wait_for` timeouts are increased (e.g., from 15 to 30 seconds) to accommodate LLM latency.
2. **Given** a real LLM call that times out **When** the timeout occurs **Then** an explicit `A2ARPCError` (Timeout) is raised and properly handled by Maestro without blocking the Event Loop.

## Tasks / Subtasks

- [x] **Task 1 — Augmenter les timeouts des appels LLM** (AC: #1)
  - [x] 1.1 Augmenter le timeout par défaut dans `LLMService` (Acadomie et Gourmet) à 30 secondes (30000 ms)
  - [x] 1.2 Documenter ou ajouter la variable dans `.env.example`
- [x] **Task 2 — Vérifier les timeouts A2A globaux** (AC: #1)
  - [x] 2.1 Vérifier si `common/a2a_client.py` ou Maestro ont des timeouts qui doivent être ajustés pour laisser le temps au LLM de répondre (modifié `DEFAULT_A2A_TIMEOUT` à 30s)
- [x] **Task 3 — Valider la gestion d'erreur dans Maestro** (AC: #2)
  - [x] 3.1 S'assurer que Maestro gère correctement les timeouts des agents (vérifié dans `main.py`, exception handler ok)
- [x] **Task 4 — Valider avec des tests** (AC: #2)
  - [x] 4.1 Vérifier que les tests de timeout existants passent toujours avec les nouvelles valeurs (validé avec `test_gourmet_resilience.py`)

## Dev Notes

### Contexte
Les appels aux LLM réels prennent plus de temps que les mocks (parfois plusieurs secondes). Il faut s'assurer que toute la chaîne (Maestro -> Agent -> LLM) n'expire pas trop vite.

### Timeouts
- `LLMService` : Actuellement à 10s. À passer à 30s.
- Maestro : À vérifier.

## Dev Agent Record

### Agent Model Used
Gemini 3 Flash

### File List
- `src/agent_acadomie/app/services/llm_service.py`
- `src/agent_gourmet/app/services/llm_service.py`
- `src/common/config.py`
- `.env.example`
- `_bmad-output/implementation-artifacts/6-2-adaptation-des-timeouts-et-resilience-a2a.md`

### Completion Notes List
- Création du fichier de story.
- Augmentation du timeout par défaut dans `LLMService` (Acadomie et Gourmet) à 30s.
- Augmentation du `DEFAULT_A2A_TIMEOUT` à 30s dans `config.py`.
- Ajout de `DEFAULT_A2A_TIMEOUT` et des timeouts LLM dans `.env.example`.
- Vérification que Maestro gère correctement les erreurs A2ARPCError (Timeout) via son exception handler global et les blocs try/except locaux.
- Validation avec les tests de résilience de Gourmet qui passent à 100%.

