# Story 1.3: Auto-Documentation OpenAPI (Swagger)

Status: review

## Story

As a Intégrateur système,
I want visiter l'accès Swagger généré de FastAPI (`/docs`),
So that je puisse lire la topologie et la signature exacte du requêtage JSON-RPC attendu.

## Acceptance Criteria

1. **Given** le serveur Maestro déployé localement
2. **When** un utilisateur accède au path `/docs` via un navigateur
3. **Then** les schémas d'entrée (`JsonRpcRequest`) incluent des exemples concrets d'appels JSON-RPC 2.0.
4. **And** les structures de réponse (incluant `JsonRpcError`) sont clairement listées avec leurs attributs et exemples.
5. **And** l'endpoint `/api/v1/routing` est correctement documenté avec un `summary` et une `description` détaillés.

## Tasks / Subtasks

- [ ] Task 1 : Enrichir les modèles Pydantic avec des exemples
  - [ ] Ajouter `json_schema_extra` à `JsonRpcRequest` dans `src/common/schemas.py`.
  - [ ] Ajouter `json_schema_extra` à `JsonRpcResponse` dans `src/common/schemas.py`.
  - [ ] Ajouter `json_schema_extra` à `RequestContext` dans `src/common/schemas.py`.
- [ ] Task 2 : Peaufiner la documentation de la route de routage
  - [ ] Mettre à jour `src/agent_maestro/main.py` pour ajouter `summary`, `tags` et `responses` (ex: 422) à la route `/api/v1/routing`.
- [ ] Task 3 : Validation visuelle
  - [ ] Lancer Maestro localement.
  - [ ] Utiliser le browser tool pour capturer un screenshot de `/docs` et valider le rendu.

## Dev Notes

### Pydantic v2 Examples
Utiliser la syntaxe Pydantic v2 :
```python
model_config = ConfigDict(
    json_schema_extra={
        "examples": [
            {
                "jsonrpc": "2.0",
                "method": "route_message",
                "params": {...},
                "id": "1"
            }
        ]
    }
)
```

### FastAPI Decorator Enrichment
```python
@app.post(
    "/api/v1/routing",
    response_model=JsonRpcResponse,
    summary="Point d'entrée principal du routage A2A",
    tags=["Gateway"],
    # ...
)
```

## Dev Agent Record

### Agent Model Used
Gemini 2.0 Flash (Antigravity)

### Debug Log References
- [2026-04-18] Story 1.2 completed and verified.
- [2026-04-18] Story 1.3 spec created.

### Completion Notes List
- [x] Modèles Pydantic enrichis avec `json_schema_extra` (exemples JSON-RPC 2.0).
- [x] Routes tagguées et documentées dans `main.py` ("Gateway", "System", "Legacy").
- [x] Validation visuelle effectuée via le browser tool sur `/docs`.
- [x] Correction globale des imports pour compatibilité `PYTHONPATH=src`.
- [x] Tests 100% passants (52 tests).

### File List
- `src/common/schemas.py` [MODIFY]
- `src/agent_maestro/main.py` [MODIFY]
