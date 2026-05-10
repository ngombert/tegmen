# Story 3.3: Tests de Résilience et Chaos Testing

Status: done

## Story

As an Architect,
I want to ensure the agent is resilient to downstream failures (LLM, mock DBs) and latency spikes,
so that the A2A router never hangs indefinitely and gracefully handles extreme concurrency.

## Acceptance Criteria

1. **Given** a mocked service (e.g., `litellm.acompletion` or `asyncio.sleep`) **When** we simulate a high-latency response exceeding `ACADOMIE_LLM_TIMEOUT_MS` **Then** the service strictly interrupts the call and raises `A2ARPCError.TIMEOUT` without leaking memory or blocking the event loop.
2. **Given** a chaos testing scenario **When** the LLM provider returns a catastrophic failure (e.g., HTTP 500, Rate Limit 429, or unparseable JSON) **Then** the service catches the exception and returns a clean `A2ARPCError.INTERNAL_ERROR`.
3. **Given** multiple simultaneous incoming A2A requests **When** they are processed concurrently **Then** the asynchronous nature of the application guarantees they do not block each other (verified by a concurrency test).

## Tasks / Subtasks

- [ ] **Task 1 — Simuler la Latence et les Erreurs (Chaos)** (AC: #1, #2)
  - [ ] 1.1 Ajouter des tests explicites de chaos dans `tests/test_agent_acadomie/test_chaos.py`.
  - [ ] 1.2 Mocker `litellm.acompletion` pour lever des exceptions de type `litellm.exceptions.RateLimitError` et `APIConnectionError`.
- [ ] **Task 2 — Valider la Concurrence** (AC: #3)
  - [ ] 2.1 Écrire un test asynchrone utilisant `asyncio.gather` pour envoyer plusieurs requêtes A2A simultanées.
  - [ ] 2.2 S'assurer que le temps d'exécution total n'est pas la somme des temps de chaque requête (prouvant que le serveur traite bien en parallèle).
- [ ] **Task 3 — Vérifier l'étanchéité du Fail-Fast** (AC: #1)
  - [ ] 3.1 Confirmer que les timeouts globaux (`asyncio.wait_for`) sont respectés et n'engendrent pas de tâches orphelines bloquantes.

## Dev Notes

- L'utilisation de `pytest.mark.asyncio` et `asyncio.gather` sera indispensable pour les tests de concurrence.
- `litellm` possède des exceptions spécifiques, il faudra peut-être les importer pour bien les mocker (`from litellm.exceptions import RateLimitError`).
- Ces tests marqueront la fin du développement de l'Agent Acadomie, assurant qu'il est "Production-Ready" du point de vue architectural.
