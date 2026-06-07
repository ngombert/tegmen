import pytest
from sqlalchemy.orm import DeclarativeBase

from agent_maestro.app.db.base import Base as MaestroBase
from agent_gourmet.app.db.base import Base as GourmetBase
from agent_acadomie.app.db.base import Base as AcadomieBase
from agent_explorer.app.db.base import Base as ExplorerBase

from agent_maestro.app.db.session import engine as maestro_engine, DATABASE_URL as maestro_db_url
from agent_gourmet.app.db.session import engine as gourmet_engine, DATABASE_URL as gourmet_db_url
from agent_acadomie.app.db.session import engine as acadomie_engine, DATABASE_URL as acadomie_db_url
from agent_explorer.app.db.session import engine as explorer_engine, DATABASE_URL as explorer_db_url


def test_bases_are_distinct():
    """Verify that each agent has an isolated declarative Base class."""
    assert MaestroBase is not GourmetBase
    assert MaestroBase is not AcadomieBase
    assert MaestroBase is not ExplorerBase
    assert GourmetBase is not AcadomieBase
    assert GourmetBase is not ExplorerBase
    assert AcadomieBase is not ExplorerBase

    assert issubclass(MaestroBase, DeclarativeBase)
    assert issubclass(GourmetBase, DeclarativeBase)
    assert issubclass(AcadomieBase, DeclarativeBase)
    assert issubclass(ExplorerBase, DeclarativeBase)


def test_naming_conventions_applied():
    """Verify that the naming convention is applied to the metadata of each agent."""
    for base in [MaestroBase, GourmetBase, AcadomieBase, ExplorerBase]:
        convention = base.metadata.naming_convention
        assert convention is not None
        assert convention["ix"] == "ix_%(table_name)s_%(column_0_N_name)s"
        assert convention["uq"] == "uq_%(table_name)s_%(column_0_N_name)s"
        assert convention["ck"] == "ck_%(table_name)s_%(constraint_name)s"
        assert convention["fk"] == "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s"
        assert convention["pk"] == "pk_%(table_name)s"


def test_engines_and_urls_are_distinct():
    """Verify that engines are separate and URLs are distinct."""
    assert maestro_engine is not gourmet_engine
    assert maestro_engine is not acadomie_engine
    assert maestro_engine is not explorer_engine
    
    # Check default db names in URL match expectations
    assert "maestro" in maestro_db_url
    assert "gourmet" in gourmet_db_url
    assert "acadomie" in acadomie_db_url
    assert "explorer" in explorer_db_url
