# Story 1.3 : Filtres Avancés et Pagination

## Metadata

- **Status:** ready-for-dev
- **Epic:** 1 — Recherche et Découverte de Recettes
- **Story ID:** 1.3
- **Story Key:** `1-3-filtres-avances-et-pagination`
- **Created:** 2026-05-02
- **Sprint Status File:** `_bmad-output/implementation-artifacts/sprint-status-agent-gourmet.yaml`

---

## User Story

**As a** famille utilisant Tegmen,
**I want** pouvoir affiner ma recherche de recettes avec des filtres (tags, exclusions, temps, pagination),
**So that** je reçoive des résultats ciblés et en volume contrôlé.

---

## Acceptance Criteria

**AC1 — Filtrage par tags (FR2, FR3)**
> **Given** le service de recherche existant
> **When** une requête contient `tags_include` (ex: `["plat", "rapide"]`)
> **Then** seuls les recettes possédant TOUS ces tags sont retournées
> **When** une requête contient `tags_exclude` (ex: `["dessert"]`)
> **Then** les recettes possédant l'un de ces tags sont exclues

**AC2 — Exclusion par ingrédients (FR3)**
> **When** une requête contient `ingredients_exclude` (ex: `["gluten", "arachide"]`)
> **Then** toute recette contenant l'un de ces ingrédients (même partiellement dans le nom) est exclue

**AC3 — Restriction par temps de préparation (FR5)**
> **When** une requête contient `max_prep_time` (en minutes)
> **Then** seules les recettes avec un `prep_time <= max_prep_time` sont retournées

**AC4 — Pagination (FR4)**
> **When** une requête contient `limit` et `offset`
> **Then** le service retourne au maximum `limit` résultats à partir de l'index `offset`
> **And** le champ `total_count` de la réponse contient toujours le nombre total de matches (avant pagination)

**AC5 — Logique Cumulative (AND)**
> **And** tous les filtres sont cumulatifs (logique ET). Une recette doit satisfaire TOUTES les conditions pour être incluse.

**AC6 — Validation Pydantic Strict (NFR-INT-1)**
> **And** tous les paramètres sont validés par un schéma Pydantic strict (`SearchRequest` mis à jour ou `SearchFilters` imbriqué)
> **And** les types sont strictement respectés (pas de cast implicite)

---

## Tasks / Subtasks

- [x] Task 1 : Mise à jour des Schémas Pydantic (AC: #6)
  - [x] Mettre à jour `SearchRequest` dans `src/agent_gourmet/app/schemas/recipe.py` pour inclure les nouveaux filtres et paramètres de pagination
  - [x] Utiliser des types optionnels (`list[str] | None`, `int | None`)
  - [x] Définir des valeurs par défaut pour `limit` (ex: 10) et `offset` (0)

- [x] Task 2 : Implémentation de la logique de filtrage (AC: #1, #2, #3, #4, #5)
  - [x] Mettre à jour `RecipeService.search_recipes()` dans `src/agent_gourmet/app/services/recipe_service.py`
  - [x] Implémenter le filtrage `tags_include` (logique "contient tout")
  - [x] Implémenter le filtrage `tags_exclude` (logique "ne contient aucun")
  - [x] Implémenter le filtrage `ingredients_exclude` (logique "ne contient aucun ingrédient dont le nom matche")
  - [x] Implémenter le filtrage `max_prep_time`
  - [x] Appliquer la pagination (`slice` de la liste finale) après avoir calculé le `total_count`

- [x] Task 3 : Tests Unitaires et de Service (AC: #1, #2, #3, #4, #5)
  - [x] Ajouter `test_search_filters_tags()`
  - [x] Ajouter `test_search_filters_exclusions()`
  - [x] Ajouter `test_search_filters_prep_time()`
  - [x] Ajouter `test_search_pagination()` : vérifier `limit`, `offset` et `total_count` cohérents

- [x] Task 4 : Tests d'Intégration A2A
  - [x] Ajouter `test_a2a_search_complex_filters()` : requête JSON-RPC avec plusieurs filtres combinés
  - [x] Ajouter `test_a2a_search_pagination()` : vérifier le découpage des résultats via A2A

---

## Dev Notes

### Structure de SearchRequest recommandée

```python
class SearchRequest(BaseModel):
    model_config = ConfigDict(strict=True)
    
    query: str = ""
    tags_include: list[str] | None = None
    tags_exclude: list[str] | None = None
    ingredients_exclude: list[str] | None = None
    max_prep_time: int | None = None
    limit: int = 10
    offset: int = 0
```

*Note : Le champ `tag` (simple string) de la story précédente peut être déprécié ou intégré dans `tags_include`.*

### Algorithme de filtrage suggéré

1. Initialiser `matches = []`
2. Pour chaque recette dans `RECIPES_DB`:
   - Vérifier `query` (nom ou ingrédient)
   - Vérifier `max_prep_time`
   - Vérifier `tags_include` (tous les tags demandés doivent être présents)
   - Vérifier `tags_exclude` (aucun des tags exclus ne doit être présent)
   - Vérifier `ingredients_exclude` (aucun des ingrédients de la recette ne doit matcher un ingrédient exclu)
   - Si tout match, ajouter à `matches`
3. Calculer `total_count = len(matches)`
4. Appliquer pagination : `results = matches[offset : offset + limit]`
5. Retourner `SearchResponse(results=results, total_count=total_count)`

### Pièges à éviter
- Ne pas oublier que `ingredients_exclude` doit vérifier la présence des ingrédients exclus dans la liste des ingrédients de la recette.
- S'assurer que le `total_count` est celui de la liste filtrée *avant* pagination.
