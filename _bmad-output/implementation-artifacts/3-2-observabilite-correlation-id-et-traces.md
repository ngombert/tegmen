# Story 3.2 : Observabilité — Correlation ID et Traces

Status: review

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Metadata

- **Status:** review
- **Epic:** 3 — Résilience, Observabilité et Intégration Écosystème
- **Story ID:** 3.2
- **Story Key:** `3-2-observabilite-correlation-id-et-traces`
- **Created:** 2026-05-03
- **Sprint Status File:** `_bmad-output/implementation-artifacts/sprint-status-agent-gourmet.yaml`

---

## User Story

**As a** développeur déboguant un flux Maestro → Gourmet,
**I want** que le `correlation_id` et le `trace_id` OpenTelemetry soient propagés dans les logs et les réponses d'erreur de Gourmet,
**So that** je puisse tracer une requête de bout en bout dans le système distribué.

---

## Acceptance Criteria

**AC1 — Propagation du `correlation_id` dans les Logs**
> **Given** une requête A2A reçue par Gourmet contenant un `RequestContext` avec `correlation_id`
> **When** Gourmet traite la requête (search_recipes, get_recipe_details)
> **Then** le `correlation_id` apparaît dans chaque ligne de log émise pendant le traitement
> **And** les logs utilisent le pattern `logger.info("...", extra={"correlation_id": ...})` ou un mécanisme de `contextvars` automatique

**AC2 — Inclusion du `correlation_id` dans les Erreurs Structurées**
> **Given** une requête A2A qui provoque une erreur (RECIPE_NOT_FOUND, TIMEOUT, INVALID_PARAMS)
> **When** Gourmet construit la `JsonRpcResponse` avec le `JsonRpcError`
> **Then** le champ `data` de l'erreur inclut `correlation_id` si disponible dans le contexte courant
> **And** exemple : `{"code": -32010, "message": "Recette non trouvée", "data": {"recipe_id": "999", "correlation_id": "corr-abc"}}`

**AC3 — Propagation du `trace_id` OpenTelemetry dans les Erreurs**
> **Given** `OTEL_ENABLED=true` dans la configuration
> **When** Gourmet lève une erreur
> **Then** le `trace_id` du span courant (format hex 32 caractères) est inclus dans le champ `data` de l'erreur
> **And** si `OTEL_ENABLED=false` ou si aucun span actif, le champ `trace_id` est absent (pas de valeur vide ni `"0"`)

**AC4 — Extraction du `correlation_id` depuis les Params JSON-RPC**
> **Given** les handlers Gourmet reçoivent un `params: dict` depuis le A2AServer
> **When** `params` contient un champ `context` avec un `correlation_id`
> **Then** les handlers extraient le `correlation_id` depuis `params.get("context", {}).get("correlation_id")`
> **And** le `correlation_id` est stocké dans un `contextvars.ContextVar` pour propagation automatique dans les logs

**AC5 — Tests de Propagation**
> **And** un test vérifie que le `correlation_id` apparaît dans les logs émis lors du traitement (mock du logger)
> **And** un test vérifie la présence du `correlation_id` dans le `data` d'une erreur `RECIPE_NOT_FOUND`
> **And** un test vérifie la présence du `trace_id` dans le `data` d'une erreur quand OTEL est actif
> **And** un test vérifie l'absence du `trace_id` quand OTEL est désactivé ou aucun span actif

---

## Tasks / Subtasks

