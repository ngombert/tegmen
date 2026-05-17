
## Deferred from: code review (Epic 5)
- Fuite mémoire potentielle (lazy deletion) : contrainte acceptée pour le MVP in-memory.
- Divergence de logique dans `classify_intent` (router_inst vs get_all_scores) : optimisation voulue pour la performance du chemin standard.
- Test async/sync mélangés dans TestClient : fragile mais fonctionne dans le contexte actuel.
- Pas de test spécifique pour `/chat` : l'endpoint legacy est amené à être déprécié.

## Deferred from: stabilisation Maestro Phase 2 (2026-05-10)
- **ActiveCleanupWorker sessions** : Implémentation d'une tâche de fond `asyncio` dans `InMemorySessionStore` pour purge périodique des sessions expirées (remplacer la lazy deletion). Hook dans le lifespan FastAPI. Priorité 🟡.

## Deferred from: code review de 6-5-prompts-generiques-de-transition (2026-05-16)
- **Cache du prompt fichier** : `Path.read_text()` est appelé à chaque requête. Ajouter un cache au démarrage (lecture unique au `lifespan`) une fois les prompts stabilisés. Priorité 🟢.
- **Gourmet prompt sans appelant** : Le `LLMService` de Gourmet charge le prompt mais aucun service ne l'appelle encore sans `system_prompt` explicite. À brancher quand Gourmet sera doté d'un service d'orchestration LLM (Phase 2). Priorité 🟢.
- **Robustesse du chemin `Path(__file__).parent.parent`** : Potentiellement fragile en mode wheel/editable install. À passer en `importlib.resources` si le projet est empaqueté. Priorité 🟢.

