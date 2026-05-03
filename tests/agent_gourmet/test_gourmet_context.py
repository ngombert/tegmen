import pytest
from agent_gourmet.app.context import set_correlation_id, get_correlation_id
import asyncio

def test_correlation_id_basic():
    """Test that we can set and get correlation_id."""
    cid = "test-cid-123"
    set_correlation_id(cid)
    assert get_correlation_id() == cid

@pytest.mark.asyncio
async def test_correlation_id_async_isolation():
    """Test that correlation_id is isolated between async tasks."""
    
    async def task1():
        set_correlation_id("cid-1")
        await asyncio.sleep(0.1)
        return get_correlation_id()
        
    async def task2():
        set_correlation_id("cid-2")
        await asyncio.sleep(0.05)
        return get_correlation_id()
        
    res1, res2 = await asyncio.gather(task1(), task2())
    
    assert res1 == "cid-1"
    assert res2 == "cid-2"
