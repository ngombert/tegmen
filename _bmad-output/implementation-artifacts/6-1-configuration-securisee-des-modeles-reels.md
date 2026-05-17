# Story 6.1: Configuration Sécurisée des Modèles Réels

Status: review

## Story

As a Developer,
I want to configure `litellm` to call real models (e.g., `gpt-4o-mini` or `claude-3-haiku`) via environment variables,
so that I can unplug mocks in development/production environments while maintaining API key security.

## Acceptance Criteria

1. **Given** the Tegmen ecosystem **When** API keys (e.g., `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`) are defined in a `.env` file **Then** they are loaded and used by `litellm` without being tracked by Git.
2. **Given** the repository configuration **When** Gitleaks is run **Then** it prevents accidental commit of API keys, respecting `.gitleaks.toml`.
3. **Given** the `LLMService` **When** a configuration flag or environment variable is set **Then** it allows switching between a `MockLLM` (or mocked behavior) and the `RealLLM` (actual API calls).

## Tasks / Subtasks

- [x] **Task 1 — Configurer les variables d'environnement** (AC: #1)
  - [x] 1.1 Ajouter les variables d'exemple dans `.env.example` (sans valeurs réelles)
  - [x] 1.2 S'assurer que `.env` est ignoré par Git (vérifier `.gitignore`)
- [x] **Task 2 — Vérifier la configuration Gitleaks** (AC: #2)
  - [x] 2.1 Vérifier que `.gitleaks.toml` contient des règles pour les clés d'API courantes (repose sur les règles par défaut de Gitleaks 8+)
- [x] **Task 3 — Implémenter le mécanisme de bascule Mock/Real** (AC: #3)
  - [x] 3.1 Modifier `LLMService` pour supporter un mode mock basé on une variable d'environnement (ex: `USE_MOCK_LLM=true`)
  - [x] 3.2 Permettre l'injection ou la configuration facile du modèle à utiliser
- [x] **Task 4 — Valider avec des tests** (AC: #1, #3)
  - [x] 4.1 Ajouter un test vérifiant que le mode mock fonctionne
  - [x] 4.2 S'assurer que les tests existants ne sont pas cassés et continuent d'utiliser des mocks

## Dev Notes

### Contexte
Cette story fait partie de l'Epic "MVP V1.5 - Transition vers un Moteur LLM Réel". L'objectif est de préparer le terrain pour l'utilisation de vrais modèles en sécurisant les clés et en permettant de basculer facilement entre mock et réel.

### Mode Mock
Actuellement, les tests mockent `litellm.acompletion`. Pour le développement local sans clés, il serait utile d'avoir un mode mock intégré au service qui renvoie une réponse statique si `USE_MOCK_LLM` est à `true` ou si les clés nécessaires sont manquantes.

### Gitleaks
Vérifier que `.gitleaks.toml` est présent et configuré pour détecter les clés OpenAI, Anthropic, etc.

## Dev Agent Record

### Agent Model Used
Gemini 3 Flash

### File List
- `.env.example`
- `src/agent_acadomie/app/services/llm_service.py`
- `tests/test_agent_acadomie/test_llm_service.py`
- `src/agent_gourmet/app/services/llm_service.py`
- `tests/agent_gourmet/test_llm_service.py`
- `_bmad-output/implementation-artifacts/6-1-configuration-securisee-des-modeles-reels.md`
- `_bmad-output/implementation-artifacts/sprint-status-agent-acadomie.yaml`

### Completion Notes List
- Création du fichier de story.
- Ajout des variables `OPENAI_API_KEY` et `ANTHROPIC_API_KEY` dans `.env.example`.
- Vérification que `.env` est ignoré par Git.
- Vérification de la configuration Gitleaks (repose sur les règles par défaut).
- Implémentation du mode mock dans `LLMService` via `USE_MOCK_LLM` pour Acadomie ET Gourmet.
- Ajout de la possibilité de surcharger le modèle dans `generate_response`.
- Création des tests dans `test_llm_service.py` pour les deux agents et validation (passent à 100%).
- Note: Un conflit de collecte pytest existe entre `tests/test_agent_acadomie/` et `tests/test_agent_acadomie.py` pré-existant, mais les tests de l'agent passent en les lançant explicitement.

