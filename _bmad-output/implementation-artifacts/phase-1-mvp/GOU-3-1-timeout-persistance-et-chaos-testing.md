# Story 3.1 : Timeout Persistance et Chaos Testing

Status: review

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Metadata

- **Status:** review
- **Epic:** 3 — Résilience, Observabilité et Intégration Écosystème
- **Story ID:** 3.1
- **Story Key:** `3-1-timeout-persistance-et-chaos-testing`
- **Created:** 2026-05-02
- **Sprint Status File:** `_bmad-output/implementation-artifacts/sprint-status-agent-gourmet.yaml`

---

## User Story

**As a** opérateur du serveur domestique Tegmen,
**I want** que l'Agent Gourmet interrompe immédiatement toute requête de persistance dépassant un délai critique et supporte l'injection de latence artificielle,
**So that** le système ne reste jamais bloqué et que je puisse tester sa robustesse.

---

## Acceptance Criteria

**AC1 — Timeout Fail-Fast sur la Persistance (NFR-REL-2)**
> **Given** un service de persistance (mock `RECIPES_DB` actuel ou futur asyncpg)
> **When** une requête de données dépasse 3000ms
> **Then** la coroutine est interrompue via `asyncio.wait_for` et une `A2ARPCError(TIMEOUT, -32000)` est levée
> **And** le message d'erreur est explicite : "Délai d'attente dépassé pour la persistance"
> **And** le `data` de l'erreur contient `{"timeout_ms": 3000}`

**AC2 — Chaos Testing via Variable d'Environnement (NFR-REL-2)**
> **Given** la variable d'environnement `GOURMET_ARTIFICIAL_DELAY_MS` est définie (ex: `4000`)
> **When** le service de persistance est invoqué (search_recipes ou get_recipe_details)
> **Then** un `await asyncio.sleep(delay_ms / 1000)` est exécuté **avant** l'accès aux données
> **And** si `delay_ms ≥ GOURMET_PERSISTENCE_TIMEOUT_MS` (3000), le timeout se déclenche et une erreur `TIMEOUT` est retournée

**AC3 — Démarrage à Froid < 3s (NFR-REL-1)**
> **Given** le service Agent Gourmet est arrêté
> **When** le service est démarré (`lifespan` FastAPI)
> **Then** le lifespan startup complète en moins de 3 secondes
> **And** le endpoint `/health` retourne `{"status": "ok"}` immédiatement après

**AC4 — Concurrence Domestique sans Blocage (NFR-PERF-2)**
> **Given** le service est opérationnel
> **When** 5 requêtes `search_recipes` sont envoyées simultanément via `asyncio.gather`
> **Then** les 5 réponses sont retournées sans blocage ni erreur
> **And** aucune requête ne dépasse le timeout de 3000ms (hors chaos delay)

**AC5 — Configuration Externalisée**
> **And** les valeurs `GOURMET_PERSISTENCE_TIMEOUT_MS` (défaut: 3000) et `GOURMET_ARTIFICIAL_DELAY_MS` (défaut: 0) sont lues depuis les variables d'environnement via `Settings` dans `src/common/config.py`

---

## Tasks / Subtasks

