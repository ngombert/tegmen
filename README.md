# Family-Agents (Tegmen)

Une équipe d'agents IA autonomes pour assister la famille au quotidien. Ce projet implémente un orchestrateur (Maestro) capable de router intelligemment les demandes vers des agents spécialisés via le protocole A2A.

## 🏗 Architecture

Le projet est conçu comme un ensemble de **microservices** communiquant via le protocole **A2A (Agent-to-Agent)**.

### Les Agents
*   **🎹 Maestro (Gateway)** : Le point d'entrée unique. Il analyse l'intention de l'utilisateur (via Semantic Router optimisé pour le français) et délègue la tâche à l'agent approprié.
*   **🍳 Gourmet** : Spécialiste culinaire (Recettes, listes de courses).
*   **🎓 Acadomie** : Assistant scolaire (Emploi du temps, notes, aide aux devoirs).
*   **🌍 Explorer** : Expert voyage et loisirs (Destinations, activités, météo).

### Fonctionnalités Clés
*   **Routage Sémantique Local** : Utilisation de `multilingual-e5-small` en mémoire pour une classification rapide et privée.
*   **Privacy-First** : Cavardage automatique des PII (données personnelles) dans tous les journaux.
*   **Contrôle Parental (RBAC)** : Filtrage des requêtes basé sur le profil utilisateur (ex: restrictions enfants).
*   **Résilience & Observabilité** : Instrumentation OpenTelemetry complète, Timeouts SLA, et dégradation gracieuse en cas de panne d'un agent.

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
PYTHONPATH=src uv run python3 scripts/verify_all.py
```

### Exécuter les tests manuellement

Pour lancer les tests avec le rapport de couverture :

```bash
PYTHONPATH=src uv run pytest tests/ -vv
```

## 📂 Structure du Projet
```
src/
├── agent_maestro/   # API Gateway & Semantic Router
├── agent_gourmet/   # Microservice Cuisine
├── agent_acadomie/  # Microservice Scolaire
├── agent_explorer/  # Microservice Voyage
├── common/          # Code partagé (DB, A2A, Config, Auth)
└── web-client/      # (Optionnel) Interface web simplifiée
```

---
*Projet finalisé - Epic 4 terminée avec succès.*
