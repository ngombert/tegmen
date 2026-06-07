import pytest
import jwt
import os
import asyncio
from unittest.mock import patch, AsyncMock, MagicMock
from httpx import AsyncClient, ASGITransport

from agent_maestro.main import app, push_context, pop_context, clear_contexts
from agent_gourmet.app.api.routers.a2a import handle_message_send as gourmet_message_send
from agent_acadomie.app.api.routers.a2a import handle_message_send as acadomie_message_send
from common.config import config

def get_auth_headers(role="parent"):
    payload = {
        "family_id": "test-family", 
        "user_id": "user-parent-1",
        "role": role
    }
    token = jwt.encode(
        payload,
        config.JWT_SECRET,
        algorithm=config.JWT_ALGORITHM
    )
    return {"Authorization": f"Bearer {token}"}

@pytest.fixture(autouse=True)
async def recreate_maestro_db_engine():
    """Recreate the engine and session factory to bind to the current event loop of this test."""
    from common.database import create_session_factory
    import agent_maestro.app.db.session as maestro_db_session
    from sqlalchemy.ext.asyncio import create_async_engine
    from sqlalchemy.pool import NullPool

    # Dispose the old one
    await maestro_db_session.engine.dispose()

    # Create a new engine with NullPool for the current test loop
    new_engine = create_async_engine(
        maestro_db_session.DATABASE_URL,
        poolclass=NullPool
    )
    maestro_db_session.engine = new_engine
    maestro_db_session.async_session_factory = create_session_factory(new_engine)

    yield

    # Clean up
    await new_engine.dispose()

@pytest.mark.asyncio
async def test_specialist_yield_detection():
    """Test that specialists detect out-of-domain questions and yield."""
    with patch.dict(os.environ, {"USE_MOCK_LLM": "true"}):
        gourmet_params = {
            "message": {
                "parts": [{"text": "Je voudrais de l'aide pour mes devoirs de maths scolaires."}]
            },
            "contextId": "ctx-123"
        }
        res_gourmet = await gourmet_message_send(gourmet_params)
        assert res_gourmet.get("status") == "yield"
        assert "Gourmet" in res_gourmet["message"]

        # Test Acadomie Yield
        acadomie_params = {
            "message": {
                "parts": [{"text": "Quelle est la recette de la tarte aux pommes ?"}]
            },
            "contextId": "ctx-456"
        }
        res_acadomie = await acadomie_message_send(acadomie_params)
        assert res_acadomie.get("status") == "yield"
        assert "Acadomie" in res_acadomie["message"]

@pytest.mark.asyncio
@patch("agent_maestro.main.call_remote_agent")
async def test_maestro_suspend_and_resume(mock_call):
    """Test that when Gourmet yields, context is pushed and active agent switches to digression."""
    # Setup mock responses
    mock_call.side_effect = [
        # First call: Gourmet yields on math question
        {
            "status": "yield",
            "message": "Je suis l'agent Gourmet et je ne peux pas répondre aux devoirs.",
            "context_stack": []
        },
        # Second call: Acadomie answers the math homework (digression)
        {
            "jsonrpc": "2.0",
            "result": {
                "messageId": "msg-123",
                "role": "agent",
                "parts": [{"text": "Le résultat de 2+2 est 4."}]
            },
            "id": "1"
        }
    ]

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        session_id = "test-session-suspend-resume"
        headers = get_auth_headers()

        # Step 1: Force active agent to Gourmet in session store
        from agent_maestro.main import session_store
        await session_store.set(session_id, "agent_gourmet")

        # Step 2: Clear contexts table
        await clear_contexts(session_id)

        # Step 3: Send math question -> triggers Gourmet yield, re-route to digression agent
        req_payload = {
            "jsonrpc": "2.0",
            "method": "route_message",
            "params": {
                "message": "Aide-moi pour mes devoirs de maths.",
                "session_id": session_id
            },
            "id": "1"
        }
        response = await ac.post("/api/v1/routing", json=req_payload, headers=headers)
        assert response.status_code == 200
        res_json = response.json()
        assert "result" in res_json
        # The digression agent answered
        assert "Le résultat de 2+2 est 4." in res_json["result"]["message"]

        # Step 4: Verify that the active agent has switched to the digression agent (not Gourmet)
        active = await session_store.get(session_id)
        assert active != "agent_gourmet"  # Switched away from Gourmet

        # Step 5: Verify that the Gourmet context is still in the stack (not popped immediately)
        from agent_maestro.app.db.session import async_session_factory
        from agent_maestro.app.db.models.context import Context
        from sqlalchemy import select
        async with async_session_factory() as session:
            stmt = select(Context).where(Context.session_id == session_id)
            res = await session.execute(stmt)
            ctx_list = res.scalars().all()
            assert len(ctx_list) == 1
            assert ctx_list[0].agent == "agent_gourmet"
            assert ctx_list[0].context_data.get("digression_messages") == 0

