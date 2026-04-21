import asyncio
import httpx
from common.tracing import setup_tracing, instrument_client
from opentelemetry import trace

async def test_tracing():
    print("--- Initializing Tracing (Console Export) ---")
    setup_tracing("test-service")
    instrument_client()
    
    tracer = trace.get_tracer(__name__)
    
    with tracer.start_as_current_span("parent-span") as parent:
        print("Inside parent span")
        async with httpx.AsyncClient() as client:
            print("Making HTTP request (should trigger a child span)...")
            try:
                # Use a local or non-existent URL just to see the span
                await client.get("http://localhost:8000/health")
            except Exception:
                pass
    
    print("--- Tracing Test Complete ---")
    print("Check the console output above for JSON spans.")

if __name__ == "__main__":
    asyncio.run(test_tracing())
