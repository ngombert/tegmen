# Story 5.1: Cache Mémoire et SessionStore

## Story Foundation
**Description:** Implémenter un `SessionStore` asynchrone utilisant un dictionnaire Python avec TTL (Time To Live).

### Acceptance Criteria
- **AC 1:** Maestro peut stocker le dernier `agent_id` utilisé pour un `session_id`.
- **AC 2:** Les données expirent automatiquement après 10 minutes d'inactivité.
- **AC 3:** L'implémentation est abstraite via une interface pour permettre un passage futur à Redis.

## Developer Context

### Technical Requirements
- Le `SessionStore` doit être défini dans le microservice Maestro (`src/agent_maestro`).
- Il doit proposer une interface abstraite (`BaseSessionStore`) et une implémentation concrète en mémoire (`InMemorySessionStore`).
- Méthodes requises : `get(session_id)`, `set(session_id, agent_id)`, `delete(session_id)`.
- Gestion asynchrone stricte : toutes les méthodes I/O doivent être des coroutines `async`.

### Architecture Compliance
- Pydantic v2 pour d'éventuels schémas de données si nécessaire, bien qu'un simple dict avec un timestamp pour la péremption suffise.
- Pas de tâches de fond bloquantes (`time.sleep()`).
- Zéro exception silencieuse (Fail-Fast).
- Utilisation de `asyncio` pour toute opération I/O éventuelle.

### File Structure Requirements
- `src/agent_maestro/session.py` : Contiendra l'interface abstraite et l'implémentation `InMemorySessionStore`.

### Testing Requirements
- Tests unitaires dans `tests/test_maestro_session.py`.
- L'asynchronisme doit être testé avec `pytest.mark.asyncio`.
- Le fonctionnement du TTL doit être testé (par exemple avec `freezegun` ou via des mocks du module `time`).

### Project Context Reference
- Respect strict de Python >=3.13, typage explicite (`mypy` compatible), format `snake_case` pour les méthodes.

## Status
Status: ready-for-dev
