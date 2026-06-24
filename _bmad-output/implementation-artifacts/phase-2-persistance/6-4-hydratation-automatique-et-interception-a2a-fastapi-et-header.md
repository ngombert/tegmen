# Story 6.4: Hydratation Automatique et Interception A2A (FastAPI & Header)

Status: ready-for-dev

## Story

As a agent spécialiste,
I want recevoir automatiquement mon contexte hydraté et sécurisé sans écrire de code d'accès à la base de données,
So that je puisse me concentrer uniquement sur ma logique métier de traitement.

## Contexte

**FRs couvertes :** FR8 (Relancer automatiquement la session avec l'agent expert), FR14 (Accès sécurisé et transparent aux données de session)
**NFRs couvertes :** NFR7 (Intégrité des données), NFR10 (Isolation Maestro)

## Acceptance Criteria

### AC1 — Interception du Header A2A et Hydratation
- **Given** une requête JSON-RPC envoyée par Maestro à un agent spécialiste (ex: Gourmet)
- **When** la requête contient l'en-tête HTTP `X-Claim-Check-ID`
- **Then** le serveur FastAPI de l'agent spécialiste intercepte l'en-tête via le middleware ou une dépendance d'injection
- **And** le serveur récupère le payload de contexte associé à ce `claim_check_id` auprès de Maestro (ou du repository partagé)
- **And** il injecte un objet Pydantic de type `RequestContext` entièrement hydraté dans les paramètres du routeur de l'agent spécialiste.

### AC2 — Sécurisation de l'Appelant
- **Given** la dépendance d'hydratation de contexte `get_hydrated_context` dans `src/common/a2a_server.py`
- **When** elle est invoquée lors d'une requête A2A
- **Then** elle extrait l'identité de l'appelant (`user_id` et `family_id` transmis dans les métadonnées de requête ou les headers)
- **And** elle applique le contrôle d'accès ACL défini dans la Story 6.3 auprès du repository de contexte
- **And** elle bloque l'exécution et renvoie une erreur si l'appelant n'est pas autorisé à consulter ou modifier ce contexte.

---

## Tasks / Subtasks

### Task 1: Création du Middleware / Dépendance d'Hydratation A2A (AC1, AC2)
- [ ] Modifier `src/common/a2a_server.py`
  - [ ] Importer `BaseContextRepository` et l'exception `ContextAccessDeniedError`
  - [ ] Implémenter la dépendance FastAPI `get_hydrated_context` :
    - [ ] Extraire `X-Claim-Check-ID` de l'en-tête de requête FastAPI (`request.headers`)
    - [ ] Extraire les identifiants d'identité `X-User-ID` et `X-Family-ID` (ou décoder le jeton de sécurité A2A disponible)
    - [ ] Si `X-Claim-Check-ID` est absent, retourner `None` ou un contexte vierge (rétrocompatibilité Phase 1)
    - [ ] Si présent, charger le contexte depuis le repository injecté en effectuant le contrôle ACL avec le `user_id` extrait
    - [ ] Convertir les données chargées en une instance du schéma Pydantic `RequestContext` ou équivalent
- [ ] Injecter la dépendance dans la signature des fonctions d'endpoints A2A :
  ```python
  async def handle_rpc_request(payload: RPCRequest, context: RequestContext = Depends(get_hydrated_context)):
  ```

### Task 2: Transmission du Header côté Client A2A (AC1)
- [ ] Mettre à jour le client A2A dans `src/common/a2a_client.py`
  - [ ] Modifier la méthode d'appel (ex: `send_request` ou `call_agent`) pour accepter un paramètre optionnel `claim_check_id: Optional[str] = None`
  - [ ] Si `claim_check_id` est spécifié, l'ajouter automatiquement aux en-têtes HTTP de la requête sortante sous le nom `X-Claim-Check-ID`
  - [ ] Transmettre également l'identité de l'utilisateur demandeur dans les en-têtes (ex: `X-User-ID`, `X-Family-ID`) de manière sécurisée

### Task 3: Tests d'Intégration A2A avec Hydratation (AC1, AC2)
- [ ] Écrire des tests d'intégration dans `tests/common/test_a2a_hydrator.py`
  - [ ] Simuler une requête A2A sans en-tête `X-Claim-Check-ID` et valider qu'aucune erreur n'est levée (rétrocompatibilité)
  - [ ] Simuler une requête A2A avec un `X-Claim-Check-ID` valide, vérifier que le contexte est correctement hydraté et reçu par la fonction de l'agent spécialiste
  - [ ] Simuler une requête avec un `X-Claim-Check-ID` pour lequel le demandeur n'a pas les droits ACL, et valider que la dépendance lève un rejet HTTP 403 / code d'erreur JSON-RPC approprié

---

## Dev Notes

- **Zéro Couplage DB pour les Agents (Pattern 2B) :** Les agents spécialistes n'ont pas besoin de se connecter à la base de données Maestro. Le middleware de `a2a_server.py` peut faire un appel A2A interne vers Maestro (ex: un endpoint technique `/context/retrieve`) pour récupérer le contexte, ou utiliser un repository partagé si les agents partagent le même réseau de données à accès direct. L'approche d'appel API interne vers Maestro (Gateway) est hautement recommandée pour conserver l'isolation stricte des bases de données.
- **Rétrocompatibilité (NFR9) :** Les requêtes sans `X-Claim-Check-ID` doivent être traitées nominalement, en fournissant un contexte vide ou par défaut.

### Project Structure Notes

- Le code d'interception et d'hydratation doit être implémenté de manière générique dans `src/common/a2a_server.py` et `src/common/a2a_client.py` pour bénéficier à tous les agents de l'écosystème.

### References

- [Architecture: docs/architecture.md#API & Communication Patterns]
- [Source: _bmad-output/planning-artifacts/phase-2-persistance/epics.md#Story 6.4]

## Dev Agent Record

### Agent Model Used

{{agent_model_name_version}}

### Debug Log References

### Completion Notes List

### File List
