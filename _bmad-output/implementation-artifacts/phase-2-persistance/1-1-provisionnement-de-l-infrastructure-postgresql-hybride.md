# Story 1.1: Provisionnement de l'Infrastructure PostgreSQL Hybride

Status: done

## Story

As a administrateur système,
I want disposer d'un conteneur PostgreSQL supportant `pgvector` et initialisant automatiquement des bases logiques séparées au démarrage,
So that je puisse préparer le terrain pour la persistance isolée et sémantique de chaque agent.

## Contexte

> [!IMPORTANT]
> C'est la **PREMIÈRE story de toute la Phase 2 Persistance**. Elle ne produit aucun code applicatif Python — elle pose uniquement l'infrastructure Docker/PostgreSQL qui sera consommée par les stories suivantes (1.2: ORM/Alembic, 4.2: pgvector tables, etc.).

**FRs couvertes :** FR12 (Déploiement isolé des BDD)
**NFRs couvertes :** NFR4 (Isolation de la Persistance), NFR6 (Zero Downtime Mutuel)

## Acceptance Criteria

### AC1 — Image Docker pgvector fonctionnelle

```gherkin
Given un environnement Docker vierge (aucun volume tegmen_postgres_data existant)
When je lance la commande `docker compose up db -d`
Then l'image `pgvector/pgvector:pg18` est téléchargée et le conteneur `tegmen-db` démarre
And le healthcheck `pg_isready -U postgres` passe en `healthy` sous 30 secondes
```

### AC2 — Création automatique des bases logiques

```gherkin
Given le conteneur `tegmen-db` est en état `healthy`
When je me connecte au serveur PostgreSQL avec l'utilisateur `postgres`
Then les bases de données `maestro`, `gourmet`, `acadomie`, `explorer` existent
And chacune possède un utilisateur dédié portant le même nom que la base (ex: user `gourmet` pour la base `gourmet`)
And cet utilisateur a tous les privilèges sur sa base respective
```

### AC3 — Extension `vector` activée sur chaque base

```gherkin
Given les bases logiques `maestro`, `gourmet`, `acadomie`, `explorer` sont créées
When je me connecte à chacune d'entre elles
Then l'extension `vector` est installée et listée dans `pg_extension`
And je peux créer une colonne de type `vector(3)` sans erreur
```

### AC4 — Idempotence et non-régression

```gherkin
Given le conteneur `tegmen-db` tourne avec des données existantes
When je relance `docker compose up db -d` (sans supprimer les volumes)
Then le conteneur redémarre normalement sans tenter de recréer les bases (scripts d'init ne s'exécutent qu'au premier lancement)
And les agents existants (gourmet, maestro, etc.) continuent de se connecter normalement
```

### AC5 — Aucune régression sur les services existants

```gherkin
Given le docker-compose.yml mis à jour
When je lance `docker compose config` (validation syntaxique)
Then aucune erreur n'est levée
And les services `gourmet`, `maestro`, `explorer`, `acadomie`, `frontend` conservent exactement leurs configurations respectives (ports, profiles, volumes, variables d'environnement)
```

## Tasks / Subtasks

### Task 1: Remplacer l'image Docker PostgreSQL (AC1)

**Fichier :** `docker-compose.yml` (ligne 7)

- [x] Remplacer `image: postgres:18-alpine` par `image: pgvector/pgvector:pg18`
- [x] Conserver TOUS les autres paramètres du service `db` à l'identique (environment, volumes, healthcheck, ports)

> [!WARNING]
> **Anti-pattern à éviter :** NE PAS construire un Dockerfile custom pour PostgreSQL. L'architecture Phase 2 prescrit explicitement l'utilisation de l'image pré-construite `pgvector/pgvector:pg18` (ref: architecture.md ligne 91, ligne 318). Un build custom ajouterait une complexité inutile et ralentirait le CI.

```diff
 services:
   db:
-    image: postgres:18-alpine
+    image: pgvector/pgvector:pg18
     container_name: tegmen-db
```

