---
stepsCompleted: [1, 2, 3, 4, 5, 6, 7, 8]
inputDocuments: [
  '_bmad-output/planning-artifacts/prd_agent_acadomie.md',
  '_bmad-output/planning-artifacts/prd_agent_gourmet.md',
  '_bmad-output/planning-artifacts/prd_agent_maestro.md',
  'docs/A2A.md',
  '_bmad-output/project-context.md',
  'docs/adk.md'
]
workflowType: 'architecture'
project_name: 'tegmen'
user_name: 'Nicolas'
date: '2026-04-16'
lastStep: 8
status: 'complete'
completedAt: '2026-04-16'
---

# Architecture Decision Document

_This document builds collaboratively through step-by-step discovery. Sections are appended as we work through each architectural decision together._

## Project Context Analysis

### Requirements Overview

**Functional Requirements:**
Le système est structuré autour d'un point de contact asynchrone (Maestro) qui centralise le routage sémantique et gère l'authentification/l'hydratation du contexte de l'utilisateur. Ces requêtes sont transmises vers des agents spécialistes (Gourmet, Acadomie) opérant indépendamment sous le protocole Agent-to-Agent (A2A). Les sous-agents privilégieront une architecture "Lean" et sans état basée directement sur `litellm` et les schémas `pydantic` (abandon de l'orchestrateur complexe de l'ADK visé initialement) afin de garantir une synchronisation fluide avec les requêtes réseau JSON-RPC.

**Non-Functional Requirements:**
- **Performance:** Surcharge de routage locale (semantic-router) sous 100ms-300ms ; Asynchronisme absolu pour ne pas bloquer l'Event Loop. L'absence de framework ADK stateful garantit zéro friction d'allocation mémoire supplémentaire lors du requêtage A2A.
- **Sécurité et Gouvernance:** Application du "Bouclier Actif de Contexte" masquant les PII et restreignant l'identité et le périmètre des requêtes en amont (RBAC implicite).
- **Fiabilité et UX:** Focus sur la résilience avec une politique "Fail-Fast" réseau interdisant les attentes infinies. En cas de dysfonctionnement d'un spécialiste, l'architecture impose une **Dégradation Gracieuse** (Graceful Degradation) : le Gateway Maestro récupère l'erreur 422/Timeout et retourne une réponse conversationnelle polie à l'utilisateur, préservant la confiance familiale.

**Scale & Complexity:**
Conception distribuée asynchrone exigeant une intégration sans contact (contractuelle) très robuste.
- Primary domain: API Backend / Eco-système Multi-Agents "Lean"
- Complexity level: Medium-High
- Estimated architectural components: 4+ (Maestro, Gourmet, Acadomie, et les protocoles A2A partagés).

### Technical Constraints & Dependencies

- **Choix Technologiques Liés :** Python 3.13+, `uv`, `fastapi`/`uvicorn`, asynchronisme de bout en bout (`asyncpg`), inférence générative minimaliste via `litellm`, et transport via l'API standardisée `a2a-sdk`.
- **Audit et Tests :** L'exigence radicale d'une validation locale en CI ("Zéro appel réseau/LLM distant").

### Cross-Cutting Concerns Identified

- **État A2A 100% Stateless :** Élimination du risque de duplication d'état interne grâce au choix de passer le contexte métier exclusivement et inconditionnellement dans le payload de la requête JSON-RPC.
- **Consumer-Driven Contract Testing :** En raison de la décentralisation des nœuds A2A, il est vital d'implémenter des tests de validation de contrats sur l'endpoint `.well-known/agent-card.json` et sur les signatures Pydantic échangées entre Maestro et l'écosystème.
- **Transversalité Sécurité / Erreurs :** Déclarer formellement aux API un standard sur la façon dont les noeuds remontent l'information au Gateway en cas d'erreur sans divulguer aucune information technique complexe aux utilisateurs finaux.

## Starter Template Evaluation

### Primary Technology Domain

