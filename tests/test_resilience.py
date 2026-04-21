import pytest
import httpx
from common.a2a_client import call_remote_agent
from common.exceptions import A2ARPCError
from common.agent_registry import agent_registry

@pytest.mark.asyncio
async def test_a2a_timeout_exception(httpx_mock):
    """
    Test que call_remote_agent lève une A2ARPCError(TIMEOUT) 
    si l'agent mocké dépasse le délai imparti.
    """
    # 1. Préparer le registre avec un agent fictif
    agent_name = "slow-agent"
    agent_url = "http://slow-agent:8000"
    agent_registry.register_agent(agent_name, agent_url)
    
    # 2. Mocker la réponse avec un délai supérieur au timeout par défaut (5s)
    # On simule un timeout côté httpx
    httpx_mock.add_exception(httpx.TimeoutException("Request timed out"), url=f"{agent_url}/a2a/SendMessage")
    
    # 3. Vérifier que l'exception métier est bien levée
    with pytest.raises(A2ARPCError) as exc_info:
        await call_remote_agent(agent_name, "Hello")
    
    assert exc_info.value.code == A2ARPCError.TIMEOUT
    assert "délai" in exc_info.value.message

@pytest.mark.asyncio
async def test_a2a_custom_timeout(httpx_mock):
    """
    Test que l'on peut passer un timeout personnalisé.
    """
    agent_name = "fast-agent"
    agent_url = "http://fast-agent:8000"
    agent_registry.register_agent(agent_name, agent_url)
    
    # Simuler un timeout très court (0.1s)
    httpx_mock.add_exception(httpx.TimeoutException("Too slow"), url=f"{agent_url}/a2a/SendMessage")
    
    with pytest.raises(A2ARPCError) as exc_info:
        await call_remote_agent(agent_name, "Hello", timeout=0.1)
    
    assert exc_info.value.code == A2ARPCError.TIMEOUT
