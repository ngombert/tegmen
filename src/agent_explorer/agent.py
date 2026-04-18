from google.adk.agents import LlmAgent
from google.adk.models.lite_llm import LiteLlm
import litellm

from common.config import config
from common.utils import load_prompt
import os
from agent_explorer.tools import (
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
    instruction=load_prompt(os.path.join(os.path.dirname(__file__), "instruction.md")),
    tools=[search_destinations, get_activities, get_weather_forecast],
)


def get_agent() -> LlmAgent:
    """Get the Explorer agent instance."""
    return agent