API Backend / Microservices Python asynchrones (Brownfield project).

### Starter Options Considered

- **Générateur CLI Standard (ex: fastapi-template)** : Rejeté, car les dossiers des microservices existent déjà (`src/agent_*`).
- **Refonte Standardisée via Shared Libs (`src/common/`)** : Sélectionnée pour garantir que chaque nœud respecte l'implémentation "Lean" (LiteLLM pur).

### Selected Starter: Standardized Lean FastAPI Template via `src/common/`

**Rationale for Selection:**
Dans un projet hybride et Brownfield, la meilleure fondation n'est pas un code généré depuis zéro, mais une bibliothèque commune centralisée. Uniformiser le point d'entrée FastAPI avec l'A2A SDK dans `common` assure que Maestro, Gourmet et Acadomie hériteront des mêmes protocoles d'erreur et du même format Pydantic, sans duplication et sans la surcouche d'état d'orchestrateurs tiers.

**Commandes de Mise à jour des Dépendances (à incorporer dans le Makefile/Script local) :**

```bash
uv lock --update
uv add fastapi@>=0.135.3 uvicorn litellm@>=1.83.4 pydantic
uv add --dev pytest pytest-asyncio pytest-httpx
```

**Architectural Decisions Provided by Starter:**

**Language & Runtime:**
Python 3.13+ ultra-strict avec lockfile géré de manière immuable par `uv` (v0.11.7+).

**Styling Solution:**
N/A (Système A2A purement Backend JSON).

**Build Tooling:**
`uv` comme package manager unique, avec virtual environment strict isolant l'Event Loop asynchrone.

**Testing Framework:**
Conformité avec "Zéro réseau en CI" : la fondation inclut `pytest` injecté avec `pytest-asyncio` (`asyncio_mode="auto"`) et `pytest-httpx` pour garantir le mocking de tous les appels JSON-RPC.

**Code Organization:**
Tous les agents devront s'aligner sur :
- `src/agent_NAME/app/api/routers/` pour l'exposition du protocole A2A.
- `src/agent_NAME/app/schemas/` pour les contrats Pydantic.
- `src/common/a2a_server.py|a2a_client.py` pour mutualiser la topologie réseau de l'écosystème.

**Development Experience:**
Redémarrages chauds via `uvicorn --reload`, documentation intra-nœuds auto-générée via OpenAPI/Swagger pour faciliter la validation visuelle des JSON-RPC par l'équipe, intégration `litellm` décorrélée des abstractions lourdes d'état de session.

**Note:** L'uniformisation macro et l'implémentation de la librairie d'échange A2A partagée dans `src/common/` devrait être la toute première User Story d'implémentation.

## Core Architectural Decisions

### Decision Priority Analysis

**Critical Decisions (Block Implementation):**
- Standardisation du contexte d'autorisation JWT dans Maestro pour le "Context Shield".
- Fichier racine `docker-compose.yml` pour le maillage réseau local inter-agents.

**Important Decisions (Shape Architecture):**
- Stratégie de caching en mémoire pour le routeur sémantique de Maestro garantissant <100ms de latence.

**Deferred Decisions (Post-MVP):**
- Streaming WebSocket temps réel.
- Base de données Vectorielle (RAG) et Mémoire à long terme multi-sessions.

### Data Architecture & Memory

- **Database:** PostgreSQL (Driver asynchrone `asyncpg` + `sqlalchemy[asyncio]`).
- **Caching Strategy (Routing):** Utilisation prioritaire de la RAM locale (In-Memory Cache) pour stocker les embeddings du Semantic Router et garantir les délais d'acheminement stricts (<100ms).
- **Agent Memory (Short Term):** Strictement déléguée à Maestro. L'historique contextuel immédiat est injecté via le payload JSON-RPC (`"context": { "chat_history": [...] }`). Les agents spécialistes opèrent donc de manière "Stateless" et n'ont pas à maintenir de session DB propre à un flux conversationnel de leur côté.
- **Agent Memory (Long Term):** Deferred. Pas de Base de Données de Graphes (GraphDB) ni de base de données Vectorielle.

