"""Main entry point for Agent Explorer microservice."""

import uvicorn
from fastapi import FastAPI

from src.agent_explorer.agent import agent
from src.common.a2a_server import create_a2a_app
from src.common.config import config
from src.common.logger import setup_logger
from contextlib import asynccontextmanager

logger = setup_logger("agent_explorer")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan - startup and shutdown events."""
    logger.info("🚀 Starting Agent Explorer...")
    yield
    logger.info("👋 Shutting down Agent Explorer...")


# Create A2A application
a2a_app = create_a2a_app(
    agent=agent,
    agent_name="agent_explorer",
    agent_description="Expert en voyages familiaux et activités de loisirs.",
    public_url=config.EXPLORER_URL,
    skills=[
        {
            "id": "travel",
            "name": "Voyages",
            "description": "Rechercher des destinations de vacances",
        },
        {
            "id": "activities",
            "name": "Activités",
            "description": "Trouver des activités locales",
        },
        {
            "id": "weather",
            "name": "Météo",
            "description": "Vérifier la météo d'une destination",
        },
    ],
)

# Create main FastAPI app
app = FastAPI(
    title="Agent Explorer",
    description="Microservice A2A pour les voyages et les loisirs",
    version="0.1.0",
    lifespan=lifespan,
)

# Mount A2A app at root
app.mount("/", a2a_app.build())


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
