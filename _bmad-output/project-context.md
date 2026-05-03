---
project_name: 'Tegmen (Family-Agents)'
user_name: 'Nicolas'
date: '2026-04-15'
sections_completed: ['technology_stack', 'language_rules', 'framework_rules', 'testing_rules', 'quality_rules', 'workflow_rules', 'anti_patterns']
status: 'complete'
rule_count: 23
optimized_for_llm: true
---

# Project Context for AI Agents

_This file contains critical rules and patterns that AI agents must follow when implementing code in this project. Focus on unobvious details that agents might otherwise miss._

---

## Technology Stack & Versions

- **Python**: >=3.13
- **Packager**: `uv` (Astral) - Indispensable pour la gestion d'environnement.
- **Core AI**: `google-adk` (>=1.18.0) pour l'orchestration, `litellm` (>=1.80.5).
- **Routage Local**: `semantic-router` (>=0.1.12) et `sentence-transformers` (>=5.2.0) au niveau du gateway.
- **Frontend / API**: `fastapi` (>=0.124.4) propulsé par `uvicorn` (>=0.38.0).
- **Database**: PostgreSQL géré par `sqlalchemy[asyncio]` (>=2.0.45) et `asyncpg` (>=0.31.0).
- **Protocoles (Microservices)**: HTTP / JSON-RPC via `a2a-sdk` (>=0.3.21). **Règle Topologique** : L'agent Maestro = Client A2A / API Gateway, agents (Gourmet, Explorer...) = serveurs A2A isolés.
- **Tests (Dev)**: `pytest` (>=9.0.2), `pytest-asyncio` (>=1.3.0) en `asyncio_mode = "auto"`. Couverture obligatoire.
- **Validation Stricte de la Baseline (Audit en Continu)** : L'état actuel de `pyproject.toml` et `uv.lock` constitue la baseline technique. Tout ajout de nouvelle dépendance est une action à haut impact exigeant une justification et une validation humaine explicite.

## Critical Implementation Rules

### Language-Specific Rules (Python)

- **Strict Typing:** Must use strict Python Type Hints (mypy/pyright compatible) across the entire codebase. No generic `Any` types without explicit justification.
- **Asynchronous Patterns:** Strict usage of `async/await`. Avoid any blocking code in the main event loop. All I/O operations (database via `asyncpg`, LLM calls via `litellm`, internal routing) must be asynchronous.
- **Environment & Dependencies:** Strict usage of `uv` for package management. Do not use `pip` commands directly. Ensure environment isolation.

### Framework-Specific Rules

- **FastAPI / Pydantic :** Utilisation systématique de Pydantic (v2) pour la validation stricte des schémas d'entrée/sortie (`model_validate`). La structure de dossiers impose de placer les endpoints dans `app/api/routers/` et les objets métier dans `app/schemas/`.
- **Architecture Multi-Agents A2A :** Le système adopte la séparation Agent-to-Agent. L'agent principal (Maestro) agit comme client A2A et API Gateway, tandis que les agents spécialisés (Gourmet, Explorer...) sont des serveurs A2A indépendants.
- **Registre d'Agents Config-Driven (ADR 2026-04-18) :** Le catalogue des agents disponibles est défini exclusivement dans `config/agents.yaml` (hors `src/`) et chargé par `src/common/agent_registry.py`. Maestro ne possède aucun import Python direct vers les modules des sous-agents. L'ajout d'un agent se fait par configuration (nom, URL, description, utterances sémantiques), sans modification du code source. Les URLs sont surchargeables par variable d'environnement (`AGENT_<NAME>_URL`). Le mode monolithe (imports in-process) est formellement interdit.
- **Résilience Réseau A2A :** Le protocole de communication (HTTP / JSON-RPC avec `a2a-sdk`) exige la configuration de time-outs stricts et d'une politique de retry. Rattrapage obligatoire des exceptions `A2ARPCError` et `httpx.TimeoutException` en production.
- **Tests des interactions A2A :** Tous les tests ciblant une transmission inter-agents doivent isoler le réseau et mocker les appels. **Règle Stricte (Audit A2A)** : Toute réponse simulée ou réelle pour `message/send` doit impérativement être validée contre `a2a.types.SendMessageResponse` (ou modèle équivalent du SDK). L'utilisation de dictionnaires JSON "plats" non validés est formellement interdite afin de garantir l'interopérabilité avec Maestro.
- **Google ADK & Routage Sémantique :** Utilisation de `google-adk` pour l'orchestration LLM. Le triage par Maestro de l'intention utilisateur s'effectue via `semantic-router` (et `sentence-transformers`) afin de limiter fortement la consommation inutile de tokens et la latence.

### Testing Rules

