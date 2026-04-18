# Story 3.2: Réception et Routage de l'Intention (Dispatch A2A)

Status: done

## Story

As a Gateway Maestro,
I want dispatcher les appels vers les agents spécialisés via HTTP lorsqu'une intention est reconnue,
so that le système fonctionne comme une fédération d'agents microservices.

## Acceptance Criteria

1. Maestro identifie l'agent via le routeur sémantique.
2. Si un agent distant est requis, Maestro utilise `RemoteAgentClient` pour lui envoyer le message.
3. Les erreurs réseau ou timeout (5s) retournent une erreur JSON-RPC structurée.
4. Le chitchat local est servi directement depuis Maestro sans appel extérieur.

## Tasks / Subtasks

- [x] Task 1 : Activer le dispatcher dans `route_request` (JSON-RPC) (AC: #1, #2)
- [x] Task 2 : Activer le dispatcher dans `/chat` (REST) (AC: #1, #2)
- [x] Task 3 : Gérer les erreurs d'agents distants (AC: #3)
- [x] Task 4 : Implémenter le pool de réponses chitchat locales (AC: #4)
- [x] Task 5 : Valider avec des tests d'intégration (`tests/agent_maestro/test_gateway.py`)

## Dev Agent Record

### Agent Model Used
Gemini 2.0 Flash (Antigravity)

### Completion Notes
- ✅ AC #1, #2, #3, #4 satisfied.
- ✅ Gestion des erreurs JSON-RPC code -32603 pour les agents indisponibles.
- ✅ Pool de 5 réponses chitchat variées pour une meilleure UX.
