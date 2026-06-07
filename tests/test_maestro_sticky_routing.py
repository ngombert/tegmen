import pytest
from unittest.mock import patch, MagicMock

from agent_maestro.router import classify_intent, THRESHOLD_CLARIFICATION, THRESHOLD_ROUTING


@patch("agent_maestro.router.get_all_scores")
def test_classify_intent_without_active_agent(mock_get_all_scores):
    """Without active_agent, classify_intent uses get_all_scores (unified path)."""
    mock_get_all_scores.return_value = {
        "gourmet": 0.45,
        "acadomie": 0.10,
        "chitchat": 0.25
    }
    
    route, score = classify_intent("Je veux préparer à manger")
    
    assert route == "gourmet"
    assert score == 0.45
    mock_get_all_scores.assert_called_once_with("Je veux préparer à manger")

@patch("agent_maestro.router.get_all_scores")
def test_classify_intent_with_active_agent_bonus(mock_get_all_scores):
    # Mock scores without bonus
    mock_get_all_scores.return_value = {
        "gourmet": 0.35, # just below routing threshold of 0.40
        "acadomie": 0.10,
        "chitchat": 0.25
    }
    
    # With active agent 'gourmet', it gets a * 1.3 bonus.
    # 0.35 * 1.3 = 0.455. It should become the top score and cross the routing threshold.
    route, score = classify_intent("message bidon", active_agent="gourmet")
    
    assert route == "gourmet"
    assert round(score, 3) == 0.455
    
@patch("agent_maestro.router.get_all_scores")
def test_classify_intent_bonus_capped_at_1(mock_get_all_scores):
    # Mock scores with a very high base score
    mock_get_all_scores.return_value = {
        "explorer": 0.90,
    }
    
    # 0.90 * 1.3 = 1.17, which should be capped at 1.0
    route, score = classify_intent("message bidon", active_agent="agent_explorer")
    
    assert route == "explorer"
    assert score == 1.0

@patch("agent_maestro.router.get_all_scores")
def test_classify_intent_active_agent_not_in_top(mock_get_all_scores):
    # Mock scores where active agent has a very low score
    mock_get_all_scores.return_value = {
        "gourmet": 0.80,
        "acadomie": 0.10
    }
    
    # Active agent is acadomie. 0.10 * 1.3 = 0.13. 
    # Gourmet remains the winner with 0.80.
    route, score = classify_intent("message bidon", active_agent="acadomie")
    
    assert route == "gourmet"
    assert score == 0.80

@patch("agent_maestro.router.get_all_scores")
def test_classify_intent_semantic_escape_hatch(mock_get_all_scores):
    # Mock scores where a new agent has a very high score (> 0.95)
    mock_get_all_scores.return_value = {
        "gourmet": 0.80, # Active agent
        "acadomie": 0.96 # Very high score (> 0.95)
    }
    
    # Normally, 0.80 * 1.3 = 1.0, so gourmet would win or tie.
    # BUT, because acadomie > 0.95, the escape hatch triggers and no bonus is applied.
    route, score = classify_intent("message bidon", active_agent="gourmet")
    
    assert route == "acadomie"
    assert score == 0.96


@patch("agent_maestro.router.get_all_scores")
def test_classify_intent_unified_path_same_source(mock_get_all_scores):
    """Both with and without active_agent use the same get_all_scores source."""
    mock_get_all_scores.return_value = {
        "gourmet": 0.50,
        "acadomie": 0.30,
        "chitchat": 0.10,
    }
    
    # Without active agent
    route1, score1 = classify_intent("test message")
    # With active agent that doesn't change the winner
    route2, score2 = classify_intent("test message", active_agent="agent_chitchat")
    
    # Both should use the same underlying scores
    assert route1 == "gourmet"
    assert score1 == 0.50
    # gourmet still wins (chitchat 0.10 * 1.3 = 0.13 < 0.50)
    assert route2 == "gourmet"
    assert score2 == 0.50
    # get_all_scores was called for both paths
    assert mock_get_all_scores.call_count == 2


@patch("agent_maestro.router.get_all_scores")
def test_classify_intent_empty_scores(mock_get_all_scores):
    """When get_all_scores returns an empty dict, classify_intent returns unknown."""
    mock_get_all_scores.return_value = {}
    
    route, score = classify_intent("some message")
    
    assert route == "unknown"
    assert score == 0.0


@patch("agent_maestro.router.get_all_scores")
def test_classify_intent_empty_scores_with_active_agent(mock_get_all_scores):
    """Empty scores with active_agent should also return unknown."""
    mock_get_all_scores.return_value = {}
    
    route, score = classify_intent("some message", active_agent="agent_gourmet")
    
    assert route == "unknown"
    assert score == 0.0


def test_classify_intent_empty_message():
    """Empty message should return unknown without calling get_all_scores."""
    route, score = classify_intent("")
    
    assert route == "unknown"
    assert score == 0.0


def test_classify_intent_none_active_agent_equivalent():
    """Passing None as active_agent should behave the same as not passing it."""
    with patch("agent_maestro.router.get_all_scores") as mock:
        mock.return_value = {"gourmet": 0.60, "chitchat": 0.20}
        
        route1, score1 = classify_intent("test")
        route2, score2 = classify_intent("test", active_agent=None)
        
        assert (route1, score1) == (route2, score2)
        assert route1 == "gourmet"


@patch("agent_maestro.router.get_all_scores")
def test_classify_intent_short_input_lock(mock_get_all_scores):
    """A single-word message should force routing to the active agent with confidence 1.0."""
    mock_get_all_scores.return_value = {
        "gourmet": 0.05,
        "chitchat": 0.88,
    }
    
    # Active agent is gourmet. Single-word input "consulter".
    # It should bypass chitchat and lock to gourmet.
    route, score = classify_intent("consulter", active_agent="agent_gourmet")
    
    assert route == "gourmet"
    assert score == 1.0

