"""Main entry point for Agent Acadomie microservice (Lean Mode)."""

import uvicorn
from fastapi import FastAPI

from agent_acadomie.app.api.routers.a2a import ACADOMIE_METHODS
from common.a2a_server import create_a2a_app
from common.config import config
from common.agent_registry import agent_registry
from common.logger import setup_logger
from contextlib import asynccontextmanager

logger = setup_logger("agent_acadomie")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan - startup and shutdown events."""
    logger.info("🚀 Starting Agent Acadomie (Lean Mode)...")
    
    # Initialize DB engine
    from agent_acadomie.app.db.session import engine as db_engine
    logger.info("🗄️ Database engine initialized for Acadomie.")
    
    yield
    
    # Clean up DB engine
    try:
        from agent_acadomie.app.db.session import engine as db_engine
        logger.info("🔌 Disposing Database engine for Acadomie...")
        await db_engine.dispose()
    except Exception as e:
        logger.error(f"Failed to dispose Database engine for Acadomie: {e}", exc_info=True)
    logger.info("👋 Shutting down Agent Acadomie...")


# Create A2A application using the Lean pattern
a2a_app = create_a2a_app(
    agent=None,  # ADK Agent dependency removed
    agent_name="agent_acadomie",
    agent_description="Assistant scolaire pour l'aide aux devoirs et l'organisation.",
    public_url=agent_registry.get_agent_url("acadomie") or "http://localhost:8002",
    version="1.0.0",
    methods=ACADOMIE_METHODS,
    skills=[
        {
            "id": "homework",
            "name": "homework",
            "description": "Consulter la liste des devoirs scolaires à faire, ajouter un nouveau devoir avec matière, consigne et date limite. Couvre les exercices, les leçons à apprendre et les projets scolaires.",
        },
        {
            "id": "calendar",
            "name": "calendar",
            "description": "Consulter le calendrier scolaire, les événements à venir (examens, sorties scolaires, réunions parents-professeurs, vacances). Permet d'anticiper l'organisation familiale.",
        },
        {
            "id": "grades",
            "name": "grades",
            "description": "Consulter les notes et résultats scolaires de l'élève par matière. Suivi de la progression académique, moyennes et dernières évaluations.",
        },
        {
            "id": "organization",
            "name": "organization",
            "description": "Fournir des conseils personnalisés d'organisation scolaire, de planification des révisions et de gestion du temps pour les devoirs et examens.",
        },
    ],
)

# Create main FastAPI app
app = FastAPI(
    title="Agent Acadomie",
    description="Microservice A2A pour l'aide scolaire (Architecture Lean)",
    version="1.0.0",
    lifespan=lifespan,
)


@app.get("/health", tags=["System"])
async def health():
    """Endpoint de santé pour monitoring."""
    return {"status": "ok", "agent": "acadomie", "mode": "lean"}


# Mount A2A app at root - handles /a2a/SendMessage, /a2a/AgentCard, etc.
# NOTE: Must be mounted AFTER explicit routes (e.g., /health)
app.mount("/", a2a_app)


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8002)
