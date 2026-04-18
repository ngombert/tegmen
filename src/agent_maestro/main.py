"""FastAPI application for Maestro - Family Agents entry point with A2A routing."""

import os
import uuid
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware

from agent_maestro.router import classify_intent, warmup
from agent_maestro.schemas import ChatRequest, ChatResponse, HealthResponse
from common.schemas import JsonRpcRequest, JsonRpcResponse, JsonRpcError
from common.config import config
from common.a2a_client import call_remote_agent, AGENT_URLS
from common.logger import setup_logger

logger = setup_logger("maestro")


# Initialized with Lean A2A standards

# Check if running in microservices mode (agents are remote)
MICROSERVICES_MODE = os.getenv("MICROSERVICES_MODE", "false").lower() == "true"


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan - startup and shutdown events."""
    logger.info("🚀 Starting Tegmen Maestro...")
    logger.info(f"📦 Loading embedding model: {config.EMBEDDING_MODEL}")
    warmup()
    logger.info("✅ Semantic router ready!")
    if MICROSERVICES_MODE:
        logger.info("🔗 Microservices mode: Agents will be called via A2A")
        for name, url in AGENT_URLS.items():
            logger.info(f"   - {name}: {url}")
    else:
        logger.info("📦 Monolith mode: Agents loaded locally")
    yield
    logger.info("👋 Shutting down Tegmen Maestro...")


app = FastAPI(
    title="Tegmen Maestro - Family Agents Gateway",
    description="Assistant familial intelligent avec agents spécialisés (A2A)",
    version="0.1.0",
    lifespan=lifespan,
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
async def route_request(request: JsonRpcRequest):
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
async def chat(request: ChatRequest):
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
        if MICROSERVICES_MODE and route != "unknown":
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
    routes_info = [
        {"name": "gourmet", "description": "Cuisine, recettes, menus"},
        {"name": "acadomie", "description": "École, devoirs, calendrier scolaire"},
        {"name": "explorer", "description": "Voyages, sorties, activités"},
        {"name": "unknown", "description": "Questions générales (fallback)"},
    ]

    if MICROSERVICES_MODE:
        for route in routes_info:
            if route["name"] in AGENT_URLS:
                route["url"] = AGENT_URLS[route["name"]]

    return {"routes": routes_info, "microservices_mode": MICROSERVICES_MODE}
