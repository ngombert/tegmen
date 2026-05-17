import pytest
import os
from unittest.mock import patch, MagicMock
from agent_acadomie.app.services.llm_service import LLMService

@pytest.mark.asyncio
async def test_llm_service_mock_mode():
    """Test that LLMService returns mock response when USE_MOCK_LLM is true."""
    service = LLMService()
    
    with patch.dict(os.environ, {"USE_MOCK_LLM": "true"}):
        response = await service.generate_response("System", "User")
        assert "réponse simulée" in response
        assert "Mock LLM" in response

@pytest.mark.asyncio
async def test_llm_service_real_mode_mocked():
    """Test that LLMService calls litellm when USE_MOCK_LLM is false (mocking litellm)."""
    service = LLMService()
    
    with patch.dict(os.environ, {"USE_MOCK_LLM": "false"}):
        with patch("litellm.acompletion") as mock_acomplete:
            response_mock = MagicMock()
            message_mock = MagicMock()
            message_mock.content = "Real response"
            response_mock.choices = [MagicMock(message=message_mock)]
            mock_acomplete.return_value = response_mock
            
            response = await service.generate_response("System", "User")
            assert response == "Real response"
            mock_acomplete.assert_called_once()
