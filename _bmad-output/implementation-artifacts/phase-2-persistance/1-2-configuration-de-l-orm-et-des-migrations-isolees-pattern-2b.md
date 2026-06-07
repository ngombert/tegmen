# Story 1.2: Configuration de l'ORM et des Migrations Isolées (Pattern 2B)

Status: done

## Story

As a administrateur système,
I want configurer SQLAlchemy asynchrone et Alembic de manière indépendante pour chaque microservice existant,
so that je puisse déployer chaque agent avec un Zero Downtime contrôlé sans risque de conflit avec le reste de l'écosystème.

## Dépendances

- **Story 1.1** (Provisionnement PostgreSQL Hybride) doit être **terminée**. Elle fournit le conteneur `pgvector/pgvector:pg18`, le script `scripts/init-multiple-dbs.sh` avec activation de l'extension `vector`, et les 4 bases logiques (maestro, gourmet, acadomie, explorer).

## Acceptance Criteria

1. **Given** les microservices de la plateforme (`agent_maestro`, `agent_gourmet`, `agent_acadomie`, `agent_explorer`)
   **When** j'initialise l'environnement de base de données
   **Then** chaque agent possède son propre environnement Alembic isolé dans `src/<agent_name>/app/db/alembic/`

2. **Given** un agent avec son environnement Alembic configuré
   **When** l'agent démarre et se connecte à la base de données
   **Then** il utilise une connexion asynchrone (`asyncpg`) pointant vers sa propre base logique via la variable d'environnement `DATABASE_URL`

3. **Given** deux agents avec des environnements Alembic distincts
   **When** j'exécute une migration dans un agent (ex: `alembic upgrade head` dans `agent_gourmet`)
   **Then** la structure de la base de données de l'autre agent reste intacte et inchangée

4. **Given** un agent avec son module `db/` configuré
   **When** je crée un nouveau modèle ORM et génère une migration via `alembic revision --autogenerate`
   **Then** la migration est générée dans le dossier `versions/` spécifique à cet agent et ne référence aucun modèle d'un autre agent

5. **Given** l'ensemble du projet
   **When** je lance la suite de tests
   **Then** les tests vérifient que chaque agent peut créer indépendamment son engine, sa session factory, et exécuter une migration de test sans interférence

## Tasks / Subtasks

