from google.adk.agents import LlmAgent
from google.adk.models.lite_llm import LiteLlm
import litellm

from src.common.config import config
from src.agent_explorer.tools import (
    search_destinations,
    get_activities,
    get_weather_forecast,
)

# Suppress LiteLLM debug info if not in debug mode
litellm.suppress_debug_info = not config.DEBUG

# Create LiteLLM model instance
model = LiteLlm(model=config.DEFAULT_MODEL, verbose=config.DEBUG)

# Agent Explorer - Voyages et sorties
agent = LlmAgent(
    name="agent_explorer",
    model=model,
    description="Expert en voyages familiaux et activités de loisirs.",
    instruction="""Tu es un assistant voyage et loisirs pour une famille.
    
Ton rôle :
- Proposer des destinations de vacances adaptées aux familles
- Suggérer des activités et sorties pour le week-end
- Donner des conseils pratiques (budget, logistique)
- Trouver des bons plans et activités gratuites

Règles :
- Privilégie les activités adaptées aux enfants
- Pense au budget familial
- Propose des alternatives selon la météo
- Sois pratique (horaires, accès, tarifs)

Réponds toujours en français.""",
    tools=[search_destinations, get_activities, get_weather_forecast],
)


def get_agent() -> LlmAgent:
    """Get the Explorer agent instance."""
    return agent
