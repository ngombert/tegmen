from typing import Any, Callable
from functools import wraps
from pydantic import ValidationError

from agent_acadomie.app.logger import setup_acadomie_logger
from common.exceptions import A2ARPCError
from common.a2a_utils import format_a2a_message
from agent_acadomie.app.context import (
    set_correlation_id,
    reset_correlation_id,
    enrich_error_data,
)
from agent_acadomie.app.schemas.homework import HomeworkListRequest, HomeworkListResponse, HomeworkAddRequest
from agent_acadomie.app.services.homework_service import HomeworkService

logger = setup_acadomie_logger("acadomie_a2a")
homework_service = HomeworkService()

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
async def handle_message_send(params: dict[str, Any] | None) -> dict[str, Any]:
    """
    Handler for message/send JSON-RPC method (standard Tegmen chat).
    Initial implementation with basic keyword dispatch.
    """
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
        return format_a2a_message("Je n'ai pas bien compris votre message. Comment puis-je vous aider pour l'école ?", context_id)
    
    # Simple keyword-based dispatch for Lean Acadomie
    if any(k in text for k in ["devoir", "exercice", "leçon"]):
        return format_a2a_message("Je peux vous aider avec les devoirs. Que souhaitez-vous consulter ou ajouter ?", context_id)
    
    if any(k in text for k in ["calendrier", "examen", "vacance", "événement"]):
        return format_a2a_message("Je peux consulter le calendrier scolaire pour vous. Que voulez-vous savoir ?", context_id)

    if any(k in text for k in ["note", "résultat", "moyenne"]):
        return format_a2a_message("Je peux vous montrer les notes. Pour quelle matière ?", context_id)

    if any(k in text for k in ["conseil", "organisation", "révision"]):
        return format_a2a_message("Je peux vous donner des conseils d'organisation. Quel est votre besoin ?", context_id)
    
    return format_a2a_message("Je suis l'agent Acadomie. Je peux vous aider pour les devoirs, le calendrier et les notes. Que voulez-vous faire ?", context_id)

@with_context
async def handle_homework_list(params: dict[str, Any] | None) -> dict[str, Any]:
    """Handler for homework/list JSON-RPC method."""
    request_data = params or {}
    
    # Extract family_id from context if not in params
    if "family_id" not in request_data and "context" in request_data:
        ctx = request_data["context"]
        if isinstance(ctx, dict) and "family_id" in ctx:
            request_data["family_id"] = ctx["family_id"]
            
    request = HomeworkListRequest(**request_data)
    homeworks = await homework_service.get_homework(request.family_id, request.include_completed)
    response = HomeworkListResponse(homeworks=homeworks, total_count=len(homeworks))
    return response.model_dump()

@with_context
async def handle_homework_add(params: dict[str, Any] | None) -> dict[str, Any]:
    """Handler for homework/add JSON-RPC method."""
    request_data = params or {}
    
    # Extract family_id from context if not in params
    if "family_id" not in request_data and "context" in request_data:
        ctx = request_data["context"]
        if isinstance(ctx, dict) and "family_id" in ctx:
            request_data["family_id"] = ctx["family_id"]
            
    request = HomeworkAddRequest(**request_data)
    new_hw = await homework_service.add_homework(request)
    return new_hw.model_dump()

# Methods mapping for A2AServer registration
ACADOMIE_METHODS = {
    "message/send": handle_message_send,
    "homework/list": handle_homework_list,
    "homework/add": handle_homework_add,
}
