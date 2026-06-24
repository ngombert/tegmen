# Story 5.1: Migration et Schéma de Persistance de Session (Alembic)

Status: ready-for-dev

## Story

As a développeur backend,
I want définir une table `user_sessions` dans la base Maestro et configurer sa migration via Alembic,
So that les sessions utilisateurs soient associées de manière unique et persistantes en base de données.

## Contexte

**FRs couvertes :** FR14 (Stockage et association de l'état de session au couple `(family_id, user_id)`), FR17 (Sauvegarde d'un résumé de contexte/historique en base)
**NFRs couvertes :** NFR10 (Isolation Maestro - gestion exclusive de l'état utilisateur dans la base `maestro`)

## Acceptance Criteria

### AC1 — Schéma de la Table de Session
- **Given** la base de données PostgreSQL de Maestro
- **When** j'applique la migration Alembic sous `src/agent_maestro/app/db/alembic/`
- **Then** la table `user_sessions` est créée avec les champs :
  - `id` (Integer/UUID, Clé primaire)
  - `family_id` (String(255), indexé, non nullable)
  - `user_id` (String(255), indexé, non nullable)
  - `session_id` (String(255), unique, non nullable)
  - `active_agent` (String(100), nullable)
  - `active_claim_check_id` (UUID/String, nullable)
  - `context_summary` (JSON/Text, nullable)
  - `updated_at` (DateTime avec fuseau horaire, mis à jour automatiquement)
  - `created_at` (DateTime avec fuseau horaire, valeur par défaut `NOW()`)
- **And** une contrainte d'unicité stricte (`UniqueConstraint`) est établie sur le couple `(family_id, user_id)`.

### AC2 — Isolation des Migrations
- **Given** la configuration d'Alembic dans le projet
- **When** je lance la migration de Maestro
- **Then** le script s'exécute uniquement sur la base `maestro` sans impacter les schémas des autres agents (Gourmet, Acadomie, Explorer).

---

## Tasks / Subtasks

### Task 1: Modélisation ORM de la Session Utilisateur (AC1)
- [ ] Créer le modèle SQLAlchemy `UserSession` dans `src/agent_maestro/app/db/models/user_session.py`
  - [ ] Définir les colonnes conformément aux critères de l'AC1
  - [ ] Ajouter l'indexation sur `family_id` et `user_id`
  - [ ] Déclarer la contrainte d'unicité composite sur `(family_id, user_id)`
  - [ ] Utiliser `func.now()` pour `created_at` et configurer le déclencheur onupdate pour `updated_at`
- [ ] Exposer le modèle `UserSession` dans `src/agent_maestro/app/db/models/__init__.py` pour permettre la détection automatique par Alembic

### Task 2: Génération et Exécution de la Migration Alembic (AC1, AC2)
- [ ] Générer une nouvelle révision de migration pour Maestro :
  - [ ] `cd src/agent_maestro && uv run alembic -c app/db/alembic.ini revision --autogenerate -m "create_user_sessions_table"`
  - [ ] Vérifier le fichier généré dans `src/agent_maestro/app/db/alembic/versions/`
- [ ] Appliquer la migration sur la base de données locale/docker :
  - [ ] `cd src/agent_maestro && uv run alembic -c app/db/alembic.ini upgrade head`
  - [ ] Valider que la table a bien été créée dans la base `maestro` uniquement

### Task 3: Tests d'Intégrité de Base de Données (AC1)
- [ ] Créer un test d'intégration `test_user_session_db_integrity` dans `tests/agent_maestro/test_user_session_schema.py`
  - [ ] Tester l'insertion d'une session valide
  - [ ] Tester la contrainte d'unicité : tenter d'insérer deux sessions différentes pour le même couple `(family_id, user_id)` et vérifier qu'une exception d'intégrité (`IntegrityError`) est levée
  - [ ] Tester que `updated_at` change correctement lors d'une mise à jour de ligne

---

## Dev Notes

- **Modèles de base :** Importer `Base` depuis `agent_maestro.app.db.base` pour hériter des métadonnées partagées de l'agent Maestro.
- **Isolation stricte (Pattern 2B) :** Ne pas importer ou mélanger les modèles de Maestro avec les modèles des agents spécialistes.
- **Fuseaux horaires :** Utiliser des objets DateTime avec fuseau horaire (`timezone=True`) pour éviter les divergences d'horloge entre les serveurs et la BDD.

### Project Structure Notes

- Le modèle doit résider dans `src/agent_maestro/app/db/models/user_session.py`.
- Le script de migration doit être généré dans l'environnement Alembic de l'agent Maestro (`src/agent_maestro/app/db/alembic/`).

### References

- [Architecture: docs/architecture.md#Data Architecture]
- [Source: _bmad-output/planning-artifacts/phase-2-persistance/epics.md#Story 5.1]

## Dev Agent Record

### Agent Model Used

{{agent_model_name_version}}

### Debug Log References

### Completion Notes List

### File List
