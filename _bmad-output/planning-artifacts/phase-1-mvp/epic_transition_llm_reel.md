# Epic : MVP V1.5 - Transition vers un Moteur LLM Réel

## Contexte et Objectif
Suite à l'évaluation du MVP initial (qui utilisait des mocks et des "Memory Repositories"), il a été décidé de ne pas ajouter de nouveaux agents (comme Explorer) ni de construire immédiatement une infrastructure de Mémoire complexe (Phase 2). 

L'objectif de cet Epic ("MVP V1.5") est de remplacer les appels mockés par de **véritables appels à un LLM générique** pour les agents existants. Cela permet de :
1. Introduire le chaos réel (non-déterminisme, latence réseau).
2. Tester la résilience de notre architecture A2A et de notre validation stricte Pydantic face à de vraies réponses LLM.
3. Obtenir de premiers retours utilisateurs réels sur l'interaction avant d'investir dans une architecture de Mémoire (Core).

## Prérequis
- `litellm` est déjà intégré.
- L'injection de dépendance `Depends(get_llm_client)` est déjà en place.

## Stories

### Story 1: Configuration Sécurisée des Modèles Réels
**En tant que** développeur,
**Je veux** configurer `litellm` pour qu'il puisse appeler de vrais modèles (ex: `gpt-4o-mini` ou `claude-3-haiku`) via des variables d'environnement,
**Afin de** débrancher les mocks en environnement de développement/production tout en conservant la sécurité des clés d'API.

*Critères d'acceptation :*
- Les clés d'API (ex: `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`) sont lues depuis un fichier `.env` non tracké par Git.
- La configuration Gitleaks (`.gitleaks.toml`) est respectée et empêche tout commit accidentel des clés.
- L'injection de dépendance permet de basculer facilement entre le `MockLLM` (pour la CI) et le `RealLLM` (pour l'usage local).

### Story 2: Adaptation des Timeouts et Résilience A2A
**En tant qu'** architecte système,
**Je veux** ajuster les limites de temps (timeouts) de notre architecture asynchrone,
**Afin de** supporter la latence réelle introduite par les appels réseau vers les fournisseurs de LLM.

*Critères d'acceptation :*
- Les `asyncio.wait_for` des appels internes aux agents sont augmentés (ex: 15 à 30 secondes).
- Si le LLM réel ne répond pas à temps, une exception `A2ARPCError` explicite (Timeout) est toujours levée et proprement gérée par Maestro sans bloquer l'Event Loop.

### Story 3: Robustesse de la Validation Pydantic face au LLM
**En tant que** développeur,
**Je veux** m'assurer que les réponses du vrai LLM sont correctement parsées dans nos schémas de sortie stricts,
**Afin de** garantir que les éventuelles hallucinations ou erreurs de formatage JSON du modèle ne fassent pas planter l'agent.

*Critères d'acceptation :*
- Utilisation des fonctionnalités de *Structured JSON Outputs* (si supportées par le modèle choisi via `litellm`).
- Les erreurs de parsing Pydantic (`ValidationError`) lors du retour du LLM sont rattrapées proprement.
- L'agent renvoie une erreur de service formatée à Maestro plutôt qu'un crash brut de l'application en cas d'échec de parsing.

### Story 4: Encodeur Universel via LiteLLM
**En tant qu'** architecte/développeur,
**Je veux** un encodeur universel dans `semantic-router` qui utilise `LiteLLM`,
**Afin de** pouvoir utiliser n'importe quel modèle d'embedding supporté par LiteLLM (OpenRouter, Gemini, etc.) simplement en changeant la variable `EMBEDDING_MODEL`.

*Critères d'acceptation :*
- Création d'une classe `LiteLLMEncoder` (ou similaire) héritant de `BaseEncoder` dans `semantic-router`.
- Les embeddings sont générés via `litellm.embedding`.
- Le routeur sémantique utilise cet encodeur si configuré.

### Story 5: Prompts Génériques de Transition
**En tant que** Product Manager,
**Je veux** injecter un prompt système générique minimaliste pour Acadomie et Gourmet,
**Afin de** guider sommairement le vrai LLM sur son rôle sans encore implémenter la "Spécialisation métier experte" (qui fera l'objet de la vraie Phase 2).

*Critères d'acceptation :*
- Le prompt définit l'identité basique de l'agent et la directive stricte de répondre uniquement aux capacités demandées.
- Le prompt n'inclut pas encore de logique métier complexe (pas de gestion d'allergies avancée ou de pédagogie fine).

### Story 6: Connexion du LLM aux Handlers de Gourmet
**En tant que** développeur,
**Je veux** connecter le `LLMService` aux handlers ou services de l'agent Gourmet,
**Afin de** permettre à l'agent de générer de vraies réponses via un modèle LLM (comme ceux d'OpenRouter) plutôt que de retourner uniquement des données simulées.

*Critères d'acceptation :*
- `LLM_DEFAULT_MODEL` est ajouté dans `config.py`.
- Un handler ou service dans Gourmet utilise `LLMService` pour générer une réponse.
- La réponse utilise le prompt système défini dans `system_prompt.md`.
- Les tests passent ou sont mis à jour si nécessaire.


