"""FastAPI application for Maestro - Family Agents entry point with A2A routing."""

import os
import uuid
import random
import asyncio
from contextlib import asynccontextmanager
from typing import Optional, Any
from sqlalchemy import select, delete
from fastapi import FastAPI, HTTPException, Request, Depends
from fastapi.middleware.cors import CORSMiddleware

from agent_maestro.router import classify_intent, get_all_scores, warmup, THRESHOLD_ROUTING, THRESHOLD_CLARIFICATION
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
from common.tracing import setup_tracing, instrument_app, instrument_client
from agent_maestro.session import InMemorySessionStore
from agent_maestro.app.db import session as maestro_db_session
from agent_maestro.app.db.models.context import Context

logger = setup_logger("maestro")

session_store = InMemorySessionStore()

async def push_context(session_id: str, agent: str, context_data: dict = None) -> None:
    """Push a suspended agent context to the DB stack."""
    if not session_id:
        return
    async with maestro_db_session.async_session_factory() as session:
        async with session.begin():
            db_context = Context(
                session_id=session_id,
                agent=agent,
                context_data=context_data or {}
            )
            session.add(db_context)
            logger.info(f"Context Stack | Pushed '{agent}' for session {session_id}")

async def pop_context(session_id: str) -> tuple[str, dict] | None:
    """Pop the most recent suspended context for the session."""
    if not session_id:
        return None
    async with maestro_db_session.async_session_factory() as session:
        async with session.begin():
            stmt = (
                select(Context)
                .where(Context.session_id == session_id)
                .order_by(Context.created_at.desc())
                .limit(1)
            )
            result = await session.execute(stmt)
            db_context = result.scalar_one_or_none()
            if db_context:
                agent = db_context.agent
                context_data = db_context.context_data
                await session.delete(db_context)
                logger.info(f"Context Stack | Popped '{agent}' for session {session_id}")
                return agent, context_data
    return None

async def clear_contexts(session_id: str) -> None:
    """Clear all suspended contexts for the session."""
    if not session_id:
        return
    async with maestro_db_session.async_session_factory() as session:
        async with session.begin():
            stmt = delete(Context).where(Context.session_id == session_id)
            await session.execute(stmt)
            logger.info(f"Context Stack | Cleared all contexts for session {session_id}")

async def prune_zombie_contexts(session_id: str) -> None:
    """Prune context stack if it exceeds age threshold (5 minutes)."""
    if not session_id:
        return
    from datetime import datetime, timezone, timedelta
    cutoff = datetime.now(timezone.utc) - timedelta(minutes=5)
    async with maestro_db_session.async_session_factory() as session:
        async with session.begin():
            stmt = delete(Context).where(
                (Context.session_id == session_id) & (Context.created_at < cutoff)
            )
            await session.execute(stmt)

def extract_text_from_result(result: Any) -> str:
    """Helper to extract text response from raw A2A JSON-RPC result."""
    if result:
        if isinstance(result, dict):
            if "parts" in result:
                for part in result["parts"]:
                    if isinstance(part, dict) and "text" in part:
                        return part["text"]
            if "message" in result:
                return result["message"]
            if "text" in result:
                return result["text"]
        if hasattr(result, "parts") and result.parts:
            for part in result.parts:
                if hasattr(part, "root") and hasattr(part.root, "text"):
                    return part.root.text
                if hasattr(part, "text"):
                    return part.text
    return str(result)


# Initialized with Lean A2A standards