- [x] **Task 1 — Ajouter Alembic aux dépendances** (AC: #1, #4)
  - [x] Exécuter `uv add alembic>=1.18.4` pour ajouter la dépendance Alembic au `pyproject.toml`
  - [x] Vérifier que `uv.lock` is mis à jour et que `alembic` est disponible dans l'environnement

- [x] **Task 2 — Créer le module `db/` de base pour `common/`** (AC: #2, #4)
  - [x] Refactorer `src/common/database.py` pour en faire un module **réutilisable et paramétrable** (factory pattern) plutôt qu'un singleton global avec `config.DATABASE_URL` en dur
  - [x] Créer la fonction factory `create_async_engine_for_agent(database_url: str, debug: bool = False) -> AsyncEngine`
  - [x] Créer la fonction factory `create_session_factory(engine: AsyncEngine) -> async_sessionmaker[AsyncSession]`
  - [x] Conserver la classe `Base(DeclarativeBase)` dans `common/database.py` — Mais **ATTENTION** : chaque agent devra définir sa propre `Base` locale dans `app/db/base.py` pour l'isolation des metadata Alembic (voir Task 3)
  - [x] Conserver le helper `get_db()` comme dépendance FastAPI générique (en le rendant paramétrable via la session_factory)

- [x] **Task 3 — Créer le module `db/` isolé pour chaque agent** (AC: #1, #2)
  - [x] Pour chaque agent (`agent_maestro`, `agent_gourmet`, `agent_acadomie`, `agent_explorer`), créer la structure :
    ```
    src/<agent_name>/app/db/
    ├── __init__.py
    ├── base.py          # Base déclarative locale + metadata naming_convention
    ├── session.py       # Engine & session factory utilisant les factories de common
    └── models/
        └── __init__.py  # Import centralisé des modèles futurs
    ```
  - [x] Dans `base.py` de chaque agent : définir `class Base(DeclarativeBase)` avec `metadata = MetaData(naming_convention={...})` — **NE PAS** importer `Base` depuis `common/database.py` pour garantir l'isolation des metadata
  - [x] Dans `session.py` de chaque agent : créer l'engine et la session factory en lisant `DATABASE_URL` depuis `os.environ` (ou `common.config`) et en utilisant les factories de `common/database.py`
  - [x] Dans `session.py` : exposer `get_db()` comme dépendance FastAPI locale à l'agent
  - [x] La `naming_convention` pour MetaData doit être identique entre tous les agents pour la cohérence :
    ```python
    NAMING_CONVENTION = {
        "ix": "ix_%(table_name)s_%(column_0_N_name)s",
        "uq": "uq_%(table_name)s_%(column_0_N_name)s",
        "ck": "ck_%(table_name)s_%(constraint_name)s",
        "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
        "pk": "pk_%(table_name)s",
    }
    ```

- [x] **Task 4 — Initialiser les environnements Alembic isolés** (AC: #1, #3, #4)
  - [x] Pour chaque agent, initialiser Alembic avec le template async :
    ```bash
    cd src/<agent_name>/app/db
    alembic init -t async alembic
    ```
  - [x] Structure résultante par agent :
    ```
    src/<agent_name>/app/db/
    ├── alembic/
    │   ├── env.py         # Configuré pour cet agent
    │   ├── script.py.mako # Template de migration
    │   └── versions/      # Vide au départ
    ├── alembic.ini        # Config Alembic locale
    ├── base.py
    ├── session.py
    └── models/
        └── __init__.py
    ```
  - [x] Configurer `alembic.ini` de chaque agent :
    - `script_location = alembic` (chemin relatif)
    - `sqlalchemy.url` : laisser vide ou placeholder (sera surchargé par `env.py`)
  - [x] Configurer `env.py` de chaque agent :
    - Importer `Base.metadata` depuis `<agent_name>.app.db.base` (PAS depuis common)
    - Importer les modèles de `<agent_name>.app.db.models` pour que l'autogenerate les détecte
    - Surcharger `sqlalchemy.url` depuis la variable d'environnement `DATABASE_URL`
    - Utiliser `async_engine_from_config` avec `poolclass=pool.NullPool`
    - Implémenter `run_async_migrations()` pattern standard (voir section Dev Notes)

- [x] **Task 5 — Créer une migration initiale de preuve** (AC: #3, #4)
  - [x] Pour **un seul agent** (ex: `agent_maestro`), créer un modèle de test minimal `HealthCheck` dans `app/db/models/health_check.py` :
    ```python
    class HealthCheck(Base):
        __tablename__ = "health_checks"
        id: Mapped[int] = mapped_column(primary_key=True)
        checked_at: Mapped[datetime] = mapped_column(
            DateTime(timezone=True), server_default=func.now()
        )
    ```
  - [x] Générer la migration : `alembic revision --autogenerate -m "initial_health_check"`
  - [x] Vérifier que la migration est dans `src/agent_maestro/app/db/alembic/versions/`
  - [x] Exécuter `alembic upgrade head` sur la base `maestro`
  - [x] Vérifier que les bases `gourmet`, `acadomie`, `explorer` n'ont **aucune** table `health_checks`

- [x] **Task 6 — Mettre à jour les variables d'environnement** (AC: #2)
  - [x] Vérifier / compléter dans `docker-compose.yml` que chaque service possède sa variable `DATABASE_URL` pointant vers sa base logique dédiée :
    - `maestro`: `postgresql+asyncpg://maestro:maestro@db:5432/maestro` (déjà présent)
    - `gourmet`: `postgresql+asyncpg://gourmet:gourmet@db:5432/gourmet` (déjà présent)
    - `acadomie`: `postgresql+asyncpg://acadomie:acadomie@db:5432/acadomie` **MANQUANT** — à ajouter
    - `explorer`: `postgresql+asyncpg://explorer:explorer@db:5432/explorer` (déjà présent)
  - [x] S'assurer que le service `acadomie` dans `docker-compose.yml` a bien un `depends_on: db: condition: service_healthy` (actuellement manquant)
  - [x] Mettre à jour `.env.example` avec les 4 DATABASE_URL pour le développement local hors Docker

- [x] **Task 7 — Intégrer le module db dans le lifespan des agents** (AC: #2)
  - [x] Pour chaque agent, mettre à jour le `lifespan` dans `main.py` pour :
    - Importer et initialiser l'engine au démarrage (log de connexion réussie)
    - Disposer proprement de l'engine au shutdown (`await engine.dispose()`)
  - [x] **INTERDIT** : N'exécuter **AUCUNE** migration automatique au démarrage (`alembic upgrade head` dans `main.py` est FORMELLEMENT INTERDIT — [Source: architecture.md#Data Architecture], [Source: architecture.md#Requirements to Structure Mapping])

- [x] **Task 8 — Tests** (AC: #5)
  - [x] Créer `tests/common/test_database_factory.py` :
    - Test que `create_async_engine_for_agent()` crée un engine avec l'URL fournie
    - Test que `create_session_factory()` crée une session factory fonctionnelle
  - [x] Créer `tests/test_db_isolation.py` :
    - Test d'isolation : chaque agent crée son engine vers sa propre base
    - Test que les metadata de chaque agent sont indépendantes (pas de contamination croisée)
    - Test que la `naming_convention` est correctement appliquée
  - [x] Créer `tests/<agent_name>/test_alembic_config.py` (pour au moins 2 agents) :
    - Test que `alembic.ini` est parseable et pointe vers le bon `script_location`
    - Test que `env.py` importe correctement la metadata de l'agent
    - Test que la migration initiale (si présente) est exécutable sans erreur
  - [x] **Règle de test** : Aucun test ne doit se connecter à une vraie base de données — utiliser des engines SQLite en mémoire (`sqlite+aiosqlite://`) ou mocker la connexion

### Review Findings

- [x] [Review][Patch] URL string replacement for auto-routing might fail on query string [src/agent_maestro/app/db/session.py]
- [x] [Review][Patch] Empty DATABASE_URL causes crash at module load [src/agent_maestro/app/db/session.py]
- [x] [Review][Patch] Original exception hidden if rollback raises exception [src/agent_maestro/app/db/session.py]
- [x] [Review][Patch] Original exception hidden if close raises exception [src/agent_maestro/app/db/session.py]
- [x] [Review][Patch] Unhandled exception in engine.dispose() blocks shutdown [src/agent_maestro/main.py]
- [x] [Review][Patch] Missing DATABASE_URL causes cryptic AttributeError in offline mode [src/agent_maestro/app/db/alembic/env.py]
- [x] [Review][Patch] Offline mode literal_binds may fail with asyncpg driver [src/agent_maestro/app/db/alembic/env.py]
- [x] [Review][Patch] connectable.dispose() is not in a finally block [src/agent_maestro/app/db/alembic/env.py]
- [x] [Review][Patch] Missing client-side default for checked_at column [src/agent_maestro/app/db/models/health_check.py]

## Dev Notes

### Architecture — Pattern 2B (Isolation Stricte)

Le Pattern 2B est la décision architecturale centrale de cette story. L'objectif est que chaque agent gère **en totale autonomie** ses schémas ORM, modèles, et migrations Alembic. Il n'existe **aucun** dossier `alembic` transversal partagé à la racine du monorepo.
[Source: architecture.md#Structure Patterns, ligne 141-142]

**Pourquoi une `Base` locale par agent et pas la `Base` de common ?**
Alembic utilise `Base.metadata` pour détecter les tables lors de l'autogenerate. Si tous les agents partagent la même `Base`, une migration dans `agent_gourmet` détecterait les modèles de `agent_maestro` comme "tables manquantes" et générerait du code de suppression destructeur. Chaque agent **DOIT** avoir sa propre classe `Base` avec sa propre instance de `MetaData`.

### Conventions de Nommage (Enforcement)

- **Tables** : pluriel, `snake_case` (ex: `health_checks`, `soft_facts`)
- **Colonnes** : `snake_case` strict (ex: `user_id`, `created_at`)
- **Index** : `idx_<table>_<column>` (ex: `idx_soft_facts_user_id`)
- [Source: architecture.md#Naming Patterns, lignes 134-136]

### Pattern `env.py` Asynchrone (Référence Complète)

Chaque `env.py` Alembic doit suivre ce pattern exact :

```python
import asyncio
import os
from logging.config import fileConfig

from alembic import context
from sqlalchemy import pool
from sqlalchemy.ext.asyncio import async_engine_from_config

# CRITIQUE : importer la Base LOCALE de l'agent, pas celle de common
from <agent_name>.app.db.base import Base

# CRITIQUE : importer tous les modèles pour que l'autogenerate les détecte
from <agent_name>.app.db.models import *  # noqa: F401, F403

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata

# Surcharger l'URL depuis l'env (docker-compose ou .env)
database_url = os.environ.get("DATABASE_URL")
if database_url:
    config.set_main_option("sqlalchemy.url", database_url)


def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection) -> None:
    context.configure(connection=connection, target_metadata=target_metadata)
    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)
    await connectable.dispose()


def run_migrations_online() -> None:
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
```

### Pattern `session.py` Agent (Référence)

```python
"""Database session module for <agent_name>."""

import os
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

DATABASE_URL = os.environ.get(
    "DATABASE_URL",
    "postgresql+asyncpg://<agent_short>:<agent_short>@localhost:5432/<agent_short>"
)

engine = create_async_engine(
    DATABASE_URL,
    echo=os.environ.get("DEBUG", "false").lower() == "true",
    future=True,
)

async_session_factory = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_db():
    """FastAPI dependency — yields an async session."""
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
```

### Anti-Patterns Critiques à Éviter

1. **NE PAS** exécuter `alembic upgrade head` dans le `lifespan` ou `main.py` — les migrations doivent être exécutées manuellement ou via CI/CD **avant** le redéploiement du conteneur [Source: architecture.md#Data Architecture, ligne 103]
2. **NE PAS** utiliser `common.database.Base` dans les modèles spécifiques d'un agent — cela casserait l'isolation Alembic
3. **NE PAS** importer les modèles d'un agent depuis un autre agent — c'est un anti-pattern destructeur
4. **NE PAS** créer de `Base.metadata.create_all()` dans le code de production — c'est le rôle d'Alembic exclusivement
5. **NE PAS** toucher à `common/models.py` existant dans cette story — ce fichier est hérité de la Phase 1 et sera traité séparément (migration vers les modèles locaux des agents)
6. **NE PAS** utiliser de code bloquant dans la boucle d'événements — exclusivement `asyncpg` et `SQLAlchemy[asyncio]` [Source: architecture.md#Implementation Handoff, ligne 315]

### Gestion de `common/database.py` et `common/models.py` existants

Le fichier `common/database.py` actuel contient un singleton (`engine`, `Base`, `get_db()`) qui utilise `config.DATABASE_URL` globalement. Ce fichier doit être **refactoré** pour devenir une **factory** réutilisable tout en conservant la rétrocompatibilité pour le code existant qui l'importe.

Le fichier `common/models.py` contient des modèles Phase 1 (`FamilyMember`, `Preference`, `ConversationLog`) qui utilisent `common.database.Base`. **Ne pas y toucher dans cette story**. La migration de ces modèles vers les modules `db/` des agents concernés sera traitée dans une story dédiée.

### Variables d'Environnement (docker-compose.yml — État Actuel)

| Agent | DATABASE_URL actuelle | Status |
|-------|----------------------|--------|
| `maestro` | `postgresql+asyncpg://maestro:maestro@db:5432/maestro` | Présente |
| `gourmet` | `postgresql+asyncpg://gourmet:gourmet@db:5432/gourmet` | Présente |
| `acadomie` | — | **MANQUANTE** |
| `explorer` | `postgresql+asyncpg://explorer:explorer@db:5432/explorer` | Présente |

**Note** : Le service `acadomie` n'a pas non plus de `depends_on: db` dans le docker-compose actuel.

### Structure Existante des Agents (Phase 1)

Les agents ont des structures hétérogènes. Les agents `gourmet` et `acadomie` possèdent déjà un dossier `app/` avec `api/`, `schemas/`, `services/`. L'agent `maestro` n'a pas de dossier `app/` structuré de la même façon — ses fichiers sont à la racine (`main.py`, `router.py`, etc.). L'agent `explorer` est le plus minimal (pas de dossier `app/`).

**Implications pour cette story :**
- `agent_gourmet` et `agent_acadomie` : créer `app/db/` dans le `app/` existant
- `agent_maestro` : créer le dossier `app/db/` (un `app/` n'existe pas encore au sens standard — il faudra peut-être le créer)
- `agent_explorer` : créer `app/` et `app/db/` (le plus minimal actuellement)

**Vérifier la structure exacte de chaque agent avant de créer les dossiers.** L'architecture cible exige `src/<agent_name>/app/db/` pour tous les agents. Si `app/` n'existe pas encore, le créer avec un `__init__.py`.

### Commandes Alembic — Référence Rapide

```bash
# Initialisation (une seule fois par agent, DEPUIS le dossier app/db/)
cd src/<agent_name>/app/db
alembic init -t async alembic

# Générer une migration (DEPUIS le dossier app/db/)
cd src/<agent_name>/app/db
DATABASE_URL="postgresql+asyncpg://..." alembic revision --autogenerate -m "description"

# Appliquer les migrations (DEPUIS le dossier app/db/)
cd src/<agent_name>/app/db
DATABASE_URL="postgresql+asyncpg://..." alembic upgrade head

# Vérifier le statut
DATABASE_URL="postgresql+asyncpg://..." alembic current
```

### Project Structure Notes

**Structure cible après cette story :**
```
src/
├── common/
│   ├── database.py         # Refactoré en factory (rétrocompatible)
│   ├── models.py           # Inchangé (Phase 1 legacy)
│   └── ...
├── agent_maestro/
│   ├── main.py             # Lifespan mis à jour
│   └── app/
│       └── db/
│           ├── __init__.py
│           ├── base.py     # Base locale + naming_convention
│           ├── session.py  # Engine + session factory
│           ├── alembic.ini
│           ├── alembic/
│           │   ├── env.py
│           │   ├── script.py.mako
│           │   └── versions/
│           │       └── xxxx_initial_health_check.py
│           └── models/
│               ├── __init__.py
│               └── health_check.py
├── agent_gourmet/
│   └── app/
│       └── db/             # Même structure que maestro (sans modèle de preuve)
│           ├── __init__.py
│           ├── base.py
│           ├── session.py
│           ├── alembic.ini
│           ├── alembic/
│           │   ├── env.py
│           │   ├── script.py.mako
│           │   └── versions/
│           └── models/
│               └── __init__.py
├── agent_acadomie/
│   └── app/
│       └── db/             # Même structure
├── agent_explorer/
│   └── app/
│       └── db/             # Même structure
```

**Fichiers à créer :**
- `src/<agent>/app/db/__init__.py` (x4)
- `src/<agent>/app/db/base.py` (x4)
- `src/<agent>/app/db/session.py` (x4)
- `src/<agent>/app/db/models/__init__.py` (x4)
- `src/<agent>/app/db/alembic/env.py` (x4, via `alembic init -t async`)
- `src/<agent>/app/db/alembic.ini` (x4, via `alembic init -t async`)
- `src/agent_maestro/app/db/models/health_check.py` (x1)
- `tests/common/test_database_factory.py`
- `tests/test_db_isolation.py`
- `tests/agent_maestro/test_alembic_config.py` (au minimum)

**Fichiers à modifier :**
- `pyproject.toml` (ajout alembic)
- `src/common/database.py` (refactoring en factory)
- `docker-compose.yml` (ajout DATABASE_URL et depends_on pour acadomie)
- `src/agent_maestro/main.py` (lifespan engine init)
- `src/agent_gourmet/main.py` (lifespan engine init)
- `src/agent_acadomie/main.py` (lifespan engine init)
- `src/agent_explorer/main.py` (lifespan engine init)

### Versions et Dépendances

| Dépendance | Version | Notes |
|-----------|---------|-------|
| `alembic` | `>=1.18.4` | À ajouter via `uv add` — [Source: architecture.md#Data Architecture] |
| `sqlalchemy[asyncio]` | `>=2.0.45` | Déjà présent dans pyproject.toml |
| `asyncpg` | `>=0.31.0` | Déjà présent dans pyproject.toml |

**L'ajout de `alembic` est une opération critique nécessitant validation humaine selon les règles du projet** [Source: project-context.md#Development Workflow Rules]. Signaler cette action avant exécution.

### Testing

- Framework : `pytest` + `pytest-asyncio` (mode `auto`)
- Aucun I/O réseau en CI — [Source: project-context.md#Testing Rules]
- Pour les tests d'isolation DB, utiliser des engines SQLite en mémoire (`sqlite+aiosqlite://`) pour éviter de dépendre de PostgreSQL en CI
- Si `aiosqlite` n'est pas dans les dépendances dev, il faudra l'ajouter (`uv add --dev aiosqlite`)
- Les tests de configuration Alembic peuvent parser les fichiers `.ini` et `.py` sans nécessiter de connexion DB

### References

- [Source: architecture.md#Structure Patterns — Pattern 2B] Isolation stricte Alembic par agent
- [Source: architecture.md#Data Architecture] PostgreSQL 18, Alembic >=1.18.4, proscription migrations auto
- [Source: architecture.md#Naming Patterns] Convention snake_case tables/colonnes
- [Source: architecture.md#Implementation Handoff] Isolation stricte, snake_case, asyncpg exclusif
- [Source: architecture.md#Project Structure] Structure `src/agent_NAME/app/db/alembic/`
- [Source: epics.md#Story 1.2] Acceptance Criteria BDD
- [Source: prd.md#NFR4] Isolation de la Persistance
- [Source: prd.md#NFR6] Zero Downtime Mutuel
- [Source: project-context.md#Technology Stack] Versions des dépendances
- [Source: project-context.md#Framework-Specific Rules] Dépendance database factory
- [Source: project-context.md#Testing Rules] Zéro I/O réseau en CI
- [Source: project-context.md#Development Workflow Rules] Validation humaine pour `uv add`
- [Source: docker-compose.yml] Variables DATABASE_URL existantes

## Dev Agent Record

### Agent Model Used

Gemini 3.5 Flash (Low)

### Debug Log References

- Alembic isolation validated successfully using memory and SQLite databases.
- Integration tests ran and passed: `tests/common/test_database_factory.py`, `tests/test_db_isolation.py`, `tests/agent_maestro/test_alembic_config.py`.

### Completion Notes List

- Added Alembic dependency (`alembic>=1.18.4`) and aiosqlite dev dependency.
- Refactored `common/database.py` with factory functions for engines and session makers.
- Created `app/db` structure for all four agents, ensuring strict metadata isolation.
- Initialized and configured four isolated Alembic environments inside `src/<agent>/app/db`.
- Implemented and successfully validated an initial proof migration in `agent_maestro`.
- Configured docker-compose environment variables and lifespan hooks for graceful connection handling.
- Automated tests passed successfully with 100% database isolation checked.

### File List

- `pyproject.toml`
- `uv.lock`
- `docker-compose.yml`
- `.env.example`
- `src/common/database.py`
- `src/agent_maestro/main.py`
- `src/agent_maestro/app/__init__.py`
- `src/agent_maestro/app/db/__init__.py`
- `src/agent_maestro/app/db/base.py`
- `src/agent_maestro/app/db/session.py`
- `src/agent_maestro/app/db/models/__init__.py`
- `src/agent_maestro/app/db/models/health_check.py`
- `src/agent_maestro/app/db/alembic.ini`
- `src/agent_maestro/app/db/alembic/env.py`
- `src/agent_maestro/app/db/alembic/versions/6fa2e97bcb93_initial_health_check.py`
- `src/agent_gourmet/main.py`
- `src/agent_gourmet/app/db/__init__.py`
- `src/agent_gourmet/app/db/base.py`
- `src/agent_gourmet/app/db/session.py`
- `src/agent_gourmet/app/db/models/__init__.py`
- `src/agent_gourmet/app/db/alembic.ini`
- `src/agent_gourmet/app/db/alembic/env.py`
- `src/agent_acadomie/main.py`
- `src/agent_acadomie/app/db/__init__.py`
- `src/agent_acadomie/app/db/base.py`
- `src/agent_acadomie/app/db/session.py`
- `src/agent_acadomie/app/db/models/__init__.py`
- `src/agent_acadomie/app/db/alembic.ini`
- `src/agent_acadomie/app/db/alembic/env.py`
- `src/agent_explorer/main.py`
- `src/agent_explorer/app/__init__.py`
- `src/agent_explorer/app/db/__init__.py`
- `src/agent_explorer/app/db/base.py`
- `src/agent_explorer/app/db/session.py`
- `src/agent_explorer/app/db/models/__init__.py`
- `src/agent_explorer/app/db/alembic.ini`
- `src/agent_explorer/app/db/alembic/env.py`
- `tests/common/test_database_factory.py`
- `tests/test_db_isolation.py`
- `tests/agent_maestro/test_alembic_config.py`
