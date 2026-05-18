# Story 1.3: Consultation du Calendrier Scolaire (Mock en mémoire)

Status: done

## Story

As a Family Member,
I want the agent to retrieve upcoming school events,
so that I can anticipate the family schedule.

## Acceptance Criteria

1. **Given** an incoming A2A request targeting `calendar` capabilities **When** Maestro sends a valid request **Then** the agent validates the request using strict Pydantic v2 schemas (`CalendarRequest`, `CalendarResponse`).
2. **Given** a valid calendar request **When** the agent processes it **Then** it fetches data from a local asynchronous Calendar Memory Repository mock.
3. **Given** the agent's response **When** it is returned to Maestro **Then** it returns the event list typed strictly with Pydantic.
4. **Given** the new capabilities **When** the code is reviewed **Then** the agent functions are properly documented with rich docstrings to help Maestro's semantic routing.
5. **Given** the new code **When** tests are run **Then** all new code is covered by `pytest-asyncio` tests with zero network I/O.

## Tasks / Subtasks

- [ ] **Task 1 — Définir les schémas Pydantic stricts** (AC: #1)
  - [ ] 1.1 Mettre à jour `app/schemas/calendar.py` pour définir `CalendarEvent`, `CalendarRequest`, `CalendarResponse`.
  - [ ] 1.2 S'assurer que les modèles utilisent `ConfigDict(strict=True)` et sont exposés dans `__init__.py`.
- [ ] **Task 2 — Implémenter le Repository en mémoire asynchrone** (AC: #2)
  - [ ] 2.1 Créer `app/services/calendar_service.py` et y implémenter un mock data store en mémoire.
  - [ ] 2.2 Implémenter la méthode asynchrone `get_events(family_id)`.
  - [ ] 2.3 Envelopper les appels avec `asyncio.wait_for` pour simuler un timeout d'accès aux données (fail-fast), en s'alignant sur l'implémentation de la story précédente.
- [ ] **Task 3 — Intégrer le handler A2A JSON-RPC** (AC: #3, #4)
  - [ ] 3.1 Mettre à jour `app/api/routers/a2a.py` pour ajouter la méthode `calendar/list`.
  - [ ] 3.2 Ajouter une docstring riche au handler pour faciliter le routage sémantique.
  - [ ] 3.3 Mapper la méthode dans `ACADOMIE_METHODS`.
  - [ ] 3.4 Utiliser le décorateur `@with_context`.
- [ ] **Task 4 — Ajouter les tests unitaires et d'intégration** (AC: #5)
  - [ ] 4.1 Ajouter des tests dans `tests/test_agent_acadomie/test_calendar_a2a.py` pour valider la récupération du calendrier.
  - [ ] 4.2 Tester les validations Pydantic et la gestion des erreurs.

## Dev Notes

- Continuer l'utilisation du pattern "Lean" sans ADK.
- L'identifiant `family_id` sera extrait du contexte fourni par la Gateway Maestro lors des requêtes JSON-RPC.
