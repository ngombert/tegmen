import uuid
from typing import Any, Optional

def format_a2a_message(text: str, context_id: Optional[str] = None, role: str = "agent") -> dict[str, Any]:
    """
    Standardizes the formatting of A2A messages to ensure compatibility with the A2A SDK.
    This helper ensures that 'Lean' agents return the exact structure expected by Maestro.
    """
    return {
        "messageId": str(uuid.uuid4()),
        "role": role,
        "parts": [{"text": text}],
        "contextId": context_id
    }
