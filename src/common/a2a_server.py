"""A2A Server utilities for agent microservices (Lean version)."""

from typing import Any, Callable
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from src.common.logger import setup_logger
from src.common.schemas import JsonRpcRequest, JsonRpcResponse, JsonRpcError
from src.common.exceptions import A2ARPCError

logger = setup_logger("a2a_server")

class A2AServer:
    """Lean A2A Server implementation using FastAPI."""

    def __init__(self, agent_name: str) -> None:
        self.agent_name = agent_name
        self.methods: dict[str, Callable] = {}

    def register_method(self, name: str, func: Callable) -> None:
        """Register a handler for a JSON-RPC method."""
        self.methods[name] = func

    async def handle_request(self, request: JsonRpcRequest) -> JsonRpcResponse:
        """Handle a JSON-RPC request."""
        if request.method not in self.methods:
            return JsonRpcResponse(
                id=request.id,
                error=JsonRpcError(
                    code=A2ARPCError.METHOD_NOT_FOUND,
                    message=f"Method '{request.method}' not found"
                )
            )

        handler = self.methods[request.method]
        try:
            result = await handler(request.params)
            return JsonRpcResponse(id=request.id, result=result)
        except Exception as e:
            logger.error(f"Error executing method {request.method}: {e}")
            return JsonRpcResponse(
                id=request.id,
                error=JsonRpcError(
                    code=A2ARPCError.INTERNAL_ERROR,
                    message=str(e)
                )
            )


def create_a2a_app(
    agent: Any,  # Kept for compatibility, but ADK dependencies removed
    agent_name: str,
    agent_description: str,
    skills: list[dict],
    public_url: str,
    version: str = "0.1.0",
) -> FastAPI:
    """
    Create a Lean A2A FastAPI application for an agent.
    
    NOTE: This replaces the legacy ADK-based version. 
    ADKAgentExecutor is removed as part of the transition to a pure FastAPI/Pydantic stack.
    """
    app = FastAPI(
        title=agent_name,
        description=agent_description,
        version=version
    )

    server = A2AServer(agent_name)

    @app.post("/a2a/SendMessage")
    async def send_message(rpc_request: JsonRpcRequest) -> JsonRpcResponse:
        """Endpoint for A2A communication."""
        return await server.handle_request(rpc_request)

    @app.get("/a2a/AgentCard")
    async def get_agent_card() -> dict[str, Any]:
        """Return agent metadata."""
        return {
            "name": agent_name,
            "description": agent_description,
            "url": public_url,
            "version": version,
            "skills": skills
        }

    # Helper to return the app (compatible with mount points)
    return app
