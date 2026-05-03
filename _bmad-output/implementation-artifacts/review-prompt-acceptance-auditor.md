Tu es un Acceptance Auditor. Revois ce diff par rapport aux spécifications et documents de contexte fournis.
Vérifie : les violations des critères d'acceptation, les écarts par rapport à l'intention des specs, les comportements spécifiés manquants, et les contradictions entre les contraintes des specs et le code réel.
Produis tes résultats sous forme de liste Markdown. Pour chaque point : un titre sur une ligne, l'AC/contrainte violé(e), et la preuve tirée du diff.

--- SPECS ---
# Epic 5: Gestion de Session et Routage Contextuel (Maestro)

## Vision
Transformer le Gateway Maestro d'un routeur "one-shot" vers un orchestrateur capable de maintenir un dialogue cohérent. L'objectif est d'éviter que l'utilisateur n'ait à repréciser son intention à chaque message au sein d'une même session.

## Objectifs Métier
- Améliorer l'expérience utilisateur en gérant la continuité du dialogue.
- Éviter les collisions sémantiques lors de réponses courtes (ex: "oui", "Italie", "plus de détails").
- Maintenir une architecture légère sans base de données externe pour le MVP.

## Architecture Technique
- **Stockage:** Cache en mémoire vive (In-Memory) au sein du processus Maestro.
- **Identifiant:** Utilisation du `session_id` (ou `id` JSON-RPC) pour mapper l'état.
- **Logique de Routage:** 
    1. Si un agent est actif en session et que le score de l'intention actuelle est ambigu, privilégier l'agent actif.
    2. Si l'intention est radicalement différente (score > 0.9 pour un autre agent), changer d'agent.

## User Stories

### Story 5.1: Cache Mémoire et SessionStore
**Description:** Implémenter un `SessionStore` asynchrone utilisant un dictionnaire Python avec TTL (Time To Live).
- **AC 1:** Maestro peut stocker le dernier `agent_id` utilisé pour un `session_id`.
- **AC 2:** Les données expirent automatiquement après 10 minutes d'inactivité.
- **AC 3:** L'implémentation est abstraite via une interface pour permettre un passage futur à Redis.

### Story 5.2: Sticky Routing (Affinité d'Agent)
**Description:** Modifier la logique de `route_request` pour consulter le `SessionStore`.
- **AC 1:** Si un agent est actif, Maestro tente d'abord de router vers lui.
- **AC 2:** Implémentation d'un bonus de score contextuel (+30%) pour l'agent en cours lors de la classification.
- **AC 3:** La réponse de l'agent met à jour le TTL de la session.

### Story 5.3: Commandes d'Évasion et Reset
**Description:** Permettre à l'utilisateur de sortir explicitement d'un flux.
- **AC 1:** Mots-clés réservés ("stop", "annule", "reset", "quitter") réinitialisent la session.
- **AC 2:** Si le routeur sémantique détecte une intention forte (Top score > 0.95) pour un autre agent, le verrouillage est brisé.

## Critères d'Acceptation Globaux
- Le test E2E `test_e2e_golden_path.py` doit pouvoir être étendu pour valider une conversation en 2 étapes (Question -> Réponse contextuelle).
- Zéro impact sur les performances de Maestro (latence ajoutée < 5ms).
# Story 5.1: Cache Mémoire et SessionStore

## Story Foundation
**Description:** Implémenter un `SessionStore` asynchrone utilisant un dictionnaire Python avec TTL (Time To Live).

### Acceptance Criteria
- **AC 1:** Maestro peut stocker le dernier `agent_id` utilisé pour un `session_id`.
- **AC 2:** Les données expirent automatiquement après 10 minutes d'inactivité.
- **AC 3:** L'implémentation est abstraite via une interface pour permettre un passage futur à Redis.

## Developer Context

### Technical Requirements
- Le `SessionStore` doit être défini dans le microservice Maestro (`src/agent_maestro`).
- Il doit proposer une interface abstraite (`BaseSessionStore`) et une implémentation concrète en mémoire (`InMemorySessionStore`).
- Méthodes requises : `get(session_id)`, `set(session_id, agent_id)`, `delete(session_id)`.
- Gestion asynchrone stricte : toutes les méthodes I/O doivent être des coroutines `async`.