### Task 2: Enrichir le script `init-multiple-dbs.sh` pour activer pgvector (AC2, AC3)

**Fichier :** `scripts/init-multiple-dbs.sh`

Le script existant crée déjà les bases et les utilisateurs. Il faut **ajouter** l'activation de l'extension `vector` sur chaque base créée.

- [x] Ajouter `CREATE EXTENSION IF NOT EXISTS vector;` dans la fonction `create_user_and_database()`, exécuté **dans le contexte de la base nouvellement créée** (via `psql -d "$database"`)
- [x] Utiliser `IF NOT EXISTS` pour l'idempotence (AC4)
- [x] Conserver le `set -e` et `set -u` existants pour le fail-fast

**Script modifié attendu :**

```bash
#!/bin/bash

# Script to create multiple PostgreSQL databases, users, and enable pgvector
# Mounted to /docker-entrypoint-initdb.d/

set -e
set -u

function create_user_and_database() {
	local database=$1
	echo "  Creating user and database '$database'"
	psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" <<-EOSQL
	    CREATE USER $database WITH PASSWORD '$database';
	    CREATE DATABASE $database;
	    GRANT ALL PRIVILEGES ON DATABASE $database TO $database;
EOSQL
    # Grant schema privileges and enable pgvector extension
    psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" -d "$database" <<-EOSQL
        GRANT ALL ON SCHEMA public TO $database;
        CREATE EXTENSION IF NOT EXISTS vector;
EOSQL
}

if [ -n "$POSTGRES_MULTIPLE_DATABASES" ]; then
	echo "Multiple database creation requested: $POSTGRES_MULTIPLE_DATABASES"
	for db in $(echo $POSTGRES_MULTIPLE_DATABASES | tr ',' ' '); do
		create_user_and_database $db
	done
	echo "Multiple databases created with pgvector extension"
fi
```

> [!NOTE]
> Le `CREATE EXTENSION` est exécuté par l'utilisateur `postgres` (superuser) dans le contexte `-d "$database"`. C'est le seul utilisateur qui a le droit de créer des extensions. L'utilisateur applicatif (ex: `gourmet`) pourra ensuite utiliser les types `vector` dans ses tables sans problème.

### Task 3: Script de vérification (AC2, AC3)

**Fichier à créer :** `scripts/verify-db-init.sh`

Ce script permet de valider manuellement et en CI que l'infrastructure est correctement provisionnée.

- [x] Créer un script bash qui vérifie :
  1. L'existence des 4 bases (`maestro`, `gourmet`, `acadomie`, `explorer`)
  2. L'activation de l'extension `vector` sur chacune
  3. La capacité à créer une colonne `vector(3)` (test fonctionnel)

