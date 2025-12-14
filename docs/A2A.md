# Protocol A2A (Agent-to-Agent)

## Vue d'ensemble
Le protocole A2A permet aux agents de l'écosystème Family-Agents de communiquer entre eux de manière standardisée. Il repose sur **JSON-RPC 2.0** transporté via **HTTP**.

## Architecture
Le système utilise une architecture en étoile où un agent central, le **Maestro**, route les demandes vers des agents spécialistes.

```
[Client Web/Mobile] <---> [Maestro (Router)] <---> [Agents Spécialistes]
```

## Découverte (Agent Card)
Chaque agent expose une "Carte d'Identité" (Agent Card) via l'endpoint public `/.well-known/agent-card.json`.
Cette carte contient les métadonnées de l'agent et ses capacités (skills).

### Exemple de Agent Card
```json
{
  "name": "agent_gourmet",
  "description": "Expert en cuisine et recettes.",
  "skills": [
    {
      "id": "recipe_search",
      "name": "Recherche de recette",
      "description": "Trouver des recettes selon ingrédients"
    }
  ]
}
```

## Communication JSON-RPC
Les échanges se font via des messages JSON-RPC.

### Requête (Maestro -> Spécialiste)
Le Maestro envoie une requête pour déléguer une tâche.

```json
{
  "jsonrpc": "2.0",
  "method": "generate_response",
  "params": {
    "message": "Trouve-moi une recette de lasagnes",
    "context": {
      "session_id": "12345",
      "user_preferences": {...}
    }
  },
  "id": 1
}
```

### Réponse (Spécialiste -> Maestro)
L'agent spécialiste traite la demande (éventuellement en utilisant ses outils internes) et renvoie une réponse textuelle.

```json
{
  "jsonrpc": "2.0",
  "result": {
    "message": "Voici une recette de lasagnes classiques...",
    "data": { ... } // Données structurées optionnelles
  },
  "id": 1
}
```

## Implémentation
Le projet utilise `a2a-sdk` pour faciliter la création de ces serveurs et clients.
- **Server** : `src/common/a2a_server.py`
- **Client** : `src/common/a2a_client.py`
