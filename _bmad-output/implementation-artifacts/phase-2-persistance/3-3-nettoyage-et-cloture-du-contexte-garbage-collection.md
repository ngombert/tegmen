# Story 3.3: Nettoyage et Clôture du Contexte (Garbage Collection)

Status: done

## Story

As a utilisateur,
I want que le système "oublie" un sujet suspendu si l'interruption devient la nouvelle conversation principale, ou pouvoir lui demander explicitement d'abandonner,
So that l'IA ne me relance pas sur un sujet "zombie" obsolète.

## Acceptance Criteria

### AC1 — Clôture explicite
- **Given** un contexte suspendu en base de données
- **When** l'utilisateur dit explicitement "Laisse tomber ce sujet", "Abandonne", "Reset" ou "Laisse tomber"
- **Then** Maestro supprime immédiatement le contexte suspendu de la pile en base.

### AC2 — Invalidation temporelle / Garbage Collection
- **Given** un contexte suspendu en base de données
- **When** le délai ou le nombre de messages d'interruption dépasse un seuil
- **Then** le contexte est nettoyé silencieusement de la base de données.

---

## Tasks / Subtasks

- [x] Implémenter la détection des expressions de clôture explicite et suppression du contexte en base
- [x] Mettre en œuvre le nettoyage automatique (Garbage Collection) des contextes expirés/zombies

## Implementation Notes

### Files Modified
- `src/agent_maestro/main.py`:
  - `is_escape_command()` — Détection des commandes d'évasion ("Laisse tomber", "Abandonne", etc.) + appel à `clear_contexts()`
  - `prune_zombie_contexts()` — Nettoyage des contextes créés il y a plus de 5 minutes
  - `route_request()` / `chat()` — Compteur `digression_messages` dans `context_data` JSON, GC déclenché quand `count >= 3`

### GC Strategy
- **Seuil volume :** Après 3 messages de digression, le contexte suspendu est supprimé silencieusement
- **Seuil temporel :** Contextes plus anciens que 5 minutes sont purgés par `prune_zombie_contexts()`
- **Commandes explicites :** "Laisse tomber ce sujet", "Abandonne", "Reset", etc. → `clear_contexts()`

### Test Coverage
- `tests/common/test_epic_3.py::test_escape_commands_clears_stack` — Vérifie la suppression explicite par escape command
- `tests/common/test_epic_3.py::test_digression_limit_garbage_collection` — Vérifie le GC après 3 messages de digression
