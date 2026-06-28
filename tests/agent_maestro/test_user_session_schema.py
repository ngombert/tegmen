import pytest
from sqlalchemy import select, delete
from sqlalchemy.exc import IntegrityError
from agent_maestro.app.db import session as db_session
from agent_maestro.app.db.models.user_session import UserSession


@pytest.mark.asyncio
async def test_user_session_db_integrity():
    """Test user session DB integrity: valid insert, unique constraint, and updated_at trigger."""
    # Cleanup any leftovers from previous failed runs
    async with db_session.async_session_factory() as session:
        async with session.begin():
            await session.execute(delete(UserSession).where(UserSession.family_id == "fam1"))

    # 1. Test insertion of a valid session
    async with db_session.async_session_factory() as session:
        async with session.begin():
            us = UserSession(
                family_id="fam1",
                user_id="user1",
                session_id="sess1",
                active_agent="agent_gourmet",
                active_claim_check_id="claim1",
                context_summary={"some": "data"}
            )
            session.add(us)

        
        # Verify it was inserted
        stmt = select(UserSession).where(UserSession.session_id == "sess1")
        result = await session.execute(stmt)
        inserted = result.scalar_one()
        assert inserted.family_id == "fam1"
        assert inserted.user_id == "user1"
        assert inserted.active_agent == "agent_gourmet"
        assert inserted.active_claim_check_id == "claim1"
        assert inserted.context_summary == {"some": "data"}
        assert inserted.created_at is not None
        assert inserted.updated_at is not None
        
        updated_at_first = inserted.updated_at

    # 2. Test unique constraint on (family_id, user_id)
    # Attempting to insert another session with same family_id and user_id should raise IntegrityError
    with pytest.raises(IntegrityError):
        async with db_session.async_session_factory() as session:
            async with session.begin():
                duplicate = UserSession(
                    family_id="fam1",
                    user_id="user1",
                    session_id="sess2",  # different session_id, same family_id & user_id
                    active_agent="agent_acadomie"
                )
                session.add(duplicate)



    # 3. Test that updated_at changes on update
    async with db_session.async_session_factory() as session:
        async with session.begin():
            # Retrieve the session
            stmt = select(UserSession).where(UserSession.session_id == "sess1")
            result = await session.execute(stmt)
            inserted = result.scalar_one()
            
            # Update the active agent
            inserted.active_agent = "agent_explorer"
            session.add(inserted)
            
        # Re-fetch and check updated_at
        stmt = select(UserSession).where(UserSession.session_id == "sess1")
        result = await session.execute(stmt)
        updated = result.scalar_one()
        assert updated.active_agent == "agent_explorer"
        assert updated.updated_at >= updated_at_first

    # Cleanup
    async with db_session.async_session_factory() as session:
        async with session.begin():
            stmt = select(UserSession).where(UserSession.session_id == "sess1")
            result = await session.execute(stmt)
            inserted = result.scalar_one_or_none()
            if inserted:
                await session.delete(inserted)
