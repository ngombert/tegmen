import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from agent_maestro.main import detect_explicit_agent, dispatch_with_delegation_loop
from common.schemas import RequestContext

@pytest.mark.parametrize("message, expected", [
    ("acadomie est le seul agent ?", None),
    ("gourmet, propose un menu", "gourmet"),
    ("agent explorer, trouve un vol", "explorer"),
    ("demande a gourmet", "gourmet"),
    ("parle à explorer", "explorer"),
    ("gourmet", "gourmet"),
    ("agent acadomie", "acadomie"),
    ("est-ce que gourmet est là ?", None),
    ("bonjour la famille", None),
])
def test_detect_explicit_agent_refined(message, expected):
    """Test that explicit agent detection is precise and doesn't false-trigger on simple mentions."""
    assert detect_explicit_agent(message) == expected


@pytest.mark.asyncio
@patch("agent_maestro.main.save_new_facts")
@patch("agent_maestro.main.push_context")
@patch("agent_maestro.main.pop_context")
@patch("agent_maestro.main.call_remote_agent")
async def test_dispatch_delegation_loop_basic(mock_call, mock_pop, mock_push, mock_save):
    """Test a basic delegation handoff (A -> B -> Success)."""
    # Mock pop_context and push_context
    mock_pop.return_value = None
    mock_push.return_value = None
    mock_save.return_value = None

    # First call yields to gourmet, second call succeeds
    mock_call.side_effect = [
        # First call (to acadomie) yields
        {
            "status": "yield",
            "delegate_to": "gourmet",
            "message": "Je laisse mon collègue Gourmet vous guider."
        },
        # Second call (to gourmet) succeeds
        {
            "parts": [{"text": "Voici la recette de crêpes."}]
        }
    ]
    
    context = RequestContext(
        family_id="test-family",
        user_id="test-user",
        user_name="Jean",
        role="parent",
        correlation_id="123"
    )
    
    response_text, agent_name, final_route = await dispatch_with_delegation_loop(
        route="acadomie",
        message="Je veux faire des crêpes",
        session_id="session-123",
        active_agent="agent_acadomie",
        context=context,
        request_id="req-123"
    )
    
    assert final_route == "gourmet"
    assert agent_name == "agent_gourmet"
    # The yield explanation should be prepended
    assert "Je laisse mon collègue Gourmet vous guider." in response_text
    assert "Voici la recette de crêpes." in response_text
    assert mock_call.call_count == 2


@pytest.mark.asyncio
@patch("agent_maestro.main.save_new_facts")
@patch("agent_maestro.main.push_context")
@patch("agent_maestro.main.pop_context")
@patch("agent_maestro.main.call_remote_agent")
async def test_dispatch_delegation_loop_loop_protection(mock_call, mock_pop, mock_push, mock_save):
    """Test that loop protection interrupts infinite redirections (A -> B -> A -> B...)."""
    # Mock pop_context, push_context, save_new_facts
    mock_pop.return_value = ("agent_acadomie", {})
    mock_push.return_value = None
    mock_save.return_value = None

    # Always yield back and forth
    mock_call.side_effect = [
        {"status": "yield", "delegate_to": "gourmet", "message": "Yield to Gourmet"},
        {"status": "yield", "delegate_to": "acadomie", "message": "Yield to Acadomie"},
        {"status": "yield", "delegate_to": "gourmet", "message": "Yield to Gourmet"},
        {"status": "yield", "delegate_to": "acadomie", "message": "Yield to Acadomie"},
    ]
    
    context = RequestContext(
        family_id="test-family",
        user_id="test-user",
        user_name="Jean",
        role="parent",
        correlation_id="123"
    )
    
    response_text, agent_name, final_route = await dispatch_with_delegation_loop(
        route="acadomie",
        message="Loop message",
        session_id="session-123",
        active_agent="agent_acadomie",
        context=context,
        request_id="req-123"
    )
    
    # It should break after 3 hops and return loop protection fallback
    assert final_route == "maestro"
    assert "me perds un peu" in response_text
    # 3 calls max
    assert mock_call.call_count == 3
