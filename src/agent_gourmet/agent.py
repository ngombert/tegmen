from google.adk.agents import LlmAgent
from google.adk.models.lite_llm import LiteLlm
import litellm

from src.common.config import config
from src.common.utils import load_prompt
import os
from src.agent_gourmet.tools import search_recipes, get_recipe_details

# Suppress LiteLLM debug info if not in debug mode
litellm.suppress_debug_info = not config.DEBUG


# Create LiteLLM model instance
model = LiteLlm(model=config.DEFAULT_MODEL, verbose=config.DEBUG)

# Agent Gourmet - Cuisine et recettes
agent = LlmAgent(
    name="agent_gourmet",
    model=model,
    description="Expert en cuisine familiale, recettes et planification de repas.",
    instruction=load_prompt(os.path.join(os.path.dirname(__file__), "instruction.md")),
    tools=[search_recipes, get_recipe_details],
)


def get_agent() -> LlmAgent:
    """Get the Gourmet agent instance."""
    return agent
