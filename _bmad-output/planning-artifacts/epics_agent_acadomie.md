---
stepsCompleted: [1, 2, 3, 4]
inputDocuments: [
  '_bmad-output/planning-artifacts/prd_agent_acadomie.md',
  '_bmad-output/planning-artifacts/architecture.md'
]
---

# Agent Acadomie - Epic Breakdown

## Overview

This document provides the complete epic and story breakdown for Agent Acadomie, decomposing the requirements from the PRD, UX Design if it exists, and Architecture requirements into implementable stories.

## Requirements Inventory

### Functional Requirements

FR1: L'agent doit permettre de consulter et d'ajouter des devoirs scolaires (Capacité `homework`).
FR2: L'agent doit permettre de consulter le calendrier scolaire et les événements à venir (Capacité `calendar`).
FR3: L'agent doit permettre de consulter les notes de l'élève par matière (Capacité `grades`).
FR4: L'agent doit fournir des conseils d'organisation et de révision interactifs (Capacité `organization`).
FR5: En l'absence de données réelles ou en cas d'incohérence, l'agent doit formuler son incapacité précise, afin que Maestro puisse informer correctement l'utilisateur (Fail-Fast & Anti-Hallucination).

### NonFunctional Requirements

NFR1: L'architecture doit être intégralement asynchrone (utilisation exclusive de `asyncio`, aucun blocage de l'Event Loop de FastAPI).
NFR2: Les paramètres entrants et sortants des "tools" doivent être strictement typés avec Pydantic v2 (schémas stricts dans `src/agent_acadomie/schemas/`) pour forcer la validation native.
NFR3: L'agent doit gérer activement les erreurs avec des exceptions explicites (`A2ARPCError`).
NFR4: Les docstrings de chaque outil Pydantic doivent être enrichies sémantiquement pour optimiser le filtrage par Maestro.
NFR5: Couverture de tests automatisée implémentée avec `pytest-asyncio`, isolement réseau absolu et mocks LLM (zéro appel réseau en CI).
NFR6: Observabilité et Logging Structuré : Implémentation du Structured JSON Logging, propagation des `correlation_id` et traces.
NFR7: Résilience et Chaos Testing : Tests de résilience et vérification stricte des timeouts (`asyncio.wait_for`) pour le Fail-Fast réseau A2A.

### Additional Requirements

- L'agent doit s'appuyer sur la librairie commune `src/common/` (FastAPI Lean Template, A2A Server/Client).
- L'agent fonctionnera dans son propre container Docker (utilisation de mocks en mémoire, architecture stateless "Lean").
- L'agent exploitera le `family_id` passé dans le payload JWT intercepté par Maestro.
- L'Injection de Dépendances est obligatoire pour les clients réseaux et d'inférence LLM (`litellm`) afin de permettre un mock instantané en intégration continue.
- Chaque appel JSON-RPC doit utiliser le format `snake_case`. Le typage asynchrone avec `mypy` strict est obligatoire.
- Génération d'un `README.md` complet pour l'Agent Acadomie détaillant les schémas et commandes.

### UX Design Requirements

Aucune exigence UX (Backend A2A).

### FR Coverage Map

FR1: ACA-Epic-1 - Consultation et ajout de devoirs (Mock)
FR2: ACA-Epic-1 - Consultation du calendrier et événements (Mock)
FR3: ACA-Epic-2 - Consultation des notes de l'élève (Mock)
FR4: ACA-Epic-2 - Conseils d'organisation et de révision
FR5: ACA-Epic-3 - Charte Anti-Hallucination et Fail-Fast

## Epic List

### ACA-Epic-1: Socle Asynchrone et Contrats A2A (Gestion Quotidienne MVP)
Objectif : Permettre à la famille de tester le flux conversationnel pour consulter les devoirs et le calendrier via des schémas stricts et des mocks en mémoire, validant ainsi l'architecture A2A.
**FRs covered:** FR1, FR2

### ACA-Epic-2: Suivi Académique et Logique LLM (Notes et Organisation)
Objectif : Offrir la consultation des notes (mockées) et connecter le LLM pour qu'il génère des conseils d'organisation interactifs basés sur les données en mémoire.
**FRs covered:** FR3, FR4

### ACA-Epic-3: Intégration Écosystème et Résilience
Objectif : Sécuriser l'agent dans l'écosystème avec l'observabilité, la gestion des timeouts, et la charte anti-hallucination.
**FRs covered:** FR5

## Epic 1: ACA-Epic-1: Socle Asynchrone et Contrats A2A (Gestion Quotidienne MVP)

Permettre à la famille de tester le flux conversationnel pour consulter les devoirs et le calendrier via des schémas stricts et des mocks en mémoire, validant ainsi l'architecture A2A.

### Story 1.1: Fondation de l'Agent et Starter Template A2A

As a Developer,
I want to initialize the Acadomie agent using the `src/common/` starter template,
So that it operates as an independent, stateless asynchronous A2A server.

**Acceptance Criteria:**

**Given** the Tegmen ecosystem architecture
**When** the Acadomie agent is built and started via Docker Compose
**Then** it runs in its own container without a database connection
**And** it successfully exposes the `/message/send` JSON-RPC endpoint using FastAPI and `asyncio`
**And** it includes a basic `README.md` explaining local usage.

