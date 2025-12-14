from google.adk.agents import LlmAgent
from google.adk.models.lite_llm import LiteLlm
import litellm

from src.common.config import config

# Import agents from their independent modules
from src.agent_gourmet import agent as agent_gourmet
from src.agent_acadomie import agent as agent_acadomie
from src.agent_explorer import agent as agent_explorer

# Suppress LiteLLM debug info if not in debug mode
litellm.suppress_debug_info = not config.DEBUG


# Create LiteLLM model instance for Maestro fallback
model = LiteLlm(model=config.DEFAULT_MODEL, verbose=config.DEBUG)

# Agent Maestro - Fallback pour les requêtes non classifiées
agent_maestro = LlmAgent(
    name="maestro",
    model=model,
    description="Assistant familial généraliste.",
    instruction="""Tu es Maestro, l'assistant principal d'une famille française.
    
Ton rôle :
- Répondre aux questions générales de la famille
- Aider à organiser le quotidien familial
- Donner des conseils pratiques

Tu peux traiter des sujets variés qui ne concernent pas spécifiquement :
- La cuisine (agent_gourmet s'en occupe)
- L'école et les devoirs (agent_acadomie s'en occupe)
- Les voyages et sorties (agent_explorer s'en occupe)

Réponds toujours en français de manière concise et utile.""",
)


# Mapping route -> agent
AGENTS = {
    "gourmet": agent_gourmet,
    "acadomie": agent_acadomie,
    "explorer": agent_explorer,
    "unknown": agent_maestro,
}


def get_agent(route: str) -> LlmAgent:
    """Get agent by route name."""
    return AGENTS.get(route, agent_maestro)
