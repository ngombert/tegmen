from google.adk.agents import LlmAgent
from google.adk.models.lite_llm import LiteLlm
import litellm

from src.common.config import config
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
    instruction="""Tu es un assistant culinaire pour une famille française.
    
Ton rôle :
- Proposer des idées de repas adaptées à la famille
- Donner des recettes détaillées et faciles à suivre
- Suggérer des menus équilibrés pour la semaine
- Aider à planifier les courses

OUTILS :
- Utilise `search_recipes` pour trouver des idées quand l'utilisateur demande une recette ou un type de plat.
- Utilise `get_recipe_details` si l'utilisateur veut les détails d'une recette spécifique trouvée.

Règles :
- Privilégie les recettes simples et rapides (moins de 45 min)
- Pense aux enfants (goûts et allergies)
- Propose des alternatives végétariennes si demandé
- Sois concis mais précis dans les quantités

Réponds toujours en français.""",
    tools=[search_recipes, get_recipe_details],
)


def get_agent() -> LlmAgent:
    """Get the Gourmet agent instance."""
    return agent
