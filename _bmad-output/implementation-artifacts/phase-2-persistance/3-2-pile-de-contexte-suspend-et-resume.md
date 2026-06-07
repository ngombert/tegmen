# Story 3.2: Pile de Contexte (Suspend & Resume)

Status: done

## Story

As a utilisateur de la famille,
I want pouvoir poser une question "hors-sujet" en pleine tâche, et que l'assistant mémorise ma tâche initiale pour m'y ramener naturellement,
So that je ne perde pas le fil de mes activités.

## Acceptance Criteria

### AC1 — Sauvegarde et suspension de session (Suspend)
- **Given** une session active avec un agent spécialiste (Tunnel Mode)
- **When** l'utilisateur pose une question hors-domaine déclenchant un "Yield"
- **Then** Maestro sauvegarde l'agent actif et les données associées dans la table SQL `contexts` de Maestro
- **And** Maestro traite la nouvelle requête avec le bon spécialiste.

### AC2 — Reprise de la session d'origine (Resume)
- **Given** une session avec un contexte suspendu en base de données
- **When** l'agent de digression a répondu à la question hors-sujet
- **Then** Maestro restaure l'agent initial comme agent actif dans la session de l'utilisateur
- **And** le prochain message est envoyé à l'agent initial.

---

## Tasks / Subtasks

- [x] Définir le modèle SQL `Context` et générer sa migration Alembic pour Maestro
- [x] Appliquer la migration de base de données
- [x] Modifier Maestro pour intercepter le `YieldResponse` et enregistrer le contexte suspendu
- [x] Implémenter le dépilage du contexte et la restauration de la session active après réponse

## Implementation Notes

### Files Created
- `src/agent_maestro/app/db/models/context.py` — Modèle SQLAlchemy `Context` (id, session_id, agent, context_data JSON, created_at)
- `src/agent_maestro/app/db/alembic/versions/94a0713b6ccc_create_context_table.py` — Migration Alembic

### Files Modified
- `src/agent_maestro/app/db/models/__init__.py` — Enregistrement du modèle Context
- `src/agent_maestro/main.py` — Fonctions `push_context()`, `pop_context()`, `clear_contexts()`, `prune_zombie_contexts()` + logique yield dans `route_request()` et `/chat`

### Design Decision
Le contexte suspendu **reste en pile** entre les requêtes (il n'est pas dépilé immédiatement après la digression). L'active agent est switché vers l'agent de digression. La restauration se fait :
- Par yield retour (double yield) : l'agent de digression yield aussi → pop + restore
- Par GC (Story 3.3) : après 3 messages de digression, le contexte est nettoyé
- Par escape command : l'utilisateur demande explicitement de reset

### Test Coverage
- `tests/common/test_epic_3.py::test_maestro_suspend_and_resume` — Vérifie le push en pile et le switch d'agent actif
