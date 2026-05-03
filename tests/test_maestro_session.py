import pytest
import time
import asyncio
from typing import Optional

from agent_maestro.session import InMemorySessionStore

@pytest.mark.asyncio
async def test_session_store_set_get():
    """Test basic set and get operations."""
    store = InMemorySessionStore(ttl_seconds=600)
    session_id = "sess_123"
    agent_id = "agent_gourmet"
    
    # Initially empty
    assert await store.get(session_id) is None
    
    # Set and get
    await store.set(session_id, agent_id)
    assert await store.get(session_id) == agent_id

@pytest.mark.asyncio
async def test_session_store_delete():
    """Test explicit deletion of a session."""
    store = InMemorySessionStore(ttl_seconds=600)
    session_id = "sess_456"
    agent_id = "agent_explorer"
    
    await store.set(session_id, agent_id)
    assert await store.get(session_id) == agent_id
    
    await store.delete(session_id)
    assert await store.get(session_id) is None
    
    # Deleting a non-existent session should not raise an error
    await store.delete("non_existent")

@pytest.mark.asyncio
async def test_session_store_ttl_lazy_deletion(monkeypatch):
    """Test that TTL expiration causes lazy deletion."""
    store = InMemorySessionStore(ttl_seconds=10)
    session_id = "sess_ttl"
    agent_id = "agent_acadomie"
    
    # Mock time to a fixed timestamp
    current_time = 1000.0
    
    def mock_time():
        return current_time
        
    monkeypatch.setattr(time, "time", mock_time)
    
    await store.set(session_id, agent_id)
    
    # Should be valid at current time
    assert await store.get(session_id) == agent_id
    
    # Move time forward by 5 seconds (still valid)
    current_time += 5.0
    assert await store.get(session_id) == agent_id
    
    # Move time forward by another 6 seconds (total 11s -> expired)
    current_time += 6.0
    assert await store.get(session_id) is None
    
    # Verify it was removed from the internal dictionary
    assert session_id not in store._store

@pytest.mark.asyncio
async def test_session_store_concurrency():
    """Test that concurrent access is safe."""
    store = InMemorySessionStore(ttl_seconds=600)
    session_id = "sess_concurrent"
    
    async def worker(idx: int):
        await store.set(session_id, f"agent_{idx}")
        # Introduce a small yield to encourage context switching
        await asyncio.sleep(0.01)
        val = await store.get(session_id)
        return val
        
    # Run multiple workers concurrently
    tasks = [worker(i) for i in range(50)]
    results = await asyncio.gather(*tasks)
    
    # The final state should be one of the agents
    final_val = await store.get(session_id)
    assert final_val is not None
    assert final_val.startswith("agent_")
    
    # All tasks should have completed without errors
    assert len(results) == 50
