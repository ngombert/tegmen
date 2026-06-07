---
stepsCompleted: [1, 2, 3, 4, 5, 6, 7, 8]
workflowType: 'architecture'
lastStep: 8
status: 'complete'
completedAt: '2026-05-19'
project_name: 'tegmen'
user_name: 'Nicolas'
---

# Architecture Decision Document

_This document builds collaboratively through step-by-step discovery. Sections are appended as we work through each architectural decision together._

## Analyse du Contexte du Projet

### Aperçu des Exigences

**Exigences Fonctionnelles (FR) :**
- **Routage et Orchestration :** Routage explicite ou sémantique vers des agents experts, capacité multi-agents simultanée (Party Mode), et clarification des ambiguïtés (FR1-FR5).
- **Gestion des Interruptions :** Mécanisme de « Yield » permettant de suspendre, mémoriser et restaurer le contexte d'une session experte (FR6-FR8).
- **Mémoire Distribuée :** Auto-évaluation des nouveaux faits, stockage sémantique et relationnel (pgvector), et croisement des faits intégrés directement dans l'invite (prompt) du modèle (FR9-FR11).
- **Résilience de l'Écosystème :** Isolation complète des déploiements (bases de données indépendantes) pour garantir le Zéro Downtime mutuel (FR12-FR13).

**Exigences Non-Fonctionnelles (NFR) :**
- **Performance :** Tolérance de latence (TTFT < 15s pour le Party Mode, < 5s en Tunnel Mode), qui dépend absolument d'un retour UX en moins de 500ms (NFR1-NFR3).
- **Persistance :** Bases de données isolées (PostgreSQL/Alembic par agent) avec modèle hybride limitant l'épuisement des pools de connexions asynchrones (NFR4-NFR5).
- **Résilience :** Dégradation gracieuse éprouvée via chaos engineering avec une Timebox stricte (10s), et interception des exceptions réseau pour éviter les fuites de coroutines (NFR6-NFR8).

**Échelle & Complexité :**
- **Domaine principal :** API Backend / Microservices IA (Protocole A2A)
- **Niveau de complexité :** Élevé (Système distribué hybride avec mémoire asynchrone, persistance décentralisée et orchestration parallèle)
- **Composants architecturaux estimés :** Passerelle centrale (Maestro) responsable de l'état global + N Agents Spécialistes isolés.

### Contraintes Techniques & Dépendances

- Architecture microservices asynchrone en Python (`asyncio`, FastAPI).
- Utilisation stricte de Pydantic pour la validation bidirectionnelle des schémas d'état inter-agents (`State Update Payload`) et sécurisation du contrat JSON-RPC.
- Protocole A2A étendu pour transporter la `Context Stack` et le `new_facts_payload` (déclaré optionnel pour garantir la rétrocompatibilité).
- Dépendances requises : `google-adk`, `litellm`, `semantic-router`, `sqlalchemy[asyncio]`, `asyncpg`, gérées exclusivement via `uv`.
- L'instruction des agents par prompt système doit être infaillible pour forcer le déclenchement de la Trappe de Sortie (Yield) plutôt que de risquer une hallucination.

### Problématiques Transversales Identifiées

- **Propriété exclusive du Context Stack (Décision Architecturale) :** Afin de garantir la résilience, les agents spécialisés seront traités comme strictement « Stateless ». Maestro devient l'unique propriétaire du `Context Stack` et l'injecte via le champ `params.context` du protocole JSON-RPC. 
  *Mitigation de l'inférence :* L'augmentation redoutée des coûts de tokens (Maestro + Agent sur le même contexte) est contournée par l'utilisation du tri par `semantic-router`. En Tunnel Mode, Maestro agit comme un routeur sémantique local transparent, sans appel LLM lourd. Il réserve sa puissance d'inférence coûteuse uniquement pour les résolutions d'interruptions (Yield) et les synthèses du "Party Mode".