### Story 1.2: Consultation et Ajout de Devoirs (Mock en mémoire)

As a Family Member,
I want the agent to handle homework consultation and addition,
So that I can track daily school tasks reliably.

**Acceptance Criteria:**

**Given** an incoming A2A request targeting `homework` capabilities
**When** Maestro sends a request containing the `family_id` in the payload
**Then** the agent validates the input and output using strict Pydantic v2 schemas (`HomeworkSchema`)
**And** processes the request using a local asynchronous Memory Repository mock (no DB)
**And** returns the formatted JSON-RPC response in `snake_case`
**And** enforces a strict execution timeout (`asyncio.wait_for`) to fail-fast if delayed.

### Story 1.3: Consultation du Calendrier Scolaire (Mock en mémoire)

As a Family Member,
I want the agent to retrieve upcoming school events,
So that I can anticipate the family schedule.

**Acceptance Criteria:**

**Given** an incoming A2A request targeting `calendar` capabilities
**When** Maestro sends a valid request
**Then** the agent validates the request and fetches data from a Calendar Memory Repository
**And** returns the event list typed strictly with Pydantic
**And** the agent functions are properly documented with rich docstrings to help Maestro's semantic routing
**And** all new code is covered by `pytest-asyncio` tests with zero network I/O.

## Epic 2: ACA-Epic-2: Suivi Académique et Logique LLM (Notes et Organisation)

Offrir la consultation des notes (mockées) et connecter le LLM pour qu'il génère des conseils d'organisation interactifs basés sur les données en mémoire.

### Story 2.1: Consultation des Notes par Matière avec Contrôle d'Accès

As a Parent or the specific Student,
I want to view the student's grades by subject,
So that I can monitor academic performance securely without exposing data to unauthorized siblings.

**Acceptance Criteria:**

**Given** an incoming A2A request targeting `grades` capabilities
**When** Maestro sends a request containing the `family_id` and the `user_identity` (role/id)
**Then** the agent validates the input and output using a strict `GradeResponse` schema
**And** the agent enforces authorization, ensuring only a user with role `parent` or the specific `student_id` matching the grades can access them
**And** returns an explicit `A2ARPCError` (Access Denied) if an unauthorized user (like a sibling) attempts access, which Maestro will gracefully handle
**And** fetches the data from a Grades Memory Repository
**And** returns the formatted JSON-RPC response asynchronously
**And** enforces a strict execution timeout to fail-fast.

### Story 2.2: Génération de Conseils d'Organisation via Inférence LLM

As a Family Member,
I want the agent to give organizational and revision advice based on my context,
So that I can plan my schoolwork effectively.

**Acceptance Criteria:**

**Given** an incoming A2A request targeting `organization` capabilities
**When** Maestro sends a request for advice
**Then** the agent injects the `litellm` dependency via FastAPI `Depends()` (for easy CI mocking)
**And** retrieves the local mock context (current grades/homework) to build a safe, localized prompt
**And** calls the LLM asynchronously to generate actionable advice
**And** returns the text inside a strictly validated Pydantic response within the timeout limit.

## Epic 3: ACA-Epic-3: Intégration Écosystème et Résilience

Sécuriser l'agent dans l'écosystème avec l'observabilité, la gestion des timeouts, et la charte anti-hallucination.

### Story 3.1: Observabilité et Traçabilité (Logging Structuré & Correlation ID)

As a Developer,
I want to implement structured JSON logging and propagate correlation IDs,
So that I can easily debug distributed A2A requests between Maestro and Acadomie.

**Acceptance Criteria:**

**Given** an A2A request containing a `correlation_id` in the payload
**When** the Acadomie agent processes the request
**Then** it logs every significant event (request received, tool call, response sent) in JSON format
**And** every log entry includes the unique `correlation_id`
**And** PII (Personally Identifiable Information) are automatically redacted from the logs.

### Story 3.2: Charte Anti-Hallucination et Gestion des Erreurs A2A

As a System,
I want to strictly enforce the anti-hallucination policy on both data boundaries and LLM prompts,
So that Maestro can inform the family with 100% certainty.

**Acceptance Criteria:**

**Given** a request processed by the agent (data fetch or LLM inference)
**When** the required context data is missing or the agent prepares its response
**Then** it must return a specific error code (`A2ARPCError`) if data is not found in the mocks
**And** the `litellm` system prompt must contain strict directives ("Do not invent data if not present in the context")
**And** the output Pydantic parser must catch unauthorized claims or hallucinations.

### Story 3.3: Tests de Résilience et Chaos Testing

As a Master Test Architect,
I want to perform chaos testing by injecting latency and failure specifically into LLM calls,
So that I can verify the agent's resilience under stress.

**Acceptance Criteria:**

**Given** the Acadomie agent in a test environment
**When** artificial latency or `httpx.TimeoutException` is injected into the `litellm` client mock
**Then** the agent's strict timeouts (`asyncio.wait_for`) must trigger correctly
**And** the system must gracefully fail-fast without blocking the event loop
**And** the coverage of these resilience scenarios is validated by the CI pipeline.
