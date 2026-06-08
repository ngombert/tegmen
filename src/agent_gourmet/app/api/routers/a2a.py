from typing import Any, Callable
from functools import wraps
import uuid
from pydantic import ValidationError

from agent_gourmet.app.logger import setup_gourmet_logger
from agent_gourmet.app.services.recipe_service import RecipeService
from agent_gourmet.app.services.llm_service import LLMService
from agent_gourmet.app.schemas.recipe import SearchRequest, RecipeDetailRequest, RecipeDetailResponse
from common.exceptions import A2ARPCError
from common.a2a_utils import format_a2a_message
from agent_gourmet.app.context import (
    set_correlation_id,
    reset_correlation_id,
    enrich_error_data,
)

from common.fact_extractor import FactExtractor

logger = setup_gourmet_logger("gourmet_a2a")
recipe_service = RecipeService()
fact_extractor = FactExtractor()

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
    llm_service = LLMService()
    if not params or "message" not in params:
        raise A2ARPCError(
            code=A2ARPCError.INVALID_PARAMS,
            message="Paramètre 'message' manquant",
            data=enrich_error_data(None),
        )
    
    # Propagate contextId if present
    context_id = params.get("contextId")
    
    message_obj = params["message"]
    text = ""
    
    # Extract text from message parts
    if isinstance(message_obj, dict) and "parts" in message_obj:
        for part in message_obj["parts"]:
            if "text" in part:
                text += part["text"]
    
    text = text.lower().strip()
    
    if not text:
        return format_a2a_message("Je n'ai pas bien compris votre message. Que cherchez-vous ?", context_id)
    
    # Extract facts asynchronously
    new_facts_payload = None
    try:
        extracted_facts = await fact_extractor.extract_facts(text)
        if extracted_facts:
            new_facts_payload = {"facts": [f.model_dump() for f in extracted_facts]}
    except Exception as fe:
        logger.warning(f"Failed to extract facts in Gourmet: {fe}")

    # Extract known facts from context
    context_dict = params.get("context") or {}
    known_facts = None
    if isinstance(context_dict, dict):
        known_facts = context_dict.get("known_facts")
    elif hasattr(context_dict, "known_facts"):
        known_facts = context_dict.known_facts

    system_prompt = None
    if known_facts:
        facts_text = "\n".join(f"- {fact}" for fact in known_facts)
        from pathlib import Path
        try:
            prompt_path = Path(__file__).parent.parent / "prompts" / "system_prompt.md"
            base_prompt = prompt_path.read_text(encoding="utf-8")
        except Exception:
            base_prompt = "Tu es Gourmet, assistant culinaire de l'écosystème Tegmen."
        system_prompt = f"{base_prompt}\n\nVoici ce que je sais sur l'utilisateur :\n{facts_text}"

    # Use LLM to generate the response (Story 6.6)
    try:
        response_text = await llm_service.generate_response(text, system_prompt)
        if "[yield]" in response_text.lower():
            yield_marker = "[yield]"
            idx = response_text.lower().find(yield_marker)
            message = response_text[idx + len(yield_marker):].strip()
            if not message:
                message = "Je suis l'agent Gourmet et je passe la main."
            res = {
                "status": "yield",
                "message": message,
                "context_stack": []
            }
            if new_facts_payload:
                res["new_facts_payload"] = new_facts_payload
            return res
        res = format_a2a_message(response_text, context_id)
        if new_facts_payload:
            res["new_facts_payload"] = new_facts_payload
        return res
    except Exception as e:
        logger.error(f"Error calling LLM in handle_message_send: {e}")
        res = format_a2a_message("Désolé, je rencontre une difficulté pour vous répondre actuellement.", context_id)
        if new_facts_payload:
            res["new_facts_payload"] = new_facts_payload
        return res

# Methods mapping for A2AServer registration
GOURMET_METHODS = {
    "search_recipes": handle_search_recipes,
    "get_recipe_details": handle_get_recipe_details,
    "message/send": handle_message_send,
}
