import os
from alembic.config import Config


def test_maestro_alembic_config():
    """Verify that Maestro's alembic.ini is present and can be parsed."""
    ini_path = os.path.abspath(
        os.path.join(
            os.path.dirname(__file__),
            "../../src/agent_maestro/app/db/alembic.ini"
        )
    )
    assert os.path.exists(ini_path), f"alembic.ini not found at {ini_path}"
    
    config = Config(ini_path)
    script_location = config.get_main_option("script_location")
    assert script_location is not None
    # Can be %(here)s/alembic or alembic depending on standard template
    assert "alembic" in script_location
