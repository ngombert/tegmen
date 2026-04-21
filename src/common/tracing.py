"""OpenTelemetry tracing utility for Tegmen."""

import os
from typing import Optional
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import (
    BatchSpanProcessor,
    ConsoleSpanExporter,
)
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
from opentelemetry.propagate import set_global_textmap
from opentelemetry.trace.propagation.tracecontext import TraceContextTextMapPropagator

def setup_tracing(service_name: str, otlp_endpoint: Optional[str] = None) -> TracerProvider:
    """
    Setup OpenTelemetry tracing for a service.
    
    Args:
        service_name: Name of the service (e.g., 'agent-maestro')
        otlp_endpoint: Optional OTLP collector endpoint (e.g., 'http://localhost:4317')
    """
    # Create resource with service name
    resource = Resource.create({"service.name": service_name})
    
    # Initialize provider
    provider = TracerProvider(resource=resource)
    
    # Configure exporter (Console as requested, OTLP as fallback)
    if otlp_endpoint:
        exporter = OTLPSpanExporter(endpoint=otlp_endpoint, insecure=True)
    else:
        # Default to console for validation as requested by user
        exporter = ConsoleSpanExporter()
        
    # Add processor
    processor = BatchSpanProcessor(exporter)
    provider.add_span_processor(processor)
    
    # Set global provider
    trace.set_tracer_provider(provider)
    
    # Set global propagator (W3C Trace Context)
    set_global_textmap(TraceContextTextMapPropagator())
    
    return provider

def instrument_app(app):
    """Instrument a FastAPI application."""
    FastAPIInstrumentor.instrument_app(app)

def instrument_client():
    """
    Instrument HTTPX client globally.
    Spans will be automatically generated for all httpx requests.
    """
    HTTPXClientInstrumentor().instrument()
