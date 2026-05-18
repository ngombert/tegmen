# Story 2.3: Contrôle d'Accès Parental (RBAC Familial)

Status: done

## Story

As a Parent,
I want restreindre l'accès à certains agents (ex: Explorer) pour mes enfants,
so that ils ne puissent pas effectuer d'actions non supervisées.

## Acceptance Criteria

1. Maestro bloque l'accès à un agent si le rôle de l'utilisateur est `child` et que l'agent est dans sa liste de `restrictions`.
2. Une erreur `403 Forbidden` est retournée avec un message pédagogique.
3. Les tests valident qu'un parent peut accéder à tout, mais qu'un enfant est bloqué sur les agents restreints.

## Tasks / Subtasks

- [x] Task 1 : Implémenter `check_agent_access` dans `main.py` (AC: #1)
- [x] Task 2 : Retourner `403 Forbidden` en cas de violation (AC: #2)
- [x] Task 3 : Ajouter des cas de tests RBAC dans `tests/test_agent_maestro.py` (AC: #3)

## Dev Agent Record

### Agent Model Used
Gemini 2.0 Flash (Antigravity)

### Completion Notes
- ✅ AC #1, #2, #3 satisfied.
- ✅ Blocage explicite au niveau du Gateway Maestro avant appel A2A.
- ✅ Message d'erreur personnalisé : "Désolé, ton profil ne permet pas d'accéder à l'agent...".
