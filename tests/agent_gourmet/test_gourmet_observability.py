import pytest
from fastapi.testclient import TestClient
from agent_gourmet.main import app
from unittest.mock import MagicMock, patch
import logging

@pytest.fixture
def client():
    return TestClient(app)

def test_correlation_id_in_logs(client, caplog):
    """AC1 & AC4: Test that correlation_id is extracted and appears in logs."""
    caplog.set_level(logging.INFO)
    
    payload = {
        "jsonrpc": "2.0",
        "method": "search_recipes",
        "params": {
            "query": "carbonara",
            "context": {"correlation_id": "test-log-cid-123"}
        },
        "id": "1"
    }
    
    response = client.post("/a2a/SendMessage", json=payload)
    assert response.status_code == 200
    
    # Check if the correlation_id appears in the logs
    assert "test-log-cid-123" in caplog.text
    assert "A2A | search_recipes" in caplog.text

def test_correlation_id_in_error_response(client):
    """AC2: Test that correlation_id is included in the error data."""
    payload = {
        "jsonrpc": "2.0",
        "method": "get_recipe_details",
        "params": {
            "recipe_id": "999", # Non-existent
            "context": {"correlation_id": "test-err-cid-456"}
        },
        "id": "2"
    }
    
    response = client.post("/a2a/SendMessage", json=payload)
    data = response.json()
    
    assert "error" in data
    assert data["error"]["code"] == -32010 # RECIPE_NOT_FOUND
    assert data["error"]["data"]["correlation_id"] == "test-err-cid-456"

from opentelemetry.trace import SpanContext, TraceFlags

def _mock_otel_span(trace_id: int):
    """Create a mock OTel span with a known trace_id."""
    span_context = SpanContext(
        trace_id=trace_id,
        span_id=0x1234567890ABCDEF,
        is_remote=False,
        trace_flags=TraceFlags.SAMPLED,
    )

    span = MagicMock()
    span.get_span_context.return_value = span_context
    return span

def test_trace_id_in_error_when_otel_enabled(client, monkeypatch):
    """AC3: Test that trace_id is included in error when OTel is enabled."""
    # Enable OTel via config
    monkeypatch.setattr("common.config.config.OTEL_ENABLED", True)
    
    known_trace_id = 0xABCDEF1234567890ABCDEF1234567890
    mock_span = _mock_otel_span(known_trace_id)
    
    with patch("opentelemetry.trace.get_current_span", return_value=mock_span):
        payload = {
            "jsonrpc": "2.0",
            "method": "get_recipe_details",
            "params": {
                "recipe_id": "999",
                "context": {"correlation_id": "test-otel-cid"}
            },
            "id": "3"
        }
        response = client.post("/a2a/SendMessage", json=payload)
        data = response.json()
        
        assert "error" in data
        assert data["error"]["data"]["trace_id"] == format(known_trace_id, "032x")
        assert data["error"]["data"]["correlation_id"] == "test-otel-cid"

def test_trace_id_absent_when_otel_disabled(client, monkeypatch):
    """AC3: Test that trace_id is NOT included in error when OTel is disabled."""
    monkeypatch.setattr("common.config.config.OTEL_ENABLED", False)
    
    payload = {
        "jsonrpc": "2.0",
        "method": "get_recipe_details",
        "params": {
            "recipe_id": "999"
        },
        "id": "4"
    }
    response = client.post("/a2a/SendMessage", json=payload)
    data = response.json()
    
    assert "error" in data
    assert "trace_id" not in data["error"]["data"]

def test_correlation_id_absent_when_no_context(client):
    """AC4: Test that system works normally without context."""
    payload = {
        "jsonrpc": "2.0",
        "method": "get_recipe_details",
        "params": {
            "recipe_id": "999"
        },
        "id": "5"
    }
    response = client.post("/a2a/SendMessage", json=payload)
    data = response.json()
    
    assert "error" in data
    assert "correlation_id" not in data["error"]["data"]