```bash
#!/bin/bash
# Verify database initialization: bases, users, pgvector extension
# Usage: docker exec tegmen-db /bin/bash /scripts/verify-db-init.sh
#    or: docker exec tegmen-db bash -c "POSTGRES_USER=postgres bash /scripts/verify-db-init.sh"

set -e

PGUSER="${POSTGRES_USER:-postgres}"
DATABASES="maestro gourmet acadomie explorer"
ERRORS=0

echo "=== Vérification de l'infrastructure PostgreSQL ==="

for db in $DATABASES; do
    echo ""
    echo "--- Base: $db ---"

    # 1. Check database exists
    if psql -U "$PGUSER" -lqt | cut -d \| -f 1 | grep -qw "$db"; then
        echo "  ✅ Base '$db' existe"
    else
        echo "  ❌ Base '$db' MANQUANTE"
        ERRORS=$((ERRORS + 1))
        continue
    fi

    # 2. Check vector extension
    EXT_COUNT=$(psql -U "$PGUSER" -d "$db" -tAc "SELECT count(*) FROM pg_extension WHERE extname = 'vector';")
    if [ "$EXT_COUNT" -eq 1 ]; then
        echo "  ✅ Extension 'vector' activée"
    else
        echo "  ❌ Extension 'vector' MANQUANTE"
        ERRORS=$((ERRORS + 1))
    fi

    # 3. Check user exists
    USER_EXISTS=$(psql -U "$PGUSER" -tAc "SELECT 1 FROM pg_roles WHERE rolname = '$db';" 2>/dev/null || echo "0")
    if [ "$USER_EXISTS" = "1" ]; then
        echo "  ✅ Utilisateur '$db' existe"
    else
        echo "  ❌ Utilisateur '$db' MANQUANT"
        ERRORS=$((ERRORS + 1))
    fi

    # 4. Functional test: create and drop a vector column
    psql -U "$PGUSER" -d "$db" -c "CREATE TABLE IF NOT EXISTS _pgvector_test (id serial, embedding vector(3));" > /dev/null 2>&1
    if [ $? -eq 0 ]; then
        echo "  ✅ Colonne vector(3) créable"
        psql -U "$PGUSER" -d "$db" -c "DROP TABLE IF EXISTS _pgvector_test;" > /dev/null 2>&1
    else
        echo "  ❌ Impossible de créer une colonne vector(3)"
        ERRORS=$((ERRORS + 1))
    fi
done

echo ""
echo "=== Résultat ==="
if [ $ERRORS -eq 0 ]; then
    echo "✅ Toutes les vérifications passées avec succès !"
    exit 0
else
    echo "❌ $ERRORS erreur(s) détectée(s)"
    exit 1
fi
```

- [x] Monter ce script dans le conteneur via le docker-compose.yml (même volume que le script init)

```diff
     volumes:
       - tegmen_postgres_data:/var/lib/postgresql/18/docker
       - ./scripts/init-multiple-dbs.sh:/docker-entrypoint-initdb.d/init-multiple-dbs.sh
+      - ./scripts/verify-db-init.sh:/scripts/verify-db-init.sh
```

### Task 4: Test d'infrastructure pytest (AC2, AC3, AC5)

**Fichier à créer :** `tests/test_infrastructure_db.py`

- [x] Créer un test pytest qui valide la configuration Docker Compose (parsing YAML statique, sans lancer Docker)
- [x] Vérifier que l'image est bien `pgvector/pgvector:pg18`
- [x] Vérifier que les 4 bases sont listées dans `POSTGRES_MULTIPLE_DATABASES`
- [x] Vérifier que le script d'init est monté dans `/docker-entrypoint-initdb.d/`
- [x] Vérifier que le script d'init contient `CREATE EXTENSION`

