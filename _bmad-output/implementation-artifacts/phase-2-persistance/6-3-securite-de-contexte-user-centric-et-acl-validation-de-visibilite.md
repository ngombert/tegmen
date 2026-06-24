# Story 6.3: Sécurité de Contexte User-Centric et ACL (Validation de Visibilité)

Status: ready-for-dev

## Story

As a utilisateur de la famille,
I want que mes contextes de discussion privés (notes personnelles, surprises) soient inaccessibles aux autres membres de la famille,
So that mon intimité et le secret de mes actions soient garantis.

## Contexte

**FRs couvertes :** FR14 (Contextes isolés et sécurisés par couple `family_id` et `user_id`)
**NFRs couvertes :** NFR10 (Isolation stricte et sécurité d'accès aux données de session)

## Acceptance Criteria

### AC1 — Attribution des droits de propriété et d'accès
- **Given** la création d'un nouveau contexte dans le repository
- **When** Maestro ou un agent sauvegarde ce contexte
- **Then** il doit obligatoirement spécifier un `owner_id` (propriétaire, typiquement le `user_id` de l'utilisateur ayant initié l'échange) et une liste optionnelle d'utilisateurs autorisés `authorized_users` (contenant au moins le propriétaire).

### AC2 — Contrôle d'accès strict (ACL)
- **Given** un contexte existant dans le repository associé à un propriétaire `owner_id` et à une liste `authorized_users`
- **When** un utilisateur identifié par son `requester_user_id` tente de charger ce contexte (via `get_context` ou via l'intercepteur A2A)
- **Then** l'accès est immédiatement autorisé si `requester_user_id == owner_id` ou si `requester_user_id` est inclus dans `authorized_users`
- **And** si l'utilisateur n'est pas autorisé, le système lève une exception de sécurité stricte `ContextAccessDeniedError` (qui produit une réponse HTTP 403 Forbidden au niveau de l'API Gateway/Maestro, et empêche l'hydratation du contexte de l'expert).

---

## Tasks / Subtasks

### Task 1: Extension des méthodes du Repository (AC1, AC2)
- [ ] Modifier les signatures de `BaseContextRepository` et `PostgresContextRepository` pour inclure le contrôle d'accès
  - [ ] Mettre à jour `save_context` pour accepter et enregistrer les paramètres `owner_id: str` et `authorized_users: list[str]`
  - [ ] Mettre à jour `get_context` pour accepter un paramètre `requester_user_id: str`
- [ ] Implémenter la logique ACL à l'intérieur de `get_context` :
  - [ ] Récupérer la ligne de contexte correspondante
  - [ ] Si aucune ligne n'est trouvée ou si elle est expirée, renvoyer `None`
  - [ ] Si le contexte existe, vérifier si `requester_user_id == owner_id` ou si `requester_user_id in authorized_users`
  - [ ] Si la vérification échoue, lever `ContextAccessDeniedError` (définie à l'étape suivante)

### Task 2: Définition de l'Exception de Sécurité et Gestion des Erreurs (AC2)
- [ ] Créer la classe d'exception `ContextAccessDeniedError` dans `src/common/exceptions.py`
  - [ ] Elle doit hériter de `PermissionError`
  - [ ] Elle doit inclure des attributs d'informations (ex: `user_id` demandeur, `owner_id` du contexte)
- [ ] Adapter Maestro (`src/agent_maestro/main.py`) pour intercepter cette exception et retourner un code d'erreur JSON-RPC normalisé (ou un code HTTP 403) avec un message d'erreur clair et sécurisé (ex: "Accès non autorisé au contexte demandé").

### Task 3: Écriture des Tests d'Intrusions et de Sécurité (AC1, AC2)
- [ ] Créer le fichier de test `tests/test_context_security.py` conformément aux instructions de test
  - [ ] **Arrange :** Insérer un contexte avec `owner_id="papa"` et `authorized_users=["papa", "maman"]`
  - [ ] **Act & Assert (Happy Path) :** Vérifier que "papa" et "maman" peuvent lire le contexte avec succès
  - [ ] **Act & Assert (Intruder Path) :** Tenter de lire le contexte en tant que "enfant_leo" et vérifier qu'une exception `ContextAccessDeniedError` est bien levée
  - [ ] **Act & Assert (None User) :** Tenter de lire le contexte avec un identifiant vide ou invalide et valider le rejet immédiat

---

## Dev Notes

- **Intimité intra-foyer (Use Case) :** Ce contrôle d'accès est capital pour éviter que les enfants ne découvrent les préparatifs d'une surprise parentale (ex: voyage surprise) ou que des informations scolaires privées ne soient divulguées entre enfants.
- **Principe du Moindre Privilège :** Par défaut, si `authorized_users` n'est pas spécifié lors de la sauvegarde du contexte, il doit être initialisé avec uniquement le `owner_id` (accès strictement personnel).

### Project Structure Notes

- L'exception doit être ajoutée à `src/common/exceptions.py`.
- La logique de sécurité doit être validée dans `src/infrastructure/postgres_context_repository.py` et exposée dans `tests/test_context_security.py`.

### References

- [Architecture: docs/architecture.md#Authentication & Security]
- [Source: _bmad-output/planning-artifacts/phase-2-persistance/epics.md#Story 6.3]

## Dev Agent Record

### Agent Model Used

{{agent_model_name_version}}

### Debug Log References

### Completion Notes List

### File List
