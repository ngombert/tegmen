"""
Session management for Maestro Gateway.
Provides an abstract interface and an in-memory implementation for storing
contextual session state (e.g., affinity to a specific agent).
"""

from abc import ABC, abstractmethod
from typing import Optional, Dict, Tuple
import time
import asyncio

from common.logger import setup_logger

logger = setup_logger("maestro.session")


class BaseSessionStore(ABC):
    """
    Abstract Base Class for Maestro Session Store.
    Implementations must handle asynchronous operations and TTL expiration.
    """

    @abstractmethod
    async def get(self, session_id: str) -> Optional[str]:
        """
        Retrieve the agent_id associated with a session_id.
        Returns None if the session does not exist or has expired.
        """
        pass

    @abstractmethod
    async def set(self, session_id: str, agent_id: str) -> None:
        """
        Store the agent_id for a session_id, updating its TTL.
        """
        pass

    @abstractmethod
    async def delete(self, session_id: str) -> None:
        """
        Delete the session data for a given session_id.
        """
        pass


class InMemorySessionStore(BaseSessionStore):
    """
    In-Memory implementation of BaseSessionStore using a dictionary.
    Features lazy deletion for expired entries to avoid blocking background tasks.
    """

    def __init__(self, ttl_seconds: int = 600):
        """
        Initialize the in-memory session store.
        
        Args:
            ttl_seconds: Time to live for a session in seconds (default: 10 minutes).
        """
        self.ttl_seconds = ttl_seconds
        # store format: { session_id: (agent_id, expiry_timestamp) }
        self._store: Dict[str, Tuple[str, float]] = {}
        self._lock = asyncio.Lock()

    async def get(self, session_id: str) -> Optional[str]:
        """
        Get the agent_id for a session_id. Performs lazy deletion if expired.
        """
        async with self._lock:
            if session_id not in self._store:
                return None
            
            agent_id, expiry_time = self._store[session_id]
            
            if time.time() > expiry_time:
                # Expired -> Lazy deletion
                del self._store[session_id]
                logger.debug(f"Session {session_id} expired and was removed.")
                return None
                
            return agent_id

    async def set(self, session_id: str, agent_id: str) -> None:
        """
        Store the agent_id for a session_id with a new TTL.
        """
        expiry_time = time.time() + self.ttl_seconds
        async with self._lock:
            self._store[session_id] = (agent_id, expiry_time)
            logger.debug(f"Session {session_id} set to agent '{agent_id}' (TTL: {self.ttl_seconds}s)")

    async def delete(self, session_id: str) -> None:
        """
        Explicitly delete a session_id from the store.
        """
        async with self._lock:
            if session_id in self._store:
                del self._store[session_id]
                logger.debug(f"Session {session_id} manually deleted.")
