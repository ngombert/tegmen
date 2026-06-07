# Story 2.1: Intégrité du Protocole A2A et Rétrocompatibilité

Status: done

## Story

As a agent système (Maestro),
I want que mon protocole A2A supporte les nouveaux champs (Yield, ContextStack, NewFacts) tout en gardant une validation Pydantic stricte,
So that je puisse communiquer avec les agents Phase 2 sans casser la communication avec les agents Phase 1 existants.

## Contexte

**FRs couvertes :** N/A (Infrastructure Protocole)
**NFRs couvertes :** NFR7 (Intégrité des Données), NFR9 (Rétrocompatibilité A2A)

## Acceptance Criteria

### AC1 — Rétrocompatibilité avec la Phase 1
- **Given** les schémas partagés dans `src/common/schemas.py`
- **When** je reçois une réponse d'un agent sans les champs Phase 2 (ex: pas de `new_facts_payload`)
- **Then** la validation Pydantic réussit sans erreur (Rétrocompatibilité - NFR9)

### AC2 — Validation stricte des données
- **Given** les schémas partagés dans `src/common/schemas.py`
- **When** un payload mal formé est envoyé
- **Then** une erreur de validation Pydantic stricte est levée (Intégrité - NFR7)

---

## Tasks / Subtasks

### Task 1: Créer les schémas Pydantic Phase 2
- [x] Définir `ContextStackItem` pour la pile de contextes.
- [x] Définir `FactSchema` pour modéliser les faits extraits.
- [x] Définir `YieldResponse` pour modéliser le retour de contrôle (Yield).

### Task 2: Étendre `RequestContext`
- [x] Ajouter le champ optionnel `context_stack: list[ContextStackItem] | None = None` dans `RequestContext`.

### Task 3: Étendre le client A2A (`a2a_client.py`)
- [x] Ajouter le paramètre `return_raw: bool = False` pour retourner la réponse JSON-RPC brute si demandée par Maestro.

---

## Dev Agent Record

### Agent Model Used
Gemini 3.5 Flash (Low)

### Completion Notes
- Modélisation complète des entités de la Phase 2 dans `src/common/schemas.py`.
- Adaptation du client A2A pour permettre l'extraction brute de ces champs.
