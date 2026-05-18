# Story 6.3: Injection des Clés d'API dans le Router Maestro

Status: review

## Story

As a Developer,
I want to ensure that the necessary API keys (`OPENAI_API_KEY`, etc.) are correctly injected into the Maestro environment for the use of `semantic-router`,
so that intent encoding no longer depends on mocks and uses the real model (`text-embedding-3-small` or equivalent).

## Acceptance Criteria

1. **Given** the Maestro router **When** it starts **Then** it has access to `OPENAI_API_KEY` (or other keys) if it uses a remote embedding model.
2. **Given** `router.py` in Maestro **When** it initializes `semantic-router` **Then** it uses the configured embedding model and passes the necessary credentials if applicable.

## Tasks / Subtasks

- [x] **Task 1 — Vérifier l'injection des clés dans Maestro** (AC: #1)
  - [x] 1.1 S'assurer que `OPENAI_API_KEY` est lue par Maestro si le modèle l'exige (ajouté dans `config.py`)
- [x] **Task 2 — Vérifier et adapter `router.py`** (AC: #2)
  - [x] 2.1 Vérifier quel encodeur est utilisé par `semantic-router` dans `router.py` (c'était `HuggingFaceEncoder`)
  - [x] 2.2 S'assurer qu'il peut utiliser un modèle distant (ex: OpenAI) si configuré (ajouté le support de `OpenAIEncoder`)
- [x] **Task 3 — Valider avec des tests** (AC: #1, #2)
  - [x] 3.1 Vérifier que les tests de Maestro passent toujours (validé avec `test_agent_maestro.py` et `test_maestro_*.py`)

## Dev Notes

### Contexte
Maestro utilise `semantic-router` pour classifier les intentions. Actuellement, il utilise probablement un modèle local (`intfloat/multilingual-e5-small`) ou un mock. La story demande de s'assurer qu'on peut utiliser un vrai modèle (comme `text-embedding-3-small` d'OpenAI) qui nécessite une clé d'API.

## Dev Agent Record

### Agent Model Used
Gemini 3 Flash

### File List
- `src/agent_maestro/router.py`
- `src/common/config.py`
- `_bmad-output/implementation-artifacts/6-3-injection-des-cles-api-dans-le-router-maestro.md`

### Completion Notes List
- Création du fichier de story.
- Ajout de `OPENAI_API_KEY` dans la classe `Settings` de `config.py`.
- Modification de `router.py` pour importer `OpenAIEncoder` et l'utiliser si `EMBEDDING_MODEL` commence par `text-embedding-`.
- Validation avec les tests de Maestro qui passent tous avec succès.

