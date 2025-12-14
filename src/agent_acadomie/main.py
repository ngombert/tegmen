"""Main entry point for Agent Acadomie microservice."""

import uvicorn
from fastapi import FastAPI

from src.agent_acadomie.agent import agent
from src.common.a2a_server import create_a2a_app
from src.common.config import config


# Create A2A application
a2a_app = create_a2a_app(
    agent=agent,
    agent_name="agent_acadomie",
    agent_description="Assistant scolaire pour l'aide aux devoirs et l'organisation.",
    public_url=config.ACADOMIE_URL,
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
)

# Mount A2A app at root
app.mount("/", a2a_app.build())


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
