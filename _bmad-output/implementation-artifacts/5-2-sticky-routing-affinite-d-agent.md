# Story 5.2: Sticky Routing (Affinité d'Agent)

## Story Foundation
**Description:** Modifier la logique de routage dans `route_request` (et idéalement `classify_intent`) pour consulter le `SessionStore`.

### Acceptance Criteria
- **AC 1:** Si une session active pointe vers un agent, Maestro priorise ou influence le routage vers cet agent.
- **AC 2:** Implémentation d'un bonus de score contextuel (+30% soit +0.3) pour l'agent en cours lors de la classification de l'intention.
- **AC 3:** Chaque interaction réussie avec un agent met à jour ou initie le TTL de la session avec cet agent.

## Developer Context

### Technical Requirements
- Le composant `InMemorySessionStore` développé lors de la Story 5.1 doit être instancié de manière globale (singleton) dans `main.py` (ou géré via une dépendance FastAPI). 
- Le endpoint `route_request` (A2A gateway) reçoit un `session_id`. JSON-RPC 2.0 transmet généralement un `id` qui peut servir d'identifiant de session ou, mieux encore, on peut utiliser le `context.correlation_id` ou un paramètre explicite passé par le client pour identifier la "session" (dans notre cas, utiliser `context.correlation_id` comme `session_id` par défaut s'il n'y a pas d'autre clé, ou utiliser un champ "session_id" ajouté dans `request.params` si on veut un suivi strict).
- **Routage :** Dans `classify_intent` (ou en l'enveloppant), si l'agent actif est récupéré, ajouter +0.3 à son score s'il fait partie des scores évalués.
- Mise à jour du store : Une fois qu'un agent (A) a été appelé avec succès, faire `await store.set(session_id, A)`.

### Architecture Compliance
- Utiliser l'injection de dépendances de FastAPI pour injecter le `SessionStore` ou l'initialiser proprement au démarrage (`lifespan`).
- Ne pas casser le fallback "unknown" ni "chitchat".

### File Structure Requirements
- `src/agent_maestro/main.py` : Instancier le store, modifier `route_request` et `chat` pour interagir avec le store.
- `src/agent_maestro/router.py` : Adapter `classify_intent` ou créer une nouvelle fonction `classify_intent_with_context` prenant l'agent actif en paramètre.

### Testing Requirements
- Mettre à jour ou ajouter de nouveaux tests unitaires pour le routage.
- Utiliser `pytest`.

### Project Context Reference
- Asynchronisme strict.
- Attention aux imports croisés.

## Status
Status: ready-for-dev
