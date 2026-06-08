# Story 4.4: Résolution de Conflits Sémantiques (Mise à jour des Faits)

Status: done

## Story

As a utilisateur,
I want que le système comprenne quand je change d'avis ou que ma situation évolue, et qu'il mette à jour ses connaissances au lieu d'accumuler des faits contradictoires,
So that l'assistant reste pertinent dans le temps.

## Acceptance Criteria

1. **Given** un fait existant en mémoire (ex: "Nicolas aime les épinards")
2. **When** une nouvelle conversation indique le contraire ("Je déteste les épinards maintenant")
3. **Then** le processus d'extraction génère un nouveau fait
4. **And** le système identifie le conflit sémantique avec le fait précédent lors de l'insertion
5. **And** l'ancien fait est désactivé (`is_active = False`) pour les soft facts en cas de similarité sémantique élevée (seuil configurable via `CONFLICT_SIMILARITY_THRESHOLD`, par défaut `0.92`).
6. **And** pour les hard facts, la mise à jour par clé identique écrase ou met à jour l'ancien fait (déjà partiellement fait, à consolider).

## Tasks / Subtasks

- [x] Implémenter la détection de conflits sémantiques pour les Soft Facts (AC: 4, 5)
  - [x] Définir la configuration `CONFLICT_SIMILARITY_THRESHOLD` dans le système (dans `src/common/config.py` ou par défaut à `0.92`)
  - [x] Dans `store_facts` de `fact_service.py`, pour chaque soft fact à insérer, calculer son embedding
  - [x] Rechercher les soft facts existants de la même famille ayant une similarité cosinus supérieure au seuil (distance cosinus < `1 - threshold`)
  - [x] Mettre à jour les soft facts conflictuels trouvés en les passant à `is_active = False` avant d'insérer le nouveau fait
- [x] Consolider la gestion des conflits pour les Hard Facts (AC: 6)
  - [x] S'assurer que les hard facts sur la même clé sont bien mis à jour et que l'importance est mise à jour (déjà implémenté dans 4.2, ajouter des assertions de tests complémentaires si besoin)
- [x] Écrire et exécuter les tests (AC: 1, 2, 3, 4, 5, 6)
  - [x] Écrire `test_conflict_resolution_soft_synthetic` dans `tests/common/test_epic_4.py` en mockant les embeddings pour obtenir des vecteurs avec une similarité contrôlée (> 0.92 et < 0.92)
  - [x] Écrire `test_conflict_resolution_hard` dans `tests/common/test_epic_4.py`
  - [x] Lancer les tests et valider le comportement

## Dev Notes

- La distance cosinus de pgvector est définie comme `1 - cosine_similarity`. Donc, une similarité supérieure à `0.92` correspond à une distance cosinus inférieure à `0.08` (`1 - 0.92`).
- Dans `test_conflict_resolution_soft_synthetic`, nous pouvons utiliser des mock embeddings synthétiques spécifiques pour contrôler la distance cosinus exacte sans appeler le modèle de sentence-transformers.

### References

- [Source: epics.md#Story 4.4]
- [Rule: test-writing.md](file:///home/ngombert/projects/tegmen/.agent/rules/test-writing.md)

## Dev Agent Record

### Agent Model Used

Gemini 3.5 flash (Low)

### Debug Log References

### Completion Notes List

### File List
