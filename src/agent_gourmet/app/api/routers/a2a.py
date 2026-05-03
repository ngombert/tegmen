from typing import Any, Callable
from functools import wraps
from pydantic import ValidationError

from agent_gourmet.app.logger import setup_gourmet_logger
from agent_gourmet.app.services.recipe_service import RecipeService
from agent_gourmet.app.schemas.recipe import SearchRequest, RecipeDetailRequest, RecipeDetailResponse
from common.exceptions import A2ARPCError
from agent_gourmet.app.context import (
    set_correlation_id,
    reset_correlation_id,
    enrich_error_data,
)

logger = setup_gourmet_logger("gourmet_a2a")
recipe_service = RecipeService()

def with_context(func: Callable) -> Callable:
    @wraps(func)
    async def wrapper(params: dict[str, Any] | None) -> dict[str, Any]:
        # Extract correlation_id from context
        ctx = (params or {}).get("context", {})
        cid = ctx.get("correlation_id") if isinstance(ctx, dict) else None
        
        # Set context token
        token = set_correlation_id(cid)
        method_name = func.__name__.replace('handle_', '')
        logger.info(f"A2A | {method_name}")
        
        try:
            return await func(params)
        except ValidationError as e:
            raise A2ARPCError(
                code=A2ARPCError.INVALID_PARAMS,
                message=f"Paramètres invalides : {str(e)}",
                data=enrich_error_data(None),
            )
        except A2ARPCError as e:
            e.data = enrich_error_data(e.data)
            raise
        except Exception as e:
            # We log error type instead of full exception to avoid leaking PII via stacktrace
            logger.error(f"Unexpected error in {method_name}: {type(e).__name__} - {str(e)}")
            raise A2ARPCError(
                code=A2ARPCError.INTERNAL_ERROR,
                message=f"Erreur interne lors de {method_name}",
                data=enrich_error_data(None),
            )
        finally:
            reset_correlation_id(token)
            
    return wrapper

@with_context
async def handle_search_recipes(params: dict[str, Any] | None) -> dict[str, Any]:
    """Handler for search_recipes JSON-RPC method."""
    request_data = params or {}
    request = SearchRequest(**request_data)
    response = await recipe_service.search_recipes(request)
    return response.model_dump()

@with_context
async def handle_get_recipe_details(params: dict[str, Any] | None) -> dict[str, Any]:
    """Handler for get_recipe_details JSON-RPC method."""
    request_data = params or {}
    request = RecipeDetailRequest(**request_data)
    detail = await recipe_service.get_recipe_details(request.recipe_id)
    response = RecipeDetailResponse(recipe=detail)
    return response.model_dump()

@with_context
async def handle_message_send(params: dict[str, Any] | None) -> dict[str, Any]:
    """
    Handler for message/send JSON-RPC method (standard Tegmen chat).
    Dispatches to business logic based on natural language text.
    """
    if not params or "message" not in params:
        raise A2ARPCError(
            code=A2ARPCError.INVALID_PARAMS,
            message="Paramètre 'message' manquant",
            data=enrich_error_data(None),
        )
    
    message_obj = params["message"]
    text = ""
    
    # Extract text from message parts
    if isinstance(message_obj, dict) and "parts" in message_obj:
        for part in message_obj["parts"]:
            if "text" in part:
                text += part["text"]
    
    text = text.lower().strip()
    
    if not text:
        return {"message": "Je n'ai pas bien compris votre message. Que cherchez-vous ?"}
    
    # Simple keyword-based dispatch for Lean Gourmet
    if any(k in text for k in ["recette", "cherche", "propose", "manger"]):
        # Very simple heuristic
        query = text.replace("recette de", "").replace("cherche", "").replace("je veux", "").strip()
        
        request = SearchRequest(query=query)
        response = await recipe_service.search_recipes(request)
        
        if response.total_count == 0:
            return {"message": f"Désolé, je n'ai pas trouvé de recette pour '{query}'."}
        
        res_list = [r.name for r in response.results[:3]]
        return {"message": f"Voici ce que j'ai trouvé : {', '.join(res_list)}. Laquelle vous intéresse ?"}
    
    return {"message": "Je suis l'agent Gourmet. Je peux vous aider à trouver des recettes. Que cherchez-vous ?"}

# Methods mapping for A2AServer registration
GOURMET_METHODS = {
    "search_recipes": handle_search_recipes,
    "get_recipe_details": handle_get_recipe_details,
    "message/send": handle_message_send,
}
