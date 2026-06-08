# Story 4.5: Découverte Sémantique et Retrieval (Top-K)

Status: done

## Story

As a agent système (Maestro),
I want pouvoir interroger efficacement la base de données décentralisée pour retrouver les faits les plus pertinents sans saturer la latence ni le contexte du LLM,
So that je puisse fournir un prompt enrichi mais concis aux agents spécialistes.

## Acceptance Criteria

1. **Given** une requête utilisateur nécessitant du contexte
2. **When** Maestro cherche des faits associés
3. **Then** seuls les Top-K faits les plus pertinents (score sémantique le plus haut, c'est-à-dire distance cosinus minimale) sont récupérés.
4. **And** le nombre Top-K est configurable (par défaut `5`).
5. **And** la base utilise un index HNSW pour accélérer les recherches sémantiques à grande échelle.
6. **And** les faits inactifs (`is_active = False`) sont exclus du retrieval.

## Tasks / Subtasks

- [x] Créer une migration de base de données pour ajouter l'index HNSW (AC: 5)
  - [x] Générer une nouvelle migration Alembic pour Maestro
  - [x] Déclarer l'index HNSW sur la colonne `embedding` de `soft_facts` en utilisant la distance cosinus
- [x] Rendre Top-K configurable (AC: 4)
  - [x] Ajouter `DEFAULT_FACTS_TOP_K` (par défaut `5`) dans `src/common/config.py`
- [x] Optimiser et filtrer la recherche de faits (AC: 3, 6)
  - [x] Dans `fact_service.py` -> `search_relevant_facts`, s'assurer que `is_active == True` est bien appliqué (déjà fait, à blinder).
  - [x] Utiliser le paramètre `top_k` dynamique.
- [x] Écrire et exécuter les tests (AC: 1, 2, 3, 4, 5, 6)
  - [x] Écrire `test_top_k_bounds_overflow` dans `tests/common/test_epic_4.py`
  - [x] Écrire `test_fact_with_null_embedding` dans `tests/common/test_epic_4.py`
  - [x] Ajouter un test marqué `@pytest.mark.requires_model` pour vérifier le fonctionnement avec le vrai modèle (E5-small) si activé.

## Dev Notes

- L'index HNSW sur pgvector se déclare en SQLAlchemy avec `postgresql_using="hnsw"` et `postgresql_ops={"embedding": "vector_cosine_ops"}`.
- La migration doit s'assurer que l'extension vector est chargée avant de créer l'index.

### References

- [Source: epics.md#Story 4.5]
- [Rule: test-writing.md](file:///home/ngombert/projects/tegmen/.agent/rules/test-writing.md)

## Dev Agent Record

### Agent Model Used

Gemini 3.5 Sonnet (High)

### Debug Log References

### Completion Notes List

### File List