```python
"""Tests d'infrastructure pour la configuration PostgreSQL Phase 2.

Ces tests valident statiquement la configuration Docker Compose
et le script d'initialisation sans lancer aucun conteneur.
"""

from pathlib import Path

import yaml
import pytest


PROJECT_ROOT = Path(__file__).resolve().parent.parent
COMPOSE_FILE = PROJECT_ROOT / "docker-compose.yml"
INIT_SCRIPT = PROJECT_ROOT / "scripts" / "init-multiple-dbs.sh"

EXPECTED_DATABASES = {"maestro", "gourmet", "acadomie", "explorer"}
EXPECTED_IMAGE = "pgvector/pgvector:pg18"


@pytest.fixture
def compose_config() -> dict:
    """Charge et retourne la configuration docker-compose."""
    assert COMPOSE_FILE.exists(), f"docker-compose.yml introuvable: {COMPOSE_FILE}"
    with COMPOSE_FILE.open() as f:
        return yaml.safe_load(f)


@pytest.fixture
def init_script_content() -> str:
    """Charge et retourne le contenu du script d'init."""
    assert INIT_SCRIPT.exists(), f"Script d'init introuvable: {INIT_SCRIPT}"
    return INIT_SCRIPT.read_text()


class TestDockerComposeDB:
    """Validation statique du service 'db' dans docker-compose.yml."""

    def test_db_service_exists(self, compose_config: dict) -> None:
        assert "db" in compose_config["services"], \
            "Le service 'db' est absent du docker-compose.yml"

    def test_pgvector_image(self, compose_config: dict) -> None:
        db_service = compose_config["services"]["db"]
        assert db_service["image"] == EXPECTED_IMAGE, \
            f"Image attendue: {EXPECTED_IMAGE}, trouvée: {db_service['image']}"

    def test_multiple_databases_configured(self, compose_config: dict) -> None:
        db_env = compose_config["services"]["db"]["environment"]
        db_list_raw = db_env.get("POSTGRES_MULTIPLE_DATABASES", "")
        db_set = {db.strip() for db in db_list_raw.split(",") if db.strip()}
        assert db_set == EXPECTED_DATABASES, \
            f"Bases attendues: {EXPECTED_DATABASES}, trouvées: {db_set}"

    def test_init_script_mounted(self, compose_config: dict) -> None:
        volumes = compose_config["services"]["db"].get("volumes", [])
        init_mount = any(
            "init-multiple-dbs.sh" in str(v)
            and "/docker-entrypoint-initdb.d/" in str(v)
            for v in volumes
        )
        assert init_mount, \
            "Le script init-multiple-dbs.sh n'est pas monté dans /docker-entrypoint-initdb.d/"

    def test_healthcheck_configured(self, compose_config: dict) -> None:
        hc = compose_config["services"]["db"].get("healthcheck")
        assert hc is not None, "Pas de healthcheck configuré pour le service db"


class TestInitScript:
    """Validation du contenu du script d'initialisation."""

    def test_creates_extension_vector(self, init_script_content: str) -> None:
        assert "CREATE EXTENSION" in init_script_content, \
            "Le script d'init ne contient pas 'CREATE EXTENSION'"
        assert "vector" in init_script_content, \
            "Le script d'init ne mentionne pas l'extension 'vector'"

    def test_idempotent_extension(self, init_script_content: str) -> None:
        assert "IF NOT EXISTS" in init_script_content, \
            "Le script d'init doit utiliser 'IF NOT EXISTS' pour l'idempotence"

    def test_fail_fast_enabled(self, init_script_content: str) -> None:
        assert "set -e" in init_script_content, \
            "Le script d'init doit contenir 'set -e' pour le fail-fast"

    def test_strict_variables(self, init_script_content: str) -> None:
        assert "set -u" in init_script_content, \
            "Le script d'init doit contenir 'set -u' pour la détection de variables non définies"


class TestExistingServicesIntegrity:
    """Vérifie qu'aucun service existant n'a été cassé."""

    AGENTS = ["gourmet", "maestro", "acadomie", "explorer"]

    def test_all_agent_services_present(self, compose_config: dict) -> None:
        services = compose_config["services"]
        for agent in self.AGENTS:
            assert agent in services, \
                f"Service '{agent}' manquant dans docker-compose.yml"

    def test_agent_database_urls_unchanged(self, compose_config: dict) -> None:
        """Vérifie que les DATABASE_URL des agents n'ont pas été modifiées."""
        services = compose_config["services"]

        expected_urls = {
            "gourmet": "postgresql+asyncpg://gourmet:gourmet@db:5432/gourmet",
            "maestro": "postgresql+asyncpg://maestro:maestro@db:5432/maestro",
            "explorer": "postgresql+asyncpg://explorer:explorer@db:5432/explorer",
        }

        for agent, expected_url in expected_urls.items():
            env = services[agent].get("environment", [])
            # Environment can be list or dict format
            if isinstance(env, list):
                url_found = any(
                    f"DATABASE_URL={expected_url}" in item for item in env
                )
            else:
                url_found = env.get("DATABASE_URL") == expected_url
            assert url_found, \
                f"DATABASE_URL pour '{agent}' incorrecte ou manquante"
```

> [!TIP]
> Le package `pyyaml` est une dépendance transitive déjà présente (via les dépendances existantes). **Ne pas ajouter** `pyyaml` au `pyproject.toml` à moins qu'un `ImportError` se produise à l'exécution des tests, auquel cas ajouter `pyyaml>=6.0` dans le groupe `[dependency-groups] dev`.

### Task 5: Mise à jour de la documentation (optionnel mais recommandé)

