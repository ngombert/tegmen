# Story 3.1: Intégration Modèle Vectoriel In-Memory

Status: done

## Story

As a Système Maestro,
I want charger les définitions sémantiques des agents depuis la configuration,
so that l'orchestrateur soit découplé du code des agents spécialisés.

## Acceptance Criteria

1. `src/agent_maestro/router.py` charge les utterances dynamiquement depuis l'agent registry.
2. L'agent `chitchat` est maintenu comme une route codée en dur (système).
3. Le routeur utilise `auto_sync="local"` pour éviter les erreurs d'index asynchrones.
4. Une fonction `reload_router()` permet de rafraîchir l'index à chaud.

## Tasks / Subtasks

- [x] Task 1 : Refactoriser `router.py` pour utiliser `agent_registry.get_agents()` (AC: #1)
- [x] Task 2 : Implémenter la persistence de `chitchat` (AC: #2)
- [x] Task 3 : Ajouter l'initialisation paresseuse et le rechargement (AC: #3, #4)
- [x] Task 4 : Valider avec des tests unitaires (`tests/agent_maestro/test_router_dynamic.py`)

## Dev Agent Record

### Agent Model Used
Gemini 2.0 Flash (Antigravity)

### Completion Notes
- ✅ AC #1, #2, #3, #4 satisfied.
- ✅ Utilisation de `sentence-transformers/all-MiniLM-L6-v2` pour les embeddings.
- ✅ Découplage total : l'ajout d'un agent dans `agents.yaml` est immédiatement pris en compte après un rechargement.
