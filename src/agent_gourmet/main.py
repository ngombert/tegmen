"""Main entry point for Agent Gourmet microservice."""

import uvicorn
from fastapi import FastAPI

from src.agent_gourmet.agent import agent
from src.common.a2a_server import create_a2a_app
from src.common.config import config
from src.common.logger import setup_logger
from contextlib import asynccontextmanager

logger = setup_logger("agent_gourmet")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan - startup and shutdown events."""
    logger.info("🚀 Starting Agent Gourmet...")
    yield
    logger.info("👋 Shutting down Agent Gourmet...")


# Create A2A application
a2a_app = create_a2a_app(
    agent=agent,
    agent_name="agent_gourmet",
    agent_description="Expert en cuisine familiale, recettes et planification de repas.",
    public_url=config.GOURMET_URL,
    skills=[
        {
            "id": "search_recipes",
            "name": "Rechercher Recette",
            "description": "Rechercher des recettes par nom ou tag (ex: 'pâtes', 'végétarien')",
        },
        {
            "id": "get_recipe_details",
            "name": "Détails Recette",
            "description": "Obtenir les ingrédients et étapes d'une recette spécifique",
        },
    ],
)

# Create main FastAPI app
app = FastAPI(
    title="Agent Gourmet",
    description="Microservice A2A pour la cuisine et les recettes",
    version="0.1.0",
    lifespan=lifespan,
)

# Mount A2A app at root
app.mount("/", a2a_app)


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
