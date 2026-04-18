import pytest
from src.common.exceptions import A2ARPCError

def test_a2a_rpc_error_initialization():
    """Test that A2ARPCError initializes with correct fields."""
    error = A2ARPCError(code=-32000, message="Timeout occurring", data={"detail": "Network lag"})
    assert error.code == -32000
    assert error.message == "Timeout occurring"
    assert error.data == {"detail": "Network lag"}

def test_a2a_rpc_error_default_data():
    """Test that A2ARPCError has None as default data."""
    error = A2ARPCError(code=-32603, message="Internal error")
    assert error.data is None

def test_a2a_rpc_error_inheritance():
    """Test that A2ARPCError inherits from Exception."""
    error = A2ARPCError(code=0, message="Test")
    assert isinstance(error, Exception)
