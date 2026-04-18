import re
from common.logger import setup_logger

logger = setup_logger("privacy")

# Regex for common PII patterns
EMAIL_PATTERN = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
# Simple French phone number pattern (supports spaces, dots, dashes, +33)
PHONE_PATTERN = r'(\+33|0)[1-9]([\s\.\-]?\d{2}){4}'

def sanitize_message(message: str) -> str:
    """
    Sanitize a message by masking sensitive PII data.
    """
    if not message:
        return message
    
    original_message = message
    
    # Mask Emails
    message = re.sub(EMAIL_PATTERN, "[EMAIL]", message)
    
    # Mask Phone Numbers
    message = re.sub(PHONE_PATTERN, "[PHONE]", message)
    
    if message != original_message:
        logger.info("PII detected and masked in message.")
        
    return message

def log_audit_trail(event_type: str, user_id: str, family_id: str, extra: dict = None):
    """
    Log an audit event for traceability.
    """
    audit_data = {
        "event": event_type,
        "user_id": user_id,
        "family_id": family_id,
        "timestamp": "auto", # Logger usually handles this
    }
    if extra:
        audit_data.update(extra)
        
    logger.info(f"AUDIT | {audit_data}")
