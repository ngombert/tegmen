import logging
from typing import Optional
from sqlalchemy.ext.asyncio import async_sessionmaker, AsyncSession
from sqlalchemy import select, update, delete
from agent_maestro.session import BaseSessionStore
from agent_maestro.app.db.models.user_session import UserSession

logger = logging.getLogger("maestro.session")


class PostgresSessionStore(BaseSessionStore):
    """
    PostgreSQL implementation of BaseSessionStore.
    Saves and updates session details in the database, failing fast on database errors.
    """

    def __init__(self, session_factory: async_sessionmaker[AsyncSession]):
        self.session_factory = session_factory

    async def get(self, session_id: str) -> Optional[str]:
        """
        Retrieve the agent_id associated with a session_id.
        """
        async with self.session_factory() as session:
            stmt = select(UserSession.active_agent).where(UserSession.session_id == session_id)
            result = await session.execute(stmt)
            return result.scalar_one_or_none()

    async def set(self, session_id: str, agent_id: str) -> None:
        """
        Store the agent_id for a session_id.
        """
        import uuid
        async with self.session_factory() as session:
            async with session.begin():
                stmt = select(UserSession).where(UserSession.session_id == session_id)
                result = await session.execute(stmt)
                db_session = result.scalar_one_or_none()
                if db_session:
                    db_session.active_agent = agent_id
                else:
                    db_session = UserSession(
                        family_id=f"dummy_family_{uuid.uuid4()}",
                        user_id=f"dummy_user_{uuid.uuid4()}",
                        session_id=session_id,
                        active_agent=agent_id
                    )
                    session.add(db_session)


    async def delete(self, session_id: str) -> None:
        """
        Delete the session data for a given session_id.
        """
        async with self.session_factory() as session:
            async with session.begin():
                stmt = delete(UserSession).where(UserSession.session_id == session_id)
                await session.execute(stmt)

    async def get_by_user(self, family_id: str, user_id: str) -> Optional[UserSession]:
        """
        Retrieve a user session model by the unique couple (family_id, user_id).
        """
        async with self.session_factory() as session:
            stmt = select(UserSession).where(
                UserSession.family_id == family_id,
                UserSession.user_id == user_id
            )
            result = await session.execute(stmt)
            return result.scalar_one_or_none()

    async def set_by_user(
        self,
        family_id: str,
        user_id: str,
        session_id: str,
        agent_id: Optional[str],
        active_claim_check_id: Optional[str] = None,
        context_summary: Optional[dict] = None
    ) -> UserSession:
        """
        Upsert a user session based on the unique couple (family_id, user_id).
        """
        async with self.session_factory() as session:
            async with session.begin():
                stmt = select(UserSession).where(
                    UserSession.family_id == family_id,
                    UserSession.user_id == user_id
                )
                result = await session.execute(stmt)
                db_session = result.scalar_one_or_none()

                if db_session:
                    db_session.session_id = session_id
                    db_session.active_agent = agent_id
                    db_session.active_claim_check_id = active_claim_check_id
                    db_session.context_summary = context_summary
                else:
                    db_session = UserSession(
                        family_id=family_id,
                        user_id=user_id,
                        session_id=session_id,
                        active_agent=agent_id,
                        active_claim_check_id=active_claim_check_id,
                        context_summary=context_summary
                    )
                    session.add(db_session)
                
                await session.flush()
                return db_session
