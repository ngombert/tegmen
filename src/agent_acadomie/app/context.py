"""Request-scoped context for observability (correlation_id, trace_id)."""

import contextvars
from common.config import config

# Context variable for correlation_id, scoped to the current async context
_correlation_id_var: contextvars.ContextVar[str | None] = contextvars.ContextVar(
    "acadomie_correlation_id", default=None
)


def set_correlation_id(cid: str | None) -> contextvars.Token[str | None]:
    """Store correlation_id in the current async context and return a token."""
    return _correlation_id_var.set(cid)

def reset_correlation_id(token: contextvars.Token[str | None]) -> None:
    """Reset correlation_id to its previous value using a token."""
    _correlation_id_var.reset(token)


def get_correlation_id() -> str | None:
    """Retrieve correlation_id from the current async context."""
    return _correlation_id_var.get()


def get_current_trace_id() -> str | None:
    """Extract trace_id from the active OpenTelemetry span (hex, 32 chars).

    Returns None if OTEL is disabled or no valid span is active.
    """
    if not getattr(config, "OTEL_ENABLED", False):
        return None

    try:
        from opentelemetry import trace

        span = trace.get_current_span()
        ctx = span.get_span_context()
        if ctx and ctx.is_valid:
            # trace_id is an integer, format as 32-char hex string
            return format(ctx.trace_id, "032x")
    except (ImportError, Exception):
        # Graceful fallback if opentelemetry is not installed or any error occurs
        pass
    return None


def enrich_error_data(data: dict | None) -> dict:
    """Add correlation_id and trace_id to an error's data dict.

    Returns a new dict (never mutates the input).
    """
    enriched = dict(data) if data else {}

    cid = get_correlation_id()
    if cid:
        enriched["correlation_id"] = cid

    tid = get_current_trace_id()
    if tid:
        enriched["trace_id"] = tid

    return enriched
