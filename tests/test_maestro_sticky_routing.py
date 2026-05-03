import pytest
from unittest.mock import patch, MagicMock

from agent_maestro.router import classify_intent, THRESHOLD_CLARIFICATION, THRESHOLD_ROUTING

@patch("agent_maestro.router.get_router")
def test_classify_intent_without_active_agent(mock_get_router):
    mock_router = MagicMock()
    mock_result = MagicMock()
    mock_result.name = "gourmet"
    mock_result.similarity_score = 0.45
    mock_router.return_value = mock_result
    mock_get_router.return_value = mock_router
    
    # Use a message that is somewhat ambiguous or scores generally
    route, score = classify_intent("Je veux préparer à manger")
    # It should classify as gourmet normally
    assert route == "gourmet"
    # The score should be greater than 0
    assert score == 0.45

@patch("agent_maestro.router.get_all_scores")
def test_classify_intent_with_active_agent_bonus(mock_get_all_scores):
    # Mock scores without bonus
    mock_get_all_scores.return_value = {
        "gourmet": 0.35, # just below routing threshold of 0.40
        "acadomie": 0.10,
        "chitchat": 0.25
    }
    
    # 1. Without active agent, the best route should be 'gourmet', but with its original score 0.35
    # Since we mocked get_all_scores but the original implementation of classify_intent 
    # only calls get_all_scores when active_agent is provided, we must test the active_agent branch.
    
    # 2. With active agent 'gourmet', it gets a * 1.3 bonus.
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
