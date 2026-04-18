import pytest
from pydantic import ValidationError
from common.schemas import JsonRpcRequest, JsonRpcResponse, JsonRpcError, RequestContext

def test_json_rpc_request_valid():
    """Test valid JsonRpcRequest."""
    data = {
        "jsonrpc": "2.0",
        "method": "get_info",
        "params": {"id": 123},
        "id": "req-1"
    }
    request = JsonRpcRequest(**data)
    assert request.method == "get_info"
    assert request.id == "req-1"

def test_json_rpc_request_strict():
    """Test that JsonRpcRequest is strict (rejects extra fields)."""
    data = {
        "jsonrpc": "2.0",
        "method": "get_info",
        "params": {"id": 123},
        "id": "req-1",
        "extra": "invalid"
    }
    with pytest.raises(ValidationError):
        JsonRpcRequest(**data)

def test_request_context_valid():
    """Test valid RequestContext."""
    ctx = RequestContext(
        family_id="fam-1",
        user_id="user-1",
        correlation_id="corr-1"
    )
    assert ctx.family_id == "fam-1"
    assert ctx.language == "fr"  # Default value

def test_json_rpc_response_success():
    """Test successful JsonRpcResponse."""
    data = {
        "jsonrpc": "2.0",
        "result": {"status": "ok"},
        "id": "req-1"
    }
    response = JsonRpcResponse(**data)
    assert response.result == {"status": "ok"}
    assert response.error is None

def test_json_rpc_error_valid():
    """Test JsonRpcError schema."""
    data = {"code": -32600, "message": "Invalid Request"}
    error = JsonRpcError(**data)
    assert error.code == -32600