@pytest.mark.asyncio
async def test_escape_commands_clears_stack():
    """Test that escape commands clear the suspended context stack."""
    session_id = "test-session-escape"
    # Push dummy contexts
    await push_context(session_id, "agent_acadomie")
    
    # Verify it exists in db
    from sqlalchemy import select
    from agent_maestro.app.db.session import async_session_factory
    from agent_maestro.app.db.models.context import Context
    
    async with async_session_factory() as session:
        stmt = select(Context).where(Context.session_id == session_id)
        res = await session.execute(stmt)
        assert len(res.scalars().all()) > 0

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        headers = get_auth_headers()
        req_payload = {
            "jsonrpc": "2.0",
            "method": "route_message",
            "params": {
                "message": "Laisse tomber ce sujet",
                "session_id": session_id
            },
            "id": "2"
        }
        response = await ac.post("/api/v1/routing", json=req_payload, headers=headers)
        assert response.status_code == 200
        
        # Verify stack is cleared
        async with async_session_factory() as session:
            stmt = select(Context).where(Context.session_id == session_id)
            res = await session.execute(stmt)
            assert len(res.scalars().all()) == 0

@pytest.mark.asyncio
@patch("agent_maestro.main.call_remote_agent")
async def test_digression_limit_garbage_collection(mock_call):
    """Test that after 3 digression messages, the suspended context is garbage collected."""
    # We need enough mock responses for: yield+digression (2) + 3 follow-up messages
    def make_normal_response(text="Réponse normale."):
        return {
            "jsonrpc": "2.0",
            "result": {"parts": [{"text": text}]},
            "id": "1"
        }

    mock_call.side_effect = [
        # First call: Gourmet yields
        {
            "status": "yield",
            "message": "Je suis l'agent Gourmet.",
            "context_stack": []
        },
        # Digression call — Acadomie answers
        make_normal_response("Réponse de Acadomie."),
        # 3 follow-up messages (each routed to whatever agent is active)
        make_normal_response("Réponse 1"),
        make_normal_response("Réponse 2"),
        make_normal_response("Réponse 3"),
    ]

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        session_id = "test-session-gc"
        headers = get_auth_headers()
        from agent_maestro.main import session_store
        await session_store.set(session_id, "agent_gourmet")
        await clear_contexts(session_id)

        # Trigger yield and suspend — context pushed with digression_messages=0
        req_payload = {
            "jsonrpc": "2.0",
            "method": "route_message",
            "params": {
                "message": "De maths.",
                "session_id": session_id
            },
            "id": "1"
        }
        await ac.post("/api/v1/routing", json=req_payload, headers=headers)
        
        # Now context is in db. Verify context has digression_messages = 0
        from agent_maestro.app.db.models.context import Context
        from agent_maestro.app.db.session import async_session_factory
        from sqlalchemy import select
        async with async_session_factory() as session:
            stmt = select(Context).where(Context.session_id == session_id)
            res = await session.execute(stmt)
            ctx_list = res.scalars().all()
            assert len(ctx_list) == 1
            assert ctx_list[0].context_data.get("digression_messages") == 0

        # Send 1st follow-up message → digression_messages incremented to 1
        req_payload["params"]["message"] = "Encore un truc"
        await ac.post("/api/v1/routing", json=req_payload, headers=headers)
        async with async_session_factory() as session:
            stmt = select(Context).where(Context.session_id == session_id)
            res = await session.execute(stmt)
            ctx_list = res.scalars().all()
            assert len(ctx_list) == 1
            assert ctx_list[0].context_data.get("digression_messages") == 1

        # Send 2nd follow-up message → digression_messages incremented to 2
        await ac.post("/api/v1/routing", json=req_payload, headers=headers)
        async with async_session_factory() as session:
            stmt = select(Context).where(Context.session_id == session_id)
            res = await session.execute(stmt)
            ctx_list = res.scalars().all()
            assert len(ctx_list) == 1
            assert ctx_list[0].context_data.get("digression_messages") == 2

        # Send 3rd follow-up → digression_messages hits >= 3 → garbage collected
        await ac.post("/api/v1/routing", json=req_payload, headers=headers)
        async with async_session_factory() as session:
            stmt = select(Context).where(Context.session_id == session_id)
            res = await session.execute(stmt)
            ctx_list = res.scalars().all()
            assert len(ctx_list) == 0
