# Story 4.1: Disjoncteur Temporel "Fail-Fast"

Status: done

## Story

As a Maestro Gateway,
I want imposer un délai critique (SLA Timeout) sur tout échange A2A sortant vers un spécialiste,
so that je ne gèle jamais l'application si un agent tiers tombe en panne.

## Acceptance Criteria

1. **Timeout Configurable** : Le client `A2AClient` accepte un paramètre `timeout` (par défaut 5.0s).
2. **Levée d'Exception** : Si l'agent cible ne répond pas dans le délai imparti, une exception `A2ARPCError` avec le code `TIMEOUT` (-32000) est levée.
3. **Non-Blocage** : Le timeout est géré de manière asynchrone via `httpx` sans bloquer l'Event Loop de FastAPI.
4. **Test de Validation** : Un test `pytest` simulant une latence réseau supérieure au timeout confirme la levée de l'exception.

## Tasks / Subtasks

- [ ] Task 1 : Modifier `src/common/a2a_client.py` pour supporter le timeout dynamique.
- [ ] Task 2 : S'assurer que `A2ARPCError` comporte bien le code `TIMEOUT`.
- [ ] Task 3 : Écrire un test d'intégration simulant un timeout via `respx` ou un mock `httpx`.

## Dev Notes

### Architecture & Contraintes
- Utiliser `httpx.Timeout(timeout=...)` pour la configuration.
- Le timeout doit être propagé depuis la configuration de l'agent (registre) ou une valeur par défaut globale.
- Attention à la gestion des exceptions `httpx.TimeoutException` qui doivent être catchées et wrappées dans `A2ARPCError`.

## Dev Agent Record

### Agent Model Used
N/A

### Completion Notes
- Ajout de `DEFAULT_A2A_TIMEOUT` (5.0s) dans `config.py`.
- Support du timeout dynamique dans `RemoteAgentClient`.
- Correction de l'URL de transport pour inclure `/a2a/SendMessage`.
- Gestion des exceptions `httpx.TimeoutException`, `A2AClientTimeoutError` et `A2AClientHTTPError` (503) pour lever une `A2ARPCError(TIMEOUT)`.
- Ajout de tests automatisés dans `tests/test_resilience.py`.
- Ajout de la méthode `register_agent` dans `AgentRegistry` pour faciliter les tests.