- **Framework & Asynchronisme :** Utilisation exclusive de `pytest` avec `pytest-asyncio` (configuré en `asyncio_mode="auto"`). Tout test ciblant une logique FastAPI ou un service asynchrone doit impérativement être une coroutine (`async def test_...`).
- **Isolation Réseau & Mocks (LLM + A2A) :** Règle d'or : "Zéro I/O réseau en CI". Il est formellement interdit de faire appel à de vraies API de LLM (utiliser le retour mocké de `litellm`) ou de lancer de vrais appels A2A inter-agents. Le SDK client doit systématiquement être mocké.
- **Périmètre et Cas aux Limites :** Une couverture systématique de la logique métier (schémas Pydantic, routes FastAPI) est attendue. Les scénarios de défaillance (time-outs RPC, payloads invalides) doivent avoir leurs tests dédiés.

### Code Quality & Style Rules

- **Formatage & Linting :** Respect strict des standards Python récents (PEP8). Si des outils comme Ruff ou Black sont implémentés, l'agent doit formater son code selon leurs standards sans produire de warnings. 
- **Conventions de Nommage :** Format `snake_case` classique pour les variables locales et méthodes. Format `PascalCase` obligatoire pour les classes et particulièrement les Modèles Pydantic. Format `UPPER_SNAKE_CASE` pour les constantes globales.
- **Documentation Automatique (FastAPI) :** Toute route d'API doit systématiquement intégrer son docstring et préciser les champs `summary` et `description` afin d'alimenter correctement Swagger / OpenAPI. Ceci est crucial pour interagir facilement en A2A.
- **Documentation des Compétences (Google ADK) :** Les "Skills" exposées au LLM via l'ADK doivent impérativement avoir des docstrings exhaustives (description précise des arguments et de l'objectif), car elles servent de prompt de décision pour le module de tri.
- **Documentation Microservice Obligatoire :** Chaque agent (`src/agent_*/`) et le module `common/` doivent contenir un `README.md` dédié suivant le template standardisé du projet (cf. `docs/templates/README-gateway.template.md` pour le gateway, `docs/templates/README-agent.template.md` pour les agents domaine). Ce README doit être créé lors de l'epic fondateur de l'agent et mis à jour à chaque story modifiant l'API, la configuration ou les skills A2A. Le README ne duplique pas le Swagger (un lien suffit) mais documente le périmètre métier, le lancement standalone, les tests et le contrat A2A. L'absence de README est un critère bloquant pour la validation d'un epic.

### Development Workflow Rules

- **Environnements & Sécurité :** Séparation stricte entre l'environnement de développement local et la production. Les agents modifient uniquement le code en développement. Aucun agent ne doit modifier la base de code ou la base de données de production "à la volée". Le déploiement s'effectue via le pipeline sur la branche `main`.
- **Règles Git & Traçabilité :** Utilisation systématique des Conventional Commits (`feat:`, `fix:`, `docs:`, `chore:`), en mentionnant le nom de la story ou du composant ciblé pour la traçabilité.
- **Gestion des Dépendances (Baseline Stricte) :** `pyproject.toml` et `uv.lock` constituent le socle de dépendances. Effectuer un appel `uv add` est une opération critique nécessitant validation humaine.
- **Planification & Revues :** Les agents doivent planifier leurs actions (`docs/specs/` ou `_bmad-output/`) avant de coder ("Planifier d'abord, coder ensuite"). Si le code généré est complexe, il sera soumis à une revue adversariale automatisée (`bmad-code-review`) pour vérifier les conditions aux limites.

### Critical Don't-Miss Rules

- **Anti-Pattern Asynchrone Absolu :** Ne JAMAIS introduire de code bloquant (appels I/O synchrones classiques, fonctions comme `time.sleep()`) au sein des coroutines asyncio. Utilisez systématiquement `asyncio.sleep()` et `httpx` (ou utilitaires `aio`).
- **Sécurité et Confidentialité :** Interdiction stricte de logger en clair des données sensibles (clés API LiteLLM, tokens Google ADK) ou des PII (données de la famille, habitudes, agenda). Ces informations doivent être masquées dans les journaux système.
- **Fail-Fast (Erreurs silencieuses interdites) :** Interdiction d'écrire des blocs `except Exception: pass`. Si un sous-agent A2A échoue, l'erreur doit être loggée et transmise à Maestro pour informer formellement la famille de l'indisponibilité.
- **Anti-Hallucination :** En l'absence de données fiables (agenda vide, APIs métier indisponibles), les sous-agents ont instruction explicite de répondre qu'ils ignorent l'information plutôt que d'halluciner des résultats.

---

## Usage Guidelines

**For AI Agents:**

- Read this file before implementing any code
- Follow ALL rules exactly as documented
- When in doubt, prefer the more restrictive option
- Update this file if new patterns emerge

**For Humans:**

- Keep this file lean and focused on agent needs
- Update when technology stack changes
- Review quarterly for outdated rules
- Remove rules that become obvious over time

Last Updated: 2026-04-15
