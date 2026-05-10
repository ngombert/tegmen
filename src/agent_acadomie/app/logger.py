import json
import logging
import sys
import re
from datetime import datetime, timezone
from typing import Any

from agent_acadomie.app.context import get_correlation_id

# Regex patterns for PII redaction
PII_PATTERNS = [
    re.compile(r"fam-[a-zA-Z0-9_-]+"),
    re.compile(r"student-[a-zA-Z0-9_-]+"),
    re.compile(r"parent-[a-zA-Z0-9_-]+")
]


class JSONFormatter(logging.Formatter):
    """
    Custom logging formatter that outputs records as JSON strings.
    """

    def _redact_pii(self, text: str) -> str:
        """Redact PII patterns from text."""
        if not text:
            return text
        for pattern in PII_PATTERNS:
            text = pattern.sub("***", text)
        return text

    def format(self, record: logging.LogRecord) -> str:
        # Basic log info
        message = self._redact_pii(record.getMessage())
        
        log_entry: dict[str, Any] = {
            "timestamp": datetime.fromtimestamp(record.created, tz=timezone.utc).isoformat(),
            "level": record.levelname,
            "service": "acadomie",
            "name": record.name,
            "message": message,
        }

        # Inject correlation_id from context
        try:
            cid = get_correlation_id()
            if cid:
                log_entry["correlation_id"] = cid
        except Exception:
            pass

        # Include exception info if present
        if record.exc_info:
            log_entry["exception"] = self._redact_pii(self.formatException(record.exc_info))

        return json.dumps(log_entry)


def setup_acadomie_logger(name: str, level: int = logging.INFO) -> logging.Logger:
    """
    Setup a local logger for Acadomie with JSON formatting.
    This logger is independent of the common logger to avoid regressions.
    """
    logger = logging.getLogger(name)
    
    # Avoid duplicate handlers if already configured
    if not logger.handlers:
        logger.setLevel(level)
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(JSONFormatter())
        logger.addHandler(handler)
        
    return logger
