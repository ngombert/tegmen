from google.adk.agents import LlmAgent
from google.adk.models.lite_llm import LiteLlm
import litellm

from common.config import config
from common.utils import load_prompt
import os

# Import agents from their independent modules
from agent_gourmet.agent import agent as agent_gourmet
from agent_acadomie.agent import agent as agent_acadomie
from agent_explorer.agent import agent as agent_explorer

# Suppress LiteLLM debug info if not in debug mode
litellm.suppress_debug_info = not config.DEBUG


# Create LiteLLM model instance for Maestro fallback
model = LiteLlm(model=config.DEFAULT_MODEL, verbose=config.DEBUG)

# Agent Maestro - Fallback pour les requêtes non classifiées
agent_maestro = LlmAgent(
    name="maestro",
    model=model,
    description="Assistant familial généraliste.",
    instruction=load_prompt(os.path.join(os.path.dirname(__file__), "instruction.md")),
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
