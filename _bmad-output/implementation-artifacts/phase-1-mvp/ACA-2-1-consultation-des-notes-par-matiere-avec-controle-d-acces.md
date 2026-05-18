# Story 2.1: Consultation des Notes par Matière avec Contrôle d'Accès

Status: done

## Story

As a Parent or the specific Student,
I want to view the student's grades by subject,
so that I can monitor academic performance securely without exposing data to unauthorized siblings.

## Acceptance Criteria

1. **Given** an incoming A2A request targeting `grades` capabilities **When** Maestro sends a request containing the `family_id` and the `user_identity` (role/id) **Then** the agent validates the input and output using strict Pydantic v2 schemas (`GradeRequest`, `GradeResponse`).
2. **Given** a validated request **When** the agent processes it **Then** it enforces authorization, ensuring only a user with role `parent` or the specific `student_id` matching the grades can access them.
3. **Given** an unauthorized access attempt (like a sibling) **When** the agent verifies the identity **Then** it returns an explicit `A2ARPCError` (Access Denied), which Maestro will gracefully handle.
4. **Given** a successful authorization **When** the agent fetches data **Then** it uses a local asynchronous Grades Memory Repository mock with a strict execution timeout (`asyncio.wait_for`) to fail-fast.
5. **Given** the response data **When** it is ready **Then** it returns the formatted JSON-RPC response asynchronously.

## Tasks / Subtasks

- [ ] **Task 1 — Définir les schémas Pydantic stricts** (AC: #1)
  - [ ] 1.1 Mettre à jour `app/schemas/grades.py` pour définir `GradeItem`, `GradeRequest`, `GradeResponse`.
  - [ ] 1.2 S'assurer que la validation stricte (`ConfigDict(strict=True)`) est activée.
- [ ] **Task 2 — Implémenter le Repository et la Logique Métier** (AC: #4)
  - [ ] 2.1 Créer `app/services/grades_service.py` avec un mock data store en mémoire.
  - [ ] 2.2 Implémenter la méthode asynchrone `get_grades(family_id, student_id)`.
  - [ ] 2.3 Utiliser `asyncio.wait_for` pour simuler le timeout.
- [ ] **Task 3 — Intégrer le Contrôle d'Accès et le Handler A2A** (AC: #2, #3, #5)
  - [ ] 3.1 Mettre à jour `app/api/routers/a2a.py` avec la méthode `grades/list`.
  - [ ] 3.2 Extraire `user_identity` (contenant `role` et `id`) depuis le contexte de la requête A2A.
  - [ ] 3.3 Implémenter la logique d'autorisation : rejeter avec `A2ARPCError(code=A2ARPCError.FORBIDDEN)` si le rôle n'est pas `parent` ou si l'ID ne correspond pas à l'élève.
  - [ ] 3.4 Ajouter la méthode à `ACADOMIE_METHODS` avec le décorateur `@with_context`.
- [ ] **Task 4 — Ajouter les tests unitaires et d'intégration** (AC: #1, #2, #3)
  - [ ] 4.1 Tester le succès de l'accès pour un `parent`.
  - [ ] 4.2 Tester le succès de l'accès pour l'élève concerné (`student_id` correspondant).
  - [ ] 4.3 Tester l'échec (`A2ARPCError`) pour un accès non autorisé (frère/sœur ou identité invalide).

## Dev Notes

- Le payload A2A enverra les informations d'identité sous la clé `context.user` ou similaire, selon le design de Maestro. Mettez en place la structure Pydantic correspondante.
- L'erreur d'autorisation doit utiliser les codes JSON-RPC standards (ex: `-32001` ou une variante spécifique).