### Authentication & Security

- **Authentication Method:** JWT (JSON Web Tokens) intercepté en Bearer Token par les requêtes entrantes vers Maestro, puis décodé localement pour valider l'identité sans délai I/O réseau récursif.
- **Authorization Patterns:** Le "Bouclier Actif de Contexte" s'applique dynamiquement dans le cycle de vie de requête (Middlewares / Depends FastAPI) de Maestro. Il expurge les PII et formate un objet d'identité validé avant toute circulation A2A externe.

### API & Communication Patterns

- **API Security & Error Handling:** Intercepteur asynchrone d'exceptions central dans Maestro (politique "Graceful Degradation"). Toute brèche de validation de schéma ou Time-Out d'un Agent lors du parsing JSON-RPC est bloquée, loggée de façon aseptisée, et mutée en un message de secours conversationnel adapté à la famille. Les codes d'erreurs (422, 5X) techniques profonds ne fuient pas sur les interfaces publiques.

### Infrastructure & Deployment

- **Hosting & Namespacing:** Architecture conteneurisée microservices gérée avec `Docker Compose`. Permet une topographie claire du réseau pour l'accès inter-agents statique.
- **Scaling Strategy:** Chaque agent agit comme un container API découplé. L'approche stateless garantit qu'il est possible de scaler un processus Gourmet très sollicité de façon ciblée indépendamment de l'agent éducatif Acadomie.

## Implementation Patterns & Consistency Rules

### Pattern Categories Defined

**Critical Conflict Points Identified:**
4 zones logiques (Nommage, Structure, Format, Processus) où les agents IA générateurs de code doivent être strictement alignés.

### Naming Patterns

**API & Payload Conventions:**
- L'échange JSON-RPC (Data A2A) conservera strictement le format `snake_case` dans tous ses payloads afin de mapper nativement les variables Python, évitant les surcouches d'alias Pydantic.
- **Attention Front-End:** Le dossier `src/web-client` (TypeScript/React) attend usuellement du `camelCase`. Le client Web DOIT configurer un intercepteur de requêtes (ex: *Axios interceptor*) pour convertir à la volée le `snake_case` des API vers le `camelCase` front-end.
- Noms de méthodes JSON-RPC : format standard en `[verbe]_[domaine]` (ex: `generate_recipe`, `analyze_identity`).

**Code Naming Conventions:**
- Variables et fonctions locales : `snake_case`.
- Modèles Typés / DTO : `PascalCase` imposé avec suffixe d'interface explicite (ex: `RecipeRequest`, `IdentityModel`).

### Structure Patterns

**File Structure Patterns:**
Chaque module de microservice (Gourmet, Acadomie, Maestro) DOIT observer la stricte arborescence interne suivante :
- `app/api/routers/` : Endpoints exposés / Wrappers FastAPI.
- `app/schemas/` : Définition des classes et contrats Pydantic JSON-RPC.
- `app/services/` : Logique métier métier métier interne (encapsulation LiteLLM).

### Format Patterns

**Data Exchange Formats:**
- **Typage Strict Python 3.13+ :** Usage des built-ins obsolètes `typing.List / typing.Dict` interdit au profit des types natifs `list / dict`. Remplacement de `Optional[X]` par l'opérateur asynchrone moderne `X | None`.
- **Date/Time :** Format chaîne standard ISO-8601 imposé pour tout horodatage transitant en A2A.

### Communication Patterns

**Event System & Traceability:**
- **Correlation ID :** Absolument chaque appel JSON-RPC DOIT transporter un `correlation_id` unique pour relier l'ensemble des logs d'un sous-système (Gourmet) à la requête asynchrone parente (Maestro) lors du processus complexe de debugging en dégradation décentralisée.

### Process Patterns

