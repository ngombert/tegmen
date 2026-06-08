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
from agent_acadomie.app.schemas.calendar import CalendarRequest, CalendarResponse
from agent_acadomie.app.services.calendar_service import CalendarService
from agent_acadomie.app.schemas.grades import GradeRequest, GradeResponse, UserIdentity
from agent_acadomie.app.services.grades_service import GradesService
from agent_acadomie.app.schemas.organization import OrganizationRequest, OrganizationResponse
from agent_acadomie.app.services.llm_service import LLMService
from agent_acadomie.app.services.organization_service import OrganizationService

from common.fact_extractor import FactExtractor

logger = setup_acadomie_logger("acadomie_a2a")
homework_service = HomeworkService()
calendar_service = CalendarService()
grades_service = GradesService()
llm_service = LLMService()
organization_service = OrganizationService(llm_service, homework_service, grades_service)
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
    
    # Extract facts asynchronously
    new_facts_payload = None
    try:
        extracted_facts = await fact_extractor.extract_facts(text)
        if extracted_facts:
            new_facts_payload = {"facts": [f.model_dump() for f in extracted_facts]}
    except Exception as fe:
        logger.warning(f"Failed to extract facts in Acadomie: {fe}")

    # Check for Yield (out-of-domain)
    off_topic_keywords = ["recette", "cuisine", "repas", "plat", "ingrédient", "dîner", "diner", "gâteau", "gateau"]
    if any(kw in text for kw in off_topic_keywords):
        res = {
            "status": "yield",
            "message": "Je suis l'agent Acadomie et je ne peux répondre qu'aux questions scolaires.",
            "context_stack": []
        }
        if new_facts_payload:
            res["new_facts_payload"] = new_facts_payload
        return res
    
    # Simple keyword-based dispatch for Lean Acadomie
    if any(k in text for k in ["devoir", "exercice", "leçon"]):
        res = format_a2a_message("Je peux vous aider avec les devoirs. Que souhaitez-vous consulter ou ajouter ?", context_id)
    elif any(k in text for k in ["calendrier", "examen", "vacance", "événement"]):
        res = format_a2a_message("Je peux consulter le calendrier scolaire pour vous. Que voulez-vous savoir ?", context_id)
    elif any(k in text for k in ["note", "résultat", "moyenne"]):
        res = format_a2a_message("Je peux vous montrer les notes. Pour quelle matière ?", context_id)
    elif any(k in text for k in ["conseil", "organisation", "révision"]):
        res = format_a2a_message("Je peux vous donner des conseils d'organisation. Quel est votre besoin ?", context_id)
    else:
        res = format_a2a_message("Je suis l'agent Acadomie. Je peux vous aider pour les devoirs, le calendrier et les notes. Que voulez-vous faire ?", context_id)

    if new_facts_payload:
        res["new_facts_payload"] = new_facts_payload
    return res

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

@with_context
async def handle_calendar_list(params: dict[str, Any] | None) -> dict[str, Any]:
    """
    Handler for calendar/list JSON-RPC method.
    Retrieves the school calendar events for the family.
    Useful for checking upcoming exams, school trips, and meetings.
    """
    request_data = params or {}
    
    # Extract family_id from context if not in params
    if "family_id" not in request_data and "context" in request_data:
        ctx = request_data["context"]
        if isinstance(ctx, dict) and "family_id" in ctx:
            request_data["family_id"] = ctx["family_id"]
            
    request = CalendarRequest(**request_data)
    events = await calendar_service.get_events(request.family_id)
    response = CalendarResponse(events=events, total_count=len(events))
    return response.model_dump()

@with_context
async def handle_grades_list(params: dict[str, Any] | None) -> dict[str, Any]:
    """
    Handler for grades/list JSON-RPC method.
    Retrieves the grades for a specific student, applying role-based access control.
    """
    request_data = params or {}
    
    # Extract context
    ctx = request_data.get("context", {})
    if not isinstance(ctx, dict):
        ctx = {}
        
    # Extract family_id
    if "family_id" not in request_data and "family_id" in ctx:
        request_data["family_id"] = ctx["family_id"]
        
    # Validation of the basic request
    request = GradeRequest(**request_data)
    
    # Extract and validate user identity
    user_data = ctx.get("user") or ctx.get("user_identity")
    if not user_data:
        raise A2ARPCError(
            code=A2ARPCError.FORBIDDEN,
            message="Accès refusé : Identité de l'utilisateur non fournie dans le contexte",
            data=enrich_error_data(None),
        )
        
    user = UserIdentity(**user_data)
    
    # RBAC logic
    if user.role != "parent" and user.id != request.student_id:
        raise A2ARPCError(
            code=A2ARPCError.FORBIDDEN,
            message="Accès refusé : Vous n'avez pas l'autorisation de consulter les notes de cet élève",
            data=enrich_error_data(None),
        )
        
    grades = await grades_service.get_grades(request.family_id, request.student_id)
    
    avg = None
    if grades:
        # Simple average out of 20
        normalized_grades = [(g.grade / g.max_grade) * 20 for g in grades]
        avg = sum(normalized_grades) / len(normalized_grades)
        
    response = GradeResponse(grades=grades, average=avg)
    return response.model_dump()

@with_context
async def handle_organization_advice(params: dict[str, Any] | None) -> dict[str, Any]:
    """
    Handler for organization/advice JSON-RPC method.
    Generates personalized organizational advice using LLM based on student's context.
    """
    request_data = params or {}
    
    # Extract context
    ctx = request_data.get("context", {})
    if not isinstance(ctx, dict):
        ctx = {}
        
    # Extract family_id
    if "family_id" not in request_data and "family_id" in ctx:
        request_data["family_id"] = ctx["family_id"]
        
    # Validation
    request = OrganizationRequest(**request_data)
    
    # Call service
    advice = await organization_service.generate_advice(
        family_id=request.family_id,
        student_id=request.student_id,
        question=request.question
    )
    
    response = OrganizationResponse(advice=advice)
    return response.model_dump()

# Methods mapping for A2AServer registration
ACADOMIE_METHODS = {
    "message/send": handle_message_send,
    "homework/list": handle_homework_list,
    "homework/add": handle_homework_add,
    "calendar/list": handle_calendar_list,
    "grades/list": handle_grades_list,
    "organization/advice": handle_organization_advice,
}
