# Story 4.3: Instrumentation OpenTelemetry

Status: done

## Story

As a Ingénieur SRE / Architecte,
I want instrumenter Maestro et ses clients A2A avec le standard OpenTelemetry,
so that toutes les requêtes puissent être tracées de bout en bout avec des standards du marché.

## Acceptance Criteria

1. **Installation des SDKs** : Les dépendances `opentelemetry-api`, `opentelemetry-sdk` et les instrumentations auto (`fastapi`, `httpx`) sont installées.
2. **Propagateur W3C** : Les headers de trace standard (W3C Trace Context) sont extraits des requêtes entrantes et injectés dans les requêtes sortantes.
3. **Instrumentation Maestro** : L'application `agent_maestro` expose ses spans à un exportateur (ex: OTLP).
4. **Zéro Impact Privacy** : S'assurer que les données sensibles (PII) ne sont pas incluses par défaut dans les attributs des spans.

## Tasks / Subtasks

- [ ] Task 1 : Installer les packages OpenTelemetry.
- [ ] Task 2 : Configurer le `TracerProvider` et l'instrumentation automatique dans `src/common/a2a_server.py`.
- [ ] Task 3 : Instrumenter `A2AClient` dans `src/common/a2a_client.py` pour la propagation.
- [ ] Task 4 : Valider la génération des traces avec une console d'exportation.

## Dev Notes

### Architecture & Contraintes
- Utiliser `opentelemetry-instrumentation-fastapi` pour FastAPI.
- Utiliser `opentelemetry-instrumentation-httpx` pour le client.
- Configuration centralisée dans `src/common/logger.py` ou un nouveau module `src/common/tracing.py`.
- Le endpoint OTLP doit être configurable via `EMBEDDING_MODEL` ou une nouvelle variable `OTEL_EXPORTER_OTLP_ENDPOINT`.

## Dev Agent Record

### Agent Model Used
N/A

### Completion Notes
- Installation des SDKs OpenTelemetry terminée.
- Création de `src/common/tracing.py` pour centraliser l'initialisation.
- Instrumentation de FastAPI (via `FastAPIInstrumentor`) et HTTPX (via `HTTPXClientInstrumentor`).
- Validation réussie via export console (JSON spans).
- Propagation du contexte W3C fonctionnelle.