**Error Handling & Mocking Patterns:**
- **Exception Asynchrone :** Aucun agent autonome ne masquera une erreur systémique via un bloc `try...except` lâche. En cas de rupture Pydantic de type réseau, une exception `A2ARPCError` est explicitement levée et interceptée globalement ("Graceful Degradation").
- **Dependency Injection (Zero Network CI) :** L'instanciation en dur de connexions client réseau au sein des fonctions de traitement est prohibée. Les clients d'API externes (comme interagir avec l'interface `LiteLLM`) DOIVENT être expliciteéquipe IA vient de pointer plusieurs ajustements décisifs :ment injectés (via `FastAPI Depends()` ou en paramètres clairs d'objets) afin que les environnements de tests (sur la plateforme de CI) puissent instantanément isoler/substituer des stubs non-bloquants sans invoquer la moindre session d'I/O réseau inattendue.

### Enforcement Guidelines

**All AI Agents MUST:**
- Déclarer statiquement et sans heuristique avec les type hints (`mypy` strict activé) 100% des objets de retours asynchrones (y compris les simples exécutions sans valeur `-> None:`).
- Interdir activement tout processus standard I/O de l'écosystème synchronisé (comme `time.sleep`, ou l'injonction locale de `requests`) au profit strict de l'implémentation de la boucle d'événements (`asyncio`, `httpx`).
- Documenter publiquement sans faillir chaque description fine de fonction d'Endpoint pour auto-alimenter en temps réel le classifieur LLM dynamique (l'Embedder local) du routeur sémantique central initialisé dans Maestro.

## Project Structure & Boundaries

### Complete Project Directory Structure

```text
tegmen/
├── README.md
├── .env.example
├── docker-compose.yml       # Maillage réseau inter-agents
├── pyproject.toml           # Gestion globale des dépendances Python (uv)
├── uv.lock                  # Verrouillage exact ASGI/LiteLLM/Pydantic
├── .github/
│   └── workflows/
│       └── ci.yml           # CI avec tests hors-réseau (pytest-httpx)
├── docs/                    # Documents A2A et PRDs techniques
├── src/
│   ├── web-client/          # Interface Utilisateur (React/TS ou équivalent)
│   ├── common/              # [CROSS-CUTTING] Librairie partagée
│   │   ├── a2a_server.py    # Standardisation de l'API FastAPI A2A
│   │   ├── a2a_client.py    # Client HTTPX asynchrone générique
│   │   ├── security.py      # Middleware & validation JWT mutualisés
│   │   ├── exceptions.py    # Exceptions "Graceful" (A2ARPCError)
│   │   └── schemas.py       # Pydantic génériques et Payload contextuel
│   ├── agent_maestro/       # [EPIC] API Gateway & Context Shield
│   │   ├── Dockerfile
│   │   └── app/
│   │       ├── main.py
│   │       ├── api/routers/ # Endpoints publics (seul point d'entrée Frontend)
│   │       ├── schemas/     # RBAC & Routing models globaux
│   │       └── services/
│   │           ├── semantic_router.py # Classification des intentions (In-Memory)
│   │           └── context_shield.py  # Anonymisation PII & Hydratation JWT
│   ├── agent_gourmet/       # [EPIC] Cooking & Recipe Assistant
│   │   ├── Dockerfile
│   │   └── app/
│   │       ├── main.py
│   │       ├── api/routers/ # Endpoints internes JSON-RPC uniquement
│   │       ├── schemas/     # Modèles spécifiques Recettes / Ingrédients
│   │       └── services/
│   │           ├── recipe_manager.py  # Abstraction SQL native locale
│   │           └── litellm_client.py  # Inférence LLM confinée (Zero DB access)
│   └── agent_acadomie/      # [EPIC] Education & Homework Assistant
│       ├── Dockerfile
│       └── app/
│           ├── main.py
│           ├── api/routers/
│           ├── schemas/
│           └── services/    
└── tests/                   # Base de tests QA unifiée
    ├── conftest.py          # Fixtures globales (Injection des httpx_mock)
    ├── agent_maestro/
    ├── agent_gourmet/
    ├── agent_acadomie/
    └── common/
```

