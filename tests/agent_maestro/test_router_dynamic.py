import pytest
from unittest.mock import patch, MagicMock
from agent_maestro.router import classify_intent, reload_router
from common.agent_registry import AgentConfig

@pytest.fixture(autouse=True)
def reset_router():
    # Ensure a fresh router for each test
    with patch("agent_maestro.router.agent_registry") as mock_reg:
        # Default mock: 0 agents
        mock_reg.get_agents.return_value = {}
        reload_router()
        yield

def test_classify_chitchat():
    # Even with 0 dynamic agents, chitchat should work
    assert classify_intent("Salut") == "chitchat"

def test_classify_unknown():
    assert classify_intent("XJKYZZZ random text") == "unknown"

@patch("agent_maestro.router.agent_registry")
def test_dynamic_reloal_and_routing(mock_registry):
    # Setup mock registry with a new fake agent
    mock_agent = AgentConfig(
        name="carpet_dealer",
        description="Vendeur de tapis",
        url="http://fake",
        utterances=["Vends-moi un tapis", "Prix du tapis", "Tapis volant"]
    )
    mock_registry.get_agents.return_value = {"carpet_dealer": mock_agent}
    
    # Reload router to pick up the fake agent
    reload_router()
    
    # Test routing to the new agent
    # Using an exact utterance to ensure 1.0 score
    assert classify_intent("Vends-moi un tapis") == "carpet_dealer"
    
    # Verify chitchat still works
    assert classify_intent("Salut") == "chitchat"

def test_empty_message():
    assert classify_intent("") == "unknown"
    assert classify_intent(None) == "unknown"
