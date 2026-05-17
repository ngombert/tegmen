# Story 6.6: Connexion du LLM aux Handlers de Gourmet

## Story
**En tant que** développeur,
**Je veux** connecter le `LLMService` aux handlers ou services de l'agent Gourmet,
**Afin de** permettre à l'agent de générer de vraies réponses via un modèle LLM (comme ceux d'OpenRouter) plutôt que de retourner uniquement des données simulées.

## Acceptance Criteria
- [x] Ajouter `LLM_DEFAULT_MODEL` dans la classe `Settings` de `src/common/config.py` pour pouvoir le configurer via le `.env`.
- [x] Intégrer l'appel à `LLMService.generate_response` dans un service ou handler de Gourmet (par exemple dans `recipe_service.py` ou un nouveau handler d'inspiration).
- [x] S'assurer que l'appel utilise le prompt système chargé depuis `src/agent_gourmet/app/prompts/system_prompt.md`.
- [x] Valider le fonctionnement via un test unitaire ou d'intégration (en mockant l'appel LLM pour la CI).

## Tasks/Subtasks
- [x] 1. Ajouter `LLM_DEFAULT_MODEL` à `src/common/config.py`.
- [x] 2. Identifier ou créer le point d'entrée dans Gourmet pour l'utilisation du LLM (ex: enrichissement de la recherche ou réponse libre).
- [x] 3. Injecter `LLMService` et appeler `generate_response`.
- [x] 4. Vérifier que le prompt markdown est bien lu et transmis.
- [x] 5. Ajouter ou mettre à jour les tests pour couvrir ce comportement.

## Dev Agent Record
- Fichiers modifiés : `src/common/config.py`, `src/agent_gourmet/app/api/routers/a2a.py`, `tests/agent_gourmet/test_gourmet_a2a.py`.
- Notes : `LLM_DEFAULT_MODEL` ajouté dans la config. Le handler `message/send` de Gourmet utilise maintenant `LLMService` pour répondre via le LLM. Les tests ont été mis à jour avec un mock.

## Status
review
