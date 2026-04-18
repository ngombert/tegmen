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
    identity: dict = Depends(get_current_identity)
):
    """
    Endpoint principal du Gateway Maestro.
    
    Reçoit une requête standard JSON-RPC 2.0 et la dirige vers l'agent spécialisé 
    compétent après une classification sémantique de l'intention utilisateur.
    """
    logger.info(f"📥 Received A2A routing request: method='{request.method}', id='{request.id}'")
    
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
    identity: dict = Depends(get_current_identity)
):
    """
    Ancien endpoint de chat (Style REST).
    
    *Bientôt déprécié au profit de /api/v1/routing.*
    """
    session_id = request.session_id or str(uuid.uuid4())

    # Step 1: Classify intent with semantic router
    logger.info(f"Processing message: '{request.message}'")
    route = classify_intent(request.message)
    logger.info(f"Routing decision: route='{route}' for message='{request.message}'")

    response_text = ""
    agent_name = f"agent_{route}"

    try:
        if route != "unknown":
            # Step 2a: Call remote agent via A2A
            response_text = await call_remote_agent(
                route=route,
                message=request.message,
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