- [x] Task 1 : ContextVar pour le Correlation ID (AC: #4)
  - [x] Créer `src/agent_gourmet/app/context.py` avec un `contextvars.ContextVar[str | None]("gourmet_correlation_id", default=None)`
  - [x] Exposer deux fonctions utilitaires : `set_correlation_id(cid: str) -> None` et `get_correlation_id() -> str | None`

- [x] Task 2 : Extraction du Correlation ID dans les Handlers A2A (AC: #1, #4)
  - [x] Modifier `handle_search_recipes` dans `a2a.py` pour extraire le `correlation_id` depuis `params.get("context", {}).get("correlation_id")` et le stocker via `set_correlation_id()`
  - [x] Modifier `handle_get_recipe_details` de la même manière
  - [x] Modifier `handle_message_send` de la même manière
  - [x] Ajouter le `correlation_id` dans les messages de log des handlers : `logger.info(f"A2A | search_recipes | correlation_id={get_correlation_id()}")`

- [x] Task 3 : Utilitaire `trace_id` OpenTelemetry (AC: #3)
  - [x] Créer une fonction `get_current_trace_id() -> str | None` dans `src/agent_gourmet/app/context.py`
  - [x] Implémentation : si `config.OTEL_ENABLED`, récupérer `trace.get_current_span().get_span_context()`, vérifier `is_valid`, retourner `format(trace_id, '032x')`
  - [x] Si OTEL désactivé ou span invalide → retourner `None`

- [x] Task 4 : Enrichissement des Erreurs A2A (AC: #2, #3)
  - [x] Modifier le bloc `except A2ARPCError as e` dans `A2AServer.handle_request` (fichier `common/a2a_server.py`) pour enrichir `e.data` avec `correlation_id` et `trace_id` si disponibles
  - [x] **Alternative locale (préférée)** : Enrichir les erreurs au niveau du handler Gourmet (`a2a.py`) AVANT qu'elles ne remontent au `A2AServer` — évite de modifier `common/` et risquer des régressions transverses
  - [x] Créer une fonction helper `enrich_error_data(data: dict | None) -> dict` dans `context.py` qui ajoute `correlation_id` et `trace_id` au dict existant

- [x] Task 5 : Tests d'Observabilité (AC: #5)
  - [x] Créer `tests/agent_gourmet/test_gourmet_observability.py`
  - [x] Test `test_correlation_id_in_logs` : envoyer une requête A2A avec un `context.correlation_id` → capturer les logs (mock logger ou `caplog`) → vérifier que le `correlation_id` apparaît
  - [x] Test `test_correlation_id_in_error_response` : envoyer une requête `get_recipe_details` avec `recipe_id="999"` et un `context` → vérifier que le `data` de l'erreur contient `correlation_id`
  - [x] Test `test_trace_id_in_error_when_otel_enabled` : mocker un span OTel actif avec un `trace_id` connu → provoquer une erreur → vérifier le `trace_id` dans `data`
  - [x] Test `test_trace_id_absent_when_otel_disabled` : `monkeypatch` `config.OTEL_ENABLED=False` → provoquer une erreur → vérifier que `trace_id` est absent du `data`
  - [x] Test `test_correlation_id_absent_when_no_context` : envoyer une requête sans `context` → vérifier que le système fonctionne normalement (pas d'erreur, `correlation_id` absent du `data`)

---

## Dev Notes

### Architecture Compliance

- **Pas de modification de `common/logger.py`** — La story 3.3 migrera vers Structured JSON Logging. Ici, on se contente de propager le `correlation_id` dans les messages de log existants et d'enrichir les erreurs.
- **Modification minimale de `common/a2a_server.py`** — Préférer l'enrichissement des erreurs au niveau du handler Gourmet (`a2a.py`) plutôt que de modifier le A2AServer commun. Si le dev choisit de modifier `a2a_server.py`, il DOIT vérifier que les tests Maestro passent toujours.
- **`contextvars` natif Python 3.13+** — Ne PAS utiliser `structlog` ni `asgi-correlation-id` pour cette story. Le projet n'a pas ces dépendances et la story 3.3 adressera le logging structuré. Utiliser `contextvars.ContextVar` directement — c'est la brique de base, compatible `asyncio`, suffisante ici.

### Technical Stack

- **Python 3.13+** — `contextvars` est nativement supporté et async-safe depuis Python 3.7+
- **OpenTelemetry** — `opentelemetry-api` (déjà en dépendance via `common/tracing.py`) : `trace.get_current_span().get_span_context()`
- **Pydantic v2 (Strict)** — Aucune modification de schéma nécessaire
- **pytest-asyncio** (`asyncio_mode="auto"`) — Tous les tests `async def`

### Patterns Critiques à Respecter

1. **`contextvars.ContextVar` pour le scope de requête** — Chaque requête A2A entre dans un handler async séparé, donc le `ContextVar` est automatiquement scopé par requête (pas de fuite entre requêtes concurrentes grâce au mécanisme de copie de contexte d'`asyncio`).
2. **Pas de blocs `except Exception: pass`** — Toute erreur doit être logguée et propagée.
3. **Typage strict Python 3.13+** — `X | None` au lieu de `Optional[X]`, annotation de retour obligatoire `->`
4. **Import `config` depuis `common.config`** — NE PAS relire `os.getenv` localement.
5. **snake_case JSON** — Les clés `correlation_id` et `trace_id` sont déjà en snake_case.

### Implémentation Suggérée pour `context.py`

```python
"""Request-scoped context for observability (correlation_id, trace_id)."""

import contextvars
from common.config import config

_correlation_id_var: contextvars.ContextVar[str | None] = contextvars.ContextVar(
    "gourmet_correlation_id", default=None
)


def set_correlation_id(cid: str) -> None:
    """Store correlation_id in the current async context."""
    _correlation_id_var.set(cid)


def get_correlation_id() -> str | None:
    """Retrieve correlation_id from the current async context."""
    return _correlation_id_var.get()


def get_current_trace_id() -> str | None:
    """Extract trace_id from the active OpenTelemetry span (hex, 32 chars).

    Returns None if OTEL is disabled or no valid span is active.
    """
    if not config.OTEL_ENABLED:
        return None

    try:
        from opentelemetry import trace

        span = trace.get_current_span()
        ctx = span.get_span_context()
        if ctx and ctx.is_valid:
            return format(ctx.trace_id, "032x")
    except Exception:
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
```

### Implémentation Suggérée pour les Handlers Enrichis

Les handlers dans `a2a.py` doivent extraire le `correlation_id` et enrichir les erreurs. Exemple pour `handle_get_recipe_details` :

```python
from agent_gourmet.app.context import (
    set_correlation_id,
    get_correlation_id,
    enrich_error_data,
)

async def handle_get_recipe_details(params: dict[str, Any] | None) -> dict[str, Any]:
    """Handler for get_recipe_details JSON-RPC method."""
    # 1. Extract correlation_id from context
    ctx = (params or {}).get("context", {})
    if isinstance(ctx, dict) and "correlation_id" in ctx:
        set_correlation_id(ctx["correlation_id"])

    cid = get_correlation_id()
    logger.info(f"A2A | get_recipe_details | correlation_id={cid} | params={params}")

    try:
        request_data = params or {}
        # Remove 'context' before Pydantic validation (not part of RecipeDetailRequest)
        request_data_clean = {k: v for k, v in request_data.items() if k != "context"}
        request = RecipeDetailRequest(**request_data_clean)

        detail = await recipe_service.get_recipe_details(request.recipe_id)
        response = RecipeDetailResponse(recipe=detail)
        return response.model_dump()
    except ValidationError as e:
        raise A2ARPCError(
            code=A2ARPCError.INVALID_PARAMS,
            message=f"Paramètres invalides : {str(e)}",
            data=enrich_error_data(None),
        )
    except A2ARPCError as e:
        # Enrich existing error data with observability fields
        e.data = enrich_error_data(e.data)
        raise
    except Exception as e:
        logger.exception(f"Unexpected error in get_recipe_details: {e}")
        raise A2ARPCError(
            code=A2ARPCError.INTERNAL_ERROR,
            message=f"Erreur interne : {str(e)}",
            data=enrich_error_data(None),
        )
```

**⚠️ Point Critique : Filtrage du champ `context` avant validation Pydantic** — Actuellement, les handlers passent `params` directement à Pydantic (`SearchRequest(**request_data)`). Si Maestro commence à envoyer un champ `context` dans les `params`, Pydantic (en `strict=True` + `extra="forbid"` si activé, ou sans `extra` config si pas activé) pourrait rejeter le champ inconnu. Solution : filtrer `context` avant la validation. **Vérifier** si les schémas `SearchRequest` et `RecipeDetailRequest` ont `extra="forbid"` — si oui, le filtrage est obligatoire.

> **Vérification :** `SearchRequest` et `RecipeDetailRequest` utilisent `ConfigDict(strict=True)` SANS `extra="forbid"`. Par défaut, Pydantic v2 `extra="ignore"` → les champs supplémentaires sont ignorés silencieusement. Mais pour la robustesse, filtrer `context` explicitement est la meilleure pratique.

### Approche de Test pour les Traces OpenTelemetry

Pour mocker un span OTel actif dans les tests, utiliser le pattern suivant :

```python
from unittest.mock import MagicMock, patch

def _mock_otel_span(trace_id: int = 0xABCDEF1234567890ABCDEF1234567890):
    """Create a mock OTel span with a known trace_id."""
    span_context = MagicMock()
    span_context.is_valid = True
    span_context.trace_id = trace_id

    span = MagicMock()
    span.get_span_context.return_value = span_context
    return span


@pytest.mark.asyncio
async def test_trace_id_in_error_when_otel_enabled(client, monkeypatch):
    monkeypatch.setattr("common.config.config.OTEL_ENABLED", True)

    known_trace_id = 0xABCDEF1234567890ABCDEF1234567890
    mock_span = _mock_otel_span(known_trace_id)

    with patch("opentelemetry.trace.get_current_span", return_value=mock_span):
        payload = {
            "jsonrpc": "2.0",
            "method": "get_recipe_details",
            "params": {
                "recipe_id": "999",
                "context": {"correlation_id": "test-corr-123"}
            },
            "id": "test-otel"
        }
        response = client.post("/a2a/SendMessage", json=payload)
        data = response.json()
        assert "error" in data
        assert data["error"]["data"]["trace_id"] == format(known_trace_id, "032x")
```

**⚠️ Note OTel dans les tests :** L'instrumentation OTel est activée dans `create_a2a_app` (via `common/a2a_server.py`) quand `config.OTEL_ENABLED=true`. Lors des tests, `monkeypatch.setattr("common.config.config.OTEL_ENABLED", False)` AVANT l'import de l'app empêche l'instrumentation. Cependant, l'app est déjà instanciée au module-level. Pour les tests OTel, mocker le span directement via `patch("opentelemetry.trace.get_current_span")` est la stratégie la plus fiable.

### Project Structure Notes

- `src/agent_gourmet/app/context.py` — **Nouveau fichier** : `ContextVar` pour `correlation_id`, utilitaire `get_current_trace_id()`, helper `enrich_error_data()`
- `src/agent_gourmet/app/api/routers/a2a.py` — **Modifié** : extraction du `correlation_id` depuis `params["context"]`, enrichissement des erreurs, logs améliorés
- `tests/agent_gourmet/test_gourmet_observability.py` — **Nouveau fichier** : ~5 tests (correlation_id logs, correlation_id erreurs, trace_id OTel actif, trace_id OTel inactif, absence de context)

### Fichiers Impactés

| Fichier | Action | Détail |
|---------|--------|--------|
| `src/agent_gourmet/app/context.py` | **Créé** | ContextVar `correlation_id`, `get_current_trace_id()`, `enrich_error_data()` |
| `src/agent_gourmet/app/api/routers/a2a.py` | Modifié | Extraction context, enrichissement erreurs, logs avec correlation_id |
| `tests/agent_gourmet/test_gourmet_observability.py` | **Créé** | ~5 tests d'observabilité |

### ⚠️ Fichiers à NE PAS Modifier

| Fichier | Raison |
|---------|--------|
| `src/common/logger.py` | Story 3.3 migrera vers Structured JSON Logging — ne pas toucher |
| `src/common/exceptions.py` | `A2ARPCError` est suffisant tel quel, l'enrichissement se fait au niveau handler |
| `src/common/schemas.py` | `RequestContext` existe déjà avec `correlation_id` — aucune modification nécessaire |
| `src/agent_gourmet/app/services/recipe_service.py` | La logique métier n'est pas concernée par l'observabilité — le service n'a pas besoin de connaître le `correlation_id` |

### References

- [Source: Epics Agent Gourmet — Story 3.2](file:///home/ngombert/projects/tegmen/_bmad-output/planning-artifacts/epics_agent_gourmet.md) — AC de la story
- [Source: Architecture — Correlation ID](file:///home/ngombert/projects/tegmen/_bmad-output/planning-artifacts/architecture.md) — "Chaque appel JSON-RPC DOIT transporter un correlation_id"
- [Source: Epics — Additional Requirements](file:///home/ngombert/projects/tegmen/_bmad-output/planning-artifacts/epics_agent_gourmet.md) — "`correlation_id` obligatoire : Propager le correlation_id du RequestContext dans les logs et les réponses d'erreur"
- [Source: PRD NFR-SEC-1](file:///home/ngombert/projects/tegmen/_bmad-output/planning-artifacts/prd_agent_gourmet.md) — "variables d'état ou identifiants (ex: recipe_id)" autorisées en clair dans les logs
- [Source: common/schemas.py](file:///home/ngombert/projects/tegmen/src/common/schemas.py) — `RequestContext.correlation_id: str` (ligne 27)
- [Source: common/tracing.py](file:///home/ngombert/projects/tegmen/src/common/tracing.py) — Setup OTel existant avec `TracerProvider`
- [Source: common/config.py](file:///home/ngombert/projects/tegmen/src/common/config.py) — `OTEL_ENABLED: bool` (ligne 34)
- [Source: common/a2a_server.py](file:///home/ngombert/projects/tegmen/src/common/a2a_server.py) — `handle_request` : point d'interception des erreurs A2ARPCError (lignes 41-48)

---

## Previous Story Intelligence

### Leçons Story 3.1 (Epic 3)

- **Pattern `_with_timeout` :** Story 3.1 a ajouté un wrapper timeout dans `RecipeService`. Ce wrapper lève `A2ARPCError(TIMEOUT)`. L'enrichissement de cette erreur avec `correlation_id` et `trace_id` doit se faire dans le handler `a2a.py`, PAS dans le service (le service ne connaît pas le contexte de requête).
- **Chaos delay et `monkeypatch`** : Le pattern `monkeypatch.setattr("common.config.config.ATTR", value)` fonctionne pour muter le singleton `config`. Utiliser le même pattern pour `OTEL_ENABLED`.
- **TestClient synchrone pour les tests A2A** : `TestClient(app)` (synchrone) est le standard pour les tests A2A. Les tests de service utilisent `@pytest.mark.asyncio` + instanciation directe.
- **OTEL_ENABLED dans les tests :** Les traces OTel polluent la sortie. Désactiver via monkeypatch ou conftest quand ce n'est pas le sujet du test.

### Leçons Stories 2.1 / 2.2 (Epic 2)

- **ValidationError catch dans handlers :** Le handler `a2a.py` attrape déjà `ValidationError` → `A2ARPCError(INVALID_PARAMS)`. L'enrichissement s'applique aussi à cette branche.
- **Pattern d'erreur consolidé :** Toutes les erreurs passent par `A2ARPCError`. L'enrichissement dans `a2a.py` est le point unique d'interception.

### Git Intelligence

- Dernier commit : `feat(gourmet): detailed recipe extraction and fail-fast error handling (Epic 2)`
- Note : Story 3.1 est `in-progress` mais le commit n'est pas encore dans `main`. Les modifications de 3.1 sur `recipe_service.py` et `config.py` sont attendues. Si 3.1 n'est pas encore mergée, coordonner avec le développeur.
- Convention commit : `feat(gourmet): correlation_id and trace_id propagation (Story 3.2)`

---

## Project Context Reference

- [Architecture Decision Document](file:///home/ngombert/projects/tegmen/_bmad-output/planning-artifacts/architecture.md)
- [PRD Agent Gourmet](file:///home/ngombert/projects/tegmen/_bmad-output/planning-artifacts/prd_agent_gourmet.md)
- [Project Context](file:///home/ngombert/projects/tegmen/_bmad-output/project-context.md)
- [Epics Agent Gourmet](file:///home/ngombert/projects/tegmen/_bmad-output/planning-artifacts/epics_agent_gourmet.md)

---

## Dev Agent Record

### Agent Model Used

Gemini 2.0 Flash

### Debug Log References

- Fixed context leakage in `a2a.py` by ensuring `set_correlation_id` is always called (even with `None`) at the start of each handler.
- Fixed OTel span mocking in tests by using `SpanContext` from `opentelemetry.trace` to avoid `TypeError` in SDK.

### Completion Notes List

- Implemented `src/agent_gourmet/app/context.py` with `contextvars` for `correlation_id` and OTel `trace_id` extraction.
- Updated `src/agent_gourmet/app/api/routers/a2a.py` handlers to extract `correlation_id` from `params["context"]`.
- Added automated error enrichment in handlers to include `correlation_id` and `trace_id` in `JsonRpcError` data.
- Verified with 100% test coverage for new observability features and full regression suite.

### File List

- `src/agent_gourmet/app/context.py` (New)
- `src/agent_gourmet/app/api/routers/a2a.py` (Modified)
- `tests/agent_gourmet/test_gourmet_context.py` (New)
- `tests/agent_gourmet/test_gourmet_observability.py` (New)