- **Cycle de Vie et Péremption des Contextes :** Maestro doit intégrer un mécanisme de nettoyage (Garbage Collection) des contextes suspendus. Si une "Trappe de Sortie" s'éternise et devient une nouvelle conversation pérenne (mesuré par le volume d'échanges hors-contexte ou un timeout), la pile d'interruption doit être silencieusement nettoyée. De plus, lors de la proposition de retour au sujet initial, Maestro doit être capable de gérer une clôture explicite ("laisse tomber ce sujet finalement") pour vider manuellement la pile.
- **Réseau, A2A et Chaos Testing :** L'orchestration asynchrone (ex: `asyncio.gather` en Party Mode) expose le système à des risques de timeouts en chaîne. Des tests de résilience intensifs (contrats inter-services, timeouts réseau simulés) sont indispensables.
- **Intégrité de la Persistance Distribuée :** L'absence de base SQL centralisée reporte la responsabilité de l'intégration des données sur le modèle linguistique (agrégation par le prompt) et sur l'infaillibilité du validateur Pydantic inter-services.

## Starter Template Evaluation

### Primary Technology Domain
API Backend (Microservices IA) - **Évolution Brownfield (Phase 2)**

### Starter Options Considered
- **Nouveau Boilerplate Externe (Tiangolo, etc.) :** Rejeté. Repartir de zéro casserait l'écosystème MVP fonctionnel.
- **Base de Code Phase 1 (Existant) :** La structure actuelle du projet sous `src/` sert de fondation (starter) pour la Phase 2.

### Selected Starter: Tegmen Phase 1 Codebase

**Rationale for Selection:**
Le projet étant dans sa Phase 2, le MVP est déjà fonctionnel avec son architecture microservices (Maestro + Agents Spécialistes). L'adoption d'un nouveau starter template serait un anti-pattern total. La fondation technique ayant déjà été éprouvée, la stratégie est de bâtir par-dessus l'existant en y greffant la couche de persistance (Alembic, asyncpg, pgvector).

**Architectural Decisions Provided by Existing Base:**

**Language & Runtime:**
Python 3.13 géré de manière stricte via `uv` avec un workspace/environnement virtuel déjà configuré.

**Build Tooling:**
Le fichier `pyproject.toml` (et `uv.lock`) existant fixe déjà la baseline stricte des dépendances. Toute nouvelle dépendance pour la persistance (comme `sqlalchemy[asyncio]` ou `asyncpg`) s'ajoutera via des commandes `uv add` ciblées.

**Testing Framework:**
L'infrastructure `pytest` et `pytest-asyncio` est déjà en place. Les mocks du SDK A2A existent et doivent simplement être étendus pour supporter le `new_facts_payload` et la `Context Stack`.

**Code Organization:**
La structure du monorepo est déjà standardisée :
- Routage principal : `src/agent_maestro/`
- Microservices indépendants : `src/agent_gourmet/`, `src/agent_acadomie/`, `src/agent_explorer/`
- Librairies partagées (A2A, Registry) : `src/common/`

**Development Experience:**
Boucle de développement asynchrone existante (FastAPI + uvicorn) prête à accueillir les schémas Pydantic étendus de la Phase 2.

## Core Architectural Decisions

### Decision Priority Analysis

**Critical Decisions (Block Implementation):**
- **Stratégie de Migration :** Exécution manuelle/CI d'Alembic. Bloquant pour la mise en place des pipelines de déploiement et des scripts d'environnement.
- **Support pgvector (Dépendance technique) :** L'image Docker de la base de données devra être modifiée (ex: passage de `postgres:18-alpine` à `pgvector/pgvector:pg18`) pour supporter les embeddings des "Soft-Facts".

**Important Decisions (Shape Architecture):**
- **Sécurité A2A :** API Key partagée (`X-A2A-Secret`) - maintien de la décision de la Phase 1. Le réseau fermé de Docker apporte une sécurité périmétrique, et le token assure l'authentification applicative entre les microservices.
- **Infrastructure Locale :** Réutilisation et adaptation du `docker-compose.yml` existant.

**Deferred Decisions (Post-MVP):**
- Métriques et monitoring avancé (Prometheus/Grafana).

### Data Architecture

- **SGBD :** PostgreSQL (Version ciblée : 18).
- **Migration :** Alembic (>= 1.18.4) avec exécution manuelle ou via CI/CD (`alembic upgrade head`), proscrivant formellement l'exécution automatique au démarrage de l'app pour éviter les corruptions lors du "Zero Downtime".
- **Isolation :** Un conteneur Postgres unique en développement avec des bases logiques séparées (`maestro`, `gourmet`, `acadomie`, `explorer`) initialisées par un script d'entrée (`init-multiple-dbs.sh`).

