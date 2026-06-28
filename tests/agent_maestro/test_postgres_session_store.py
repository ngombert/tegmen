import pytest
from unittest.mock import patch
from sqlalchemy import select, delete
from agent_maestro.app.db.session import async_session_factory
from agent_maestro.app.db.models.user_session import UserSession
from agent_maestro.session import PostgresSessionStore


@pytest.mark.asyncio
async def test_postgres_session_store_lifecycle():
    """Test full session store lifecycle: set, get, get_by_user, set_by_user, delete."""
    store = PostgresSessionStore(async_session_factory)
    family_id = "test-fam-store"
    user_id = "test-user-store"
    session_id = "test-sess-store-1"
    
    # 0. Cleanup any leftovers
    async with async_session_factory() as session:
        async with session.begin():
            await session.execute(delete(UserSession).where(UserSession.family_id == family_id))
            
    # 1. Initially none
    val = await store.get(session_id)
    assert val is None
    
    db_sess = await store.get_by_user(family_id, user_id)
    assert db_sess is None
    
    # 2. Set by user (create)
    db_sess = await store.set_by_user(
        family_id=family_id,
        user_id=user_id,
        session_id=session_id,
        agent_id="agent_gourmet",
        active_claim_check_id="claim-123",
        context_summary={"foo": "bar"}
    )
    assert db_sess.family_id == family_id
    assert db_sess.user_id == user_id
    assert db_sess.session_id == session_id
    assert db_sess.active_agent == "agent_gourmet"
    
    # Verify via get
    val = await store.get(session_id)
    assert val == "agent_gourmet"
    
    # Verify via get_by_user
    db_sess = await store.get_by_user(family_id, user_id)
    assert db_sess is not None
    assert db_sess.active_agent == "agent_gourmet"
    assert db_sess.active_claim_check_id == "claim-123"
    assert db_sess.context_summary == {"foo": "bar"}
    
    # 3. Update via set
    await store.set(session_id, "agent_explorer")
    val = await store.get(session_id)
    assert val == "agent_explorer"
    
    # 4. Upsert/Update via set_by_user (different session_id)
    session_id_2 = "test-sess-store-2"
    db_sess = await store.set_by_user(
        family_id=family_id,
        user_id=user_id,
        session_id=session_id_2,
        agent_id="agent_acadomie",
        active_claim_check_id="claim-456",
        context_summary={"updated": True}
    )
    assert db_sess.session_id == session_id_2
    assert db_sess.active_agent == "agent_acadomie"
    
    # Previous session_id should not exist (since it was updated for this user)
    val = await store.get(session_id)
    assert val is None
    
    # New session_id should exist
    val = await store.get(session_id_2)
    assert val == "agent_acadomie"
    
    # 5. Delete
    await store.delete(session_id_2)
    val = await store.get(session_id_2)
    assert val is None
    
    db_sess = await store.get_by_user(family_id, user_id)
    assert db_sess is None


@pytest.mark.asyncio
async def test_postgres_session_store_db_error_bubble():
    """Verify that database errors propagate (fail fast) rather than falling back to in-memory."""
    store = PostgresSessionStore(async_session_factory)
    
    # Mock session_factory to raise an exception on call
    with patch.object(store, "session_factory", side_effect=Exception("Database connection lost")):
        with pytest.raises(Exception, match="Database connection lost"):
            await store.get("some_session")
            
        with pytest.raises(Exception, match="Database connection lost"):
            await store.set("some_session", "agent_gourmet")
            
        with pytest.raises(Exception, match="Database connection lost"):
            await store.get_by_user("fam", "user")
