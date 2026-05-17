Tu es l'Edge Case Hunter. Utilise le skill `bmad-review-edge-case-hunter` pour inspecter chaque branche de condition et limite dans ce diff. Tu as accès en lecture au projet pour comprendre le contexte si nécessaire. Rapporte uniquement les cas limites non gérés (edge cases).

Diff à analyser :
```diff
diff --git a/src/agent_gourmet/app/api/routers/a2a.py b/src/agent_gourmet/app/api/routers/a2a.py
index 903be9a..3255f3b 100644
--- a/src/agent_gourmet/app/api/routers/a2a.py
+++ b/src/agent_gourmet/app/api/routers/a2a.py
@@ -5,6 +5,7 @@ from pydantic import ValidationError
 
 from agent_gourmet.app.logger import setup_gourmet_logger
 from agent_gourmet.app.services.recipe_service import RecipeService
+from agent_gourmet.app.services.llm_service import LLMService
 from agent_gourmet.app.schemas.recipe import SearchRequest, RecipeDetailRequest, RecipeDetailResponse
 from common.exceptions import A2ARPCError
 from common.a2a_utils import format_a2a_message
@@ -16,6 +17,7 @@ from agent_gourmet.app.context import (
 
 logger = setup_gourmet_logger("gourmet_a2a")
 recipe_service = RecipeService()
+llm_service = LLMService()
 
 def with_context(func: Callable) -> Callable:
     @wraps(func)
@@ -100,21 +102,13 @@ async def handle_message_send(params: dict[str, Any] | None) -> dict[str, Any]:
     if not text:
         return format_a2a_message("Je n'ai pas bien compris votre message. Que cherchez-vous ?", context_id)
     
-    # Simple keyword-based dispatch for Lean Gourmet
-    if any(k in text for k in ["recette", "cherche", "propose", "manger"]):
-        # Very simple heuristic
-        query = text.replace("recette de", "").replace("cherche", "").replace("je veux", "").strip()
-        
-        request = SearchRequest(query=query)
-        response = await recipe_service.search_recipes(request)
-        
-        if response.total_count == 0:
-            return format_a2a_message(f"Désolé, je n'ai pas trouvé de recette pour '{query}'.", context_id)
-        
-        res_list = [r.name for r in response.results[:3]]
-        return format_a2a_message(f"Voici ce que j'ai trouvé : {', '.join(res_list)}. Laquelle vous intéresse ?", context_id)
-    
-    return format_a2a_message("Je suis l'agent Gourmet. Je peux vous aider à trouver des recettes. Que cherchez-vous ?", context_id)
+    # Use LLM to generate the response (Story 6.6)
+    try:
+        response_text = await llm_service.generate_response(text)
+        return format_a2a_message(response_text, context_id)
+    except Exception as e:
+        logger.error(f"Error calling LLM in handle_message_send: {e}")
+        return format_a2a_message("Désolé, je rencontre une difficulté pour vous répondre actuellement.", context_id)
 
 # Methods mapping for A2AServer registration
 GOURMET_METHODS = {
diff --git a/src/common/config.py b/src/common/config.py
index 8e08f47..a9e8562 100644
--- a/src/common/config.py
+++ b/src/common/config.py
@@ -15,6 +15,13 @@ class Settings:
     DEFAULT_MODEL: str = os.getenv(
         "DEFAULT_MODEL", "openrouter/google/gemini-2.0-flash-001"
     )
+    LLM_DEFAULT_MODEL: str = os.getenv(
+        "LLM_DEFAULT_MODEL", DEFAULT_MODEL
+    )
+
+    # OpenAI Configuration
+    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
+
 
     # Database Configuration
     DATABASE_URL: str = os.getenv(
@@ -40,7 +47,8 @@ class Settings:
 
     # Agent URLs (A2A Communication)
     MAESTRO_URL: str = os.getenv("MAESTRO_URL", "http://localhost:8000")
-    DEFAULT_A2A_TIMEOUT: float = float(os.getenv("DEFAULT_A2A_TIMEOUT", "5.0"))
+    DEFAULT_A2A_TIMEOUT: float = float(os.getenv("DEFAULT_A2A_TIMEOUT", "30.0"))
+
 
     # Gourmet Resilience Configuration
     GOURMET_PERSISTENCE_TIMEOUT_MS: int = int(os.getenv("GOURMET_PERSISTENCE_TIMEOUT_MS", "3000"))
diff --git a/tests/agent_gourmet/test_gourmet_a2a.py b/tests/agent_gourmet/test_gourmet_a2a.py
index 737e7a7..a4255b5 100644
--- a/tests/agent_gourmet/test_gourmet_a2a.py
+++ b/tests/agent_gourmet/test_gourmet_a2a.py
@@ -1,6 +1,7 @@
 import pytest
 from fastapi.testclient import TestClient
 from agent_gourmet.main import app
+from unittest.mock import patch, AsyncMock
 
 @pytest.fixture
 def client():
@@ -13,8 +14,11 @@ def test_a2a_agent_card(client):
     assert data["name"] == "agent_gourmet"
     assert "search_recipes" in str(data["skills"])
 
-def test_a2a_send_message_search(client):
-    # Test message/send dispatching to search_recipes
+@patch("agent_gourmet.app.api.routers.a2a.llm_service.generate_response", new_callable=AsyncMock)
+def test_a2a_send_message_search(mock_generate, client):
+    # Test message/send using LLM
+    mock_generate.return_value = "Voici une délicieuse recette de carbonara."
+    
     payload = {
         "jsonrpc": "2.0",
         "method": "message/send",
```
