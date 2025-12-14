"""Integration test for A2A communication."""

import httpx
import asyncio
import sys

MAESTRO_URL = "http://localhost:8000"
GOURMET_URL = "http://localhost:8001"


async def test_maestro_gourmet_flow():
    print("⏳ Waiting for health checks...")

    async with httpx.AsyncClient(timeout=10.0) as client:
        # Check Maestro Health
        try:
            resp = await client.get(f"{MAESTRO_URL}/health")
            if resp.status_code == 200:
                print("✅ Maestro is UP")
            else:
                print(f"❌ Maestro health failed: {resp.status_code}")
                return
        except Exception as e:
            print(f"❌ Maestro connection failed: {e}")
            return

        # Check Gourmet Agent Card
        try:
            resp = await client.get(f"{GOURMET_URL}/.well-known/agent-card.json")
            if resp.status_code == 200:
                print("✅ Gourmet is UP and exposing Agent Card")
            else:
                print(f"❌ Gourmet agent card failed: {resp.status_code}")
                return
        except Exception as e:
            print(f"❌ Gourmet connection failed: {e}")
            return

        print("\n🚀 Testing Chat Flow: Maestro -> Gourmet (A2A)")

        # Scenario: User asks for pasta recipe
        payload = {
            "message": "Je veux une recette de pâtes carbonara",
            "session_id": "test-session-123",
        }

        print(f"   Sending: '{payload['message']}'")
        try:
            resp = await client.post(f"{MAESTRO_URL}/chat", json=payload, timeout=30.0)
            if resp.status_code == 200:
                data = resp.json()
                print(f"   Response Status: {resp.status_code}")
                print(f"   Agent Used: {data.get('agent')}")
                print(f"   Route: {data.get('route')}")
                print(f"   Message: {data.get('message')}")

                # Assertions
                if data.get("route") == "gourmet":
                    print("✅ Routing correct: 'gourmet'")
                else:
                    print(
                        f"❌ Routing failed: expected 'gourmet', got '{data.get('route')}'"
                    )

                if "carbonara" in data.get("message", "").lower():
                    print("✅ Response content relevant (mentions carbonara)")
                else:
                    print("⚠️ Response might not be specific enough (check logs)")
            else:
                print(f"❌ Chat request failed: {resp.status_code} - {resp.text}")

        except Exception as e:
            print(f"❌ Chat request error: {e}")


if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(test_maestro_gourmet_flow())