**Fichier :** `scripts/README.md` (à créer si inexistant)

- [x] Documenter l'utilisation de `verify-db-init.sh`
- [x] Documenter la procédure de réinitialisation complète des bases (suppression du volume Docker)

### Review Findings (AI)

**Revue adversariale du 2026-05-20 — 1 decision_needed · 9 patch · 1 defer · 3 dismissed**

#### Décision requise
- [x] [Review][Decision] **Compatibilité volume Docker avec l'image pgvector** — Le volume est monté sur `/var/lib/postgresql/18/docker` mais l'image `pgvector/pgvector:pg18` utilise par défaut `/var/lib/postgresql/data`. Sans env var `PGDATA`, le conteneur initialise un cluster éphémère au path par défaut et ignore le volume nommé, causant une perte de données silencieuse. Faut-il (A) corriger le path du volume vers `/var/lib/postgresql/data`, (B) ajouter `PGDATA=/var/lib/postgresql/18/docker` en variable d'env du service `db`, ou (C) vérifier que le comportement actuel est intentionnel ? [docker-compose.yml:14] (Choix A validé : volume mis à jour vers /var/lib/postgresql/data)

#### Patches à appliquer
- [x] [Review][Patch] **`set -e` + `$?` incompatibles dans `verify-db-init.sh`** — `set -e` fait avorter le script avant d'atteindre le `if [ $? -eq 0 ]` sur failure psql. Remplacer par `set +e` localement ou utiliser `|| true` + pattern alternatif. [scripts/verify-db-init.sh:6,46-53]
- [x] [Review][Patch] **`DATABASES` codé en dur dans `verify-db-init.sh`** — désynchronisé de `POSTGRES_MULTIPLE_DATABASES` dans `docker-compose.yml`. Lire la liste depuis l'env var ou documenter explicitement la contrainte de synchronisation manuelle. [scripts/verify-db-init.sh:9]
- [x] [Review][Patch] **`EXT_COUNT` vide cause un crash bash** — si psql retourne une chaîne vide, `[ "" -eq 1 ]` lève `integer expression expected`. Ajouter une vérification ou un défaut : `EXT_COUNT="${EXT_COUNT:-0}"`. [scripts/verify-db-init.sh:28]
- [x] [Review][Patch] **`$POSTGRES_MULTIPLE_DATABASES` non quoté dans `init-multiple-dbs.sh`** — risque de word-splitting si la valeur contient des espaces autour des virgules. Quoter la variable : `"$POSTGRES_MULTIPLE_DATABASES"`. [scripts/init-multiple-dbs.sh:26]
- [x] [Review][Patch] **Healthcheck sans `start_period`** — avec 5 retries × 5s = 25s max, AC1 (healthy sous 30s) n'est pas garanti sur cold start incluant l'init script. Ajouter `start_period: 10s`. [docker-compose.yml:16-21]
- [x] [Review][Patch] **`test_healthcheck_configured` trop permissif (AC1 gap)** — n'asserte que la présence du healthcheck, pas ses paramètres de timing. Ajouter des assertions sur `interval`, `retries` et idéalement `start_period`. [tests/test_infrastructure_db.py:65-67]
- [x] [Review][Patch] **`acadomie` absent de `test_agent_database_urls_unchanged`** — silencieusement non testé alors qu'il figure dans `AGENTS`. Si `acadomie` n'a pas de `DATABASE_URL`, documenter ce choix explicitement dans le test. [tests/test_infrastructure_db.py:107-111]
- [x] [Review][Patch] **`test_creates_extension_vector` trop vague** — deux assertions séparées (`CREATE EXTENSION` + `vector`) passent si une autre extension est créée et que `vector` apparaît dans un commentaire. Asserter la chaîne complète `CREATE EXTENSION IF NOT EXISTS vector`. [tests/test_infrastructure_db.py:73-80]
- [x] [Review][Patch] **`USER_EXISTS` sensible au whitespace psql** — `-tA` peut laisser un `\n` terminal ; la comparaison `= "1"` échoue alors à tort. Utiliser `$(... | tr -d '[:space:]')` ou `xargs`. [scripts/verify-db-init.sh:37]

