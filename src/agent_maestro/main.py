"""FastAPI application for Maestro - Family Agents entry point with A2A routing."""

import os
import uuid
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request, Depends
from fastapi.middleware.cors import CORSMiddleware

from agent_maestro.router import classify_intent, warmup
from agent_maestro.schemas import ChatRequest, ChatResponse, HealthResponse
from common.schemas import JsonRpcRequest, JsonRpcResponse, JsonRpcError
from common.config import config
from common.a2a_client import call_remote_agent
from common.agent_registry import agent_registry
from common.auth import get_current_identity
from common.privacy import sanitize_message, log_audit_trail
from common.users import get_user_profile
from common.schemas import JsonRpcRequest, JsonRpcResponse, JsonRpcError, RequestContext
from common.logger import setup_logger

logger = setup_logger("maestro")


# Initialized with Lean A2A standards

# Maestro is now a pure A2A Gateway. 
# It routes all non-native requests to specialized agents via A2A.


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan - startup and shutdown events."""
    logger.info("🚀 Starting Tegmen Maestro...")
    logger.info(f"📦 Loading embedding model: {config.EMBEDDING_MODEL}")
    warmup()
    logger.info("✅ Semantic router ready!")
    logger.info("🔗 A2A Gateway Mode: Agents loaded from registry")
    for agent in agent_registry.list_agents():
        logger.info(f"   - {agent['name']}: {agent['url']}")
    yield
    logger.info("👋 Shutting down Tegmen Maestro...")


app = FastAPI(
    title="Tegmen Maestro - Family Agents Gateway",
    description="Assistant familial intelligent avec agents spécialisés (A2A)",
    version="0.1.0",
    lifespan=lifespan,
    swagger_ui_parameters={"persistAuthorization": True},
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for development
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


async def get_request_context(
    identity: dict = Depends(get_current_identity),
    request_obj: Request = None
) -> RequestContext:
    """
    Dependency that hydrates the full RequestContext from JWT identity and User Profile.
    """
    user_id = identity.get("user_id")
    family_id = identity.get("family_id")
    
    profile = get_user_profile(user_id, family_id)
    if not profile:
        logger.error(f"Profile not found for user_id={user_id}, family_id={family_id}")
        raise HTTPException(status_code=403, detail="Profil utilisateur introuvable ou accès refusé")
    
    # In a real app, correlation_id should come from headers or body
    correlation_id = str(uuid.uuid4())
    
    return RequestContext(
        family_id=family_id,
        user_id=user_id,
        user_name=profile.name,
        role=profile.role,
        correlation_id=correlation_id,
        preferences=profile.preferences,
        restrictions=profile.restrictions
    )

def check_agent_access(agent_name: str, context: RequestContext):
    """
    Check if the user has permission to access a specific agent.
    """
    if context.role == "child" and agent_name in (context.restrictions or []):
        logger.warning(f"RBAC | User {context.user_id} (Child) blocked from accessing {agent_name}")
        raise HTTPException(
            status_code=403, 
            detail=f"Désolé, ton profil ne permet pas d'accéder à l'agent '{agent_name}'."
        )


@app.get("/health", response_model=HealthResponse, tags=["System"], summary="État de santé")
async def health_check():
    """Vérifie que l'agent Maestro est en ligne et prêt à router."""
    return HealthResponse()


@app.post(
    "/api/v1/routing", 
    response_model=JsonRpcResponse, 
    tags=["Gateway"],
    summary="Point d'entrée principal du routage A2A",
    responses={
        422: {"description": "Erreur de validation structurelle de la requête JSON-RPC"}
    }
)
async def route_request(
    request: JsonRpcRequest,
    context: RequestContext = Depends(get_request_context)
):
    """
    Endpoint principal du Gateway Maestro.
    
    Reçoit une requête standard JSON-RPC 2.0 et la dirige vers l'agent spécialisé 
    compétent après une classification sémantique de l'intention utilisateur.
    """
    logger.info(f"📥 Received A2A routing request: method='{request.method}', user='{context.user_name}'")
    
    # Apply PII filter if message is present in params
    if request.params and "message" in request.params:
        original_msg = request.params["message"]
        request.params["message"] = sanitize_message(original_msg)
        
    # Audit Trail
    log_audit_trail(
        event_type="a2a_routing",
        user_id=context.user_id,
        family_id=context.family_id,
        extra={"method": request.method, "rpc_id": str(request.id), "role": context.role}
    )

    # Mock implementation for Story 1.2
    # In Story 3.1, this will calls the real semantic router and specialized agents
    return JsonRpcResponse(
        jsonrpc="2.0",
        result={
            "message": "Message reçu par Maestro (Mock Gateway)",
            "status": "routing_to_be_implemented_in_story_3"
        },
        id=request.id
    )


@app.post("/chat", response_model=ChatResponse, tags=["Legacy"], summary="Vieux point d'entrée REST Chat")
async def chat(
    request: ChatRequest,
    context: RequestContext = Depends(get_request_context)
):
    """
    Ancien endpoint de chat (Style REST).
    
    Effectue une classification d'intention et délègue à l'agent spécialisé.
    """
    session_id = request.session_id or str(uuid.uuid4())

    # Step 0: Privacy & Audit
    sanitized_message = sanitize_message(request.message)
    log_audit_trail(
        event_type="legacy_chat",
        user_id=context.user_id,
        family_id=context.family_id,
        extra={"session_id": session_id, "role": context.role}
    )

    # Step 1: Classify intent with semantic router
    logger.info(f"Processing message for {context.user_name}: '{sanitized_message}'")
    route = classify_intent(sanitized_message)
    logger.info(f"Routing decision: route='{route}' for message='{sanitized_message}'")
    
    # Step 1.5: RBAC Check
    check_agent_access(f"agent_{route}", context)

    response_text = ""
    agent_name = f"agent_{route}"

    try:
        if route != "unknown":
            # Step 2a: Call remote agent via A2A
            response_text = await call_remote_agent(
                route=route,
                message=sanitized_message,
                context_id=session_id,
            )
            agent_name = f"agent_{route}"
            
        if not response_text:
            response_text = "Je n'ai pas pu traiter votre demande. Veuillez réessayer."

        return ChatResponse(
            message=response_text,
            agent=agent_name,
            session_id=session_id,
            route=route,
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Agent error: {str(e)}")


@app.get("/routes", tags=["System"], summary="Liste des agents et URLS")
async def list_routes():
    """Liste les agents spécialisés disponibles et leurs descriptions."""
    return {
        "agents": agent_registry.list_agents(),
        "gateway": "maestro",
        "protocol": "A2A/JSON-RPC 2.0"
    }
