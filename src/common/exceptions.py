"""Custom exceptions for A2A communication."""

class A2ARPCError(Exception):
    """Exception raised for A2A RPC errors."""

    # Standard JSON-RPC 2.0 error codes
    PARSE_ERROR = -32700
    INVALID_REQUEST = -32600
    METHOD_NOT_FOUND = -32601
    INVALID_PARAMS = -32602
    INTERNAL_ERROR = -32603

    # A2A specific error codes (SLA and availability)
    TIMEOUT = -32000
    AGENT_UNAVAILABLE = -32001
    FORBIDDEN = -32002

    # Domain-specific error codes (Agent Gourmet)
    RECIPE_NOT_FOUND = -32010

    def __init__(self, code: int, message: str, data: dict | None = None) -> None:
        self.code = code
        self.message = message
        self.data = data
        super().__init__(f"{code}: {message}")
