# Story 4.1: Extraction et Évaluation des Nouveaux Faits

Status: done

## Story

As a agent spécialiste,
I want extraire de la conversation des informations potentiellement utiles pour l'avenir et en évaluer l'importance,
So that Maestro puisse les consolider dans la mémoire globale de la famille.

## Acceptance Criteria

1. **Given** une conversation contenant une nouvelle information
2. **When** l'agent spécialiste génère sa réponse
3. **Then** il inclut un bloc `new_facts_payload` validé par Pydantic dans son retour JSON-RPC
4. **And** chaque fait est accompagné d'un `importance_score` pour aider Maestro à filtrer le bruit.

## Tasks / Subtasks

- [x] Définir les schémas Pydantic partagés (AC: 3, 4)
  - [x] Ajouter `FactSchema` et `NewFactsPayload` dans `src/common/schemas.py`
  - [x] Intégrer `new_facts_payload` dans `JSONRPCResponse` ou `RequestContext`
- [x] Implémenter l'extraction de faits (AC: 1, 2, 4)
  - [x] Créer `src/common/fact_extractor.py` utilisant `litellm.acompletion`
  - [x] Ajouter une heuristique regex robuste ou mock d'extraction pour les tests hors-ligne (éviter les appels réseau ou de modèle lourd)
- [x] Intégrer l'extraction dans Gourmet et Acadomie (AC: 3)
  - [x] Modifier les handlers de routes de Gourmet et Acadomie pour appeler l'extracteur et enrichir la réponse
- [x] Créer et exécuter les tests (AC: 1, 2, 3, 4)
  - [x] Écrire `test_fact_extraction_from_response` et `test_fact_schema_validation` dans `tests/common/test_epic_4.py`
  - [x] Vérifier que tous les tests passent avec succès

## Dev Notes

- L'extraction utilise `litellm.acompletion` mais doit basculer de manière transparente vers un comportement simulé par expressions régulières (ou mock codé en dur basé sur des mots clés) si un mode mock est activé afin de garantir des tests unitaires ultra-rapides et déconnectés de toute dépendance de modèle externe dans la CI.

### References

- [Source: epics.md#Story 4.1]

## Dev Agent Record

### Agent Model Used

Gemini 3.5 Flash (Low)

### Debug Log References

### Completion Notes List

### File List

- `src/common/schemas.py`
- `src/common/fact_extractor.py`
- `src/agent_gourmet/app/api/routers/a2a.py`
- `src/agent_acadomie/app/api/routers/a2a.py`
- `tests/common/test_epic_4.py`