### Architectural Boundaries & Data Flow

**API Boundaries (Network Confinement):**
- **External Frontier:** Seul le port de `src/agent_maestro/` est exposé au réseau de l'hôte public (et au `web-client`). Il porte la responsabilité intégrale du filtrage AuthZ/AuthN.
- **Internal A2A Boundary:** Les nœuds spécialisés (`gourmet`, `acadomie`) opèrent dans des sous-réseaux virtuels Docker fermés et ne servent que des réponses JSON-RPC conformes en provenance d'un tunnel certifié inter-microservices (`maestro`).

**Data & State Boundaries (Schema-per-Service):**
- **Souveraineté des Données :** Le cluster PostgreSQL est logiquement cloisonné (Schema-per-service). Maestro opère un schéma maître (utilisateurs, sessions, PII, RBAC). Chaque sous-agent possède et migre (via Alembic) son propre schéma de données purement métier (ex: le schéma *Gourmet* pour les recettes de familles privées).
- **Le Lien Identitaire (Network Foreign Key) :** Puisque les requêtes inter-agents respectent l'État Stateless sans lecture croisée des bases (pas de jointure SQL inter-schéma), Maestro identifie la famille via le JWT et passe ce `family_id` strictment dans le payload. Le service Python local (ex: Gourmet) utilise alors nativement ce `family_id` comme identifiant pour isoler ses extractions SQL via sa connexion asynchrone dédiée (`sqlalchemy`) **avant** de transférer ces données vérifiées au LLM.

### Integrations and Dependency Patterns

**Le Modèle "Agent vs Data" (Zero MCP Server) :**
D'un point de vue intégration LLM, le besoin explicite d'empêcher les failles et injections de prompts destructrices (règle du Fail-Fast sécurisé) interdit de laisser le LLM (LiteLLM) piloter l'accès SQL en direct via une connexion de type Serveur de Protocole MCP. Les appels vers `asyncpg` sont exécutés impérativement et de façon déterministe via la couche Python `app/services/` du microservice concerné, ce qui permet de valider le contrat Pydantic et d'assembler le contexte sans risque réseau.

**Exception Handling Translation:**
Le dysfonctionnement de la base de données (erreur SQL Timeout) ou les échecs du réseau interne fermé (Timeout A2A entre Maestro et Acadomie) ne transpirent jamais vers le client frontal. L'erreur asynchrone lève l'une des classes standards définies dans `src/common/exceptions.py`. Lorsqu'elle est capturée par Maestro, elle est mutée en un simple message vocal ou écrit conversationnel validé pour apaiser l'application familiale.

## Architecture Validation Results

### Coherence Validation ✅

**Decision Compatibility:**
Toutes nos décisions s'imbriquent sans friction architecturale : l'usage exclusif de Python 3.13 avec `fastapi` et le typage strict (`pydantic`) supporte parfaitement l'approche JSON-RPC `stateless` choisie. Le rejet volontaire d'un orchestrateur complexe LLM (comme un serveur MCP DB en backend direct) au profit de connecteurs simples et de code asynchrone méticuleux (`LiteLLM` pur) garantit un contrôle absolu et déterministe de l'Event Loop.

**Pattern Consistency:**
L'obligation fondamentale du patron d'Injection de Dépendances (DI) pour les clients réseaux (`httpx`) et les moteurs d'inférence (`litellm`) codifiée à l'étape 5 soutient de façon irréprochable l'exigence des Testeurs QA : "Zéro I/O réseau non mocké en CI" sans faire de compromis sur la couverture des tests métier.

**Structure Alignment:**
La séparation physique (sous-réseaux Docker Compose) combinée au cloisonnement strict des bases de données par domaine ("Schema-per-service" Postgres) et au filtrage d'Authentification relégué exclusivement au Gateway (Maestro) assure la robustesse aux changements des spécialistes sans interdépendance de l'état système.

