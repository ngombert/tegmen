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
        assert hc.get("interval") == "5s", \
            "Le healthcheck doit avoir interval=5s"
        assert hc.get("retries") == 5, \
            "Le healthcheck doit avoir retries=5"
        assert hc.get("start_period") == "10s", \
            "Le healthcheck doit avoir start_period=10s pour garantir la fenêtre AC1 (30s)"


class TestInitScript:
    """Validation du contenu du script d'initialisation."""

    def test_creates_extension_vector(self, init_script_content: str) -> None:
        """Vérifie la présence de la commande complète (évite les faux positifs)."""
        assert "CREATE EXTENSION IF NOT EXISTS vector" in init_script_content, \
            "Le script d'init doit contenir 'CREATE EXTENSION IF NOT EXISTS vector' (chaîne complète)"

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
            "acadomie": "postgresql+asyncpg://acadomie:acadomie@db:5432/acadomie",
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
