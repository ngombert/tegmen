"""Main entry point for Agent Gourmet microservice."""

import uvicorn
from fastapi import FastAPI

from agent_gourmet.app.api.routers.a2a import GOURMET_METHODS
from common.a2a_server import create_a2a_app
from common.config import config
from common.agent_registry import agent_registry
from common.logger import setup_logger
from contextlib import asynccontextmanager

logger = setup_logger("agent_gourmet")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan - startup and shutdown events."""
    logger.info("🚀 Starting Agent Gourmet (Lean Mode)...")
    yield
    logger.info("👋 Shutting down Agent Gourmet...")


# Create A2A application using the new Lean pattern
a2a_app = create_a2a_app(
    agent=None, # ADK Agent dependency removed
    agent_name="agent_gourmet",
    agent_description="Expert en cuisine familiale, recettes et planification de repas.",
    public_url=agent_registry.get_agent_url("gourmet") or "http://localhost:8001",
    version="1.0.0",
    methods=GOURMET_METHODS,
    skills=[
        {
            "id": "search_recipes",
            "name": "search_recipes",
            "description": "Recherche exhaustive dans la base de recettes. Supporte les filtres par mots-clés (nom, ingrédients) et par tags (ex: végétarien, italien). Retourne une liste de résumés de recettes.",
            "parameters": {
                "query": "Chaîne de caractères optionnelle pour la recherche textuelle",
                "tag": "Tag optionnel pour filtrer par catégorie"
            }
        },
        {
            "id": "get_recipe_details",
            "name": "get_recipe_details",
            "description": "Récupère l'intégralité des informations d'une recette : liste structurée des ingrédients avec quantités, étapes de préparation détaillées, temps de cuisson, nombre de parts et niveau de difficulté.",
            "parameters": {
                "recipe_id": "Identifiant unique de la recette (requis)"
            }
        },
    ],
)

# Create main FastAPI app
app = FastAPI(
    title="Agent Gourmet",
    description="Microservice A2A pour la cuisine et les recettes (Architecture Lean)",
    version="1.0.0",
    lifespan=lifespan,
)

# Mount A2A app at root - handles /a2a/SendMessage, /a2a/AgentCard, etc.
app.mount("/", a2a_app)

@app.get("/health", tags=["System"])
async def health():
    """Endpoint de santé pour monitoring."""
    return {"status": "ok", "agent": "gourmet", "mode": "lean"}