#### Différés (pre-existing)
- [x] [Review][Defer] **Credentials faibles user=password** — pré-existant avant cette story, acceptable pour dev local mais sans garde ni commentaire explicite. [scripts/init-multiple-dbs.sh:13] — deferred, pre-existing

## Dev Notes

### Décisions d'architecture

| Décision | Source | Détail |
|---|---|---|
| Image `pgvector/pgvector:pg18` | architecture.md L91, L318 | Image pré-construite, pas de Dockerfile custom |
| Bases logiques séparées | architecture.md L104 | Un conteneur Postgres unique, 4 bases : `maestro`, `gourmet`, `acadomie`, `explorer` |
| Script `init-multiple-dbs.sh` | architecture.md L104, L182 | Provisionnement au premier démarrage via `/docker-entrypoint-initdb.d/` |
| Extension `vector` sur chaque base | architecture.md L268, L318 | `CREATE EXTENSION vector` requis avant toute utilisation de `pgvector` |
| Pas de migration auto au démarrage | architecture.md L103 | Alembic est géré manuellement ou par CI (Story 1.2) |

### Contraintes techniques

- **Volume Docker :** Le chemin du volume de données est `tegmen_postgres_data:/var/lib/postgresql/18/docker`. Ce chemin est spécifique à la configuration existante. Vérifier que le data directory de l'image `pgvector/pgvector:pg18` est compatible. La valeur standard est `/var/lib/postgresql/data`. Si l'image pgvector utilise ce chemin standard, ajuster le mapping du volume en conséquence.

> [!WARNING]
> **Piège connu avec les volumes Docker :** Les scripts dans `/docker-entrypoint-initdb.d/` ne s'exécutent QUE si le data directory est vierge (premier `docker compose up`). Si un volume `tegmen_postgres_data` existe déjà avec une ancienne image `postgres:18-alpine`, il faut supprimer le volume pour que les scripts se relancent :
> ```bash
> docker compose down -v   # Supprime les volumes
> docker compose up db -d  # Recrée tout de zéro
> ```

### Anti-patterns à éviter

1. **NE PAS** construire un Dockerfile custom pour PostgreSQL — utiliser l'image pré-construite
2. **NE PAS** modifier les variables d'environnement des agents existants (`DATABASE_URL`, ports, profiles)
3. **NE PAS** ajouter de dépendances Python dans `pyproject.toml` pour cette story
4. **NE PAS** exécuter les migrations Alembic automatiquement au démarrage (réservé à Story 1.2)
5. **NE PAS** modifier le code Python applicatif (`src/`) — cette story est purement infrastructure
6. **NE PAS** oublier le `IF NOT EXISTS` sur le `CREATE EXTENSION` (idempotence)

### Vérification manuelle rapide

Après implémentation, les commandes suivantes doivent passer :

```bash
# 1. Nettoyer et recréer
docker compose down -v
docker compose up db -d
docker compose exec db pg_isready -U postgres  # Attend que le conteneur soit prêt

# 2. Vérifier les bases
docker compose exec db psql -U postgres -c "\l" | grep -E "maestro|gourmet|acadomie|explorer"

# 3. Vérifier pgvector sur chaque base
for db in maestro gourmet acadomie explorer; do
  echo "=== $db ==="
  docker compose exec db psql -U postgres -d $db -c "SELECT extname FROM pg_extension WHERE extname = 'vector';"
done

# 4. Test fonctionnel pgvector
docker compose exec db psql -U postgres -d gourmet -c "CREATE TABLE _test (v vector(3)); DROP TABLE _test;"

# 5. Script de vérification automatisé
docker compose exec db bash /scripts/verify-db-init.sh

# 6. Tests pytest
uv run pytest tests/test_infrastructure_db.py -v
```

### Project Structure Notes

