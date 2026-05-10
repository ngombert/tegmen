
## Deferred from: code review (Epic 5)
- Fuite mémoire potentielle (lazy deletion) : contrainte acceptée pour le MVP in-memory.
- Divergence de logique dans `classify_intent` (router_inst vs get_all_scores) : optimisation voulue pour la performance du chemin standard.
- Test async/sync mélangés dans TestClient : fragile mais fonctionne dans le contexte actuel.
- Pas de test spécifique pour `/chat` : l'endpoint legacy est amené à être déprécié.

## Deferred from: stabilisation Maestro Phase 2 (2026-05-10)
- **ActiveCleanupWorker sessions** : Implémentation d'une tâche de fond `asyncio` dans `InMemorySessionStore` pour purge périodique des sessions expirées (remplacer la lazy deletion). Hook dans le lifespan FastAPI. Priorité 🟡.
