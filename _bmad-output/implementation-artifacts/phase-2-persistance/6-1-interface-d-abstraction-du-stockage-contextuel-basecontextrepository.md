# Story 6.1: Interface d'Abstraction du Stockage Contextuel (BaseContextRepository)

Status: ready-for-dev

## Story

As a développeur backend,
I want définir une interface abstraite pour le stockage du contexte,
So that je puisse découpler la logique d'hydratation A2A de la base de données sous-jacente et permettre une transition future vers Redis.

## Contexte

**FRs couvertes :** FR7 (Mémorisation de l'état lors d'une digression)
**NFRs couvertes :** NFR10 (Isolation Maestro - propriété exclusive du Context Stack par Maestro)

## Acceptance Criteria

### AC1 — Contrat de l'Interface d'Abstraction
- **Given** le fichier `src/common/context_repository.py`
- **When** je définis la classe abstraite `BaseContextRepository`
- **Then** elle expose les méthodes asynchrones indispensables suivantes avec des typages explicites :
  - `save_context(claim_key: str, payload: dict, ttl_seconds: int = 3600) -> None` : enregistre le payload associé à une clé avec un temps de vie (TTL)
  - `get_context(claim_key: str) -> Optional[dict]` : récupère le payload de contexte s'il existe et n'est pas expiré, sinon renvoie `None`
  - `delete_context(claim_key: str) -> None` : supprime explicitement un contexte
- **And** la classe hérite de `abc.ABC` et documente précisément les arguments et les exceptions attendues.

### AC2 — Indépendance de la Persistance
- **Given** les imports de `BaseContextRepository`
- **When** un module (par exemple `a2a_server.py` ou Maestro) utilise ce repository
- **Then** il ne doit dépendre d'aucune classe concrète de base de données (SQLAlchemy, Redis, etc.), garantissant une isolation totale de la logique métier.

---

## Tasks / Subtasks

### Task 1: Création du fichier d'interface (AC1)
- [ ] Créer le fichier `src/common/context_repository.py`
- [ ] Déclarer la classe abstraite `BaseContextRepository` en important `ABC` et `abstractmethod` de `abc`
- [ ] Implémenter les signatures et docstrings de `save_context`, `get_context`, et `delete_context`
- [ ] Définir des exceptions d'erreurs génériques pour le repository (ex: `ContextNotFoundError`, `ContextRepositoryError`) dans le même module ou dans `src/common/exceptions.py`

### Task 2: Validation de la compatibilité et types (AC1, AC2)
- [ ] Utiliser des annotations de type appropriées (`typing.Optional`, `typing.Any`, etc.)
- [ ] S'assurer qu'aucun import lié à SQLAlchemy ou à des bases de données réelles n'est présent dans ce fichier pour préserver l'isolation d'abstraction

---

## Dev Notes

- **Conception :** L'objectif principal de cette story est d'établir le contrat d'interface. Ne pas implémenter de logique de base de données concrète ici, celle-ci fera l'objet de la Story 6.2.
- **Pattern Claim Check :** Le `claim_key` (ou `claim_check_id`) est l'identifiant unique (généralement un UUID) qui sert de jeton pour récupérer ou modifier le contexte conversationnel à court terme.

### Project Structure Notes

- L'interface doit être placée dans `src/common/context_repository.py` car elle est partagée entre Maestro et le serveur A2A pour l'hydratation automatique des requêtes.

### References

- [Architecture: docs/architecture.md#API & Communication Patterns]
- [Source: _bmad-output/planning-artifacts/phase-2-persistance/epics.md#Story 6.1]

## Dev Agent Record

### Agent Model Used

{{agent_model_name_version}}

### Debug Log References

### Completion Notes List

### File List
