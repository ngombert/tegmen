import os
import pytest
from unittest.mock import patch, MagicMock
from common.agent_registry import AgentRegistry

@pytest.fixture
def mock_yaml_config():
    return {
        "agents": [
            {
                "name": "test_agent",
                "description": "A test agent",
                "url": "http://test:8000",
                "utterances": ["hello", "test"]
            }
        ]
    }

@pytest.mark.asyncio
async def test_registry_loading(mock_yaml_config):
    # Reset singleton for testing
    AgentRegistry._instance = None
    
    with patch("common.agent_registry.os.path.exists", return_value=True):
        with patch("common.agent_registry.yaml.safe_load", return_value=mock_yaml_config):
            with patch("builtins.open", MagicMock()):
                registry = AgentRegistry()
                assert "test_agent" in registry._agents
                assert registry.get_agent_url("test_agent") == "http://test:8000"

@pytest.mark.asyncio
async def test_registry_env_override(mock_yaml_config):
    # Reset singleton
    AgentRegistry._instance = None
    
    with patch.dict(os.environ, {"AGENT_TEST_AGENT_URL": "http://override:9000"}):
        with patch("common.agent_registry.os.path.exists", return_value=True):
            with patch("common.agent_registry.yaml.safe_load", return_value=mock_yaml_config):
                with patch("builtins.open", MagicMock()):
                    registry = AgentRegistry()
                    assert registry.get_agent_url("test_agent") == "http://override:9000"

@pytest.mark.asyncio
async def test_registry_list_agents(mock_yaml_config):
    # Reset singleton
    AgentRegistry._instance = None
    
    with patch("common.agent_registry.os.path.exists", return_value=True):
        with patch("common.agent_registry.yaml.safe_load", return_value=mock_yaml_config):
            with patch("builtins.open", MagicMock()):
                registry = AgentRegistry()
                # Clear any lingering agents (though instance was reset)
                # Ensure we only have the mock agent
                agents = registry.list_agents()
                assert len(agents) == 1
                assert agents[0]["name"] == "test_agent"