### Architecture Compliance
- Pydantic v2 pour d'éventuels schémas de données si nécessaire, bien qu'un simple dict avec un timestamp pour la péremption suffise.
- Pas de tâches de fond bloquantes (`time.sleep()`).
- Zéro exception silencieuse (Fail-Fast).
- Utilisation de `asyncio` pour toute opération I/O éventuelle.

### File Structure Requirements
- `src/agent_maestro/session.py` : Contiendra l'interface abstraite et l'implémentation `InMemorySessionStore`.

### Testing Requirements
- Tests unitaires dans `tests/test_maestro_session.py`.
- L'asynchronisme doit être testé avec `pytest.mark.asyncio`.
- Le fonctionnement du TTL doit être testé (par exemple avec `freezegun` ou via des mocks du module `time`).

### Project Context Reference
- Respect strict de Python >=3.13, typage explicite (`mypy` compatible), format `snake_case` pour les méthodes.

## Status
Status: ready-for-dev
# Story 5.2: Sticky Routing (Affinité d'Agent)

## Story Foundation
**Description:** Modifier la logique de routage dans `route_request` (et idéalement `classify_intent`) pour consulter le `SessionStore`.

### Acceptance Criteria
- **AC 1:** Si une session active pointe vers un agent, Maestro priorise ou influence le routage vers cet agent.
- **AC 2:** Implémentation d'un bonus de score contextuel (+30% soit +0.3) pour l'agent en cours lors de la classification de l'intention.
- **AC 3:** Chaque interaction réussie avec un agent met à jour ou initie le TTL de la session avec cet agent.

## Developer Context

