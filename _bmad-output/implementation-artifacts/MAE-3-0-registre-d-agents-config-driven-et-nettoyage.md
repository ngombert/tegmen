# Story 3.0: Registre d'Agents Config-Driven et Nettoyage

Status: done

## Story

As a Développeur Tegmen,
I want que la liste des agents soit gérée de manière externe et dynamique,
so that je puisse ajouter un agent sans redéployer le Gateway Maestro.

## Acceptance Criteria

1. `config/agents.yaml` centralise le nom, l'URL et les utterances de chaque agent.
2. `src/common/agent_registry.py` lit ce fichier et expose une API propre (`get_agent_url`, `get_agents`).
3. Suppression des URLs codées en dur dans `src/common/a2a_client.py`.

## Tasks / Subtasks

- [x] Task 1 : Créer `config/agents.yaml` (AC: #1)
- [x] Task 2 : Implémenter le singleton `agent_registry` (AC: #2)
- [x] Task 3 : Nettoyer `a2a_client.py` (AC: #3)
- [x] Task 4 : Valider le chargement dynamique via un test unitaire.

## Dev Agent Record

### Agent Model Used
Gemini 2.0 Flash (Antigravity)

### Completion Notes
- ✅ AC #1, #2, #3 satisfied.
- ✅ Support pour le rechargement dynamique des agents.
- ✅ Architecture découplée facilitant le scaling.
