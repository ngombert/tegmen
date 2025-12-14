from google.adk.agents import LlmAgent
from google.adk.models.lite_llm import LiteLlm
import litellm

from src.common.config import config
from src.agent_acadomie.tools import (
    get_school_calendar,
    get_student_grades,
    get_homework,
)

# Suppress LiteLLM debug info if not in debug mode
litellm.suppress_debug_info = not config.DEBUG

# Create LiteLLM model instance
model = LiteLlm(model=config.DEFAULT_MODEL, verbose=config.DEBUG)

# Agent Acadomie - École et devoirs
agent = LlmAgent(
    name="agent_acadomie",
    model=model,
    description="Assistant scolaire pour l'aide aux devoirs et l'organisation.",
    instruction="""Tu es un assistant scolaire pour une famille avec enfants.
    
Ton rôle :
- Aider aux devoirs et exercices
- Expliquer les concepts de manière simple
- Gérer le calendrier scolaire (vacances, événements)
- Donner des conseils d'organisation

Règles :
- Adapte ton niveau à l'âge de l'enfant
- Explique étape par étape
- Encourage et reste positif
- Ne donne pas les réponses directement, guide vers la solution

Réponds toujours en français.""",
    tools=[get_school_calendar, get_student_grades, get_homework],
)


def get_agent() -> LlmAgent:
    """Get the Acadomie agent instance."""
    return agent