### Authentication & Security

- **Sécurité Externe :** Maestro agit comme API Gateway et valide les JWT pour garantir l'identité de l'utilisateur (Phase 1).
- **Sécurité Inter-Agents (A2A) :** API Key partagée (`X-A2A-Secret`). Maestro transmet ce token dans ses en-têtes HTTP JSON-RPC, et les agents spécialisés le valident localement.

### API & Communication Patterns

- **Réseau :** Appels HTTP internes asynchrones (via `httpx`). Le protocole JSON-RPC de la Phase 1 est étendu pour supporter les nouveaux schémas de données (`Yield`, `Context Stack`, `correlation_id`) sans altérer les interfaces de base.
- **Traçabilité :** Tout payload entrant dans l'API Gateway se voit attribuer un `correlation_id` unique qui cascade à travers toutes les requêtes inter-agents (A2A).
- **SDK Versioning :** Les contrats définis dans `src/common/` doivent évoluer par ajouts optionnels. Toute rupture de contrat impose un versionnement de l'API A2A pour maintenir le "Zero Downtime Mutuel".

### Infrastructure & Deployment

- **Orchestration locale :** Docker Compose avec intégration des profils Docker (`profiles: ["gourmet", "all", "agents"]`) pour lancer les microservices de manière granulaire selon les besoins du développeur. L'image Postgres sera mise à jour pour supporter `pgvector`.

## Implementation Patterns & Consistency Rules

### Pattern Categories Defined

**Critical Conflict Points Identified:**
3 zones de conflits critiques identifiées entre les agents spécialisés (Nommage Pydantic/JSON, Propriété des schémas BDD, et Flux de contrôle métier).

### Naming Patterns

**API & Code Naming Conventions (JSON-RPC & Pydantic):**
- **Règle :** Reprise du standard de la Phase 1 (`src/common/schemas.py`). Utilisation stricte du `snake_case` pour tous les champs d'API JSON, paramètres RPC et variables Python.
- **Exemple :** `family_id`, `new_facts_payload`, `context_stack` (Jamais de camelCase).

**Database Naming Conventions (SQLAlchemy/Alembic):**
- **Règle :** Noms de tables au pluriel en `snake_case`. Colonnes en `snake_case` stricts.
- **Exemple :** Table `soft_facts`, colonne `user_id`, index `idx_soft_facts_user`.

### Structure Patterns

**Project Organization & File Structure:**
- **Règle (Pattern 2B) :** Isolation stricte (Microservices). Chaque agent possède et gère en totale autonomie ses schémas, modèles ORM, et versions de migration Alembic.
- **Exemple :** Les migrations d'Acadomie iront exclusivement dans `src/agent_acadomie/app/db/alembic/`. Il n'y aura aucun dossier `alembic` transversal partagé à la racine du monorepo.

### Format & Communication Patterns

**API Response Formats (Yield Pattern):**
- **Règle (Pattern 3B) :** Une "Trappe de Sortie" (Yield) est un flux de contrôle métier nominal, pas une erreur système. Elle ne doit jamais être levée via une exception Python. Elle doit être retournée comme un objet Pydantic standard imbriqué dans la propriété `result` du JSON-RPC.
- **Exemple :**
  ```json
  "result": {
    "status": "yield",
    "context_stack": [{"intent": "math_homework"}],
    "message": "Je rends la main, ce n'est pas mon domaine."
  }
  ```

### Enforcement Guidelines

**All AI Agents MUST:**
- Respecter le `snake_case` universel pour garantir la compatibilité Pydantic/SQLAlchemy sans alias.
- Restreindre l'étendue de leurs modifications de schémas (Alembic/ORM) strictement à leur propre périmètre (dossier de l'agent).
- Renoncer au traitement par exception (try/except) pour le routage sémantique, en faveur d'un typage fort (Pydantic `YieldResponse`).

**Pattern Enforcement:**
- Ces modèles feront autorité pour le linter (Ruff) et les revues de code (`bmad-code-review`).
- Toute modification d'un composant partagé (`src/common/`) pour des besoins spécifiques à un agent sera systématiquement rejetée.

