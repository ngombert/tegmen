# Family-Agents (Tegmen)

Une équipe d'agents IA autonomes pour assister la famille au quotidien.

## 🏗 Architecture

Le projet est conçu comme un ensemble de **microservices** communiquant via le protocole **A2A (Agent-to-Agent)**.

### Les Agents
*   **🎹 Maestro (Gateway)** : Le point d'entrée unique. Il analyse l'intention de l'utilisateur (via Semantic Router) et délègue la tâche à l'agent approprié.
*   **🍳 Gourmet** : Spécialiste culinaire (Recettes, listes de courses).
*   **🎓 Acadomie** : Assistant scolaire (Emploi du temps, notes, aide aux devoirs).
*   **🌍 Explorer** : Expert voyage et loisirs (Destinations, activités, météo).

### Stack Technique
*   **Langage** : Python 3.12+
*   **Gestionnaire de paquets** : `uv`
*   **IA** : Google ADK, LiteLLM, Semantic Router
*   **Base de données** : PostgreSQL (Async SQLAlchemy)
*   **Infra** : Docker & Docker Compose

## 🚀 Démarrage Rapide

### Prérequis
*   Docker & Docker Compose
*   `uv` (recommandé pour le développement local)

### Installation

1.  **Cloner le dépôt**
    ```bash
    git clone <repo_url>
    cd tegmen
    ```

2.  **Configurer l'environnement**
    ```bash
    cp .env.example .env
    # Editer .env avec vos clés API (OpenRouter/Gemini, etc.)
    ```

3.  **Lancer les services**
    ```bash
    docker-compose up --build
    ```
    Les agents seront accessibles sur :
    *   Maestro : http://localhost:8000
    *   Gourmet : http://localhost:8001
    *   Acadomie : http://localhost:8002
    *   Explorer : http://localhost:8003

## 🧪 Vérification et Tests

Pour s'assurer que tout fonctionne (tests unitaires, routage, et communication inter-agents), utilisez le script global :

```bash
./scripts/verify_all.py
```

Ce script exécute :
1.  Les tests unitaires (`pytest`)
2.  La vérification du routeur sémantique
3.  Un test d'intégration A2A (Maestro -> Gourmet)

## 📚 Documentation
*   [Protocole A2A](docs/A2A.md) : Détails sur la communication entre agents.

## 📂 Structure du Projet
```
src/
├── agent_maestro/   # API Gateway & Semantic Router
├── agent_gourmet/   # Microservice Cuisine
├── agent_acadomie/  # Microservice Scolaire
├── agent_explorer/  # Microservice Voyage
└── common/          # Code partagé (DB, A2A, Config)
```
