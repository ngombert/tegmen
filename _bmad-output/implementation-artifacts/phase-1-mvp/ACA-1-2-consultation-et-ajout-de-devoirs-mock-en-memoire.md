# Story 1.2: Consultation et Ajout de Devoirs (Mock en mémoire)

Status: done

## Story

As a Family Member,
I want the agent to handle homework consultation and addition,
so that I can track daily school tasks reliably.

## Acceptance Criteria

1. **Given** an incoming A2A request targeting `homework` capabilities **When** Maestro sends a request containing the `family_id` in the payload **Then** the agent validates the input and output using strict Pydantic v2 schemas (`HomeworkSchema`).
2. **Given** a valid homework request **When** the agent processes it **Then** it uses a local asynchronous Memory Repository mock (no actual database connection).
3. **Given** the agent's response **When** it is returned to Maestro **Then** it is a properly formatted JSON-RPC response in `snake_case`.
4. **Given** the asynchronous operation **When** the memory repository is accessed **Then** the agent enforces a strict execution timeout (`asyncio.wait_for`) to fail-fast if delayed.

## Tasks / Subtasks

- [ ] **Task 1 — Définir les schémas Pydantic stricts** (AC: #1)
  - [ ] 1.1 Mettre à jour `app/schemas/homework.py` pour définir `HomeworkItem`, `HomeworkListRequest`, `HomeworkListResponse`, `HomeworkAddRequest`.
  - [ ] 1.2 S'assurer que les modèles utilisent `ConfigDict(strict=True)` et sont exposés dans `__init__.py`.
- [ ] **Task 2 — Implémenter le Repository en mémoire asynchrone** (AC: #2, #4)
  - [ ] 2.1 Créer `app/services/homework_service.py` et y implémenter un mock data store en mémoire (ex: liste de dictionnaires ou objets Pydantic filtrables par `family_id`).
  - [ ] 2.2 Implémenter la méthode asynchrone `get_homework(family_id)`.
  - [ ] 2.3 Implémenter la méthode asynchrone `add_homework(family_id, homework_data)`.
  - [ ] 2.4 Envelopper les appels avec `asyncio.wait_for` pour simuler un timeout d'accès aux données (fail-fast).
- [ ] **Task 3 — Intégrer les handlers A2A JSON-RPC** (AC: #3)
  - [ ] 3.1 Mettre à jour `app/api/routers/a2a.py` pour ajouter les méthodes `homework/list` et `homework/add`.
  - [ ] 3.2 Implémenter la logique de dispatching dans ces handlers et mapper les méthodes dans `ACADOMIE_METHODS`.
  - [ ] 3.3 Utiliser le décorateur `@with_context` pour la gestion des erreurs (`A2ARPCError`) et propagation du `correlation_id`.
- [ ] **Task 4 — Ajouter les tests unitaires et d'intégration** (AC: #1, #3)
  - [ ] 4.1 Ajouter des tests dans `tests/test_agent_acadomie/test_homework_a2a.py` pour valider la liste et l'ajout de devoirs.
  - [ ] 4.2 Tester les validations Pydantic (données manquantes, types invalides).
  - [ ] 4.3 Tester la gestion des timeouts et les erreurs renvoyées (A2ARPCError).

## Dev Notes

- **Architecture Lean**: Continuez à suivre le modèle de l'agent Gourmet. Ne pas utiliser l'ADK ou de dépendances de BDD réelles.
- **Fail-Fast**: Utilisez `asyncio.wait_for` pour chaque appel au repository en mémoire afin de garantir le respect des SLA du système.
- L'identifiant `family_id` sera extrait du contexte fourni par la Gateway Maestro lors des requêtes JSON-RPC. Les mocks doivent permettre de filtrer sur ce champ.