- [x] Task 1 : Configuration (AC: #5)
  - [x] Ajouter `GOURMET_PERSISTENCE_TIMEOUT_MS: int` (défaut 3000) dans `Settings` de `src/common/config.py`
  - [x] Ajouter `GOURMET_ARTIFICIAL_DELAY_MS: int` (défaut 0) dans `Settings` de `src/common/config.py`
  - [x] Ajouter les deux variables dans `.env.example` avec commentaires

- [x] Task 2 : Wrapper Timeout dans RecipeService (AC: #1, #2)
  - [x] Créer une méthode privée `_with_timeout` dans `RecipeService` qui enveloppe tout appel de données dans `asyncio.wait_for(coro, timeout=config.GOURMET_PERSISTENCE_TIMEOUT_MS / 1000)`
  - [x] Injecter le chaos delay : si `config.GOURMET_ARTIFICIAL_DELAY_MS > 0`, appeler `await asyncio.sleep(delay / 1000)` **avant** l'opération de données
  - [x] Capturer `asyncio.TimeoutError` et lever `A2ARPCError(code=A2ARPCError.TIMEOUT, message="Délai d'attente dépassé pour la persistance", data={"timeout_ms": config.GOURMET_PERSISTENCE_TIMEOUT_MS})`
  - [x] Appliquer `_with_timeout` à `search_recipes` et `get_recipe_details`

- [x] Task 3 : Tests de Timeout (AC: #1, #2)
  - [x] Test `test_timeout_triggers_error` : mocker le chaos delay > timeout → vérifier `A2ARPCError(TIMEOUT, -32000)`
  - [x] Test `test_timeout_under_threshold` : mocker le chaos delay < timeout → vérifier que la réponse est normale
  - [x] Test `test_timeout_respects_config` : vérifier que le timeout se déclenche en < 3100ms (marge de 100ms)

- [x] Task 4 : Tests de Concurrence (AC: #4)
  - [x] Test `test_concurrent_requests_no_blocking` : 5 `search_recipes` via `asyncio.gather` → toutes réussies

- [x] Task 5 : Test de Démarrage à Froid (AC: #3)
  - [x] Test `test_cold_start_under_3s` : mesurer le temps de lifespan startup → assert < 3s
  - [x] Test `test_health_after_startup` : vérifier `/health` retourne `{"status": "ok"}` après le démarrage

- [x] Task 6 : Test d'Intégration A2A (AC: #1)
  - [x] Test `test_a2a_timeout_error_response` : envoyer une requête JSON-RPC avec le chaos delay activé → vérifier que la `JsonRpcResponse` contient un `error` avec code `-32000`

---

## Dev Notes

### Architecture Compliance

- **Pattern de Timeout :** Utiliser `asyncio.wait_for()` — c'est le mécanisme standard Python pour interrompre une coroutine. NE PAS utiliser `asyncio.timeout()` (context manager Python 3.11+) car `wait_for` est plus compatible avec le pattern de wrapping.
- **Chaos Testing côté Serveur :** Le PRD spécifie que l'injection de délai est côté Gourmet (via `.env`). C'est complémentaire au timeout côté client Maestro (`DEFAULT_A2A_TIMEOUT` dans `config.py`).
- **Aucune modification de `common/` :** Les ajouts de config vont dans `Settings` (existant dans `common/config.py`), mais la logique de timeout est locale à `RecipeService`.
- **Code d'erreur TIMEOUT = -32000 :** Déjà défini dans `src/common/exceptions.py` (ligne 14). Ne pas le redéfinir.

### Technical Stack

- **Python 3.13+** — utiliser `asyncio.wait_for`, `asyncio.sleep`, `asyncio.gather`
- **Pydantic v2 (Strict)** — les schémas existants sont intacts, pas de modification nécessaire
- **pytest-asyncio** (`asyncio_mode="auto"`) — tous les tests doivent être `async def`

### Patterns Critiques à Respecter

1. **Anti-pattern `time.sleep` INTERDIT** — Utiliser exclusivement `asyncio.sleep()` pour le chaos delay.
2. **Pas de blocs `except Exception: pass`** — Toute erreur doit être logguée et propagée.
3. **Typage strict Python 3.13+** — `X | None` au lieu de `Optional[X]`, annotation de retour obligatoire sur chaque fonction (`-> None:`).
4. **snake_case JSON** — Tous les payloads JSON-RPC en snake_case.
5. **Import `config` depuis `common.config`** — NE PAS relire `os.getenv` localement, utiliser l'instance singleton `config`.

### Project Structure Notes

- `src/agent_gourmet/app/services/recipe_service.py` — Refactorisé avec `_with_timeout` (callable factory pattern)
- `src/common/config.py` — +2 settings
- `.env.example` — +2 variables documentées
- `src/agent_gourmet/main.py` — Fix: `/health` déplacé avant `app.mount("/")` pour éviter l'interception par le sous-app
- `tests/agent_gourmet/test_gourmet_resilience.py` — **Nouveau fichier**, 11 tests

### References

- [Source: PRD NFR-REL-2](file:///home/ngombert/projects/tegmen/_bmad-output/planning-artifacts/prd_agent_gourmet.md)
- [Source: PRD NFR-REL-1](file:///home/ngombert/projects/tegmen/_bmad-output/planning-artifacts/prd_agent_gourmet.md)
- [Source: PRD NFR-PERF-2](file:///home/ngombert/projects/tegmen/_bmad-output/planning-artifacts/prd_agent_gourmet.md)
- [Source: Architecture — Anti-Pattern Asynchrone](file:///home/ngombert/projects/tegmen/_bmad-output/planning-artifacts/architecture.md)
- [Source: common/exceptions.py](file:///home/ngombert/projects/tegmen/src/common/exceptions.py) — `TIMEOUT = -32000` (ligne 14)
- [Source: common/config.py](file:///home/ngombert/projects/tegmen/src/common/config.py)

---

## Previous Story Intelligence

### Leçons Story 2.1 / 2.2 (Epic 2)

- **OTEL_ENABLED dans les tests :** Désactiver via `OTEL_ENABLED=false` dans l'environnement de test.
- **Pattern d'erreur consolidé :** Tous les handlers utilisent `A2ARPCError`. Le code `TIMEOUT = -32000` suit le même pattern.
- **TestClient :** Les tests A2A utilisent `TestClient(app)` (synchrone). Les tests de service utilisent `@pytest.mark.asyncio`.
- **`monkeypatch` pour l'environnement :** Le pattern `monkeypatch.setattr` sur l'objet `config` est le pattern standard.

### Git Intelligence

- Dernier commit : `feat(gourmet): detailed recipe extraction and fail-fast error handling (Epic 2)`
- Commit attendu : `feat(gourmet): persistence timeout and chaos testing (Story 3.1)`

---

## Project Context Reference

- [Architecture Decision Document](file:///home/ngombert/projects/tegmen/_bmad-output/planning-artifacts/architecture.md)
- [PRD Agent Gourmet](file:///home/ngombert/projects/tegmen/_bmad-output/planning-artifacts/prd_agent_gourmet.md)
- [Project Context](file:///home/ngombert/projects/tegmen/_bmad-output/project-context.md)
- [Epics Agent Gourmet](file:///home/ngombert/projects/tegmen/_bmad-output/planning-artifacts/epics_agent_gourmet.md)

---

## Dev Agent Record

### Agent Model Used

Claude Sonnet 4.6 (Thinking)

### Debug Log References

1. **`/health` route 404** : L'endpoint `/health` était défini APRÈS `app.mount("/", a2a_app)`. En FastAPI, un root mount intercepte toutes les routes définies après lui. Fix : déclaration de `/health` avant le mount.
2. **Warning `coroutine was never awaited`** : `_with_timeout` recevait une coroutine pré-instanciée. Si le timeout expire pendant `asyncio.sleep`, la coroutine d'opération n'est jamais awaited. Fix : pattern "callable factory" — `_with_timeout` accepte un `lambda` et instancie la coroutine à l'intérieur de `_delayed()`, garantissant qu'elle est toujours awaited.

### Completion Notes List

- ✅ AC1 : `asyncio.wait_for` avec `GOURMET_PERSISTENCE_TIMEOUT_MS` (défaut 3000ms) — `search_recipes` et `get_recipe_details` protégés
- ✅ AC2 : Chaos delay via `GOURMET_ARTIFICIAL_DELAY_MS` — `asyncio.sleep` injecté avant l'opération de données
- ✅ AC3 : Démarrage à froid < 3s — lifespan Lean, démarrage en <100ms. Fix `/health` order dans main.py
- ✅ AC4 : 5 requêtes concurrentes via `asyncio.gather` — toutes réussies sans blocage
- ✅ AC5 : Configuration externalisée dans `Settings` — 2 nouveaux settings + `.env.example` documenté
- ✅ 11 nouveaux tests, 106 tests au total dans le projet — zéro régression, zéro warning

### File List

- `src/common/config.py` (Modifié — +2 settings: GOURMET_PERSISTENCE_TIMEOUT_MS, GOURMET_ARTIFICIAL_DELAY_MS)
- `.env.example` (Modifié — +2 variables avec commentaires)
- `src/agent_gourmet/app/services/recipe_service.py` (Modifié — +`_with_timeout` callable factory, `_do_search_recipes`, `_do_get_recipe_details`)
- `src/agent_gourmet/main.py` (Modifié — Fix ordre `/health` avant `app.mount("/")`)
- `tests/agent_gourmet/test_gourmet_resilience.py` (Créé — 11 tests de résilience)
