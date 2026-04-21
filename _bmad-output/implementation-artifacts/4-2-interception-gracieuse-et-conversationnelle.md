# Story 4.2: Interception "Gracieuse" et Conversationnelle

Status: done

## Story

As a Utilisateur (Famille),
I want qu'en cas de panne système, l'erreur soit interceptée pour prévenir le crash avec un code technique (500),
so that je reçoive une phrase d'explication douce de la part du bot.

## Acceptance Criteria

1. **Exception Handler Global** : Un `exception_handler` FastAPI est enregistré dans `main.py`.
2. **Interception des Erreurs A2A** : Les erreurs `A2ARPCError` (Timeout, ConnectionRefused) sont capturées.
3. **Réponse Dégradée** : Au lieu d'une erreur JSON brute, le système retourne une réponse JSON-RPC valide contenant un message d'excuse convivial (ex: "Désolé, l'agent spécialisé ne répond pas pour le moment...").
4. **Maintien de la Structure** : La réponse doit respecter le format `JsonRpcResponse` avec le champ `result` contenant le message de fallback ou un champ `error` explicatif.

## Tasks / Subtasks

- [ ] Task 1 : Implémenter l'Exception Handler dans `main.py`.
- [ ] Task 2 : Définir les messages de fallback conversationnels dans `src/common/utils.py` ou `config.py`.
- [ ] Task 3 : Valider avec un test unitaire simulant une exception non gérée.

## Dev Notes

### Architecture & Contraintes
- Utiliser `@app.exception_handler(A2ARPCError)`.
- S'assurer que le status code HTTP reste 200 (OK) pour JSON-RPC si le protocole le permet, ou 500 avec un corps structuré.
- Le message doit être localisé (Français par défaut).

## Dev Agent Record

### Agent Model Used
N/A

### Completion Notes
- Ajout de `FALLBACK_RESPONSES` dans `main.py` pour des réponses humaines.
- Implémentation d'un `exception_handler` FastAPI pour `A2ARPCError`.
- Capture des erreurs dans `route_request` et `chat` pour retourner une réponse 200 OK structurée avec un message convivial.
- Validation réussie via tests d'intégration simulant un timeout d'agent.
