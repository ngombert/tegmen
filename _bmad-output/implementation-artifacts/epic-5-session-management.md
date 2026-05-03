# Epic 5: Gestion de Session et Routage Contextuel (Maestro)

## Vision
Transformer le Gateway Maestro d'un routeur "one-shot" vers un orchestrateur capable de maintenir un dialogue cohérent. L'objectif est d'éviter que l'utilisateur n'ait à repréciser son intention à chaque message au sein d'une même session.

## Objectifs Métier
- Améliorer l'expérience utilisateur en gérant la continuité du dialogue.
- Éviter les collisions sémantiques lors de réponses courtes (ex: "oui", "Italie", "plus de détails").
- Maintenir une architecture légère sans base de données externe pour le MVP.

## Architecture Technique
- **Stockage:** Cache en mémoire vive (In-Memory) au sein du processus Maestro.
- **Identifiant:** Utilisation du `session_id` (ou `id` JSON-RPC) pour mapper l'état.
- **Logique de Routage:** 
    1. Si un agent est actif en session et que le score de l'intention actuelle est ambigu, privilégier l'agent actif.
    2. Si l'intention est radicalement différente (score > 0.9 pour un autre agent), changer d'agent.

## User Stories

### Story 5.1: Cache Mémoire et SessionStore
**Description:** Implémenter un `SessionStore` asynchrone utilisant un dictionnaire Python avec TTL (Time To Live).
- **AC 1:** Maestro peut stocker le dernier `agent_id` utilisé pour un `session_id`.
- **AC 2:** Les données expirent automatiquement après 10 minutes d'inactivité.
- **AC 3:** L'implémentation est abstraite via une interface pour permettre un passage futur à Redis.

### Story 5.2: Sticky Routing (Affinité d'Agent)
**Description:** Modifier la logique de `route_request` pour consulter le `SessionStore`.
- **AC 1:** Si un agent est actif, Maestro tente d'abord de router vers lui.
- **AC 2:** Implémentation d'un bonus de score contextuel (+30%) pour l'agent en cours lors de la classification.
- **AC 3:** La réponse de l'agent met à jour le TTL de la session.

### Story 5.3: Commandes d'Évasion et Reset
**Description:** Permettre à l'utilisateur de sortir explicitement d'un flux.
- **AC 1:** Mots-clés réservés ("stop", "annule", "reset", "quitter") réinitialisent la session.
- **AC 2:** Si le routeur sémantique détecte une intention forte (Top score > 0.95) pour un autre agent, le verrouillage est brisé.

## Critères d'Acceptation Globaux
- Le test E2E `test_e2e_golden_path.py` doit pouvoir être étendu pour valider une conversation en 2 étapes (Question -> Réponse contextuelle).
- Zéro impact sur les performances de Maestro (latence ajoutée < 5ms).
