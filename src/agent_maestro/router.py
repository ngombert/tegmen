"""Semantic Router for intent classification - Dynamic Config Powered."""

from typing import Optional, Dict
from semantic_router import Route
from semantic_router.routers import SemanticRouter
from semantic_router.encoders import HuggingFaceEncoder

from common.config import config
from common.agent_registry import agent_registry
from common.logger import setup_logger

logger = setup_logger("router")

# Initialize encoder with local model
encoder = HuggingFaceEncoder(name=config.EMBEDDING_MODEL)

# 1. System Internal Routes (Hardcoded as per user request)
chitchat_route = Route(
    name="chitchat",
    utterances=[
        "Bonjour", "Salut", "Comment ça va ?",
        "Raconte-moi une blague", "Quelle est la météo ?",
        "Qui es-tu ?", "Tu t'appelles comment ?",
        "Merci", "Au revoir",
        "Quelle est la capitale de la France ?",
        "Parle-moi de toi", "Bonne nuit",
    ],
)

def _build_dynamic_routes() -> list[Route]:
    """
    Load specialized agents from the registry and build semantic routes.
    """
    dynamic_routes = []
    agents = agent_registry.get_agents()
    
    for name, agent in agents.items():
        if agent.utterances:
            logger.info(f"Adding semantic route for agent: {name} ({len(agent.utterances)} utterances)")
            dynamic_routes.append(
                Route(name=name, utterances=agent.utterances)
            )
        else:
            logger.warning(f"Agent {name} has no utterances, skipping semantic route.")
            
    return dynamic_routes

# Internal router instance, initialized lazily
_router: Optional[SemanticRouter] = None

def get_router() -> SemanticRouter:
    """
    Get or initialize the SemanticRouter instance.
    """
    global _router
    if _router is None:
        logger.info("Initializing semantic router...")
        all_routes = [chitchat_route] + _build_dynamic_routes()
        _router = SemanticRouter(encoder=encoder, routes=all_routes, auto_sync="local")
        logger.info(f"Semantic router initialized with {len(_router.routes)} routes.")
    return _router

# Confidence Thresholds
THRESHOLD_ROUTING = 0.30      # Full confidence
THRESHOLD_CLARIFICATION = 0.15 # Ambiguous - ask for clarification

def classify_intent(message: str) -> tuple[str, float]:
    """
    Classify user intent using semantic similarity.

    Args:
        message: User message to classify

    Returns:
        (Route name, similarity_score)
    """
    if not message:
        return ("unknown", 0.0)
        
    router_inst = get_router()
    result = router_inst(message)
    
    route_name = result.name if result.name else "unknown"
    score = getattr(result, "similarity_score", 0.0)
    if score is None:
        score = 0.0
    
    return (route_name, float(score))

def warmup() -> None:
    """Pre-load the embedding model and verify all routes are ready."""
    router_inst = get_router()
    logger.info(f"Warming up semantic router with {len(router_inst.routes)} routes...")
    _ = classify_intent("test")
    logger.info("Semantic router warmup complete.")

def reload_router() -> None:
    """
    Rebuild the router if the registry has changed.
    """
    global _router
    logger.info("Reloading semantic router from registry...")
    dynamic_routes = _build_dynamic_routes()
    _router = SemanticRouter(encoder=encoder, routes=[chitchat_route] + dynamic_routes, auto_sync="local")
    logger.info(f"Router reloaded with {len(_router.routes)} routes.")
