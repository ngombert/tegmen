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
    route, score = classify_intent("Salut")
    assert route == "chitchat"
    assert score > 0.5

def test_classify_unknown():
    # With the unified pipeline, classify_intent always returns the best route
    # from get_all_scores. For unrecognizable text, the score will be very low.
    # The "unknown" fallback is handled by main.py's threshold dispatch.
    from common.config import config
    if config.EMBEDDING_MODEL == "intfloat/multilingual-e5-small":
        pytest.skip("E5 embedding model has a high baseline similarity score.")
    route, score = classify_intent("XJKYZZZ random text")
    assert score < 0.2  # Below any routing threshold

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
    # Using an exact utterance to ensure high enough score
    route, score = classify_intent("Vends-moi un tapis")
    assert route == "carpet_dealer"
    assert score > 0.5
    
    # Verify chitchat still works
    route, score = classify_intent("Salut")
    assert route == "chitchat"
    assert score > 0.5

def test_empty_message():
    route, score = classify_intent("")
    assert route == "unknown"
    assert score == 0.0
    
    route, score = classify_intent(None)
    assert route == "unknown"
    assert score == 0.0