## Project Structure & Boundaries

### Complete Project Directory Structure

Étant donné que Tegmen est dans sa Phase 2, la structure reflète l'évolution du monorepo existant géré par `uv`, enrichi de la couche de persistance décentralisée.

```text
tegmen/
├── README.md
├── pyproject.toml           # Gestion des dépendances par 'uv'
├── uv.lock                  # Lockfile strict
├── docker-compose.yml       # Orchestration locale (avec pgvector)
├── .env                     # Variables d'environnement
├── scripts/
│   └── init-multiple-dbs.sh # Script de provisionnement des bases logiques
├── src/
│   ├── common/              # Librairies A2A partagées
│   │   ├── schemas.py       # Schémas JSON-RPC, ContextStack, YieldResponse (snake_case)
│   │   ├── a2a_client.py
│   │   └── a2a_server.py
│   ├── agent_maestro/       # Gateway & Routeur (Propriétaire de l'état global)
│   │   ├── Dockerfile
│   │   ├── main.py
│   │   └── app/
│   │       ├── api/routers/
│   │       ├── db/          # [NOUVEAU Phase 2]
│   │       │   ├── alembic/ # Migrations propres à Maestro (Context Stack)
│   │       │   └── models/  # Modèles ORM Maestro
│   │       ├── schemas/     # Validation Pydantic (Auth, etc.)
│   │       └── services/    # Logique de routage sémantique
│   ├── agent_gourmet/       # Agent Spécialiste
│   │   ├── Dockerfile
│   │   ├── main.py
│   │   └── app/
│   │       ├── api/routers/ # Endpoints A2A internes
│   │       ├── db/          # [NOUVEAU Phase 2]
│   │       │   ├── alembic/ # Migrations isolées
│   │       │   └── models/  # Modèles ORM (pgvector)
│   │       ├── prompts/
│   │       └── services/
│   ├── agent_acadomie/      # (Structure identique)
│   └── agent_explorer/      # (Structure identique)
└── tests/
    ├── agent_maestro/       # Tests unitaires & intégration
    ├── agent_gourmet/
    └── common/              # Mocks A2A
```

### Architectural Boundaries

**API Boundaries:**
- **Frontière Externe :** Seul le port HTTP de `agent_maestro` est exposé à l'extérieur du réseau Docker. Il centralise l'authentification (JWT) et le "Context Shield" pour expurger les données sensibles (PII).
- **Frontière Interne (A2A) :** Les agents spécialisés (Gourmet, Acadomie) ne sont accessibles qu'en interne via le protocole JSON-RPC (port interne de leurs conteneurs respectifs). Ils exigent le `X-A2A-Secret`.

**Data Boundaries:**
- **Cloisonnement Strict :** Aucun agent n'a accès à la base de données d'un autre agent. Les jointures SQL inter-domaines sont **interdites** par conception.
- **Intégration des Données :** Si Gourmet a besoin de connaître une restriction issue d'Acadomie, l'information transite obligatoirement par le `Context Stack` de Maestro.

### Requirements to Structure Mapping