# Maestro is now a pure A2A Gateway. 
# It routes all non-native requests to specialized agents via A2A.


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan - startup and shutdown events."""
    if config.OTEL_ENABLED:
        setup_tracing("maestro", config.OTEL_EXPORTER_OTLP_ENDPOINT)
        instrument_client()
        
    logger.info("🚀 Starting Tegmen Maestro...")
    logger.info(f"📦 Loading embedding model: {config.EMBEDDING_MODEL}")
    warmup()
    logger.info("✅ Semantic router ready!")
    logger.info("🔗 A2A Gateway Mode: Agents loaded from registry")
    for agent in agent_registry.list_agents():
        logger.info(f"   - {agent['name']}: {agent['url']}")
    
    # Initialize DB engine connection log
    logger.info("🗄️ Database engine initialized for Maestro.")
    
    yield
    
    # Clean up DB engine
    try:
        logger.info("🔌 Disposing Database engine for Maestro...")
        await maestro_db_session.engine.dispose()
    except Exception as e:
        logger.error(f"Failed to dispose Database engine for Maestro: {e}", exc_info=True)
    logger.info("👋 Shutting down Tegmen Maestro...")


app = FastAPI(
    title="Tegmen Maestro - Family Agents Gateway",
    description="Assistant familial intelligent avec agents spécialisés (A2A)",
    version="0.1.0",
    lifespan=lifespan,
    swagger_ui_parameters={"persistAuthorization": True},
)

if config.OTEL_ENABLED:
    instrument_app(app)

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


# Curated chitchat responses for Maestro's internal personality
CHITCHAT_RESPONSES = [
    "Bonjour ! Je suis Maestro, votre assistant familial. En quoi puis-je vous aider ?",
    "Salut ! Je suis là pour vous aider avec la cuisine, les devoirs ou vos voyages !",
    "Je suis Tegmen Maestro. Je peux vous connecter à nos agents spécialisés. 🎯",
    "Ah, ça, c'est moi ! Dites-moi ce dont vous avez besoin, je m'occupe du reste.",
    "La bonne humeur est ma spécialité ! Quel est votre besoin du moment ?",
]

UNKNOWN_RESPONSE = (
    "Je n'ai pas compris votre demande. Je peux vous aider avec : "
    "🍳 la cuisine (agent Gourmet), 📚 les devoirs (agent Acadomie), "
    "🌍 les voyages (agent Explorer)."
)

# Friendly fallback responses for when specialized agents fail
FALLBACK_RESPONSES = [
    "Désolé, l'agent spécialisé semble faire une petite pause... Je ne peux pas lui parler pour le moment. 😴",
    "Oups ! J'ai un petit souci technique pour joindre mon collègue. On réessaie dans un instant ? 🛠️",
    "Mince, la connexion avec l'agent spécialisé a été coupée. Je suis navré de ce contretemps ! 🔌",
    "Désolé, je n'arrive pas à obtenir de réponse de l'agent pour le moment. Je reste à votre disposition pour autre chose ! ✨",
]

# Template for ambiguous intents
CLARIFICATION_TEMPLATE = (
    "Je ne suis pas sûr de bien comprendre... 🧐\n"
    "Voulez-vous parler à l'agent **{agent_display}** ?\n\n"
    "(Si oui, soyez un peu plus précis dans votre demande !)"
)

# Escape commands to reset session
ESCAPE_COMMANDS = {
    "stop", "annule", "annuler", "reset", "quitter", "exit", 
    "arrete", "arrête", "arreter", "stoppe", "fin", "terminé", 
    "cancel", "c'est bon", "laisse tomber", "non merci"
}
ESCAPE_RESPONSE = "Compris, nous reprenons à zéro. Comment puis-je vous aider ?"

from common.exceptions import A2ARPCError

async def is_escape_command(raw_message: str, session_id: Optional[str]) -> bool:
    if not raw_message:
        return False
    clean_msg = raw_message.strip().lower()
    is_escape = (
        clean_msg in ESCAPE_COMMANDS
        or "laisse tomber ce sujet" in clean_msg
        or "laisse tomber" in clean_msg
        or "abandonne" in clean_msg
    )
    if is_escape:
        if session_id:
            await session_store.delete(session_id)
            await clear_contexts(session_id)
        return True
    return False

def detect_explicit_agent(message: str) -> str | None:
    """Detect if the user is explicitly naming/asking for a specific agent."""
    if not message:
        return None
    msg_lower = message.lower()
    agents = ["gourmet", "acadomie", "explorer"]
    triggers = ["demande à", "demande a", "parle à", "parle a", "invoque", "appelle", "lance", "agent"]
    
    for agent in agents:
        if msg_lower.startswith(f"{agent}:") or msg_lower.startswith(f"agent {agent}:"):
            return agent
        if msg_lower.startswith(f"{agent},") or msg_lower.startswith(f"{agent} "):
            return agent
        for trigger in triggers:
            if f"{trigger} {agent}" in msg_lower or f"{agent} {trigger}" in msg_lower:
                return agent
    return None

def detect_correction(message: str) -> str | None:
    """Detect if the user is manually correcting a routing error a posteriori."""
    if not message:
        return None
    msg_lower = message.lower()
    agents = ["gourmet", "acadomie", "explorer"]
    correction_keywords = ["non", "pas", "trompé", "trompe", "erreur", "c'était pour", "c'etait pour", "je voulais", "plutôt", "plutot"]
    
    has_correction = any(kw in msg_lower for kw in correction_keywords)
    if has_correction:
        for agent in agents:
            if agent in msg_lower:
                return agent
    return None

def is_pure_correction(message: str) -> bool:
    """Detect if the message is only a routing correction with no other query context."""
    if not message:
        return False
    import string
    msg = message.lower().strip()
    msg_clean = msg.translate(str.maketrans("", "", string.punctuation))
    words = msg_clean.split()
    if len(words) <= 5:
        keywords = {
            "non", "pas", "trompé", "trompe", "erreur", "c'était", "c'etait", "cétait", "cetait",
            "pour", "je", "voulais", "plutôt", "plutot", "gourmet", "acadomie", 
            "explorer", "agent"
        }
        if all(w in keywords for w in words):
            return True
    return False

async def generate_synthesis(query: str, agent_responses: dict[str, str]) -> str:
    """Synthesize responses from multiple agents using the LLM."""
    if os.getenv("USE_MOCK_LLM", "false").lower() == "true":
        responses_summary = ", ".join([f"{agent}: {resp}" for agent, resp in agent_responses.items()])
        return f"[Synthèse] Réponses croisées de la famille pour '{query}': {responses_summary}"
        
    import litellm
    system_prompt = (
        "Tu es Tegmen Maestro, l'assistant et le chef d'orchestre de la famille. "
        "Tu as consulté plusieurs agents spécialistes pour répondre à la question de l'utilisateur. "
        "Synthétise leurs réponses de manière cohérente, chaleureuse et concise, en éliminant les répétitions et en croisant les informations utiles."
    )
    
    user_prompt = f"Question de l'utilisateur : {query}\n\nRéponses des experts consultés :\n"
    for agent, response in agent_responses.items():
        user_prompt += f"- {agent.capitalize()} : {response}\n"
    
    user_prompt += "\nGénère la synthèse finale."
    
    try:
        response = await asyncio.wait_for(
            litellm.acompletion(
                model=config.LLM_DEFAULT_MODEL,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.7,
            ),
            timeout=10.0
        )
        return response.choices[0].message.content
    except Exception as e:
        logger.error(f"Error generating synthesis: {e}")
        fallback_msg = "Voici les avis de la famille :\n"
        for agent, resp in agent_responses.items():
            fallback_msg += f"- {agent.capitalize()} : {resp}\n"
        return fallback_msg

async def call_single_agent(route: str, message: str, context_id: str, context: RequestContext) -> tuple[str, str | None]:
    """Call a single remote agent with a strict timeout and catch errors."""
    try:
        resp = await call_remote_agent(
            route=route,
            message=message,
            context_id=context_id,
            timeout=10.0,
            context=context
        )
        return route, resp
    except Exception as e:
        logger.warning(f"Party Mode | Agent '{route}' failed or timed out: {e}")
        return route, None


@app.get("/dev/token/{user_id}", tags=["Development"])
async def get_dev_token(user_id: str):
    """
    Utility endpoint to generate a JWT token for development and testing.
    DO NOT USE IN PRODUCTION.
    """
    import jwt
    from datetime import datetime, timedelta, timezone
    from common.users import MOCK_PROFILES
    
    profile = MOCK_PROFILES.get(user_id)
    if not profile:
        raise HTTPException(status_code=404, detail="Utilisateur introuvable dans les mock profiles")
        
    payload = {
        "user_id": profile.user_id,
        "family_id": profile.family_id,
        "role": profile.role,
        "exp": datetime.now(timezone.utc) + timedelta(days=1)
    }
    
    token = jwt.encode(payload, config.JWT_SECRET, algorithm=config.JWT_ALGORITHM)
    return {"access_token": token, "token_type": "bearer"}


@app.exception_handler(A2ARPCError)
async def a2a_exception_handler(request: Request, exc: A2ARPCError):
    """
    Global handler for A2A errors to provide a graceful conversational fallback.
    Returns a 200 OK with a friendly message in the result.
    """
    logger.error(f"Graceful Interception | A2A Error {exc.code}: {exc.message}")
    
    # We try to extract the original RPC ID if possible from the request
    rpc_id = None
    try:
        body = await request.json()
        rpc_id = body.get("id")
    except:
        pass

    return JsonRpcResponse(
        jsonrpc="2.0",
        result={
            "message": random.choice(FALLBACK_RESPONSES),
            "agent": "maestro",
            "route": "error_fallback",
            "technical_error": f"Error {exc.code}" # Hidden but available in JSON if needed
        },
        id=rpc_id
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
    
    raw_message = request.params.get("message", "") if request.params else ""
    session_id = None
    if request.params and "session_id" in request.params:
        s_id = request.params["session_id"]
        if s_id and isinstance(s_id, str) and s_id.strip():
            session_id = s_id.strip()

    # Escape commands check on raw message
    if await is_escape_command(raw_message, session_id):
        logger.info("Escape command intercepted, session reset.")
        return JsonRpcResponse(
            jsonrpc="2.0",
            result={"message": ESCAPE_RESPONSE, "agent": "maestro", "route": "chitchat"},
            id=request.id
        )

    # Apply PII filter
    message = sanitize_message(raw_message) if raw_message else ""
        
    # Audit Trail
    log_audit_trail(
        event_type="a2a_routing",
        user_id=context.user_id,
        family_id=context.family_id,
        extra={"method": request.method, "rpc_id": str(request.id), "role": context.role}
    )

    active_agent = await session_store.get(session_id) if session_id else None

    if session_id:
        await prune_zombie_contexts(session_id)
        # Update digression message count
        async with maestro_db_session.async_session_factory() as session:
            async with session.begin():
                stmt = select(Context).where(Context.session_id == session_id).order_by(Context.created_at.desc()).limit(1)
                res = await session.execute(stmt)
                db_ctx = res.scalar_one_or_none()
                if db_ctx:
                    data = dict(db_ctx.context_data)
                    count = data.get("digression_messages", 0) + 1
                    if count >= 3:
                        logger.info(f"Context Stack | Garbage collecting context because digression exceeded 3 messages.")
                        await session.delete(db_ctx)
                    else:
                        data["digression_messages"] = count
                        db_ctx.context_data = data

    is_party = False
    target_routes = []

    # Check for manual routing correction
    corrected_agent = detect_correction(message)
    if corrected_agent:
        logger.info(f"Manual routing correction detected: target={corrected_agent}")
        if is_pure_correction(message):
            if session_id:
                await session_store.set(session_id, f"agent_{corrected_agent}")
            return JsonRpcResponse(
                jsonrpc="2.0",
                result={
                    "message": f"D'accord, je redirige notre conversation vers l'agent {corrected_agent.capitalize()}. Que souhaitez-vous lui demander ?",
                    "agent": "maestro",
                    "route": corrected_agent
                },
                id=request.id
            )
        else:
            route = corrected_agent
            score = 1.0
            if session_id:
                await session_store.set(session_id, f"agent_{route}")
    else:
        # Check for explicit agent invocation
        explicit_agent = detect_explicit_agent(message)
        if explicit_agent:
            logger.info(f"Explicit agent routing detected: target={explicit_agent}")
            route = explicit_agent
            score = 1.0
        else:
            # Classify intent
            route, score = classify_intent(message, active_agent) if message else ("unknown", 0.0)

    logger.info(f"🎯 Intent classified: route='{route}', score={score:.4f}")

    if route == "party":
        party_keywords = ["party mode", "tous les agents", "toute la famille", "consulte tout le monde", "demande à tout le monde", "demande a tout le monde", "consulter la famille"]
        if any(kw in message.lower() for kw in party_keywords):
            target_routes = [agent["name"] for agent in agent_registry.list_agents() if agent["name"] != "maestro"]
        else:
            scores = get_all_scores(message)
            specialized_routes = [r for r, s in scores.items() if r != "chitchat" and s >= THRESHOLD_CLARIFICATION]
            specialized_routes.sort(key=lambda r: scores[r], reverse=True)
            target_routes = specialized_routes

    # RBAC Check
    if route != "party":
        check_agent_access(f"agent_{route}", context)
    else:
        # Filter target routes by RBAC before calling
        allowed_routes = []
        for r in target_routes:
            try:
                check_agent_access(f"agent_{r}", context)
                allowed_routes.append(r)
            except HTTPException:
                logger.warning(f"Party Mode | Filtered out agent_{r} due to RBAC restrictions for user {context.user_id}")
        target_routes = allowed_routes

    # Check for debug mode (admin only)
    is_admin = context.role == "parent"
    debug_requested = request.params.get("debug", False) if request.params else False
    include_debug = is_admin and debug_requested

    # Dispatch logic based on confidence thresholds
    debug_info = None
    if include_debug:
        debug_info = {
            "routing": {
                "route": route,
                "score": score,
                "thresholds": {
                    "routing": THRESHOLD_ROUTING,
                    "clarification": THRESHOLD_CLARIFICATION
                },
                "all_scores": get_all_scores(message)
            },
            "context": {
                "user_role": context.role,
                "family_id": context.family_id
            }
        }
        # Add trace ID if OTEL is enabled
        if config.OTEL_ENABLED:
            from opentelemetry import trace
            span = trace.get_current_span()
            if span:
                debug_info["trace_id"] = format(span.get_span_context().trace_id, '032x')

    try:
        if route == "party":
            # Invoke target agents in parallel
            tasks = [call_single_agent(r, message, session_id or str(request.id), context) for r in target_routes]
            results = await asyncio.gather(*tasks)
            successful_responses = {r: resp for r, resp in results if resp is not None}
            if not successful_responses:
                response_text = random.choice(FALLBACK_RESPONSES)
            else:
                response_text = await generate_synthesis(message, successful_responses)
            agent_name = "maestro"
        elif route == "chitchat" and score >= THRESHOLD_ROUTING:
            response_text = random.choice(CHITCHAT_RESPONSES)
            agent_name = "maestro"
        elif score >= THRESHOLD_ROUTING:
            # High confidence -> Direct dispatch
            raw_response = await call_remote_agent(
                route=route,
                message=message,
                context_id=session_id or str(request.id),
                return_raw=True,
            )
            if isinstance(raw_response, dict) and raw_response.get("status") == "yield":
                # active agent yielded!
                # 1. Push active agent to stack with digression_messages=0
                if session_id and active_agent:
                    await push_context(session_id, active_agent, {"digression_messages": 0})
                
                # 2. Re-classify intent without active agent to find the new route (digression)
                route, score = classify_intent(message, active_agent=None)
                logger.info(f"Yield transition | Re-routing to route={route}, score={score:.4f}")
                
                # 3. Call the digression agent
                digression_response = await call_remote_agent(
                    route=route,
                    message=message,
                    context_id=session_id or str(request.id),
                    return_raw=True,
                )
                if isinstance(digression_response, dict) and digression_response.get("status") == "yield":
                    # Double yield — both agents can't handle this. Pop and restore.
                    response_text = digression_response.get("message", "Je ne peux pas répondre actuellement.")
                    agent_name = "maestro"
                    if session_id:
                        restored = await pop_context(session_id)
                        if restored:
                            restored_agent, _ = restored
                            await session_store.set(session_id, restored_agent)
                else:
                    response_text = extract_text_from_result(digression_response)
                    agent_name = f"agent_{route}"
                    # Switch active agent to digression agent; context stays in stack
                    if session_id:
                        await session_store.set(session_id, agent_name)
            else:
                response_text = extract_text_from_result(raw_response)
                agent_name = f"agent_{route}"
                if session_id:
                    await session_store.set(session_id, agent_name)
        elif score >= THRESHOLD_CLARIFICATION:
            # Medium confidence -> Clarification
            agent_display = route.capitalize()
            response_text = CLARIFICATION_TEMPLATE.format(agent_display=agent_display)
            agent_name = "maestro"
        else:
            # Low confidence or unknown -> Unknown fallback
            response_text = UNKNOWN_RESPONSE
            agent_name = "maestro"
            route = "unknown" # Normalize for response

        result_payload = {"message": response_text, "agent": agent_name, "route": route}
        if debug_info:
            result_payload["_debug"] = debug_info

        return JsonRpcResponse(
            jsonrpc="2.0",
            result=result_payload,
            id=request.id
        )

    except A2ARPCError as e:
        # Let the global exception handler handle it if it bubbles up, 
        # or handle it here for direct JSON-RPC compliance
        logger.warning(f"A2A Failure for route '{route}': {e}")
        result_payload = {
            "message": random.choice(FALLBACK_RESPONSES),
            "agent": "maestro",
            "route": route,
            "error_code": e.code
        }
        if debug_info:
            result_payload["_debug"] = debug_info

        return JsonRpcResponse(
            jsonrpc="2.0",
            result=result_payload,
            id=request.id
        )
    except HTTPException:
        # Re-raise HTTPExceptions (401, 403, etc.) so FastAPI can handle them
        raise
    except Exception as e:
        logger.error(f"Unexpected dispatch error for route '{route}': {e}")
        result_payload = {
            "message": random.choice(FALLBACK_RESPONSES), 
            "agent": "maestro", 
            "route": route
        }
        if debug_info:
            result_payload["_debug"] = debug_info

        return JsonRpcResponse(
            jsonrpc="2.0",
            result=result_payload,
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
    session_id = session_id.strip() if session_id and session_id.strip() else None

    if await is_escape_command(request.message, session_id):
        logger.info("Escape command intercepted in legacy chat, session reset.")
        return ChatResponse(
            message=ESCAPE_RESPONSE,
            agent="maestro",
            session_id=session_id or "",
            route="chitchat"
        )

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
    active_agent = await session_store.get(session_id) if session_id else None

    if session_id:
        await prune_zombie_contexts(session_id)
        # Update digression message count
        async with maestro_db_session.async_session_factory() as session:
            async with session.begin():
                stmt = select(Context).where(Context.session_id == session_id).order_by(Context.created_at.desc()).limit(1)
                res = await session.execute(stmt)
                db_ctx = res.scalar_one_or_none()
                if db_ctx:
                    data = dict(db_ctx.context_data)
                    count = data.get("digression_messages", 0) + 1
                    if count >= 3:
                        logger.info(f"Context Stack | Garbage collecting context because digression exceeded 3 messages.")
                        await session.delete(db_ctx)
                    else:
                        data["digression_messages"] = count
                        db_ctx.context_data = data

    is_party = False
    target_routes = []

    corrected_agent = detect_correction(sanitized_message)
    if corrected_agent:
        logger.info(f"Manual routing correction detected (legacy): target={corrected_agent}")
        if is_pure_correction(sanitized_message):
            if session_id:
                await session_store.set(session_id, f"agent_{corrected_agent}")
            return ChatResponse(
                message=f"D'accord, je redirige notre conversation vers l'agent {corrected_agent.capitalize()}. Que souhaitez-vous lui demander ?",
                agent="maestro",
                session_id=session_id or "",
                route=corrected_agent,
            )
        else:
            route = corrected_agent
            score = 1.0
            if session_id:
                await session_store.set(session_id, f"agent_{route}")
    else:
        explicit_agent = detect_explicit_agent(sanitized_message)
        if explicit_agent:
            logger.info(f"Explicit agent routing detected (legacy): target={explicit_agent}")
            route = explicit_agent
            score = 1.0
        else:
            route, score = classify_intent(sanitized_message, active_agent)
            
    logger.info(f"Routing decision: route='{route}', score={score:.4f}")

    if route == "party":
        party_keywords = ["party mode", "tous les agents", "toute la famille", "consulte tout le monde", "demande à tout le monde", "demande a tout le monde", "consulter la famille"]
        if any(kw in sanitized_message.lower() for kw in party_keywords):
            target_routes = [agent["name"] for agent in agent_registry.list_agents() if agent["name"] != "maestro"]
        else:
            scores = get_all_scores(sanitized_message)
            specialized_routes = [r for r, s in scores.items() if r != "chitchat" and s >= THRESHOLD_CLARIFICATION]
            specialized_routes.sort(key=lambda r: scores[r], reverse=True)
            target_routes = specialized_routes
    
    # Step 1.5: RBAC Check
    if route != "party":
        check_agent_access(f"agent_{route}", context)
    else:
        # Filter target routes by RBAC before calling
        allowed_routes = []
        for r in target_routes:
            try:
                check_agent_access(f"agent_{r}", context)
                allowed_routes.append(r)
            except HTTPException:
                logger.warning(f"Party Mode (legacy) | Filtered out agent_{r} due to RBAC restrictions")
        target_routes = allowed_routes

    try:
        if route == "party":
            # Invoke target agents in parallel
            tasks = [call_single_agent(r, sanitized_message, session_id or str(uuid.uuid4()), context) for r in target_routes]
            results = await asyncio.gather(*tasks)
            successful_responses = {r: resp for r, resp in results if resp is not None}
            if not successful_responses:
                response_text = random.choice(FALLBACK_RESPONSES)
            else:
                response_text = await generate_synthesis(sanitized_message, successful_responses)
            agent_name = "maestro"
        elif route == "chitchat" and score >= THRESHOLD_ROUTING:
            response_text = random.choice(CHITCHAT_RESPONSES)
            agent_name = "maestro"
        elif score >= THRESHOLD_ROUTING:
            # Step 2: Call remote specialized agent via A2A
            raw_response = await call_remote_agent(
                route=route,
                message=sanitized_message,
                context_id=session_id,
                return_raw=True,
            )
            if isinstance(raw_response, dict) and raw_response.get("status") == "yield":
                # active agent yielded!
                # 1. Push active agent to stack with digression_messages=0
                if session_id and active_agent:
                    await push_context(session_id, active_agent, {"digression_messages": 0})
                
                # 2. Re-classify intent without active agent to find the new route (digression)
                route, score = classify_intent(sanitized_message, active_agent=None)
                logger.info(f"Yield transition (legacy) | Re-routing to route={route}, score={score:.4f}")
                
                # 3. Call the digression agent
                digression_response = await call_remote_agent(
                    route=route,
                    message=sanitized_message,
                    context_id=session_id,
                    return_raw=True,
                )
                if isinstance(digression_response, dict) and digression_response.get("status") == "yield":
                    # Double yield — both agents can't handle this. Pop and restore.
                    response_text = digression_response.get("message", "Je ne peux pas répondre actuellement.")
                    agent_name = "maestro"
                    if session_id:
                        restored = await pop_context(session_id)
                        if restored:
                            restored_agent, _ = restored
                            await session_store.set(session_id, restored_agent)
                else:
                    response_text = extract_text_from_result(digression_response)
                    agent_name = f"agent_{route}"
                    # Switch active agent to digression agent; context stays in stack
                    if session_id:
                        await session_store.set(session_id, agent_name)
            else:
                response_text = extract_text_from_result(raw_response)
                agent_name = f"agent_{route}"
                if session_id:
                    await session_store.set(session_id, agent_name)
        elif score >= THRESHOLD_CLARIFICATION:
            # Clarification
            agent_display = route.capitalize()
            response_text = CLARIFICATION_TEMPLATE.format(agent_display=agent_display)
            agent_name = "maestro"
        else:
            # Unknown
            response_text = UNKNOWN_RESPONSE
            agent_name = "maestro"
            route = "unknown"

        return ChatResponse(
            message=response_text,
            agent=agent_name,
            session_id=session_id,
            route=route,
        )

    except A2ARPCError as e:
        logger.warning(f"Legacy Chat A2A Failure: {e}")
        return ChatResponse(
            message=random.choice(FALLBACK_RESPONSES),
            agent="maestro",
            session_id=session_id,
            route=route,
        )
    except Exception as e:
        logger.error(f"Legacy Chat unexpected error: {e}")
        return ChatResponse(
            message="Oups, j'ai un petit souci technique. 🙊",
            agent="maestro",
            session_id=session_id,
            route=route,
        )


@app.get("/routes", tags=["System"], summary="Liste des agents et URLS")
async def list_routes():
    """Liste les agents spécialisés disponibles et leurs descriptions."""
    return {
        "agents": agent_registry.list_agents(),
        "gateway": "maestro",
        "protocol": "A2A/JSON-RPC 2.0"
    }
