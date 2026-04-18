"""A2A Client for Maestro to communicate with remote agents."""

import httpx
from typing import Optional
import uuid

from src.common.config import config

from a2a.client.transports.jsonrpc import JsonRpcTransport
from a2a.types import (
    SendMessageRequest,
    Message,
    TextPart,
    Role,
    MessageSendParams,
)


class RemoteAgentClient:
    """Client for communicating with remote A2A agents."""

    def __init__(self, agent_url: str, httpx_client: httpx.AsyncClient | None = None) -> None:
        """Initialize client with agent base URL."""
        self.agent_url = agent_url.rstrip("/")
        # Configure httpx client with base_url and SLA timeout (Story 4.1)
        self.client = httpx_client or httpx.AsyncClient(
            base_url=self.agent_url, 
            timeout=5.0
        )

    async def send_message(self, message: str, context_id: str | None = None) -> str:
        """Send a message to the remote agent and get response."""

        # Use JsonRpcTransport directly to avoid A2AClient DeprecationWarning
        transport = JsonRpcTransport(url=self.agent_url, httpx_client=self.client)

        # Create message
        text_part = TextPart(text=message)
        msg = Message(
            role=Role.user,
            parts=[text_part],
            messageId=str(uuid.uuid4()),
        )

        # Create request params (the transport expects params, not the whole Request object)
        params = MessageSendParams(
            message=msg,
            contextId=context_id,
        )

        # Send and get response result
        # JsonRpcTransport.send_message returns the 'result' part of JSON-RPC directly
        result = await transport.send_message(params)

        # Extract text from response result
        if result:
            # Handle different response types (Message or Task)
            if hasattr(result, "parts") and result.parts:
                for part in result.parts:
                    # Handle TextPart (nested root or direct)
                    if hasattr(part, "root") and hasattr(part.root, "text"):
                        return part.root.text
                    if hasattr(part, "text"):
                        return part.text

            if hasattr(result, "status") and hasattr(result, "artifacts"):
                # Task response - check for artifacts
                if result.artifacts:
                    for artifact in result.artifacts:
                        if artifact.parts:
                            for part in artifact.parts:
                                if hasattr(part, "root") and hasattr(
                                    part.root, "text"
                                ):
                                    return part.root.text
                                if hasattr(part, "text"):
                                    return part.text

        return "Pas de réponse de l'agent."

    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()


# Agent URLs configuration (from environment or defaults)
AGENT_URLS = {
    "gourmet": config.GOURMET_URL,
    "acadomie": config.ACADOMIE_URL,
    "explorer": config.EXPLORER_URL,
}


async def call_remote_agent(
    route: str, message: str, context_id: str | None = None
) -> str:
    """Call a remote agent by route name."""
    url = AGENT_URLS.get(route)
    if not url:
        return f"Agent '{route}' non trouvé."

    client = RemoteAgentClient(url)
    try:
        return await client.send_message(message, context_id)
    finally:
        await client.close()