### Technical Requirements
- Le composant `InMemorySessionStore` développé lors de la Story 5.1 doit être instancié de manière globale (singleton) dans `main.py` (ou géré via une dépendance FastAPI). 
- Le endpoint `route_request` (A2A gateway) reçoit un `session_id`. JSON-RPC 2.0 transmet généralement un `id` qui peut servir d'identifiant de session ou, mieux encore, on peut utiliser le `context.correlation_id` ou un paramètre explicite passé par le client pour identifier la "session" (dans notre cas, utiliser `context.correlation_id` comme `session_id` par défaut s'il n'y a pas d'autre clé, ou utiliser un champ "session_id" ajouté dans `request.params` si on veut un suivi strict).
- **Routage :** Dans `classify_intent` (ou en l'enveloppant), si l'agent actif est récupéré, ajouter +0.3 à son score s'il fait partie des scores évalués.
- Mise à jour du store : Une fois qu'un agent (A) a été appelé avec succès, faire `await store.set(session_id, A)`.

### Architecture Compliance
- Utiliser l'injection de dépendances de FastAPI pour injecter le `SessionStore` ou l'initialiser proprement au démarrage (`lifespan`).
- Ne pas casser le fallback "unknown" ni "chitchat".

### File Structure Requirements
- `src/agent_maestro/main.py` : Instancier le store, modifier `route_request` et `chat` pour interagir avec le store.
- `src/agent_maestro/router.py` : Adapter `classify_intent` ou créer une nouvelle fonction `classify_intent_with_context` prenant l'agent actif en paramètre.

### Testing Requirements
- Mettre à jour ou ajouter de nouveaux tests unitaires pour le routage.
- Utiliser `pytest`.

### Project Context Reference
- Asynchronisme strict.
- Attention aux imports croisés.

## Status
Status: ready-for-dev
# Story 5.3: Commandes d'Évasion et Reset

## Story Foundation
**Description:** Permettre à l'utilisateur de sortir explicitement d'un flux et de briser le "Sticky Routing".

### Acceptance Criteria
- **AC 1:** Des mots-clés réservés (ex: "stop", "annule", "reset", "quitter") permettent de réinitialiser la session (suppression du lien avec l'agent actif).
- **AC 2:** Si le routeur sémantique détecte une intention forte (Top score > 0.95) pour un autre agent, le verrouillage est brisé et la nouvelle intention l'emporte, effaçant ainsi l'ancienne session.

## Developer Context

### Technical Requirements
- Mots-clés réservés : Il faut intercepter ces mots (insensibles à la casse) avant même de faire passer la requête au routeur sémantique ou alors en faire une règle de pré-classification.
- Briser le verrouillage : Le score brut d'une autre intention (avant l'application du bonus de 1.3 à l'agent actif) doit être comparé à un seuil très élevé (`> 0.95`). Si un autre agent dépasse 0.95, il l'emporte quoiqu'il arrive et la session est mise à jour avec ce nouvel agent.

### Architecture Compliance
- Ne pas introduire de latence excessive.
- Continuer à utiliser `InMemorySessionStore`.
- Les mots-clés peuvent être gérés soit par une route spéciale dans `router.py`, soit par une simple vérification RegEx/liste dans `main.py` avant d'appeler `classify_intent`. La deuxième solution est souvent plus rapide pour des commandes d'évasion strictes.

### File Structure Requirements
- `src/agent_maestro/main.py` : Interception des mots-clés de reset pour effacer le cache (`await session_store.delete(session_id)`) et répondre ou continuer le flux.
- `src/agent_maestro/router.py` : Modifier `classify_intent` pour appliquer la règle du > 0.95 (Escape hatch sémantique).

### Testing Requirements
- Nouveaux tests pour valider que les mots-clés suppriment la session.
- Tests pour valider qu'un score très fort (ex: 0.96 pour "explorer") bat un agent actif ("gourmet") même avec son bonus.

## Status
Status: ready-for-dev


--- DIFF ---

diff --git a/src/agent_maestro/main.py b/src/agent_maestro/main.py
index 336bf0c..b518b9f 100644
--- a/src/agent_maestro/main.py
+++ b/src/agent_maestro/main.py
@@ -20,9 +20,12 @@ from common.users import get_user_profile
 from common.schemas import JsonRpcRequest, JsonRpcResponse, JsonRpcError, RequestContext
 from common.logger import setup_logger
 from common.tracing import setup_tracing, instrument_app, instrument_client
+from agent_maestro.session import InMemorySessionStore
 
 logger = setup_logger("maestro")
 
+session_store = InMemorySessionStore()
+
 
 # Initialized with Lean A2A standards
 
@@ -138,6 +141,10 @@ CLARIFICATION_TEMPLATE = (
     "(Si oui, soyez un peu plus précis dans votre demande !)"
 )
 
+# Escape commands to reset session
+ESCAPE_COMMANDS = {"stop", "annule", "annuler", "reset", "quitter", "exit", "arrete", "arrête"}
+ESCAPE_RESPONSE = "Compris, nous reprenons à zéro. Comment puis-je vous aider ?"
+
 from common.exceptions import A2ARPCError
 
 @app.get("/dev/token/{user_id}", tags=["Development"])
@@ -222,9 +229,13 @@ async def route_request(
     
     # Apply PII filter if message is present in params
     message = ""
-    if request.params and "message" in request.params:
-        message = sanitize_message(request.params["message"])
-        request.params["message"] = message
+    session_id = None
+    if request.params:
+        if "message" in request.params:
+            message = sanitize_message(request.params["message"])
+            request.params["message"] = message
+        if "session_id" in request.params:
+            session_id = request.params["session_id"]
         
     # Audit Trail
     log_audit_trail(
@@ -234,8 +245,21 @@ async def route_request(
         extra={"method": request.method, "rpc_id": str(request.id), "role": context.role}
     )
 
+    active_agent = await session_store.get(session_id) if session_id else None
+
+    # Escape commands check
+    if message and message.strip().lower() in ESCAPE_COMMANDS:
+        if session_id:
+            await session_store.delete(session_id)
+        logger.info("Escape command intercepted, session reset.")
+        return JsonRpcResponse(
+            jsonrpc="2.0",
+            result={"message": ESCAPE_RESPONSE, "agent": "maestro", "route": "chitchat"},
+            id=request.id
+        )
+
     # Classify intent
-    route, score = classify_intent(message) if message else ("unknown", 0.0)
+    route, score = classify_intent(message, active_agent) if message else ("unknown", 0.0)
     logger.info(f"🎯 Intent classified: route='{route}', score={score:.4f}")
 
     # RBAC Check
@@ -275,14 +299,18 @@ async def route_request(
         if route == "chitchat" and score >= THRESHOLD_ROUTING:
             response_text = random.choice(CHITCHAT_RESPONSES)
             agent_name = "maestro"
+            if session_id:
+                await session_store.set(session_id, "chitchat")
         elif score >= THRESHOLD_ROUTING:
             # High confidence -> Direct dispatch
             response_text = await call_remote_agent(
                 route=route,
                 message=message,
-                context_id=str(request.id),
+                context_id=session_id or str(request.id),
             )
             agent_name = f"agent_{route}"
+            if session_id:
+                await session_store.set(session_id, route)
         elif score >= THRESHOLD_CLARIFICATION:
             # Medium confidence -> Clarification
             agent_display = route.capitalize()
@@ -365,7 +393,20 @@ async def chat(
 
     # Step 1: Classify intent with semantic router
     logger.info(f"Processing message for {context.user_name}: '{sanitized_message}'")
-    route, score = classify_intent(sanitized_message)
+    active_agent = await session_store.get(session_id)
+    
+    # Escape commands check
+    if sanitized_message and sanitized_message.strip().lower() in ESCAPE_COMMANDS:
+        await session_store.delete(session_id)
+        logger.info("Escape command intercepted in legacy chat, session reset.")
+        return ChatResponse(
+            message=ESCAPE_RESPONSE,
+            agent="maestro",
+            session_id=session_id,
+            route="chitchat"
+        )
+        
+    route, score = classify_intent(sanitized_message, active_agent)
     logger.info(f"Routing decision: route='{route}', score={score:.4f}")
     
     # Step 1.5: RBAC Check
@@ -375,6 +416,7 @@ async def chat(
         if route == "chitchat" and score >= THRESHOLD_ROUTING:
             response_text = random.choice(CHITCHAT_RESPONSES)
             agent_name = "maestro"
+            await session_store.set(session_id, "chitchat")
         elif score >= THRESHOLD_ROUTING:
             # Step 2: Call remote specialized agent via A2A
             response_text = await call_remote_agent(
@@ -383,6 +425,7 @@ async def chat(
                 context_id=session_id,
             )
             agent_name = f"agent_{route}"
+            await session_store.set(session_id, route)
         elif score >= THRESHOLD_CLARIFICATION:
             # Clarification
             agent_display = route.capitalize()
diff --git a/src/agent_maestro/router.py b/src/agent_maestro/router.py
index df6f852..d06f111 100644
--- a/src/agent_maestro/router.py
+++ b/src/agent_maestro/router.py
@@ -73,12 +73,13 @@ def get_router() -> SemanticRouter:
 THRESHOLD_ROUTING = 0.40      # Full confidence (increased from 0.30)
 THRESHOLD_CLARIFICATION = 0.20 # Ambiguous (increased from 0.15)
 
-def classify_intent(message: str) -> tuple[str, float]:
+def classify_intent(message: str, active_agent: Optional[str] = None) -> tuple[str, float]:
     """
     Classify user intent using semantic similarity.
 
     Args:
         message: User message to classify
+        active_agent: Optional agent ID currently active in the session
 
     Returns:
         (Route name, similarity_score)
@@ -86,18 +87,37 @@ def classify_intent(message: str) -> tuple[str, float]:
     if not message:
         return ("unknown", 0.0)
         
-    router_inst = get_router()
-    # E5 optimization: queries should be prefixed with 'query: '
-    # However, it seems to cause issues with matching in this version of semantic-router.
-    # We use the raw message for now to ensure stability.
-    result = router_inst(message)
-    
-    route_name = result.name if result.name else "unknown"
-    score = getattr(result, "similarity_score", 0.0)
-    if score is None:
-        score = 0.0
-    
-    return (route_name, float(score))
+    if active_agent:
+        scores = get_all_scores(message)
+        if not scores:
+            return ("unknown", 0.0)
+            
+        # Normalize active_agent to route name (e.g. agent_gourmet -> gourmet)
+        active_route = active_agent[6:] if active_agent.startswith("agent_") else active_agent
+        
+        # Semantic Escape Hatch: if any intention is extremely strong (> 0.95), do not apply sticky routing
+        if max(scores.values()) > 0.95:
+            best_route = max(scores.items(), key=lambda x: x[1])
+            return best_route[0], float(best_route[1])
+        
+        # Apply bonus
+        if active_route in scores:
+            scores[active_route] = min(scores[active_route] * 1.3, 1.0)
+            
+        # Find the route with the highest score
+        best_route = max(scores.items(), key=lambda x: x[1])
+        return best_route[0], float(best_route[1])
+    else:
+        # Standard fast classification
+        router_inst = get_router()
+        result = router_inst(message)
+        
+        route_name = result.name if result.name else "unknown"
+        score = getattr(result, "similarity_score", 0.0)
+        if score is None:
+            score = 0.0
+        
+        return (route_name, float(score))
 
 def warmup() -> None:
     """Pre-load the embedding model and verify all routes are ready."""
diff --git a/src/agent_maestro/session.py b/src/agent_maestro/session.py
new file mode 100644
index 0000000..be520e2
--- /dev/null
+++ b/src/agent_maestro/session.py
@@ -0,0 +1,98 @@
+"""
+Session management for Maestro Gateway.
+Provides an abstract interface and an in-memory implementation for storing
+contextual session state (e.g., affinity to a specific agent).
+"""
+
+from abc import ABC, abstractmethod
+from typing import Optional, Dict, Tuple
+import time
+import asyncio
+
+from common.logger import setup_logger
+
+logger = setup_logger("maestro.session")
+
+
+class BaseSessionStore(ABC):
+    """
+    Abstract Base Class for Maestro Session Store.
+    Implementations must handle asynchronous operations and TTL expiration.
+    """
+
+    @abstractmethod
+    async def get(self, session_id: str) -> Optional[str]:
+        """
+        Retrieve the agent_id associated with a session_id.
+        Returns None if the session does not exist or has expired.
+        """
+        pass
+
+    @abstractmethod
+    async def set(self, session_id: str, agent_id: str) -> None:
+        """
+        Store the agent_id for a session_id, updating its TTL.
+        """
+        pass
+
+    @abstractmethod
+    async def delete(self, session_id: str) -> None:
+        """
+        Delete the session data for a given session_id.
+        """
+        pass
+
+
+class InMemorySessionStore(BaseSessionStore):
+    """
+    In-Memory implementation of BaseSessionStore using a dictionary.
+    Features lazy deletion for expired entries to avoid blocking background tasks.
+    """
+
+    def __init__(self, ttl_seconds: int = 600):
+        """
+        Initialize the in-memory session store.
+        
+        Args:
+            ttl_seconds: Time to live for a session in seconds (default: 10 minutes).
+        """
+        self.ttl_seconds = ttl_seconds
+        # store format: { session_id: (agent_id, expiry_timestamp) }
+        self._store: Dict[str, Tuple[str, float]] = {}
+        self._lock = asyncio.Lock()
+
+    async def get(self, session_id: str) -> Optional[str]:
+        """
+        Get the agent_id for a session_id. Performs lazy deletion if expired.
+        """
+        async with self._lock:
+            if session_id not in self._store:
+                return None
+            
+            agent_id, expiry_time = self._store[session_id]
+            
+            if time.time() > expiry_time:
+                # Expired -> Lazy deletion
+                del self._store[session_id]
+                logger.debug(f"Session {session_id} expired and was removed.")
+                return None
+                
+            return agent_id
+
+    async def set(self, session_id: str, agent_id: str) -> None:
+        """
+        Store the agent_id for a session_id with a new TTL.
+        """
+        expiry_time = time.time() + self.ttl_seconds
+        async with self._lock:
+            self._store[session_id] = (agent_id, expiry_time)
+            logger.debug(f"Session {session_id} set to agent '{agent_id}' (TTL: {self.ttl_seconds}s)")
+
+    async def delete(self, session_id: str) -> None:
+        """
+        Explicitly delete a session_id from the store.
+        """
+        async with self._lock:
+            if session_id in self._store:
+                del self._store[session_id]
+                logger.debug(f"Session {session_id} manually deleted.")
diff --git a/tests/test_maestro_escape_commands.py b/tests/test_maestro_escape_commands.py
new file mode 100644
index 0000000..e38f906
--- /dev/null
+++ b/tests/test_maestro_escape_commands.py
@@ -0,0 +1,77 @@
+import pytest
+from unittest.mock import patch, MagicMock
+from fastapi.testclient import TestClient
+
+from agent_maestro.main import app, session_store, ESCAPE_COMMANDS, ESCAPE_RESPONSE, get_request_context
+from common.auth import get_current_identity
+from common.schemas import JsonRpcRequest, RequestContext
+
+client = TestClient(app)
+
+@pytest.fixture(autouse=True)
+def override_dependencies():
+    def override_get_request_context():
+        return RequestContext(
+            family_id="fam1",
+            user_id="user1",
+            user_name="Test User",
+            role="parent",
+            correlation_id="corr-1",
+            preferences={},
+            restrictions=[]
+        )
+    
+    def override_get_current_identity():
+        return {"user_id": "user1", "family_id": "fam1"}
+        
+    app.dependency_overrides[get_request_context] = override_get_request_context
+    app.dependency_overrides[get_current_identity] = override_get_current_identity
+    yield
+    app.dependency_overrides.clear()
+
+@pytest.mark.asyncio
+async def test_escape_commands_intercepted_and_session_cleared():
+    session_id = "test_escape_sess"
+    
+    # 1. Set an active session manually
+    await session_store.set(session_id, "agent_gourmet")
+    assert await session_store.get(session_id) == "agent_gourmet"
+    
+    # 2. Send an escape command
+    request_data = {
+        "jsonrpc": "2.0",
+        "method": "message/send",
+        "params": {
+            "message": "stop",
+            "session_id": session_id
+        },
+        "id": "req-1"
+    }
+    
+    response = client.post("/api/v1/routing", json=request_data)
+    
+    # 3. Check response
+    assert response.status_code == 200
+    res_data = response.json()
+    assert res_data["result"]["message"] == ESCAPE_RESPONSE
+    assert res_data["result"]["route"] == "chitchat"
+    
+    # 4. Check that session was cleared
+    assert await session_store.get(session_id) is None
+
+@pytest.mark.asyncio
+async def test_all_escape_commands_recognized():
+    for cmd in ESCAPE_COMMANDS:
+        request_data = {
+            "jsonrpc": "2.0",
+            "method": "message/send",
+            "params": {
+                "message": f"  {cmd.upper()}  ", # test uppercase and spaces
+                "session_id": "any_sess"
+            },
+            "id": "req-1"
+        }
+        
+        response = client.post("/api/v1/routing", json=request_data)
+        assert response.status_code == 200
+        assert response.json()["result"]["message"] == ESCAPE_RESPONSE
diff --git a/tests/test_maestro_session.py b/tests/test_maestro_session.py
new file mode 100644
index 0000000..b0674c0
--- /dev/null
+++ b/tests/test_maestro_session.py
@@ -0,0 +1,92 @@
+import pytest
+import time
+import asyncio
+from typing import Optional
+
+from agent_maestro.session import InMemorySessionStore
+
+@pytest.mark.asyncio
+async def test_session_store_set_get():
+    """Test basic set and get operations."""
+    store = InMemorySessionStore(ttl_seconds=600)
+    session_id = "sess_123"
+    agent_id = "agent_gourmet"
+    
+    # Initially empty
+    assert await store.get(session_id) is None
+    
+    # Set and get
+    await store.set(session_id, agent_id)
+    assert await store.get(session_id) == agent_id
+
+@pytest.mark.asyncio
+async def test_session_store_delete():
+    """Test explicit deletion of a session."""
+    store = InMemorySessionStore(ttl_seconds=600)
+    session_id = "sess_456"
+    agent_id = "agent_explorer"
+    
+    await store.set(session_id, agent_id)
+    assert await store.get(session_id) == agent_id
+    
+    await store.delete(session_id)
+    assert await store.get(session_id) is None
+    
+    # Deleting a non-existent session should not raise an error
+    await store.delete("non_existent")
+
+@pytest.mark.asyncio
+async def test_session_store_ttl_lazy_deletion(monkeypatch):
+    """Test that TTL expiration causes lazy deletion."""
+    store = InMemorySessionStore(ttl_seconds=10)
+    session_id = "sess_ttl"
+    agent_id = "agent_acadomie"
+    
+    # Mock time to a fixed timestamp
+    current_time = 1000.0
+    
+    def mock_time():
+        return current_time
+        
+    monkeypatch.setattr(time, "time", mock_time)
+    
+    await store.set(session_id, agent_id)
+    
+    # Should be valid at current time
+    assert await store.get(session_id) == agent_id
+    
+    # Move time forward by 5 seconds (still valid)
+    current_time += 5.0
+    assert await store.get(session_id) == agent_id
+    
+    # Move time forward by another 6 seconds (total 11s -> expired)
+    current_time += 6.0
+    assert await store.get(session_id) is None
+    
+    # Verify it was removed from the internal dictionary
+    assert session_id not in store._store
+
+@pytest.mark.asyncio
+async def test_session_store_concurrency():
+    """Test that concurrent access is safe."""
+    store = InMemorySessionStore(ttl_seconds=600)
+    session_id = "sess_concurrent"
+    
+    async def worker(idx: int):
+        await store.set(session_id, f"agent_{idx}")
+        # Introduce a small yield to encourage context switching
+        await asyncio.sleep(0.01)
+        val = await store.get(session_id)
+        return val
+        
+    # Run multiple workers concurrently
+    tasks = [worker(i) for i in range(50)]
+    results = await asyncio.gather(*tasks)
+    
+    # The final state should be one of the agents
+    final_val = await store.get(session_id)
+    assert final_val is not None
+    assert final_val.startswith("agent_")
+    
+    # All tasks should have completed without errors
+    assert len(results) == 50
diff --git a/tests/test_maestro_sticky_routing.py b/tests/test_maestro_sticky_routing.py
new file mode 100644
index 0000000..adb90da
--- /dev/null
+++ b/tests/test_maestro_sticky_routing.py
@@ -0,0 +1,83 @@
+import pytest
+from unittest.mock import patch, MagicMock
+
+from agent_maestro.router import classify_intent, THRESHOLD_CLARIFICATION, THRESHOLD_ROUTING
+
+@patch("agent_maestro.router.get_router")
+def test_classify_intent_without_active_agent(mock_get_router):
+    mock_router = MagicMock()
+    mock_result = MagicMock()
+    mock_result.name = "gourmet"
+    mock_result.similarity_score = 0.45
+    mock_router.return_value = mock_result
+    mock_get_router.return_value = mock_router
+    
+    # Use a message that is somewhat ambiguous or scores generally
+    route, score = classify_intent("Je veux préparer à manger")
+    # It should classify as gourmet normally
+    assert route == "gourmet"
+    # The score should be greater than 0
+    assert score == 0.45
+
+@patch("agent_maestro.router.get_all_scores")
+def test_classify_intent_with_active_agent_bonus(mock_get_all_scores):
+    # Mock scores without bonus
+    mock_get_all_scores.return_value = {
+        "gourmet": 0.35, # just below routing threshold of 0.40
+        "acadomie": 0.10,
+        "chitchat": 0.25
+    }
+    
+    # 1. Without active agent, the best route should be 'gourmet', but with its original score 0.35
+    # Since we mocked get_all_scores but the original implementation of classify_intent 
+    # only calls get_all_scores when active_agent is provided, we must test the active_agent branch.
+    
+    # 2. With active agent 'gourmet', it gets a * 1.3 bonus.
+    # 0.35 * 1.3 = 0.455. It should become the top score and cross the routing threshold.
+    route, score = classify_intent("message bidon", active_agent="gourmet")
+    
+    assert route == "gourmet"
+    assert round(score, 3) == 0.455
+    
+@patch("agent_maestro.router.get_all_scores")
+def test_classify_intent_bonus_capped_at_1(mock_get_all_scores):
+    # Mock scores with a very high base score
+    mock_get_all_scores.return_value = {
+        "explorer": 0.90,
+    }
+    
+    # 0.90 * 1.3 = 1.17, which should be capped at 1.0
+    route, score = classify_intent("message bidon", active_agent="agent_explorer")
+    
+    assert route == "explorer"
+    assert score == 1.0
+
+@patch("agent_maestro.router.get_all_scores")
+def test_classify_intent_active_agent_not_in_top(mock_get_all_scores):
+    # Mock scores where active agent has a very low score
+    mock_get_all_scores.return_value = {
+        "gourmet": 0.80,
+        "acadomie": 0.10
+    }
+    
+    # Active agent is acadomie. 0.10 * 1.3 = 0.13. 
+    # Gourmet remains the winner with 0.80.
+    route, score = classify_intent("message bidon", active_agent="acadomie")
+    
+    assert route == "gourmet"
+    assert score == 0.80
+
+@patch("agent_maestro.router.get_all_scores")
+def test_classify_intent_semantic_escape_hatch(mock_get_all_scores):
+    # Mock scores where a new agent has a very high score (> 0.95)
+    mock_get_all_scores.return_value = {
+        "gourmet": 0.80, # Active agent
+        "acadomie": 0.96 # Very high score (> 0.95)
+    }
+    
+    # Normally, 0.80 * 1.3 = 1.0, so gourmet would win or tie.
+    # BUT, because acadomie > 0.95, the escape hatch triggers and no bonus is applied.
+    route, score = classify_intent("message bidon", active_agent="gourmet")
+    
+    assert route == "acadomie"
+    assert score == 0.96
