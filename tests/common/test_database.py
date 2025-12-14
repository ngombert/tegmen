import pytest
from unittest.mock import MagicMock, patch, AsyncMock
from src.common.models import FamilyMember, Preference, ConversationLog
from src.common.database import get_db


def test_family_member_model_repr():
    member = FamilyMember(id=1, name="Papa", role="parent")
    assert repr(member) == "<FamilyMember(id=1, name='Papa', role='parent')>"


def test_preference_model_repr():
    pref = Preference(id=1, category="food")
    assert repr(pref) == "<Preference(id=1, category='food')>"


def test_conversation_log_model_repr():
    log = ConversationLog(id=1, agent="gourmet", role="user")
    assert repr(log) == "<ConversationLog(id=1, agent='gourmet', role='user')>"


@pytest.mark.asyncio
async def test_get_db_yields_session():
    # Mock async_session_factory
    mock_session = AsyncMock()
    mock_session.commit = AsyncMock()
    mock_session.rollback = AsyncMock()
    mock_session.close = AsyncMock()

    # Mock the factory to return an async context manager that yields our mock_session
    # Mock the factory to return an async context manager that yields our mock_session
    mock_factory = MagicMock()
    mock_context_manager = MagicMock()
    mock_context_manager.__aenter__ = AsyncMock(return_value=mock_session)
    mock_context_manager.__aexit__ = AsyncMock(return_value=None)
    mock_factory.return_value = mock_context_manager

    with patch("src.common.database.async_session_factory", mock_factory):
        async for session in get_db():
            assert session == mock_session

        # Verify commit and close were called
        mock_session.commit.assert_awaited_once()
        mock_session.close.assert_awaited_once()


@pytest.mark.asyncio
async def test_get_db_rollback_on_error():
    # Mock session
    mock_session = AsyncMock()
    # Explicitly set methods as AsyncMock
    mock_session.rollback = AsyncMock()
    mock_session.close = AsyncMock()

    mock_factory = MagicMock()
    # Ensure the context manager methods are async
    mock_context_manager = MagicMock()
    mock_context_manager.__aenter__ = AsyncMock(return_value=mock_session)
    mock_context_manager.__aexit__ = AsyncMock(return_value=None)
    mock_factory.return_value = mock_context_manager

    with patch("src.common.database.async_session_factory", mock_factory):
        with pytest.raises(ValueError):
            async for session in get_db():
                raise ValueError("Test error")

            # Verify rollback was called
            # Use await_args or called check since assert_awaited_once behaves oddly with child mocks sometimes
            assert mock_session.rollback.await_count == 1
            assert mock_session.close.await_count == 1
