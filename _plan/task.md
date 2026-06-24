# Tâches du Projet Family-Agents (Tegmen)

## Phase 1 : Bootstrap

### Initialisation
- [x] Setup du projet avec `uv`
- [x] Ajouter les dépendances : `google-adk`, `litellm`, `semantic-router`, `sentence-transformers`, `fastapi`, `uvicorn`, `sqlalchemy[asyncio]`, `asyncpg`, `python-dotenv`, `a2a-sdk`
- [x] Créer la structure de dossiers : `src/common`, `src/agent_maestro`, `src/agent_gourmet`, `src/agent_acadomie`, `src/agent_explorer`

### Infrastructure
- [x] Créer le fichier `.env.example` avec les variables nécessaires
- [x] Créer `docker-compose.yml` pour PostgreSQL + Agents Microservices
- [x] Créer le fichier de configuration `src/common/config.py`

### Common Core
- [x] Implémenter `src/common/database.py` : SQLAlchemy async engine + session factory
- [x] Implémenter `src/common/models.py` : Tables `family_members`, `preferences`, `conversation_logs`
- [x] Créer `src/common/a2a_server.py` : Serveur A2A pour agents ADK
- [x] Créer `src/common/a2a_client.py` : Client A2A pour Maestro

---

## Phase 2 : Agent Maestro (Gateway)

### Semantic Router (Local)
- [x] Créer `src/agent_maestro/router.py` : SemanticRouter avec encoder local
- [x] Définir les routes : gourmet, acadomie, explorer, chitchat, unknown
- [x] Configurer les utterances d'entraînement pour chaque route

### API FastAPI
- [x] Créer `src/agent_maestro/main.py` : Application FastAPI avec endpoint `/chat`
- [x] Créer `src/agent_maestro/schemas.py` : Schémas Pydantic pour les requêtes/réponses
- [x] Intégrer le SemanticRouter au endpoint `/chat`
- [x] Implémenter le mode Microservices (A2A Client) vs Monolithique

### Agents ADK
- [x] Implémenter `src/agent_maestro/agents.py` : Fallback Maestro et imports flexibles
- [x] Intégrer le Runner ADK avec SessionService

### Epic : Gestion de Contexte & Isolation Utilisateur (Claim Check)
- [ ] Définir l'interface `BaseContextRepository` dans `src/common/context_repository.py`
- [ ] Implémenter la table `ContextStore` et la persistance dans `src/infrastructure/postgres_context_repository.py` (UUIDv4, JSONB, TTL, Indexation)
- [ ] Définir les schémas `VisibilityScope` et `ContextMetadata` (avec `owner_id`, `authorized_users`, `visibility_scope`) dans `src/models/context.py` ou `src/common/schemas.py`
- [ ] Implémenter le service de contrôle d'accès dans `src/common/context_service.py` (`ContextService.hydrate_context` avec détection et blocage d'accès non autorisé)
- [ ] Créer la dépendance FastAPI d'hydratation automatique `get_hydrated_context` dans `src/common/a2a_server.py`
- [ ] Adapter `src/common/a2a_client.py` pour propager et intercepter le header `X-Claim-Check-ID`
- [ ] Implémenter le mécanisme Copy-on-Write (CoW) et de fusion de version dans Maestro (`src/agent_maestro/main.py`) pour la parallélisation en mode "Party"
- [ ] Écrire le script de migration de données `migration_v4_context_acl.py` pour peupler rétroactivement le champ `owner_id` des contextes existants
- [ ] Créer une fixture `InMemoryContextRepository` pour les tests unitaires et intégrer un `TimeProvider` pour le "Time-Travel Testing" du TTL
- [ ] Écrire la suite de tests d'intrusion de sécurité parent-enfant et enfant-enfant (`tests/test_context_security.py` avec tests paramétrés)

---

## Phase 3 : Agents Spécialistes (Microservices)

### Infrastructure Agents
- [x] Créer `src/agent_gourmet/Dockerfile`
- [x] Créer `src/agent_acadomie/Dockerfile`
- [x] Créer `src/agent_explorer/Dockerfile`
- [x] Créer `src/agent_maestro/Dockerfile`

### Agent Gourmet (Repas)
- [x] Implémenter `src/agent_gourmet/agent.py` : LlmAgent spécialisé
- [x] Implémenter `src/agent_gourmet/main.py` : Serveur A2A
- [x] Définir les tools spécifiques (recherche recettes, etc.)

### Agent Acadomie (École)
- [x] Implémenter `src/agent_acadomie/agent.py` : LlmAgent spécialisé
- [x] Implémenter `src/agent_acadomie/main.py` : Serveur A2A
- [x] Définir les tools spécifiques (calendrier scolaire, notes, devoirs, etc.)

### Agent Explorer (Voyage)
- [x] Implémenter `src/agent_explorer/agent.py` : LlmAgent spécialisé
- [x] Implémenter `src/agent_explorer/main.py` : Serveur A2A
- [x] Définir les tools spécifiques (recherche destinations, activités, météo)

---

## Phase 4 : Intégration & Tests

### Tests
- [x] Tests du SemanticRouter (`tests/verify_routing.py`) - 94% success
- [x] Tests unitaires des agents spécialistes
- [x] Tests d'intégration A2A (Client <-> Server)
- [x] Verify remote agent communication (manual test or script) <!-- id: 4 -->

### Documentation
- [ ] Mettre à jour `README.md` avec instructions Microservices
- [ ] Documenter le protocole A2A

---

## Notes Techniques

### Stack
- **Microservices** : Docker + A2A Protocol (JSON-RPC over HTTP)
- **Communications** : `a2a-sdk`, `httpx`
- **LLM Provider** : OpenRouter (GEMINI 2.0 Flash)

### Architecture Microservices
```
┌─────────────────────────────────────────────────────────────┐
│                    MAESTRO (Gateway)                        │
│                   Port 8000 / Docker                        │
│ ┌────────────────┐      ┌────────────────────────────────┐  │
│ │ Semantic Router│ ───► │  A2A Client (HTTP/JSON-RPC)    │  │
│ └────────────────┘      └────────────────────────────────┘  │
└───────────┬─────────────────────┬───────────────┬───────────┘
            │                     │               │
            ▼                     ▼               ▼
     ┌──────────────┐      ┌──────────────┐   ┌──────────────┐
     │   GOURMET    │      │   ACADOMIE   │   │   EXPLORER   │
     │  Port 8001   │      │  Port 8002   │   │  Port 8003   │
     │  A2A Server  │      │  A2A Server  │   │  A2A Server  │
     │  (DB pr. db) │      │  (DB pr. db) │   │  (DB pr. db) │
     └──────────────┘      └──────────────┘   └──────────────┘
```