### Requirements Coverage Validation ✅

**Epic/Feature Coverage:**
- Le composant `agent_maestro` couvre intégralement les responsabilités névralgiques du routing et de la sécurité via le "Routeur Sémantique" In-Memory et le "Active Context Shield".
- `agent_gourmet` et `agent_acadomie` opèrent comme des cellules métier isolées garantissant la gestion de leur propre logique applicative (Recettes / Éducation) pour le reste des Epics. *L'exclusion assumée du MVP des RAG / VectorDB fiabilise considérablement la Phase 1.*

**Non-Functional Requirements Coverage:**
- **Performance (<100ms routing) :** Assurée structurellement par le caching mémoire du Gateway.
- **Privacy :** Délégation et suppression centralisée des PII dans Maestro impossible à contourner.
- **Fail-Fast & Graceful Degradation :** Gérée via l'interception globale des exceptions formatées pour la famille.

### Implementation Readiness Validation ✅

**Decision Completeness:**
Les limites entre ce que le Modèle d'IA fait (raisonnement confiné) et ce que la machine Python exécute (Extraction BDD sécurisée / API / Tolérance de pannes) sont désormais tracées dans le marbre. Les Agents IA Développeurs ne pourront plus halluciner ces limites.

**Structure & Pattern Completeness:**
Chaque couche (`src/api`, `src/schemas`, `src/services`, `tests/`) a sa convention de nommage (`snake_case` JSON vs `PascalCase` Modèles). Le document confère aussi au fichier `tegmen/.env.example` le rôle de clé de voûte pour propager instantanément les configurations locales (Endpoint LiteLLM, clés JWT) inter-microservices.

### Architecture Completeness Checklist

**✅ Requirements Analysis**
- [x] Project context thoroughly analyzed
- [x] Technical constraints identified
- [x] Cross-cutting concerns mapped

**✅ Architectural Decisions**
- [x] Technology stack fully specified (Python 3.13, uv, FastAPI, LiteLLM)
- [x] Integration patterns defined (Docker Compose, A2A JSON-RPC)
- [x] Databases access pattern formalized (Schema-per-service & Zero MCP)

**✅ Implementation Patterns**
- [x] Naming conventions established (snake_case JSON vs TS camelCase UI)
- [x] Process patterns documented (CI Zero Network / Dependency Injection rules)
- [x] Error handling formalized (Graceful Degradation exceptions limitant le Fail-Fast)

**✅ Project Structure**
- [x] Complete directory codebase defined
- [x] Microservice boundaries established 
- [x] Configurations des secrets (`.env.example`) unifiées

### Architecture Readiness Assessment

**Overall Status:** READY FOR IMPLEMENTATION
**Confidence Level:** HIGH 

**Key Strengths:**
La stricte barrière I/O : les services asynchrones Python extraient le "State" de la BDD avec des Id sécurisés avant de formater la requête LLM, annulant le risque massif de Prompt Injection sur base de données.

**Areas for Future Enhancement (Deferred):**
Introduction d'infrastructure pour des composants bidirectionnels temps réels (WebSockets) et intégration ultérieure de bases Vectorielles pour la mémorisation long terme.

### Implementation Handoff

**AI Agent Guidelines:**
- Les futurs agents implémenteurs exécutent fidèlement ce document. Il doit systématiquement être inclus en Contexte.

**First Implementation Priority:**
Le travail de l'Agent Développeur (Amelia) commencera par : 
-> Le build de l'A2A dans le namespace transversal `src/common/` (Exceptions Standards, Modèles Pydantic de routage).
-> **Action QA Bloquante :** Ajout des actions GitHub/GitLab CI (`.github/workflows/ci.yml`) pour imposer la couverture des tests (>90%) et le lint (Mypy Strict) avant validation de PR.
