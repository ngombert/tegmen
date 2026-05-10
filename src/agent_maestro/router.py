"""Semantic Router for intent classification - Dynamic Config Powered."""

from typing import Optional, Dict
from semantic_router import Route
from semantic_router.routers import SemanticRouter
from semantic_router.encoders import HuggingFaceEncoder
from semantic_router.index import LocalIndex
import numpy as np

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
        "Bonjour", "Salut", "Coucou", "Hello", "Ça va ?", "Comment ça va ?",
        "Ça gaze ?", "Bien le bonjour",
        "Raconte-moi une blague", "Quelle est la météo ?",
        "Qui es-tu ?", "Tu t'appelles comment ?", "C'est quoi ton nom ?",
        "Merci", "Merci beaucoup", "C'est gentil", "De rien",
        "Au revoir", "À plus tard", "À bientôt", "Bonne soirée",
        "Quelle est la capitale de la France ?",
        "Parle-moi de toi", "Tu sais faire quoi ?",
        "Bonne nuit", "Fais de beaux rêves",
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
        _router = SemanticRouter(encoder=encoder, routes=all_routes)
        # Ensure index is ready in this version
        if hasattr(_router, "sync"):
            _router.sync(sync_mode="local")
        logger.info(f"Semantic router initialized with {len(_router.routes)} routes.")
    return _router

# Confidence Thresholds
# Optimized for multilingual-e5-small (which tends to have higher similarity scores)
THRESHOLD_ROUTING = 0.40      # Full confidence (increased from 0.30)
THRESHOLD_CLARIFICATION = 0.20 # Ambiguous (increased from 0.15)
THRESHOLD_ESCAPE_HATCH = 0.95  # Extremely strong intent overrides sticky routing
STICKY_BONUS_MULTIPLIER = 1.3  # Bonus applied to active agent's score

def classify_intent(message: str, active_agent: Optional[str] = None) -> tuple[str, float]:
    """
    Classify user intent using semantic similarity.

    Uses get_all_scores for ALL paths (with or without active_agent)
    to guarantee numerically comparable scores.

    Args:
        message: User message to classify
        active_agent: Optional agent ID currently active in the session

    Returns:
        (Route name, similarity_score)
    """
    if not message:
        return ("unknown", 0.0)

    scores = get_all_scores(message).copy()
    if not scores:
        return ("unknown", 0.0)

    if active_agent:
        # Normalize active_agent to route name (e.g. agent_gourmet -> gourmet)
        active_route = active_agent[6:] if active_agent.startswith("agent_") else active_agent

        # Semantic Escape Hatch: if any intention is extremely strong, do not apply sticky routing
        if max(scores.values()) > THRESHOLD_ESCAPE_HATCH:
            best_route = max(scores.items(), key=lambda x: x[1])
            return best_route[0], float(best_route[1])

        # Apply bonus
        if active_route in scores:
            scores[active_route] = min(scores[active_route] * STICKY_BONUS_MULTIPLIER, 1.0)

    # Find the route with the highest score
    best_route = max(scores.items(), key=lambda x: x[1])
    return best_route[0], float(best_route[1])

def warmup() -> None:
    """Pre-load the embedding model and verify all routes are ready."""
    router_inst = get_router()
    logger.info(f"Warming up semantic router with {len(router_inst.routes)} routes...")
    _ = classify_intent("test")
    logger.info("Semantic router warmup complete.")

def get_all_scores(message: str) -> dict[str, float]:
    """
    Get maximum similarity scores for all registered routes.

    Encodes the message and queries the index directly.
    No caching — conversational messages are typically unique,
    making an unbounded lru_cache a memory leak.
    """
    if not message:
        return {}

    router_inst = get_router()
    # Encode message into embedding vector
    v = router_inst.encoder([message])
    # Convert to numpy array for compatibility with index.query
    vector = np.array(v[0])
    # Query index (get enough results to cover all routes)
    scores, routes = router_inst.index.query(vector, top_k=100)

    route_scores: dict[str, float] = {}
    for r, s in zip(routes, scores):
        route_name = str(r)
        score = float(s)
        # Keep the best score for each route
        if route_name not in route_scores or score > route_scores[route_name]:
            route_scores[route_name] = score

    # Add routes that might have 0 score if not in top_k
    for route in router_inst.routes:
        if route.name not in route_scores:
            route_scores[route.name] = 0.0

    return route_scores

def reload_router() -> None:
    """
    Rebuild the router if the registry has changed.
    """
    global _router
    dynamic_routes = _build_dynamic_routes()
    _router = SemanticRouter(encoder=encoder)
    for route in [chitchat_route] + dynamic_routes:
        _router.add(route)
    if hasattr(_router, "sync"):
        _router.sync(sync_mode="local")
    logger.info(f"Router reloaded with {len(_router.routes)} routes.")
