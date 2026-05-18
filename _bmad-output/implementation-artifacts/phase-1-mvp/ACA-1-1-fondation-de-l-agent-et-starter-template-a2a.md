# Story 1.1: Fondation de l'Agent et Starter Template A2A

Status: done

## Story

As a Developer,
I want to initialize the Acadomie agent using the `src/common/` starter template and the Lean A2A pattern,
so that it operates as an independent, stateless asynchronous A2A server aligned with the established Gourmet reference architecture.

## Acceptance Criteria

1. **Given** the Tegmen ecosystem architecture **When** the Acadomie agent is built and started via Docker Compose (`docker compose --profile acadomie up`) **Then** it runs in its own container without a database connection and boots successfully within 10 seconds.
2. **Given** the running Acadomie agent **When** a JSON-RPC request is sent to `/a2a/SendMessage` **Then** it responds with a valid `JsonRpcResponse` containing a properly formatted A2A message (via `format_a2a_message`).
3. **Given** the running Acadomie agent **When** a GET request is sent to `/a2a/AgentCard` **Then** it returns the agent metadata with all 4 skills (`homework`, `calendar`, `grades`, `organization`) and their enriched semantic descriptions.
4. **Given** the running Acadomie agent **When** a GET request is sent to `/health` **Then** it returns `{"status": "ok", "agent": "acadomie", "mode": "lean"}`.
5. **Given** the agent codebase **When** the code is reviewed **Then** it follows the `app/api/routers/`, `app/schemas/`, `app/services/` directory structure mandated by the architecture document.
6. **Given** the agent codebase **When** tests are run via `pytest tests/agent_acadomie/` **Then** all tests pass with zero network I/O (mocked A2A) and cover the A2A endpoint, agent card, and health check.
7. **Given** the agent **When** the `README.md` is consulted **Then** it documents the agent's purpose, local launch, skills, and A2A contract.

## Tasks / Subtasks

- [ ] **Task 1 — Refactoriser l'arborescence du module** (AC: #5)
  - [ ] 1.1 Créer la structure `src/agent_acadomie/app/api/routers/`, `app/schemas/`, `app/services/`
  - [ ] 1.2 Créer les fichiers `__init__.py` à chaque niveau du package
  - [ ] 1.3 Supprimer les fichiers legacy `agent.py` et `tools.py` (remplacés par la nouvelle architecture Lean)
  - [ ] 1.4 Conserver `instruction.md` s'il contient des prompts utiles (à intégrer dans les services plus tard)
