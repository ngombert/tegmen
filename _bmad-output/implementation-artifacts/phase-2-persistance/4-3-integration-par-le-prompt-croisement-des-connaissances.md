# Story 4.3: Intégration par le Prompt (Croisement des Connaissances)

Status: done

## Story

As a utilisateur de la famille,
I want que l'assistant croise spontanément ce qu'il sait de moi avec ma question,
So that j'obtienne une réponse de l'expert qui soit déjà contrainte par ma réalité (ex: agenda, goûts).

## Acceptance Criteria

1. **Given** une requête utilisateur
2. **And** un fait connu stocké en mémoire
3. **When** Maestro décide d'invoquer l'agent Gourmet (ou un autre spécialiste)
4. **Then** Maestro recherche et injecte les faits pertinents directement dans le contexte du prompt envoyé à Gourmet
5. **And** la réponse de Gourmet tient compte de cette contrainte.

## Tasks / Subtasks

- [x] Préparer l'infrastructure d'intégration des faits (AC: 4)
  - [x] Mettre à jour `RequestContext` dans `src/common/schemas.py` pour supporter `known_facts` (optionnel)
  - [x] Adapter `a2a_client.py` pour transmettre `known_facts`
- [x] Récupération parallèle et injection dans Maestro `main.py` (AC: 4)
  - [x] Utiliser `asyncio.gather` pour paralléliser le routing sémantique et la génération d'embedding + recherche SQL/vectorielle
  - [x] Injecter les `known_facts` (Hard Facts et Soft Facts concaténés/structurés) dans le payload envoyé aux agents spécialistes
- [x] Adapter les prompts et handlers des agents Gourmet et Acadomie (AC: 5)
  - [x] Injecter dynamiquement les faits dans le prompt du LLM
  - [x] Adapter Gourmet pour qu'il prenne en compte l'allergie aux noix du MVP dans ses réponses mockées
- [x] Créer et exécuter les tests (AC: 4, 5)
  - [x] Écrire `test_fact_injection_in_prompt` dans `tests/common/test_epic_4.py`
  - [x] Vérifier que tous les tests passent avec succès

## Dev Notes

- Recommandation Winston : paralléliser routing + fact retrieval via `asyncio.gather` pour réduire la latence.
- Recommandation Amelia : faire attention aux performances d'embedding.

### References

- [Source: epics.md#Story 4.3]

## Dev Agent Record

### Agent Model Used

Gemini 3.5 Flash (Low)

### Debug Log References

### Completion Notes List

### File List
