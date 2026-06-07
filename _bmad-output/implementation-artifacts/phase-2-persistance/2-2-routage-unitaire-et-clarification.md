# Story 2.2: Routage Unitaire et Clarification

Status: done

## Story

As a utilisateur de la famille,
I want que Maestro me dirige vers le bon expert (ou me demande des précisions si ambigu), ou me laisse l'invoquer par son nom,
So that j'aie une réponse précise en moins de 5 secondes.

## Contexte

**FRs couvertes :** FR1 (Routage automatique), FR2 (Invocation explicite), FR3 (Correction manuelle du routage), FR5 (Clarification d'ambiguïté)
**NFRs couvertes :** NFR2 (Latence Tunnel Mode)

## Acceptance Criteria

### AC1 — Invocation explicite par nom d'agent
- **Given** une requête de l'utilisateur
- **When** l'utilisateur nomme explicitement un agent (ex: *"Demande à gourmet..."* ou *"Gourmet: ..."*)
- **Then** Maestro force le routage vers cet expert

### AC2 — Correction manuelle a posteriori
- **Given** une mauvaise redirection ou une session active
- **When** l'utilisateur indique une correction (ex: *"Non, c'était pour gourmet"*)
- **Then** Maestro ré-aiguille la session et confirme le changement

---

## Tasks / Subtasks

### Task 1: Implémenter l'analyse de message dans Maestro
- [x] Créer `detect_explicit_agent` pour l'invocation directe.
- [x] Créer `detect_correction` et `is_pure_correction` pour gérer la réorientation.

### Task 2: Intégrer au Gateway Maestro
- [x] Intégrer dans `route_request` (A2A endpoint) et `chat` (legacy endpoint).
- [x] Assurer le nettoyage de la ponctuation pour éviter les faux-négatifs.

---

## Dev Agent Record

### Agent Model Used
Gemini 3.5 Flash (Low)

### Completion Notes
- Ajout des fonctions d'analyse textuelle robustes dans `src/agent_maestro/main.py`.
- Validation par tests unitaires.