- [ ] **Task 2 — Implémenter le routeur A2A Lean** (AC: #2)
  - [ ] 2.1 Créer `src/agent_acadomie/app/api/routers/a2a.py` — handlers JSON-RPC avec pattern `with_context` et `ACADOMIE_METHODS` dict
  - [ ] 2.2 Implémenter `handle_message_send` comme handler initial (dispatch basique `message/send`)
  - [ ] 2.3 Enregistrer le mapping de méthodes `ACADOMIE_METHODS` pour `create_a2a_app`
- [ ] **Task 3 — Créer les schémas Pydantic fondateurs** (AC: #2, #5)
  - [ ] 3.1 Créer `src/agent_acadomie/app/schemas/__init__.py` exposant les modèles publics
  - [ ] 3.2 Créer les schémas stub minimaux dans des fichiers séparés (homework.py, calendar.py, grades.py) — les modèles complets seront implémentés dans les Stories 1.2 et 1.3
- [ ] **Task 4 — Refondre `main.py` en architecture Lean** (AC: #1, #3, #4)
  - [ ] 4.1 Supprimer l'import `google-adk` (`LlmAgent`, `LiteLlm`) — passage en architecture Lean pure
  - [ ] 4.2 Passer `agent=None` + `methods=ACADOMIE_METHODS` à `create_a2a_app`
  - [ ] 4.3 Enrichir les descriptions sémantiques des 4 skills pour optimiser le filtrage Maestro
  - [ ] 4.4 Ajouter le endpoint `/health` AVANT le `app.mount("/", a2a_app)`
  - [ ] 4.5 Vérifier que le port est bien `8002` dans l'instruction `__main__` (cohérence `docker-compose.yml`)
- [ ] **Task 5 — Corriger le Dockerfile et docker-compose.yml** (AC: #1)
  - [ ] 5.1 Mettre à jour `Dockerfile` : remplacer le CMD `src.agent_acadomie.main:app` par `agent_acadomie.main:app` (aligner sur le pattern Gourmet)
  - [ ] 5.2 Ajouter le volume `config:/app/config` dans `docker-compose.yml` pour le service `acadomie` (actuellement manquant, mais nécessaire pour `agent_registry`)
  - [ ] 5.3 Retirer la dépendance `db` dans docker-compose pour le service `acadomie` (architecture Lean stateless, pas de DB pour le MVP)
- [ ] **Task 6 — Écrire les tests automatisés** (AC: #6)
  - [ ] 6.1 Créer `tests/agent_acadomie/` avec `__init__.py` et `conftest.py`
  - [ ] 6.2 Créer `tests/agent_acadomie/test_acadomie_a2a.py` : test du endpoint `/a2a/SendMessage` (message/send valide, méthode inconnue → error -32601)
  - [ ] 6.3 Tester le endpoint `/a2a/AgentCard` — vérifier les 4 skills et les métadonnées
  - [ ] 6.4 Tester le endpoint `/health`
  - [ ] 6.5 S'assurer que tous les tests utilisent `httpx.AsyncClient` et zéro réseau réel
- [ ] **Task 7 — Rédiger le README.md** (AC: #7)
  - [ ] 7.1 Créer `src/agent_acadomie/README.md` suivant le template agent standardisé du projet

## Dev Notes

### Architecture Critique : Pattern "Lean" (Pas d'ADK)

**DÉCISION FONDAMENTALE** — L'Agent Acadomie actuel utilise `google-adk` (`LlmAgent`). Il **DOIT** être migré vers le pattern Lean identique à l'Agent Gourmet. Cela signifie :
- **Zéro import** de `google.adk.agents` ou `google.adk.models`
- **Zéro import** de `litellm` au niveau module (le LLM sera injecté dans les services via DI dans les stories suivantes)
- Les handlers JSON-RPC dans `app/api/routers/a2a.py` gèrent directement les requêtes
- L'architecture est : `FastAPI → A2AServer → Handlers → Services → Schemas`

### Pattern de Référence : Agent Gourmet

Le fichier de référence principal est [a2a.py](file:///home/ngombert/projects/tegmen/src/agent_gourmet/app/api/routers/a2a.py). Suivre **exactement** ce pattern :

1. **`GOURMET_METHODS` dict** → Créer `ACADOMIE_METHODS` équivalent
2. **`with_context` decorator** → Réutiliser le même pattern (correlation_id, error enrichment)
3. **`handle_message_send`** → Dispatcher basique par mots-clés pour cette story fondatrice
4. **`format_a2a_message`** → Utiliser `common.a2a_utils.format_a2a_message` pour les réponses

### Modules `context.py` et `logger.py`

Créer des versions Acadomie de ces fichiers en suivant le pattern Gourmet :
- `src/agent_acadomie/app/context.py` → `ContextVar` pour `correlation_id` + helpers `set_correlation_id`, `reset_correlation_id`, `get_correlation_id`, `enrich_error_data`
- `src/agent_acadomie/app/logger.py` → `JSONFormatter` + `setup_acadomie_logger` (service name: `"acadomie"`)

### Imports Critiques à Utiliser

```python
# Common library (RÉUTILISER, ne pas réinventer)
from common.a2a_server import create_a2a_app
from common.config import config
from common.agent_registry import agent_registry
from common.logger import setup_logger
from common.exceptions import A2ARPCError
from common.a2a_utils import format_a2a_message
from common.schemas import JsonRpcRequest, JsonRpcResponse
```

### Descriptions Sémantiques des Skills (pour Maestro)

Les descriptions doivent être **riches et optimisées** pour le routeur sémantique de Maestro (`semantic-router` + `sentence-transformers`). Exemple enrichi :

```python
skills=[
    {
        "id": "homework",
        "name": "homework",
        "description": "Consulter la liste des devoirs scolaires à faire, ajouter un nouveau devoir avec matière, consigne et date limite. Couvre les exercices, les leçons à apprendre et les projets scolaires.",
    },
    {
        "id": "calendar",
        "name": "calendar",
        "description": "Consulter le calendrier scolaire, les événements à venir (examens, sorties scolaires, réunions parents-professeurs, vacances). Permet d'anticiper l'organisation familiale.",
    },
    {
        "id": "grades",
        "name": "grades",
        "description": "Consulter les notes et résultats scolaires de l'élève par matière. Suivi de la progression académique, moyennes et dernières évaluations.",
    },
    {
        "id": "organization",
        "name": "organization",
        "description": "Fournir des conseils personnalisés d'organisation scolaire, de planification des révisions et de gestion du temps pour les devoirs et examens.",
    },
]
```

### Dockerfile — Correction d'Import Obligatoire

Le Dockerfile actuel utilise `src.agent_acadomie.main:app`. Le pattern Gourmet fonctionnel utilise `agent_acadomie.main:app` (sans le préfixe `src.`). Vérifier la cohérence avec le `PYTHONPATH` et le `COPY` du Dockerfile.

**Pattern Gourmet de référence :**
```dockerfile
COPY src/common ./src/common
COPY src/agent_gourmet ./src/agent_gourmet
ENV PYTHONPATH=/app/src
CMD ["uvicorn", "agent_gourmet.main:app", ...]
```

⚠️ **ATTENTION** : Le Dockerfile Acadomie actuel a `PYTHONPATH=/app` et copie dans `src/`. Il faut aligner le PYTHONPATH sur `/app/src` ou adapter le CMD. Vérifier le Dockerfile Gourmet pour la bonne approche.

### Docker Compose — Volume Config Manquant

Le service `acadomie` dans `docker-compose.yml` n'a PAS le volume `./config:/app/config` (contrairement à `gourmet` et `maestro`). Ce volume est **nécessaire** pour que `agent_registry.py` puisse charger `config/agents.yaml`. À ajouter.

### Docker Compose — Dépendance DB à Retirer

Le service `acadomie` dépend actuellement de `db: condition: service_healthy`. Pour le MVP Lean (stateless, mocks en mémoire), cette dépendance est inutile et ralentit le démarrage. La retirer et supprimer `DATABASE_URL` de l'environnement.

### Project Structure Notes

**Structure cible après implémentation :**
```
src/agent_acadomie/
├── Dockerfile
├── README.md
├── instruction.md          # Conservé pour prompts futurs
├── __init__.py
├── main.py                 # Refondé (Lean, sans ADK)
└── app/
    ├── __init__.py
    ├── context.py           # ContextVar correlation_id
    ├── logger.py            # JSONFormatter Acadomie
    ├── api/
    │   ├── __init__.py
    │   └── routers/
    │       ├── __init__.py
    │       └── a2a.py       # Handlers JSON-RPC + ACADOMIE_METHODS
    ├── schemas/
    │   ├── __init__.py
    │   ├── homework.py      # HomeworkSchema (stub)
    │   ├── calendar.py      # CalendarEvent (stub)
    │   └── grades.py        # GradeResponse (stub)
    └── services/
        ├── __init__.py
        └── acadomie_service.py  # Service métier (stub pour Story 1.1)
```

**Fichiers supprimés (legacy) :**
- `agent.py` (utilisait `google-adk` → remplacé par architecture Lean)
- `tools.py` (fonctions synchrones avec `json.dumps` → remplacé par schemas Pydantic + services async)

### Testing Requirements

- **Framework :** `pytest` + `pytest-asyncio` (`asyncio_mode="auto"`)
- **Client :** `httpx.AsyncClient` (pas `TestClient` synchrone)
- **Réseau :** Zéro I/O réseau en CI — toutes les interactions sont mockées
- **Couverture :** Tests des 3 endpoints (`/a2a/SendMessage`, `/a2a/AgentCard`, `/health`) + test de méthode inconnue

**Pattern de test de référence (Agent Gourmet) :**
```python
import pytest
from httpx import AsyncClient, ASGITransport
from agent_acadomie.main import app

@pytest.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
```

### Anti-Patterns à Éviter

| ❌ Anti-Pattern | ✅ Pattern Correct |
|---|---|
| `from google.adk.agents import LlmAgent` | Architecture Lean sans ADK |
| `def get_homework(...)` (synchrone) | `async def handle_homework(...)` |
| `json.dumps(...)` comme retour | `schema.model_dump()` via Pydantic |
| `import litellm` au niveau module | Injection via `Depends()` (Story 2.2) |
| `except Exception: pass` | `except Exception: raise A2ARPCError(...)` |
| `time.sleep()` | `asyncio.sleep()` |
| `typing.Optional[X]` | `X | None` |
| `typing.List[str]` | `list[str]` |

### References

- [Source: architecture.md — Code Organization](file:///home/ngombert/projects/tegmen/_bmad-output/planning-artifacts/architecture.md#L91-L97)
- [Source: architecture.md — Structure Patterns](file:///home/ngombert/projects/tegmen/_bmad-output/planning-artifacts/architecture.md#L158-L165)
- [Source: architecture.md — Process Patterns & DI](file:///home/ngombert/projects/tegmen/_bmad-output/planning-artifacts/architecture.md#L179-L182)
- [Source: project-context.md — Testing Rules](file:///home/ngombert/projects/tegmen/_bmad-output/project-context.md#L46-L51)
- [Source: Agent Gourmet main.py (pattern de référence)](file:///home/ngombert/projects/tegmen/src/agent_gourmet/main.py)
- [Source: Agent Gourmet a2a.py (pattern handlers)](file:///home/ngombert/projects/tegmen/src/agent_gourmet/app/api/routers/a2a.py)
- [Source: Agent Gourmet context.py (observabilité)](file:///home/ngombert/projects/tegmen/src/agent_gourmet/app/context.py)
- [Source: Agent Gourmet logger.py (JSON logging)](file:///home/ngombert/projects/tegmen/src/agent_gourmet/app/logger.py)
- [Source: common/a2a_server.py (factory)](file:///home/ngombert/projects/tegmen/src/common/a2a_server.py)
- [Source: common/exceptions.py (A2ARPCError)](file:///home/ngombert/projects/tegmen/src/common/exceptions.py)
- [Source: config/agents.yaml (registre)](file:///home/ngombert/projects/tegmen/config/agents.yaml)
- [Source: docker-compose.yml](file:///home/ngombert/projects/tegmen/docker-compose.yml)

## Dev Agent Record

### Agent Model Used

(à remplir lors de l'implémentation)

### Debug Log References

### Completion Notes List

### File List
