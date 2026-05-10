# Story 3.2: Charte Anti-Hallucination et Gestion des Erreurs A2A

Status: done

## Story

As a Family Member,
I want the agent to strictly stay within its domain of expertise (schooling, homework, organization),
so that I do not receive hallucinated, misleading, or out-of-context answers from the LLM.

## Acceptance Criteria

1. **Given** a user question targeting the `organization/advice` endpoint **When** the question is unrelated to school, homework, or family organization (e.g., a recipe, general trivia) **Then** the LLM must gracefully decline to answer and redirect the user to its specific domain.
2. **Given** the system prompt of the `OrganizationService` **When** generating advice **Then** it must include strict guidelines ("Charte Anti-Hallucination") forcing the model to rely solely on the provided context (homework and grades).
3. **Given** a catastrophic failure or an attempt to bypass the prompt **When** the LLM provides an unsafe or hallucinatory response (if detectable) or if an internal validation fails **Then** the service must return an appropriate `A2ARPCError` (e.g., `INTERNAL_ERROR` or a domain-specific code).
4. **Given** the new constraints **When** the tests are run **Then** unit tests must validate the LLM's boundary conditions using simulated out-of-domain questions via `AsyncMock`.

## Tasks / Subtasks

- [ ] **Task 1 — Renforcer le System Prompt** (AC: #2)
  - [ ] 1.1 Mettre à jour `app/services/organization_service.py`.
  - [ ] 1.2 Ajouter des instructions restrictives claires au `system_prompt` (ex: "Tu es un conseiller pédagogique. Si la question ne concerne pas l'école ou l'organisation, refuse de répondre poliment.").
- [ ] **Task 2 — Valider le traitement des Out-Of-Domain (OOD)** (AC: #1)
  - [ ] 2.1 Mocker le comportement du LLM pour une question OOD afin de vérifier que le retour utilisateur reste bienveillant mais ferme (pas d'erreur A2A technique dans ce cas, juste un refus textuel).
- [ ] **Task 3 — Uniformiser les retours d'erreurs techniques** (AC: #3)
  - [ ] 3.1 Vérifier que tout plantage inattendu lève bien un code d'erreur standard (déjà en grande partie traité dans `llm_service.py`).
- [ ] **Task 4 — Ajouter les tests OOD** (AC: #4)
  - [ ] 4.1 Ajouter `test_organization_advice_out_of_domain` dans `tests/test_agent_acadomie/test_organization_a2a.py`.
  - [ ] 4.2 S'assurer que le prompt généré contient bien les clauses de restriction.

## Dev Notes

- L'anti-hallucination par le prompt ("Prompt Engineering") est la méthode "Lean" privilégiée ici. Il n'est pas nécessaire d'implémenter un classifieur de texte séparé avant le LLM.
- Le test unitaire ne pourra pas tester le LLM réel. Il testera que le *Prompt* contient bien les clauses de sécurité, et que l'application gère bien le texte retourné par le LLM (qui sera mocké pour simuler un refus poli).
