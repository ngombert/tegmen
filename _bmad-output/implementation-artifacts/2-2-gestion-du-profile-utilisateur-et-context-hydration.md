# Story 2.2: Gestion du Profile Utilisateur et Context Hydration

Status: done

## Story

As a Système de contrôle Tegmen,
I want charger les métadonnées de l'utilisateur (rôle, restrictions) au moment de l'authentification,
so that Maestro puisse adapter ses réponses et ses accès.

## Acceptance Criteria

1. `src/common/users.py` fournit un service d'accès aux profils (Mock pour le moment).
2. `RequestContext` est enrichi avec `user_name`, `role` (parent/child) et `restrictions`.
3. Une dépendance FastAPI `get_request_context` dans `main.py` hydrate automatiquement ces données depuis le JWT.

## Tasks / Subtasks

- [x] Task 1 : Créer `src/common/users.py` avec des profils de test (AC: #1)
- [x] Task 2 : Mettre à jour `RequestContext` dans `schemas.py` (AC: #2)
- [x] Task 3 : Implémenter la dépendance d'hydratation dans `main.py` (AC: #3)
- [x] Task 4 : Valider l'hydratation dans les tests d'intégration.

## Dev Agent Record

### Agent Model Used
Gemini 2.0 Flash (Antigravity)

### Completion Notes
- ✅ AC #1, #2, #3 satisfied.
- ✅ Support pour les rôles 'parent' et 'child'.
- ✅ Hydratation automatique transparente pour les développeurs d'endpoints.
