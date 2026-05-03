
## Deferred from: code review (Epic 5)
- Fuite mémoire potentielle (lazy deletion) : contrainte acceptée pour le MVP in-memory.
- Divergence de logique dans `classify_intent` (router_inst vs get_all_scores) : optimisation voulue pour la performance du chemin standard.
- Test async/sync mélangés dans TestClient : fragile mais fonctionne dans le contexte actuel.
- Pas de test spécifique pour `/chat` : l'endpoint legacy est amené à être déprécié.
