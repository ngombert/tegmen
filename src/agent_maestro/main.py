"""FastAPI application for Maestro - Family Agents entry point with A2A routing."""

import os
import uuid
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

from src.agent_maestro.router import classify_intent, warmup
from src.agent_maestro.schemas import ChatRequest, ChatResponse, HealthResponse
from src.common.config import config
from src.common.a2a_client import call_remote_agent, AGENT_URLS


# Session service for fallback Maestro agent
session_service = InMemorySessionService()

# Check if running in microservices mode (agents are remote)
MICROSERVICES_MODE = os.getenv("MICROSERVICES_MODE", "false").lower() == "true"


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan - startup and shutdown events."""
    print("🚀 Starting Tegmen Maestro...")
    print(f"📦 Loading embedding model: {config.EMBEDDING_MODEL}")
    warmup()
    print("✅ Semantic router ready!")
    if MICROSERVICES_MODE:
        print("🔗 Microservices mode: Agents will be called via A2A")
        for name, url in AGENT_URLS.items():
            print(f"   - {name}: {url}")
    else:
        print("📦 Monolith mode: Agents loaded locally")
    yield
    print("👋 Shutting down Tegmen Maestro...")


app = FastAPI(
    title="Tegmen Maestro - Family Agents Gateway",
    description="Assistant familial intelligent avec agents spécialisés (A2A)",
    version="0.1.0",
    lifespan=lifespan,
)


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    return HealthResponse()


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Main chat endpoint.
    
    1. Classify intent using SemanticRouter (local, fast)
    2. Route to appropriate agent (via A2A if microservices mode)
    3. Return agent response
    """
    session_id = request.session_id or str(uuid.uuid4())
    
    # Step 1: Classify intent with semantic router
    route = classify_intent(request.message)
    
    try:
        if MICROSERVICES_MODE and route != "unknown":
            # Step 2a: Call remote agent via A2A
            response_text = await call_remote_agent(
                route=route,
                message=request.message,
                context_id=session_id,
            )
            agent_name = f"agent_{route}"
        else:
            # Step 2b: Use local fallback (Maestro or local agents)
            from src.agent_maestro.agents import get_agent
            
            agent = get_agent(route)
            agent_name = agent.name
            user_id = request.user_id or "default_user"
            
            session = await session_service.get_session(
                app_name=config.APP_NAME,
                user_id=user_id,
                session_id=session_id,
            )
            if session is None:
                session = await session_service.create_session(
                    app_name=config.APP_NAME,
                    user_id=user_id,
                    session_id=session_id,
                )
            
            runner = Runner(
                agent=agent,
                app_name=config.APP_NAME,
                session_service=session_service,
            )
            
            user_content = types.Content(
                role="user",
                parts=[types.Part(text=request.message)]
            )
            
            response_text = ""
            async for event in runner.run_async(
                user_id=user_id,
                session_id=session_id,
                new_message=user_content,
            ):
                if event.is_final_response() and event.content and event.content.parts:
                    response_text = event.content.parts[0].text
        
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


@app.get("/routes")
async def list_routes():
    """List available routes and their descriptions."""
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