**Phase 2 Persistence (Asymétrique) :**
- **Pile de Contexte (FR7, FR8) :** Gérée par `src/agent_maestro/app/db/models/context.py` et exposée dans `src/common/schemas.py`.
- **Soft/Hard Facts (FR9, FR10) :** Stockés spécifiquement dans `src/agent_NAME/app/db/models/facts.py` (utilisant `pgvector` pour l'agent concerné).

**Processus de Développement (Zero Downtime) :**
- **Migrations Alembic :** Chaque agent maintient son historique dans `src/agent_NAME/app/db/alembic/versions/`. L'exécution automatique au démarrage (`main.py`) est interdite. Les migrations doivent être lancées via CI ou script externe avant le redéploiement du conteneur.

## Architecture Validation Results

### Coherence Validation ✅

**Decision Compatibility:**
Toutes les décisions (Python 3.13, FastAPI, uv, PostgreSQL avec `pgvector`, protocole JSON-RPC) sont parfaitement compatibles. L'architecture décentralisée pour Alembic respecte la frontière stricte des microservices imposée en Phase 1.

**Pattern Consistency:**
Le choix du `snake_case` universel garantit une interopérabilité sans friction entre SQLAlchemy, Pydantic et le payload JSON-RPC. Le traitement du Yield via un objet Pydantic normalisé est beaucoup plus performant qu'une levée d'exceptions coûteuses.

**Structure Alignment:**
La structure isolée `src/agent_NAME/app/db/alembic` soutient le "Zero Downtime" et prévient les effets de bord inter-agents.

### Requirements Coverage Validation ✅

**Functional Requirements Coverage:**
- **FR1-FR5 (Routage & Auth) :** Assurés par Maestro en bordure (JWT + semantic-router).
- **FR6-FR8 (Yield & Context Stack) :** Cœur de Maestro (modèles ORM dédiés) avec interaction `YieldResponse` via A2A.
- **FR9-FR11 (Mémoire Soft/Hard) :** Gérés individuellement par la base `pgvector` de chaque agent spécialiste.
- **FR12-FR13 (Résilience & Zero Downtime) :** Couverts par la décentralisation de l'ORM et des migrations manuelles par agent.

**Non-Functional Requirements Coverage:**
- **Performance / Temps de Réponse :** Sécurisés par la nature asynchrone de bout en bout (`httpx` + `asyncpg`) et des timeouts stricts appliqués lors du routing de Maestro.

### Implementation Readiness Validation ✅

**Decision Completeness:**
Les versions cibles (Alembic >= 1.18.4, Postgres pgvector) et les responsabilités des agents sont figées.

**Structure & Pattern Completeness:**
Les règles anti-conflits (Pattern 2B et 3B) établissent des garde-fous contraignants pour les futurs agents (BMad) en charge du développement.

### Gap Analysis Results
- **Mineur (Base de données) :** L'activation explicite de l'extension Postgres `vector` devra être traitée avant la création des tables des agents (soit via le script bash de provisionnement, soit via Alembic).

### Architecture Completeness Checklist

**✅ Requirements Analysis**
- [x] Project context thoroughly analyzed
- [x] Scale and complexity assessed
- [x] Technical constraints identified
- [x] Cross-cutting concerns mapped

**✅ Architectural Decisions**
- [x] Critical decisions documented with versions
- [x] Technology stack fully specified
- [x] Integration patterns defined
- [x] Performance considerations addressed

**✅ Implementation Patterns**
- [x] Naming conventions established
- [x] Structure patterns defined
- [x] Communication patterns specified
- [x] Process patterns documented

**✅ Project Structure**
- [x] Complete directory structure defined
- [x] Component boundaries established
- [x] Integration points mapped
- [x] Requirements to structure mapping complete

### Architecture Readiness Assessment

**Overall Status:** READY FOR IMPLEMENTATION

**Confidence Level:** HIGH. L'architecture capitalise sur l'infrastructure éprouvée de la Phase 1 tout en intégrant des schémas résilients pour la persistance à long terme.

**Key Strengths:**
- Zéro point de défaillance unique (SPOF) sur la persistance métier.
- L'intégrité inter-service est assurée par une validation stricte Pydantic (Type Safety).
- Gestion asynchrone optimisée.

**Areas for Future Enhancement:**
- Implémentation d'un système robuste d'Observabilité (OpenTelemetry, Jaeger) au-delà des logs bruts.

### Implementation Handoff

**AI Agent Guidelines (à destination des agents BMad de développement) :**
- L'isolation des bases de données est stricte. Aucun agent ne doit coder des accès directs à la base d'un autre agent.
- Utiliser rigoureusement le `snake_case` pour les attributs Pydantic inter-agents.
- Conserver le code bloquant à l'extérieur de la boucle d'événements (utiliser exclusivement `asyncpg` et `SQLAlchemy[asyncio]`).

**First Implementation Priority:**
1. Remplacer l'image PostgreSQL par `pgvector` dans `docker-compose.yml` et s'assurer que `CREATE EXTENSION vector` soit inclus dans le script d'initialisation.
2. Initialiser l'environnement de base de données (Alembic) isolément pour l'Agent Maestro (gestion du `Context Stack`).
 l'environnement de base de données (Alembic) isolément pour l'Agent Maestro (gestion du `Context Stack`).