**Fichiers à MODIFIER :**
- `docker-compose.yml` — Changer l'image du service `db` (1 ligne)
- `scripts/init-multiple-dbs.sh` — Ajouter `CREATE EXTENSION IF NOT EXISTS vector;` (1 ligne)

**Fichiers à CRÉER :**
- `scripts/verify-db-init.sh` — Script de vérification de l'infrastructure
- `tests/test_infrastructure_db.py` — Tests pytest statiques de la configuration

**Fichiers à NE PAS TOUCHER :**
- `pyproject.toml` — Aucune nouvelle dépendance
- `src/**/*` — Aucun code Python applicatif
- Les Dockerfiles des agents (`src/agent_*/Dockerfile`)
- `config/agents.yaml`
- `.env` ou `.env.example`

### Convention de commit

Utiliser le Conventional Commits :
```
feat(db): provision PostgreSQL hybride avec pgvector

- Remplace postgres:18-alpine par pgvector/pgvector:pg18
- Active CREATE EXTENSION vector sur les 4 bases logiques
- Ajoute script de vérification et tests d'infrastructure

Refs: Story 1.1, Epic 1, Phase 2 Persistance
```

### Dépendance aval (pour info)

La **Story 1.2** (Configuration de l'ORM et des Migrations Isolées) dépend directement de cette story. Elle assumera que :
- Les 4 bases existent et sont accessibles via `postgresql+asyncpg://<agent>:<agent>@db:5432/<agent>`
- L'extension `vector` est disponible sur chaque base
- Les utilisateurs ont les privilèges suffisants pour créer des tables et des index

### References

| Document | Chemin | Sections pertinentes |
|---|---|---|
| Architecture Phase 2 | `_bmad-output/planning-artifacts/phase-2-persistance/architecture.md` | L91 (pgvector image), L100-104 (Data Architecture), L117-119 (Infrastructure), L268 (Gap Analysis - vector ext), L316-320 (Implementation Handoff) |
| Epics Phase 2 | `_bmad-output/planning-artifacts/phase-2-persistance/epics.md` | L107-122 (Epic 1, Story 1.1) |
| PRD Phase 2 | `_bmad-output/planning-artifacts/phase-2-persistance/prd.md` | L55-56 (MVP - BDD indépendantes), L146-148 (NFR4, NFR5) |
| Project Context | `_bmad-output/project-context.md` | L24 (Database stack), L64 (Gestion des dépendances) |
| Docker Compose actuel | `docker-compose.yml` | L6-22 (service db), L116-117 (volumes) |
| Script init actuel | `scripts/init-multiple-dbs.sh` | Fichier complet (30 lignes) |

## Dev Agent Record

### Agent Model Used
Gemini 3.5 Flash (High)

### Debug Log References
- `uv run pytest tests/test_infrastructure_db.py -v` (Tous les tests statiques passent avec succès !)

### Completion Notes List
- Remplacement de l'image de base de données par `pgvector/pgvector:pg18` dans le fichier `docker-compose.yml` (AC1).
- Mise à jour du script d'initialisation `/scripts/init-multiple-dbs.sh` pour activer de manière idempotente l'extension `vector` de PostgreSQL sur chacune des 4 bases de données (`maestro`, `gourmet`, `acadomie`, `explorer`) (AC2, AC3).
- Création du script de vérification automatisé `/scripts/verify-db-init.sh` et configuration de son montage dans le conteneur de base de données via `docker-compose.yml` (AC2, AC3).
- Écriture d'un ensemble complet de tests pytest statiques `/tests/test_infrastructure_db.py` validant sans conteneur toute la configuration (image, bases de données, montage de scripts, activation de pgvector, intégrité des configurations des agents existants) (AC2, AC3, AC5).
- Rédaction de la documentation explicative dans `/scripts/README.md` précisant le fonctionnement et la procédure de réinitialisation des volumes.

### File List
- `docker-compose.yml` (modifié)
- `scripts/init-multiple-dbs.sh` (modifié)
- `scripts/verify-db-init.sh` (créé)
- `scripts/README.md` (créé)
- `tests/test_infrastructure_db.py` (créé)
