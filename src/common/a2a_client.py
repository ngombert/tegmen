"""A2A Client for Maestro to communicate with remote agents."""

import httpx
from typing import Optional
import uuid

from common.config import config
from common.agent_registry import agent_registry
from common.exceptions import A2ARPCError

from a2a.client.errors import A2AClientTimeoutError, A2AClientHTTPError
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

    def __init__(self, agent_url: str, httpx_client: httpx.AsyncClient | None = None, timeout: float | None = None) -> None:
        """Initialize client with agent base URL."""
        self.agent_url = agent_url.rstrip("/")
        # Configure httpx client with base_url and SLA timeout
        actual_timeout = timeout if timeout is not None else config.DEFAULT_A2A_TIMEOUT
        self.client = httpx_client or httpx.AsyncClient(
            base_url=self.agent_url, 
            timeout=actual_timeout
        )

    async def send_message(self, message: str, context_id: str | None = None, context: Optional["RequestContext"] = None) -> str:
        """Send a message to the remote agent and get response."""

        # Use JsonRpcTransport directly to avoid A2AClient DeprecationWarning
        endpoint_url = f"{self.agent_url}/a2a/SendMessage"
        transport = JsonRpcTransport(url=endpoint_url, httpx_client=self.client)

        # Create message
        text_part = TextPart(text=message)
        msg = Message(
            role=Role.user,
            parts=[text_part],
            messageId=str(uuid.uuid4()),
        )

        # Create request params
        # We include context in the params if provided
        params_dict = {
            "message": msg,
            "contextId": context_id,
        }
        if context:
            params_dict["context"] = context

        # Send and get response result
        try:
            # JsonRpcTransport.send_message returns the 'result' part of JSON-RPC directly
            # Note: MessageSendParams might not support 'context' yet if it's from the SDK, 
            # so we might need to pass a dict if the transport allows it, or use a custom model.
            # JsonRpcTransport.send_message in the SDK usually takes the params object.
            
            # For now, we'll try to pass it via the standard MessageSendParams if we can, 
            # or just rely on the fact that we're using JSON-RPC and we can extend params.
            result = await transport.send_message(params_dict)
        except (httpx.TimeoutException, A2AClientTimeoutError):
            raise A2ARPCError(
                code=A2ARPCError.TIMEOUT,
                message=f"L'agent à l'URL {self.agent_url} n'a pas répondu dans le délai imparti."
            )
        except A2AClientHTTPError as e:
            # Check if it's a network-level timeout wrapped in a 503 by the SDK
            err_msg = str(e).lower()
            if "timed out" in err_msg or "too slow" in err_msg or "timeout" in err_msg:
                raise A2ARPCError(
                    code=A2ARPCError.TIMEOUT,
                    message=f"L'agent à l'URL {self.agent_url} a rencontré une erreur de communication (délai dépassé)."
                )
            raise A2ARPCError(
                code=A2ARPCError.INTERNAL_ERROR,
                message=f"Erreur HTTP lors de l'appel A2A vers {self.agent_url}: {str(e)}"
            )
        except Exception as e:
            raise A2ARPCError(
                code=A2ARPCError.INTERNAL_ERROR,
                message=f"Erreur interne lors de l'appel A2A vers {self.agent_url}: {str(e)}"
            )

        # Extract text from response result
        if result:
            # Handle plain dictionary (Lean agents)
            if isinstance(result, dict):
                if "parts" in result:
                    for part in result["parts"]:
                        if isinstance(part, dict) and "text" in part:
                            return part["text"]
                if "message" in result:
                    return result["message"]
                if "text" in result:
                    return result["text"]

            # Handle ADK objects (Message or Task)
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
                        if hasattr(artifact, "parts") and artifact.parts:
                            for part in artifact.parts:
                                if hasattr(part, "root") and hasattr(part.root, "text"):
                                    return part.root.text
                                if hasattr(part, "text"):
                                    return part.text

        return "Pas de réponse de l'agent."

    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()


# Global client utilities
# (AGENT_URLS removed, now handled by agent_registry)


async def call_remote_agent(
    route: str, message: str, context_id: str | None = None, timeout: float | None = None, context: Optional["RequestContext"] = None
) -> str:
    """Call a remote agent by route name."""
    # Resolve agent URL from registry
    url = agent_registry.get_agent_url(route)
    if not url:
        return f"Agent '{route}' non trouvé dans le registre."

    client = RemoteAgentClient(url, timeout=timeout)
    try:
        return await client.send_message(message, context_id, context)
    finally:
        await client.close()
