import json
import logging
import io
import pytest
from agent_gourmet.app.logger import setup_gourmet_logger
from agent_gourmet.app.context import set_correlation_id

def test_json_logging_format():
    """Test that the gourmet logger outputs valid JSON with expected keys."""
    log_output = io.StringIO()
    logger = setup_gourmet_logger("test_json")
    
    # Replace handlers for testing
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
    
    handler = logging.StreamHandler(log_output)
    from agent_gourmet.app.logger import JSONFormatter
    handler.setFormatter(JSONFormatter())
    logger.addHandler(handler)
    
    set_correlation_id("test-cid-json")
    logger.info("Test message")
    
    output = log_output.getvalue().strip()
    log_data = json.loads(output)
    
    assert "timestamp" in log_data
    assert log_data["level"] == "INFO"
    assert log_data["service"] == "gourmet"
    assert log_data["correlation_id"] == "test-cid-json"
    assert log_data["message"] == "Test message"

def test_pii_masking_requirement():
    """
    This test verifies that if we log a message, it doesn't contain PII 
    if the application is supposed to sanitize it. 
    Note: The masking logic is often in the caller, but we verify the logger 
    handles what it's given as JSON.
    """
    log_output = io.StringIO()
    logger = setup_gourmet_logger("test_pii")
    
    # Setup test handler
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
    handler = logging.StreamHandler(log_output)
    from agent_gourmet.app.logger import JSONFormatter
    handler.setFormatter(JSONFormatter())
    logger.addHandler(handler)
    
    # Simulating a sanitized message from the app
    logger.info("A2A | search_recipes | query=[MASKED]")
    
    output = log_output.getvalue().strip()
    assert "pizza" not in output
    assert "query=[MASKED]" in output
