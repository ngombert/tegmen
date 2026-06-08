import pytest
from unittest.mock import patch, MagicMock

@pytest.fixture
def mock_litellm():
    """Mock for litellm.acompletion."""
    with patch("litellm.acompletion") as mock_acomplete:
        response_mock = MagicMock()
        message_mock = MagicMock()
        message_mock.content = "Voici mon conseil : fais tes devoirs en avance."
        response_mock.choices = [MagicMock(message=message_mock)]
        
        mock_acomplete.return_value = response_mock
        yield mock_acomplete

@pytest.mark.asyncio
async def test_organization_advice_success(client, mock_litellm):
    """Test successful organizational advice generation."""
    rpc_request = {
        "jsonrpc": "2.0",
        "method": "organization/advice",
        "params": {
            "student_id": "student-1",
            "context": {
                "family_id": "fam-123"
            }
        },
        "id": "1"
    }
    
    response = await client.post("/a2a/SendMessage", json=rpc_request)
    assert response.status_code == 200
    
    data = response.json()
    assert "result" in data
    assert "advice" in data["result"]
    assert "Voici mon conseil" in data["result"]["advice"]
    
    # Verify that litellm was called with the correct prompt structure
    mock_litellm.assert_called_once()
    kwargs = mock_litellm.call_args.kwargs
    assert "messages" in kwargs
    messages = kwargs["messages"]
    assert len(messages) == 2
    assert messages[0]["role"] == "system"
    assert messages[1]["role"] == "user"
    # Ensure context is included in the prompt
    user_prompt = messages[1]["content"]
    assert "Devoirs à faire" in user_prompt
    assert "Notes récentes" in user_prompt

@pytest.mark.asyncio
async def test_organization_advice_with_question(client, mock_litellm):
    """Test advice generation with a specific question."""
    rpc_request = {
        "jsonrpc": "2.0",
        "method": "organization/advice",
        "params": {
            "student_id": "student-1",
            "question": "Comment réviser les maths ?",
            "context": {
                "family_id": "fam-123"
            }
        },
        "id": "2"
    }
    
    response = await client.post("/a2a/SendMessage", json=rpc_request)
    assert response.status_code == 200
    
    data = response.json()
    assert "result" in data
    
    # Verify the question is in the prompt
    kwargs = mock_litellm.call_args.kwargs
    user_prompt = kwargs["messages"][1]["content"]
    assert "Comment réviser les maths" in user_prompt

@pytest.mark.asyncio
async def test_organization_advice_missing_params(client):
    """Test failure when required parameters are missing."""
    rpc_request = {
        "jsonrpc": "2.0",
        "method": "organization/advice",
        "params": {
            "context": {
                "family_id": "fam-123"
            }
        },
        "id": "3"
    }
    
    response = await client.post("/a2a/SendMessage", json=rpc_request)
    assert response.status_code == 200
    
    data = response.json()
    assert "error" in data
    assert data["error"]["code"] == -32602 # INVALID_PARAMS
    assert "student_id" in data["error"]["message"]

@pytest.mark.asyncio
@patch("litellm.acompletion")
async def test_organization_advice_timeout(mock_acompletion, client):
    """Test LLM timeout scenario."""
    import asyncio
    mock_acompletion.side_effect = asyncio.TimeoutError()
    
    rpc_request = {
        "jsonrpc": "2.0",
        "method": "organization/advice",
        "params": {
            "student_id": "student-1",
            "context": {
                "family_id": "fam-123"
            }
        },
        "id": "4"
    }
    
    response = await client.post("/a2a/SendMessage", json=rpc_request)
    assert response.status_code == 200
    
    data = response.json()
    assert "error" in data
    assert data["error"]["code"] == -32000 # TIMEOUT
    assert "surchargé" in data["error"]["message"]

@pytest.mark.asyncio
async def test_organization_advice_out_of_domain(client, mock_litellm):
    """Test advice generation prompt includes out-of-domain constraints."""
    rpc_request = {
        "jsonrpc": "2.0",
        "method": "organization/advice",
        "params": {
            "student_id": "student-1",
            "question": "Donne moi la recette de la tarte aux pommes.",
            "context": {
                "family_id": "fam-123"
            }
        },
        "id": "5"
    }
    
    response = await client.post("/a2a/SendMessage", json=rpc_request)
    assert response.status_code == 200
    
    # Verify the constraints are in the system prompt
    kwargs = mock_litellm.call_args.kwargs
    system_prompt = kwargs["messages"][0]["content"]
    assert "CHARTE ANTI-HALLUCINATION" in system_prompt
    assert "refuser poliment de répondre" in system_prompt
    assert "sort de ton domaine d'expertise" in system_prompt
