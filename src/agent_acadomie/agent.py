from google.adk.agents import LlmAgent
from google.adk.models.lite_llm import LiteLlm
import litellm

from src.common.config import config
from src.common.utils import load_prompt
import os
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
    instruction=load_prompt(os.path.join(os.path.dirname(__file__), "instruction.md")),
    tools=[get_school_calendar, get_student_grades, get_homework],
)


def get_agent() -> LlmAgent:
    """Get the Acadomie agent instance."""
    return agent
