# Story 6.4: Encodeur Universel via LiteLLM

## Story
**En tant qu'** architecte/développeur,
**Je veux** un encodeur universel dans `semantic-router` qui utilise `LiteLLM`,
**Afin de** pouvoir utiliser n'importe quel modèle d'embedding supporté par LiteLLM (OpenRouter, Gemini, etc.) simplement en changeant la variable `EMBEDDING_MODEL`.

## Acceptance Criteria
- [x] Création d'une classe `LiteLLMEncoder` (ou similaire) héritant de `BaseEncoder` dans `semantic-router`.
- [x] Les embeddings sont générés via `litellm.embedding`.
- [x] Le routeur sémantique utilise cet encodeur si configuré.

## Tasks/Subtasks
- [x] 1. Créer la classe `LiteLLMEncoder` dans `src/agent_maestro/router.py` ou un fichier dédié.
- [x] 2. Modifier l'initialisation de l'encodeur dans `router.py` pour utiliser `LiteLLMEncoder` de manière générique ou selon la config.
- [x] 3. Vérifier le bon fonctionnement avec un test d'embedding via LiteLLM.

## Dev Notes
- `semantic-router` attend que l'encodeur soit appelable et retourne une liste de listes de floats.
- Exemple d'appel : `encoder(["texte1", "texte2"])` -> `[[0.1, 0.2, ...], [0.3, 0.4, ...]]`.
- LiteLLM retourne un dictionnaire avec les données dans `response["data"]`.

## Dev Agent Record
- Modèle utilisé : Gemini 3.1 Pro (Low)
- Fichiers modifiés : `src/agent_maestro/router.py`, `tests/test_maestro_agnostic_encoder.py`
- Notes : Suite à la découverte de la classe native `LiteLLMEncoder` dans `semantic_router.encoders`, le code a été refactorisé pour utiliser l'implémentation officielle. L'initialisation gère maintenant correctement le repli sur les encodeurs locaux ou LiteLLM en fonction du préfixe du modèle. Les tests passent avec succès.

## Status
done

