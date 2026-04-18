"""JSON-RPC and common schemas for A2A communication."""

from pydantic import BaseModel, ConfigDict, Field

class RequestContext(BaseModel):
    """Context information for A2A requests."""
    model_config = ConfigDict(strict=True, extra="forbid")

    family_id: str
    user_id: str
    correlation_id: str
    language: str = "fr"
    preferences: dict | None = None
    restrictions: list[str] | None = None


class JsonRpcError(BaseModel):
    """JSON-RPC 2.0 error object."""
    model_config = ConfigDict(strict=True, extra="forbid")

    code: int
    message: str
    data: dict | None = None


class JsonRpcRequest(BaseModel):
    """JSON-RPC 2.0 request object."""
    model_config = ConfigDict(strict=True, extra="forbid")

    jsonrpc: str = "2.0"
    method: str
    params: dict | None = None
    id: str


class JsonRpcResponse(BaseModel):
    """JSON-RPC 2.0 response object."""
    model_config = ConfigDict(strict=True, extra="forbid")

    jsonrpc: str = "2.0"
    result: dict | None = None
    error: JsonRpcError | None = None
    id: str
