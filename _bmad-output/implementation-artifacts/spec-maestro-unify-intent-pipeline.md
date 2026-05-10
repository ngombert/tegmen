---
title: 'Unification du pipeline classify_intent et suppression du lru_cache sans TTL'
type: 'refactor'
created: '2026-05-10'
status: 'done'
baseline_commit: 'ae94e68'
context:
  - '_bmad-output/project-context.md'
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** `classify_intent` dans `router.py` utilise deux chemins de scoring incompatibles : `SemanticRouter.__call__` (sans `active_agent`) vs `get_all_scores` + `index.query` (avec `active_agent`). Les scores ne sont pas comparables numériquement, ce qui produit des comportements divergents dès 3+ agents. De plus, `_get_all_scores_cached` utilise un `lru_cache` sans TTL qui croît indéfiniment en mémoire avec des messages conversationnels toujours uniques.

**Approach:** Unifier `classify_intent` pour utiliser systématiquement `get_all_scores` sur tous les chemins, appliquer le sticky bonus et l'escape hatch de manière uniforme, et remplacer le `lru_cache` infini par un appel direct (le cache n'apporte rien sur des messages conversationnels uniques).

## Boundaries & Constraints

**Always:**
- Le `THRESHOLD_ROUTING`, `THRESHOLD_CLARIFICATION` et `THRESHOLD_ESCAPE_HATCH` restent identiques.
- Le registre `config/agents.yaml` reste la source de vérité pour les routes (ADR 2026-04-18).
- Tous les tests existants (sticky, escape, graceful, session, core) doivent passer après refactoring.
- Zéro appel réseau en tests, isolation complète.

**Ask First:**
- Modification de la signature publique de `classify_intent` (actuellement `(str, Optional[str]) -> tuple[str, float]`).
- Ajout de nouvelles dépendances.

**Never:**
- Ne pas toucher à `main.py` (les appelants ne changent pas).
- Ne pas modifier les seuils de confiance.
- Ne pas modifier `session.py` (hors scope — déféré).
- Ne pas introduire de base vectorielle externe.

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|----------|--------------|---------------------------|----------------|
| Standard sans session | `("Je veux des pâtes", None)` | `("gourmet", 0.xx)` — score issu de `get_all_scores` | N/A |
| Sticky routing actif | `("Encore une recette", "agent_gourmet")` | `("gourmet", score*1.3)` — bonus appliqué | N/A |
| Escape hatch | `("Aide-moi pour mes devoirs", "agent_gourmet")` avec acadomie > 0.95 | `("acadomie", 0.96)` — escape, pas de bonus | N/A |
| Message vide | `("", None)` | `("unknown", 0.0)` | N/A |
| Aucun score retourné | `("xyz", None)` avec index vide | `("unknown", 0.0)` | N/A |
| Score max capping | `("msg", "agent_explorer")` avec base 0.90 | `("explorer", 1.0)` — capped à 1.0 | N/A |

</frozen-after-approval>

## Code Map

- `src/agent_maestro/router.py` -- Cible principale : `classify_intent`, `get_all_scores`, `_get_all_scores_cached`
- `tests/test_maestro_sticky_routing.py` -- Tests unitaires du pipeline d'intention (sticky, bonus, escape hatch)
- `tests/test_agent_maestro.py` -- Tests d'intégration core (mock le router de haut niveau)
- `tests/test_maestro_escape_commands.py` -- Tests des commandes d'évasion (utilisent `classify_intent` indirectement)

## Tasks & Acceptance

**Execution:**
- [x] `src/agent_maestro/router.py` -- Refactorer `classify_intent` pour utiliser `get_all_scores` sur les deux chemins (avec et sans `active_agent`). Supprimer la branche `else` qui appelle `router_inst(message)`. Sélectionner le meilleur score via `max()` dans tous les cas.
- [x] `src/agent_maestro/router.py` -- Supprimer `_get_all_scores_cached` et le décorateur `@lru_cache`. L'import `lru_cache` et `functools` deviennent inutiles.
- [x] `tests/test_maestro_sticky_routing.py` -- Adapter `test_classify_intent_without_active_agent` pour mocker `get_all_scores` au lieu de `get_router`. Ajouter un test vérifiant que le chemin sans `active_agent` et le chemin avec produisent des scores comparables (même source).
- [x] `tests/test_maestro_sticky_routing.py` -- Ajouter un test pour le cas `get_all_scores` retourne un dict vide (edge case).
- [x] `tests/agent_maestro/test_router_dynamic.py` -- Adapter `test_classify_unknown` au nouveau comportement unifié (classify_intent retourne toujours la meilleure route, le seuil est géré par main.py).

**Acceptance Criteria:**
- Given aucun `active_agent`, when `classify_intent` est appelé, then il utilise `get_all_scores` (pas `router_inst.__call__`).
- Given le refactoring appliqué, when la suite de tests complète est exécutée, then 100% des tests passent (zéro régression).
- Given des messages conversationnels variés, when `classify_intent` est appelé N fois, then aucun cache mémoire ne croît de manière illimitée.

## Spec Change Log


## Design Notes

Le pipeline unifié suit ce flux :

```
classify_intent(message, active_agent?)
  │
  ├─ message vide? → return ("unknown", 0.0)
  │
  ├─ scores = get_all_scores(message)   ← TOUJOURS ce chemin
  │
  ├─ scores vide? → return ("unknown", 0.0)
  │
  ├─ active_agent?
  │   ├─ max(scores) > ESCAPE_HATCH? → return best (pas de bonus)
  │   └─ sinon → appliquer bonus au active_route
  │
  └─ return max(scores)
```

`get_all_scores` appelle directement `router_inst.encoder` + `router_inst.index.query` — c'est la même source de données que `SemanticRouter.__call__` mais avec tous les scores au lieu d'un seul.

## Verification

**Commands:**
- `cd /home/ngombert/projects/tegmen && python -m pytest tests/test_maestro_sticky_routing.py tests/test_agent_maestro.py tests/test_maestro_escape_commands.py tests/test_maestro_session.py -v` -- expected: 100% pass, zéro failure
- `cd /home/ngombert/projects/tegmen && python -m pytest tests/ -v --tb=short` -- expected: suite complète verte

## Suggested Review Order

**Pipeline d'intention unifié**

- Point d'entrée du refactoring — `get_all_scores` est maintenant le seul chemin pour les deux branches
  [`router.py:95`](../../src/agent_maestro/router.py#L95)

- Logique sticky bonus + escape hatch préservée, mais le `else` (ancien chemin divergent) est supprimé
  [`router.py:99`](../../src/agent_maestro/router.py#L99)

- Sélection du meilleur score factorisée hors du `if/else`, commune aux deux chemins
  [`router.py:114`](../../src/agent_maestro/router.py#L114)

**Suppression du cache mémoire**

- `get_all_scores` inline — plus de `_get_all_scores_cached` ni de `lru_cache` sans TTL
  [`router.py:122`](../../src/agent_maestro/router.py#L122)

**Tests**

- Test clé : vérifie que les deux chemins (avec/sans `active_agent`) utilisent la même source
  [`test_maestro_sticky_routing.py:82`](../../tests/test_maestro_sticky_routing.py#L82)

- Nouveau edge case : scores vides retournent `("unknown", 0.0)`
  [`test_maestro_sticky_routing.py:101`](../../tests/test_maestro_sticky_routing.py#L101)

- Adaptation du test d'intégration au nouveau comportement (best route, pas "unknown")
  [`test_router_dynamic.py:21`](../../tests/agent_maestro/test_router_dynamic.py#L21)
