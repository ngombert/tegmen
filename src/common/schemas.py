"""JSON-RPC and common schemas for A2A communication."""

from pydantic import BaseModel, ConfigDict, Field

class RequestContext(BaseModel):
    """Context information for A2A requests."""
    model_config = ConfigDict(
        strict=True, 
        extra="forbid",
        json_schema_extra={
            "examples": [
                {
                    "family_id": "fam-123",
                    "user_id": "user-456",
                    "correlation_id": "corr-789",
                    "language": "fr",
                    "preferences": {"theme": "dark"}
                }
            ]
        }
    )

    family_id: str
    user_id: str
    correlation_id: str
    language: str = "fr"
    preferences: dict | None = None
    restrictions: list[str] | None = None


class JsonRpcError(BaseModel):
    """JSON-RPC 2.0 error object."""
    model_config = ConfigDict(
        strict=True, 
        extra="forbid",
        json_schema_extra={
            "examples": [
                {
                    "code": -32600,
                    "message": "Invalid Request",
                    "data": {"detail": "Missing 'method' field"}
                }
            ]
        }
    )

    code: int
    message: str
    data: dict | None = None


class JsonRpcRequest(BaseModel):
    """JSON-RPC 2.0 request object."""
    model_config = ConfigDict(
        strict=True, 
        extra="forbid",
        json_schema_extra={
            "examples": [
                {
                    "jsonrpc": "2.0",
                    "method": "route_message",
                    "params": {
                        "message": "Qu'est-ce qu'on mange ce soir ?",
                        "context": {
                            "family_id": "fam-1",
                            "user_id": "user-1",
                            "correlation_id": "id-123"
                        }
                    },
                    "id": "abc-123"
                }
            ]
        }
    )

    jsonrpc: str = "2.0"
    method: str
    params: dict | None = None
    id: str


class JsonRpcResponse(BaseModel):
    """JSON-RPC 2.0 response object."""
    model_config = ConfigDict(
        strict=True, 
        extra="forbid",
        json_schema_extra={
            "examples": [
                {
                    "jsonrpc": "2.0",
                    "result": {"message": "D'accord, je demande à Gourmet !"},
                    "id": "abc-123"
                }
            ]
        }
    )

    jsonrpc: str = "2.0"
    result: dict | None = None
    error: JsonRpcError | None = None
    id: str
