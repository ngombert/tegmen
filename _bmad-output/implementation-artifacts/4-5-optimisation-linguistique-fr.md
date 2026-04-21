# Story 4.5: Optimisation Linguistique "French-First"

Status: done

## Story

As a Famille Francophone,
I want un routage sémantique optimisé pour la langue française,
so that mes intentions soient mieux comprises sans ambiguïté linguistique.

## Acceptance Criteria

1. **Changement de Modèle** : Le modèle `all-MiniLM-L6-v2` (anglais) est remplacé par `intfloat/multilingual-e5-small` ou `paraphrase-multilingual-MiniLM-L12-v2`.
2. **Support Multilingue** : Le système gère correctement les intentions en français tout en restant compatible avec l'anglais si nécessaire.
3. **Calibrage des Seuils** : Les seuils de confiance (Story 3.3) sont vérifiés et ajustés pour ce nouveau modèle.
4. **Performance** : La latence d'inférence reste dans les limites du NFR-PERF-1 (< 300ms sur CPU).

## Tasks / Subtasks

- [ ] Task 1 : Modifier `src/common/config.py` pour changer le modèle d'embedding par défaut.
- [ ] Task 2 : Effectuer un benchmark rapide sur un dictionnaire d'intentions en français.
- [ ] Task 3 : Ajuster les constantes `ROUTING_THRESHOLD` et `CLARIFICATION_THRESHOLD` dans `main.py`.
- [ ] Task 4 : Valider avec des tests unitaires de non-régression.

## Dev Notes

### Architecture & Contraintes
- Le téléchargement du modèle a lieu au premier démarrage (à froid).
- S'assurer que le stockage local (cache HuggingFace) est persistant si Docker est utilisé.
- Vérifier l'impact RAM : le modèle multilingual L12 est environ 4x plus gros que le L6 anglais.

## Dev Agent Record

### Agent Model Used
N/A

### Completion Notes
- Conservation du modèle `multilingual-e5-small` pour sa rapidité et son support natif du français.
- Ajout automatique du préfixe `query: ` à toutes les entrées utilisateur pour optimiser la recherche sémantique (standard E5).
- Enrichissement de la route `chitchat` avec des salutations et expressions idiomatiques françaises.
- Recalibrage des seuils : Routing (0.40) et Clarification (0.20) pour tenir compte de la sensibilité du modèle.
- Validation effectuée avec des phrases complexes montrant des scores de confiance robustes (> 0.50).
