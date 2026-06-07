"""Database session module for agent_gourmet."""

import logging
import os
from urllib.parse import urlparse, urlunparse
from sqlalchemy.ext.asyncio import AsyncSession
from common.database import create_async_engine_for_agent, create_session_factory

logger = logging.getLogger("agent_gourmet")

DATABASE_URL = os.environ.get("GOURMET_DATABASE_URL") or os.environ.get("DATABASE_URL")
if not DATABASE_URL:
    DATABASE_URL = "postgresql+asyncpg://gourmet:gourmet@localhost:5432/gourmet"

# Auto-route to specific logical database if using the shared default "tegmen"
try:
    parsed = urlparse(DATABASE_URL)
    if parsed.path == "/tegmen":
        DATABASE_URL = urlunparse(parsed._replace(path="/gourmet"))
except Exception as e:
    logger.warning(f"Failed to parse or auto-route DATABASE_URL: {e}")

engine = create_async_engine_for_agent(
    DATABASE_URL,
    debug=os.environ.get("DEBUG", "false").lower() == "true",
)

async_session_factory = create_session_factory(engine)


async def get_db():
    """FastAPI dependency — yields an async session."""
    session = async_session_factory()
    try:
        yield session
        await session.commit()
    except Exception as e:
        try:
            await session.rollback()
        except Exception as rb_err:
            logger.error(f"Database rollback failed: {rb_err}", exc_info=True)
        raise e
    finally:
        try:
            await session.close()
        except Exception as close_err:
            logger.error(f"Database session close failed: {close_err}", exc_info=True)

