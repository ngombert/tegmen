# Story 5.2: Implémentation du PostgresSessionStore

Status: done

## Story

As a agent système (Maestro),
I want utiliser un adaptateur `PostgresSessionStore` implémentant l'interface `BaseSessionStore`,
So that je puisse enregistrer et charger l'état de session de l'utilisateur de manière asynchrone et transparente.

## Contexte

**FRs couvertes :** FR14 (Stockage de l'affinité avec l'agent actif), FR15 (Chargement automatique de la session active lors d'une reconnexion/rafraîchissement), FR16 (Purger l'état de session lors d'une action d'escape/annulation)
**NFRs couvertes :** NFR11 (Temps de lecture/écriture en BDD inférieur à 50ms)

## Acceptance Criteria

### AC1 — Contrat d'Interface Respecté
- **Given** la classe abstraite `BaseSessionStore` définie dans `src/agent_maestro/session.py`
- **When** j'implémente la classe `PostgresSessionStore`
- **Then** elle hérite de `BaseSessionStore` et propose des surcharges asynchrones robustes pour :
  - `get(session_id) -> Optional[str]`
  - `set(session_id, agent_id)`
  - `delete(session_id)`
- **And** elle ajoute une méthode spécifique pour retrouver l'état de session par couple de clés : `get_by_user(family_id, user_id) -> Optional[UserSession]` et `set_by_user(family_id, user_id, session_id, agent_id, active_claim_check_id=None, context_summary=None)`.

### AC2 — Performances et Caching
- **Given** une requête utilisateur nécessitant l'accès aux données de session
- **When** Maestro effectue la lecture ou l'écriture en base de données
- **Then** l'impact sur la latence de traitement est strictement inférieur à 50ms (NFR11)
- **And** le store utilise des requêtes asynchrones non-bloquantes via SQLAlchemy asynchrone.

### AC3 — Purge de Session lors de l'Escape
- **Given** une session active enregistrée en base de données
- **When** l'utilisateur envoie une commande d'annulation/escape ("Laisse tomber ce sujet", "annuler")
- **Then** Maestro appelle la méthode `delete` (ou purge l'affinité `active_agent` et le claim de contexte associé)
- **And** la session en base de données est réinitialisée ou supprimée.

---

## Tasks / Subtasks

### Task 1: Implémentation du PostgresSessionStore (AC1, AC2)
- [x] Créer la classe `PostgresSessionStore` héritant de `BaseSessionStore` dans `src/agent_maestro/app/services/session_store.py` (ou directement dans `src/agent_maestro/session.py`)
  - [x] Injecter la session de base de données asynchrone (`AsyncSession` ou `async_session_factory`) de Maestro dans le constructeur
  - [x] Implémenter `get(session_id) -> Optional[str]` : recherche la session par `session_id` et retourne l'agent actif associé
  - [x] Implémenter `set(session_id, agent_id)` : crée ou met à jour l'agent actif associé à une session
  - [x] Implémenter `delete(session_id)` : supprime la ligne correspondante
  - [x] Implémenter les méthodes d'accès par utilisateur `get_by_user` et `set_by_user` utilisant le couple `(family_id, user_id)` conformément à FR14
- [x] Assurer la gestion du TTL si nécessaire ou s'appuyer sur la persistance permanente des sessions avec mise à jour du champ `updated_at`

### Task 2: Intégration du PostgresSessionStore dans Maestro (AC3)
- [x] Mettre à jour `src/agent_maestro/main.py`
  - [x] Remplacer l'instance globale de `InMemorySessionStore` par `PostgresSessionStore`
  - [x] Utiliser la factory de session asynchrone de Maestro pour alimenter le store de manière sécurisée lors des requêtes
- [x] Modifier la logique d'interception d'escape (escape commands, ex: "annuler", "laisse tomber") dans `src/agent_maestro/main.py` pour vider l'affinité de l'agent et effacer le contexte de session en base (FR16)

### Task 3: Validation des Performances et Tests (AC1, AC2, AC3)
- [x] Écrire des tests unitaires et d'intégration dans `tests/agent_maestro/test_postgres_session_store.py`
  - [x] Valider le bon déroulement du cycle de vie de la session (création, mise à jour, chargement automatique au rafraîchissement, suppression)
  - [x] Mesurer la latence des appels de base de données pour s'assurer qu'elle reste largement sous la barre des 50ms
  - [x] Simuler une commande d'escape et vérifier que les données de session en BDD sont purgées

---

## Dev Notes

- **Gestion des sessions de base de données :** Veiller à ne pas laisser de sessions SQLAlchemy ouvertes. Utiliser un bloc `async with` ou s'appuyer sur le cycle de vie de la requête FastAPI s'il s'agit d'une dépendance injectée.
- **Résilience (Fail Fast) :** Suite aux consignes explicites de l'utilisateur, l'implémentation applique un principe strict de "Fail Fast" en cas de panne de base de données (pas de repli dégradé en mémoire locale) pour préserver l'intégrité absolue de l'historique et des préférences.

### Project Structure Notes

- Le store doit être implémenté dans `src/agent_maestro/session.py` (ou un nouveau module de service sous `src/agent_maestro/app/services/session_store.py` importé par `session.py`).

### References

- [Architecture: docs/architecture.md#Data Architecture]
- [Source: _bmad-output/planning-artifacts/phase-2-persistance/epics.md#Story 5.2]

## Dev Agent Record

### Agent Model Used

Antigravity (gemini-1.5-pro-like)

### Debug Log References

- [test-run-log](file:///home/nicolas/.gemini/antigravity/brain/c88360f4-4ab0-48d9-ab97-ae8349ca6460/.system_generated/tasks/task-243.log)

### Completion Notes List

- Adaptateur PostgresSessionStore écrit et exposé.
- Remplacement du store InMemory par PostgresSessionStore dans main.py.
- Intégration de l'identité utilisateur (family_id, user_id) pour le chargement et la mise à jour automatique des sessions actives.
- Purge de session et nettoyage du contexte BDD sur réception d'une commande d'escape validés par des tests unitaires et fonctionnels complets (AsyncClient).

### File List

- [session_store.py](file:///home/nicolas/projects/tegmen/src/agent_maestro/app/services/session_store.py)
- [session.py](file:///home/nicolas/projects/tegmen/src/agent_maestro/session.py)
- [main.py](file:///home/nicolas/projects/tegmen/src/agent_maestro/main.py)
- [test_postgres_session_store.py](file:///home/nicolas/projects/tegmen/tests/agent_maestro/test_postgres_session_store.py)
- [test_maestro_escape_commands.py](file:///home/nicolas/projects/tegmen/tests/test_maestro_escape_commands.py)
