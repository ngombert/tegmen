from typing import Any
from common.logger import setup_logger
from agent_gourmet.app.services.recipe_service import RecipeService
from agent_gourmet.app.schemas.recipe import SearchRequest, RecipeDetailRequest, RecipeDetailResponse

from pydantic import ValidationError
from common.exceptions import A2ARPCError

logger = setup_logger("gourmet_a2a")
recipe_service = RecipeService()

async def handle_search_recipes(params: dict[str, Any] | None) -> dict[str, Any]:
    """Handler for search_recipes JSON-RPC method."""
    logger.info(f"A2A | search_recipes called with params: {params}")
    
    try:
        # Validate and parse params
        request_data = params or {}
        request = SearchRequest(**request_data)
        
        # Call service
        response = await recipe_service.search_recipes(request)
        
        # Return serializable dict
        return response.model_dump()
    except ValidationError as e:
        raise A2ARPCError(
            code=A2ARPCError.INVALID_PARAMS,
            message=f"Paramètres invalides : {str(e)}"
        )

async def handle_get_recipe_details(params: dict[str, Any] | None) -> dict[str, Any]:
    """Handler for get_recipe_details JSON-RPC method."""
    logger.info(f"A2A | get_recipe_details called with params: {params}")
    
    try:
        # Validate and parse params
        request_data = params or {}
        request = RecipeDetailRequest(**request_data)
        
        # Call service
        detail = await recipe_service.get_recipe_details(request.recipe_id)
        
        # Validate and return response
        response = RecipeDetailResponse(recipe=detail)
        return response.model_dump()
    except ValidationError as e:
        raise A2ARPCError(
            code=A2ARPCError.INVALID_PARAMS,
            message=f"Paramètres invalides : {str(e)}"
        )
    except A2ARPCError:
        raise
    except Exception as e:
        logger.exception(f"Unexpected error in get_recipe_details: {e}")
        raise A2ARPCError(
            code=A2ARPCError.INTERNAL_ERROR,
            message=f"Erreur interne lors de la récupération de la recette : {str(e)}"
        )

async def handle_message_send(params: dict[str, Any] | None) -> str:
    """
    Handler for message/send JSON-RPC method (standard Tegmen chat).
    Dispatches to business logic based on natural language text.
    """
    logger.info(f"A2A | message/send called with params: {params}")
    
    if not params or "message" not in params:
        raise A2ARPCError(
            code=A2ARPCError.INVALID_PARAMS,
            message="Paramètre 'message' manquant"
        )
    
    message_obj = params["message"]
    text = ""
    
    # Extract text from message parts (following A2A Message structure)
    if isinstance(message_obj, dict) and "parts" in message_obj:
        for part in message_obj["parts"]:
            if "text" in part:
                text += part["text"]
    
    text = text.lower().strip()
    
    if not text:
        return {"message": "Je n'ai pas bien compris votre message. Que cherchez-vous ?"}
    
    # Simple keyword-based dispatch for Lean Gourmet
    if any(k in text for k in ["recette", "cherche", "propose", "manger"]):
        # Extract potential query (very simple heuristic)
        query = text.replace("recette de", "").replace("cherche", "").replace("je veux", "").strip()
        
        try:
            request = SearchRequest(query=query)
            response = await recipe_service.search_recipes(request)
            
            if response.total_count == 0:
                return {"message": f"Désolé, je n'ai pas trouvé de recette pour '{query}'."}
            
            res_list = [r.name for r in response.results[:3]]
            return {"message": f"Voici ce que j'ai trouvé : {', '.join(res_list)}. Laquelle vous intéresse ?"}
        except ValidationError as e:
            raise A2ARPCError(
                code=A2ARPCError.INVALID_PARAMS,
                message=f"Requête de recherche invalide : {str(e)}"
            )
    
    return {"message": "Je suis l'agent Gourmet. Je peux vous aider à trouver des recettes. Que cherchez-vous ?"}

# Methods mapping for A2AServer registration
GOURMET_METHODS = {
    "search_recipes": handle_search_recipes,
    "get_recipe_details": handle_get_recipe_details,
    "message/send": handle_message_send,
}
