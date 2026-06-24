# Story 6.2: Implémentation du PostgresContextRepository et Gestion du TTL

Status: ready-for-dev

## Story

As a développeur backend,
I want implémenter le repository pour PostgreSQL avec gestion automatique de la péremption,
So that les contextes de discussion à court terme soient persistés de manière performante et automatiquement purgés après expiration.

## Contexte

**FRs couvertes :** FR7 (Mémorisation du contexte en BDD lors d'une digression), FR8b (Nettoyage silencieux de la pile si l'interruption s'éternise - Garbage Collection)
**NFRs couvertes :** NFR10 (Isolation Maestro - gestion dans la base `maestro`)

## Acceptance Criteria

### AC1 — Schéma de la Table de Stockage Contextuel
- **Given** la base de données PostgreSQL de Maestro
- **When** j'applique la migration Alembic sous `src/agent_maestro/app/db/alembic/`
- **Then** la table `context_store` (ou `context_claims`) est créée avec les champs suivants :
  - `claim_check_id` (UUID, Clé primaire, indexé)
  - `context_data` (JSONB, non nullable)
  - `expires_at` (DateTime avec fuseau horaire, indexé, non nullable)
  - `owner_id` (String(255), non nullable)
  - `authorized_users` (JSON, non nullable, ex: liste d'identifiants autorisés)
  - `created_at` (DateTime avec fuseau horaire, valeur par défaut `NOW()`)

### AC2 — Implémentation Concrète de BaseContextRepository
- **Given** la classe abstraite `BaseContextRepository`
- **When** j'instancie `PostgresContextRepository`
- **Then** elle implémente toutes les méthodes (`save_context`, `get_context`, `delete_context`) en utilisant SQLAlchemy asynchrone pour interagir avec la table `context_store`
- **And** la méthode `get_context` filtre automatiquement les contextes pour ne retourner les données que si `expires_at >= NOW()` (retourne `None` si expiré).

### AC3 — Garbage Collection des Contextes Expirés
- **Given** des contextes obsolètes dont la date d'expiration est dépassée (`expires_at < NOW()`)
- **When** le service de nettoyage (Garbage Collection) s'exécute
- **Then** tous les contextes expirés sont supprimés de la table de manière performante en une seule opération SQL.

---

## Tasks / Subtasks

### Task 1: Modélisation ORM et Schéma Alembic (AC1)
- [ ] Définir le modèle ORM `ContextStore` dans `src/agent_maestro/app/db/models/context_store.py`
  - [ ] Importer `Base` de `agent_maestro.app.db.base`
  - [ ] Ajouter les colonnes définies à l'AC1 avec les index pertinents sur `claim_check_id` et `expires_at`
- [ ] Exposer le modèle dans `src/agent_maestro/app/db/models/__init__.py`
- [ ] Générer la migration Alembic correspondante :
  - [ ] `cd src/agent_maestro && uv run alembic -c app/db/alembic.ini revision --autogenerate -m "create_context_store_table"`
  - [ ] Appliquer la migration sur la base locale/docker

### Task 2: Implémentation du PostgresContextRepository (AC2)
- [ ] Créer le fichier `src/infrastructure/postgres_context_repository.py`
- [ ] Implémenter la classe `PostgresContextRepository` héritant de `BaseContextRepository`
  - [ ] Injecter la session asynchrone SQLAlchemy dans le constructeur
  - [ ] Implémenter `save_context(claim_key, payload, ttl_seconds)` : calcule `expires_at = datetime.utcnow() + timedelta(seconds=ttl_seconds)` et insère ou met à jour l'enregistrement dans la table
  - [ ] Implémenter `get_context(claim_key)` : requête la table pour `claim_check_id == claim_key` et `expires_at >= func.now()`. Retourne le dictionnaire `context_data` ou `None`
  - [ ] Implémenter `delete_context(claim_key)` : supprime l'enregistrement

### Task 3: Tâche de Nettoyage (Garbage Collector) (AC3)
- [ ] Ajouter une méthode asynchrone `clean_expired_contexts()` dans `PostgresContextRepository` effectuant un `DELETE FROM context_store WHERE expires_at < NOW()`
- [ ] Dans `src/agent_maestro/main.py`, configurer une tâche de fond périodique (FastAPI background task ou boucle asynchrone de fond) s'exécutant à intervalles réguliers (ex: toutes les 60 secondes) pour appeler ce nettoyage

### Task 4: Tests Unitaires et d'Intégration (AC2, AC3)
- [ ] Créer la suite de tests dans `tests/agent_maestro/test_postgres_context_repository.py`
  - [ ] Valider l'insertion, la récupération et la suppression de contextes
  - [ ] Valider qu'un contexte expiré (dont le TTL est dépassé de quelques secondes) renvoie bien `None` lors d'un `get_context`
  - [ ] Valider que le Garbage Collector élimine bien les lignes expirées de la table

---

## Dev Notes

- **Gestion des fuseaux horaires :** Utiliser de préférence `datetime.now(timezone.utc)` au lieu de `datetime.utcnow()` car ce dernier est obsolète en Python moderne, et s'assurer que PostgreSQL interprète correctement les fuseaux horaires (`TIMESTAMPTZ` ou `DateTime(timezone=True)`).
- **Isolation :** Bien que ce repository soit utilisé par le middleware A2A, c'est Maestro qui héberge la table physique et fournit l'accès. Les agents spécialisés n'interrogent pas directement cette table, ils reçoivent le contexte hydraté par le réseau.

### Project Structure Notes

- Le modèle SQLAlchemy réside dans `src/agent_maestro/app/db/models/context_store.py`.
- L'implémentation du repository réside dans `src/infrastructure/postgres_context_repository.py`.

### References

- [Architecture: docs/architecture.md#Data Architecture]
- [Source: _bmad-output/planning-artifacts/phase-2-persistance/epics.md#Story 6.2]

## Dev Agent Record

### Agent Model Used

{{agent_model_name_version}}

### Debug Log References

### Completion Notes List

### File List
