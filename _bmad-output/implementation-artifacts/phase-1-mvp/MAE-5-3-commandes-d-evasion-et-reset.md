# Story 5.3: Commandes d'Évasion et Reset

## Story Foundation
**Description:** Permettre à l'utilisateur de sortir explicitement d'un flux et de briser le "Sticky Routing".

### Acceptance Criteria
- **AC 1:** Des mots-clés réservés (ex: "stop", "annule", "reset", "quitter") permettent de réinitialiser la session (suppression du lien avec l'agent actif).
- **AC 2:** Si le routeur sémantique détecte une intention forte (Top score > 0.95) pour un autre agent, le verrouillage est brisé et la nouvelle intention l'emporte, effaçant ainsi l'ancienne session.

## Developer Context

### Technical Requirements
- Mots-clés réservés : Il faut intercepter ces mots (insensibles à la casse) avant même de faire passer la requête au routeur sémantique ou alors en faire une règle de pré-classification.
- Briser le verrouillage : Le score brut d'une autre intention (avant l'application du bonus de 1.3 à l'agent actif) doit être comparé à un seuil très élevé (`> 0.95`). Si un autre agent dépasse 0.95, il l'emporte quoiqu'il arrive et la session est mise à jour avec ce nouvel agent.

### Architecture Compliance
- Ne pas introduire de latence excessive.
- Continuer à utiliser `InMemorySessionStore`.
- Les mots-clés peuvent être gérés soit par une route spéciale dans `router.py`, soit par une simple vérification RegEx/liste dans `main.py` avant d'appeler `classify_intent`. La deuxième solution est souvent plus rapide pour des commandes d'évasion strictes.

### File Structure Requirements
- `src/agent_maestro/main.py` : Interception des mots-clés de reset pour effacer le cache (`await session_store.delete(session_id)`) et répondre ou continuer le flux.
- `src/agent_maestro/router.py` : Modifier `classify_intent` pour appliquer la règle du > 0.95 (Escape hatch sémantique).

### Testing Requirements
- Nouveaux tests pour valider que les mots-clés suppriment la session.
- Tests pour valider qu'un score très fort (ex: 0.96 pour "explorer") bat un agent actif ("gourmet") même avec son bonus.

## Status
Status: ready-for-dev
