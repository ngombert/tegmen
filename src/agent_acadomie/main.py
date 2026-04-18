"""Main entry point for Agent Acadomie microservice."""

import uvicorn
from fastapi import FastAPI

from agent_acadomie.agent import agent
from common.a2a_server import create_a2a_app
from common.config import config
from common.agent_registry import agent_registry
from common.logger import setup_logger
from contextlib import asynccontextmanager

logger = setup_logger("agent_acadomie")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan - startup and shutdown events."""
    logger.info("🚀 Starting Agent Acadomie...")
    yield
    logger.info("👋 Shutting down Agent Acadomie...")


# Create A2A application
a2a_app = create_a2a_app(
    agent=agent,
    agent_name="agent_acadomie",
    agent_description="Assistant scolaire pour l'aide aux devoirs et l'organisation.",
    public_url=agent_registry.get_agent_url("acadomie"),
    skills=[
        {
            "id": "homework",
            "name": "Devoirs",
            "description": "Consulter / ajouter des devoirs",
        },
        {
            "id": "calendar",
            "name": "Calendrier",
            "description": "Consulter le calendrier scolaire",
        },
        {
            "id": "grades",
            "name": "Notes",
            "description": "Consulter les notes de l'élève",
        },
        {
            "id": "organization",
            "name": "Organisation",
            "description": "Conseils d'organisation et de révision",
        },
    ],
)

# Create main FastAPI app
app = FastAPI(
    title="Agent Acadomie",
    description="Microservice A2A pour l'aide scolaire",
    version="0.1.0",
    lifespan=lifespan,
)

# Mount A2A app at root
app.mount("/", a2a_app)


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
