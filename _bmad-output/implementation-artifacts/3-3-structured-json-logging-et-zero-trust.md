# Story 3.3 : Structured JSON Logging et Zero-Trust

Status: review

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

---

## Story Details

- **Status:** ready-for-dev
- **Epic:** 3 — Résilience, Observabilité et Intégration Écosystème
- **Story ID:** 3.3
- **Story Key:** `3-3-structured-json-logging-et-zero-trust`

## 📖 Story Foundation

### User Story
**As a** opérateur du serveur domestique Tegmen,
**I want** que les logs de l'Agent Gourmet soient au format JSON structuré et n'exposent jamais les données textuelles de la famille,
**So that** les logs soient exploitables par des outils d'analyse et respectent la vie privée.

### Acceptance Criteria (BDD)
- **Given** le handler logging actuel (`common/logger.py`) en format texte
- **When** Gourmet émet un log
- **Then** NFR-SEC-1 : le format de sortie est JSON structuré (un objet JSON par ligne) avec les clés `timestamp`, `level`, `service`, `correlation_id`, `message`
- **And** NFR-SEC-1 : les données textuelles de la famille (message utilisateur, contenu de recette) ne sont jamais loguées en clair — seuls les identifiants (`recipe_id`, `user_id`, `family_id`) apparaissent
- **And** la migration est implémentée comme un handler local Gourmet (pas de modification de `common/logger.py` pour éviter les régressions transverses)
- **And** un test vérifie que la sortie log est un JSON parseable
- **And** un test vérifie qu'un message contenant du texte utilisateur n'apparaît pas dans les logs

---

## 👨‍💻 Developer Context

> **⚠️ CRITICAL RULES & GUARDRAILS ⚠️**
> - **DO NOT MODIFY `src/common/logger.py`**: This file is shared across all agents. Modifying it could cause cross-agent regressions. Create a local logger setup for Gourmet.
> - **ZERO-TRUST / PII MASKING**: Never log raw user messages, natural language queries, or recipe contents. Mask them or log only IDs and status.
> - **CORRELATION ID**: The logger must automatically include the `correlation_id` from the request context using the utilities developed in Story 3.2.

### Technical Requirements
- Create `src/agent_gourmet/app/logger.py`.
- It should expose a `setup_gourmet_logger()` function that configures and returns a local logger, independent of `common.logger`.
- Use the standard `logging` module but set a custom `logging.Formatter` that outputs JSON strings (e.g., using `json.dumps`).
- The JSON object must contain:
  - `timestamp`: ISO 8601 format.
  - `level`: The log level (e.g., "INFO", "ERROR").
  - `service`: Should be "gourmet" or "gourmet_a2a".
  - `correlation_id`: Fetch dynamically from `agent_gourmet.app.context.get_correlation_id()`.
  - `message`: The sanitized log message.
- Update `src/agent_gourmet/app/api/routers/a2a.py` and any other Gourmet files to import the logger from the new local module instead of `common.logger`.
- In `a2a.py`, audit all `logger.info(...)` and `logger.exception(...)` calls. Remove any logging of `params` that contains the raw text/query.
  - For example, `logger.info(f"A2A | search_recipes | correlation_id={cid} | params={params}")` must be modified to NOT log `params["query"]` or `params["message"]`. Log only `params.keys()` or safely sanitized structures.

### Architecture Compliance
- **Isolation Microservice**: En respect de la règle d'isolation A2A, l'agent Gourmet doit gérer sa propre stratégie de log sans impacter les autres agents, d'où le besoin d'un formateur local.
- **Sécurité et Confidentialité**: Application stricte des règles du `project-context.md` : "Interdiction stricte de logger en clair des données sensibles...".

### File Structure Requirements
- Nouveaux fichiers à créer dans le domaine de Gourmet : `src/agent_gourmet/app/logger.py`.
- Tests à créer dans `tests/agent_gourmet/test_gourmet_logging.py`.

### Testing Requirements
- Create a test file `tests/agent_gourmet/test_gourmet_logging.py`.
- Test that the logger outputs valid JSON. (You can use `caplog` or create a dummy stream handler for the test).
- Test that a log message emitted with PII (e.g., simulating a user query "je veux une recette de pizza") does NOT appear in the JSON output, either because it's filtered by the formatter or because the application code strips it correctly before logging.
- Verify that `correlation_id` is successfully injected into the JSON structure.

---

### 🧠 Previous Story Intelligence (Story 3.2)
- **ContextVars Mechanism**: In Story 3.2, `agent_gourmet/app/context.py` was created to manage the request-scoped `correlation_id`.
- **Retrieval**: Use `from agent_gourmet.app.context import get_correlation_id` within the custom JSON Formatter to dynamically inject the correlation ID into every log record.

### Project Context Reference
- Follow strict `async/await` patterns.
- Follow PEP8 and strict typing rules.
- Review `_bmad-output/project-context.md` for full project guidelines (especially the "Sécurité et Confidentialité" rule).

---

## Tasks / Subtasks

- [x] Task 1 : Création du Formatter JSON
  - [x] Créer `src/agent_gourmet/app/logger.py`
  - [x] Implémenter une classe `JSONFormatter(logging.Formatter)` qui surcharge `format(record)`
  - [x] Construire un dict JSON contenant `timestamp`, `level`, `service`, `correlation_id` (via `get_correlation_id()`), `message`
- [x] Task 2 : Configuration locale du Logger
  - [x] Dans `src/agent_gourmet/app/logger.py`, implémenter `setup_gourmet_logger(name)`
  - [x] Attacher le `JSONFormatter` au logger local
- [x] Task 3 : Remplacement des imports de logging
  - [x] Dans `a2a.py` et `recipe_service.py` (si applicable), remplacer `from common.logger import setup_logger` par `from agent_gourmet.app.logger import setup_gourmet_logger`
  - [x] Instancier le logger local
- [x] Task 4 : Audit et Masking des PII
  - [x] Modifier les appels de log dans `a2a.py` pour s'assurer qu'aucun texte utilisateur n'est logué (retirer le `params={params}` brut).
  - [x] Remplacer par une version expurgée, ou ne logger que l'identifiant de la méthode appelée.
- [x] Task 5 : Implémentation des tests
  - [x] Créer `tests/agent_gourmet/test_gourmet_logging.py`
  - [x] Ajouter les tests de formatage JSON, de présence du correlation_id, et de non-présence de PII.

---

### Agent Model Used

Gemini 2.0 Flash

### Debug Log References

- Fixed `test_correlation_id_in_logs` by enabling logger propagation, allowing `caplog` to capture records from the custom logger.
- Verified JSON format compliance and PII masking via `tests/agent_gourmet/test_gourmet_logging.py`.

### Completion Notes List

- Implemented `JSONFormatter` in `src/agent_gourmet/app/logger.py` to output structured logs.
- Configured Gourmet-specific logger to automatically include `correlation_id` from context.
- Sanitized all A2A handlers in `a2a.py` to remove `params` from logs, preventing PII (user messages/queries) leakage.
- Maintained 100% test pass rate across the Gourmet suite.

### File List

- `src/agent_gourmet/app/logger.py` (New)
- `src/agent_gourmet/app/api/routers/a2a.py` (Modified)
- `tests/agent_gourmet/test_gourmet_logging.py` (New)
- `tests/agent_gourmet/test_gourmet_observability.py` (Modified)
