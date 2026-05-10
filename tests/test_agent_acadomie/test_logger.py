import json
import logging
from agent_acadomie.app.logger import JSONFormatter
from agent_acadomie.app.context import set_correlation_id, reset_correlation_id

def test_json_formatter_basic():
    """Test basic JSON logging structure."""
    formatter = JSONFormatter()
    record = logging.LogRecord(
        name="test_logger",
        level=logging.INFO,
        pathname="",
        lineno=0,
        msg="A simple message",
        args=(),
        exc_info=None
    )
    
    output = formatter.format(record)
    data = json.loads(output)
    
    assert data["level"] == "INFO"
    assert data["name"] == "test_logger"
    assert data["message"] == "A simple message"
    assert data["service"] == "acadomie"
    assert "timestamp" in data

def test_json_formatter_correlation_id():
    """Test propagation of correlation ID into logs."""
    token = set_correlation_id("test-corr-123")
    try:
        formatter = JSONFormatter()
        record = logging.LogRecord(
            name="test_logger",
            level=logging.INFO,
            pathname="",
            lineno=0,
            msg="Message with context",
            args=(),
            exc_info=None
        )
        
        output = formatter.format(record)
        data = json.loads(output)
        
        assert data["correlation_id"] == "test-corr-123"
    finally:
        reset_correlation_id(token)

def test_json_formatter_pii_redaction():
    """Test redaction of sensitive PII data."""
    formatter = JSONFormatter()
    
    # Test message with various PII
    msg = "Request failed for family fam-987 with student student-456 and parent-xyz"
    record = logging.LogRecord(
        name="test_logger",
        level=logging.ERROR,
        pathname="",
        lineno=0,
        msg=msg,
        args=(),
        exc_info=None
    )
    
    output = formatter.format(record)
    data = json.loads(output)
    
    # Assert redaction
    assert "fam-987" not in data["message"]
    assert "student-456" not in data["message"]
    assert "parent-xyz" not in data["message"]
    
    # Assert they are replaced by ***
    expected_msg = "Request failed for family *** with student *** and ***"
    assert data["message"] == expected_msg

def test_json_formatter_exception_pii_redaction():
    """Test redaction of PII in exception traces."""
    formatter = JSONFormatter()
    
    try:
        raise ValueError("Invalid student ID: student-forbidden")
    except ValueError as e:
        import sys
        exc_info = sys.exc_info()
        
    record = logging.LogRecord(
        name="test_logger",
        level=logging.ERROR,
        pathname="",
        lineno=0,
        msg="An error occurred",
        args=(),
        exc_info=exc_info
    )
    
    output = formatter.format(record)
    data = json.loads(output)
    
    assert "exception" in data
    assert "student-forbidden" not in data["exception"]
    assert "***" in data["exception"]
