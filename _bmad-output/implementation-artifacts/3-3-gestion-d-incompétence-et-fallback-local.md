# Story 3.3: Gestion d'Incompétence et Fallback Local

Status: done

## Story

As a Gateway Maestro,
I want gérer les cas d'ambiguïté ou d'incompétence de manière gracieuse,
so that l'utilisateur ne reçoive pas de réponses hors-sujet ou d'erreurs brutes.

## Acceptance Criteria

1. Le routeur retourne un score de similarité (0.0 à 1.0) pour chaque match.
2. Si le score est moyen (0.15 - 0.25), Maestro propose une clarification ("Voulez-vous parler à l'agent X ?").
3. Si le score est bas (< 0.15), Maestro propose une aide locale listant les compétences supportées.
4. Les tests valident les 3 zones de confiance (Routage, Clarification, Unknown).

## Tasks / Subtasks

- [x] Task 1 : Modifier `router.py` pour exposer le score (AC: #1)
- [x] Task 2 : Implémenter les seuils de décision dans `main.py` (AC: #2, #3)
- [x] Task 3 : Ajouter le template de clarification (AC: #2)
- [x] Task 4 : Valider avec des tests unitaires et intégration (AC: #4)

## Dev Agent Record

### Agent Model Used
Gemini 2.0 Flash (Antigravity)

### Completion Notes
- ✅ AC #1, #2, #3, #4 satisfied.
- ✅ Seuils configurés : Direct (> 0.25), Clarify (0.15-0.25), Unknown (< 0.15).
- ✅ Tests unitaires robustes couvrant les variations de scores.
