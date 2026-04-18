---
project_name: 'Tegmen (Family-Agents)'
document_type: 'Product Requirements Document'
module: 'Agent Acadomie'
status: 'Draft'
author: 'Chef de Produit (IA)'
---

# PRD : Agent Acadomie (Refonte Globale)

## 1. Vision et Objectifs
L'**Agent Acadomie** est un microservice spécialisé (serveur A2A) au sein de l'écosystème Tegmen. Son rôle est d'agir en tant qu'assistant scolaire, fournissant l'accès aux devoirs, au calendrier scolaire, aux notes, et proposant à terme des conseils d'organisation interactifs.
Il est conçu pour être interrogé de manière asynchrone par l'agent fédérateur **Maestro**, qui orchestre les requêtes de la famille (Gateway A2A).

## 2. État Actuel de l'Implémentation (As-Is Legacy)
L'infrastructure de base est opérationnelle et communique en suivant le protocole A2A, mais elle est presque entièrement mockée et enfreint plusieurs directives d'architecture. Elle nécessite une réécriture complète pour atteindre les standards de production.

### 2.1 Capacités (Skills ADK)
*   **`homework` (Devoirs)** : Consulter / ajouter des devoirs.
*   **`calendar` (Calendrier)** : Consulter le calendrier scolaire et les événements à venir.
*   **`grades` (Notes)** : Consulter les notes de l'élève par matière.
*   **`organization` (Organisation)** : Fournir des conseils d'organisation et de révision (capacité actuellement déclarée mais non gérée par des outils dédiés).

### 2.2 Stack Technique Implémentée (Dette Technique)
*   **Framework d'Exposition** : FastAPI orchestré par `uvicorn` (Valide).
*   **Protocole d'Échange** : SDK A2A `a2a-sdk` (Valide).
*   **Cerveau LLM** : `LlmAgent` de `google-adk` avec `LiteLLM` (Valide).
*   **Persistance** : **Mock local uniquement** (Données hardcodées dans `tools.py` - Dette critique).
*   **Architecture** : Fonctions métier synchrones et retours JSON formatés en chaînes de caractères (`json.dumps` - Dette critique).

---

## 3. Axes d'Amélioration (Conformité A2A & `project-context.md`)
Les éléments suivants constituent la cible technique pour la refonte "from scratch" de l'agent.

### 3.1 Migration Asynchrone Absolue (Critique)
*   **Problème :** Tous les outils actuels sont déclarés de manière synchrone (`def`).
*   **Cible :** Refactoriser intégralement les outils en `async def`. Aucune opération I/O ne doit bloquer l'Event Loop de FastAPI (utilisation exclusive de `asyncio`).

### 3.2 Implémentation Pydantic v2 (Haute Priorité)
*   **Problème :** L'agent manipule des chaînes JSON basiques sans contraintes.
*   **Cible :**
    *   Créer un répertoire `src/agent_acadomie/schemas/` contenant les schémas stricts (ex: `HomeworkSchema`, `GradeResponse`, `CalendarEvent`).
    *   Type-hinter strictement chaque paramètre entrant et sortant des "tools" avec ces objets pour forcer la validation native de FastAPI/Pydantic.

### 3.3 Gestion Active des Erreurs : Fail-Fast & Anti-Hallucination (Haute Priorité)
*   **Problème :** Les erreurs (comme l'absence de données) génèrent du texte ("Aucune note trouvée") qui est ensuite réinterprété sans certitude logique par l'orchestrateur.
*   **Cible :**
    *   Cesser les gestions silencieuses. Implémenter des exceptions explicites (A2ARPCError) en cas d'indisponibilité ou d'incohérence.
    *   Appliquer la charte Anti-Hallucination : en l'absence de données réelles, l'outil doit formuler son incapacité précise de sorte que Maestro informe correctement l'utilisateur final.

### 3.4 Persistance et Base de Données Asynchrone (Moyenne Priorité)
*   **Problème :** Absence totale de connexion à la base de données.
*   **Cible :** Connecter l'agent au serveur PostgreSQL via `sqlalchemy[asyncio]` et le driver `asyncpg`. Mettre en place un dossier de datas/models.

### 3.5 Documentation pour Triage IA (Moyenne Priorité)
*   **Problème :** Docstrings existantes mais perfectibles pour le routeur sémantique central.
*   **Cible :** Enrichir sémantiquement les docstrings de chaque outil Pydantic afin d'optimiser le filtrage des intentions par le gateway Maestro en amont.

### 3.6 Couverture de Tests Automatisée
*   **Problème :** Zéro couverture de tests identifiée.
*   **Cible :** Rédiger la suite de tests avec `pytest-asyncio`. Isoler le réseau et utiliser des mocks LLM selon le standard "Zéro I/O réseau en CI".

---

## 4. Prochaine Phase (Roadmap de Refonte Spécifique)
1. **Épique 1** : Création du socle projet asynchrone et des couches de schémas Pydantic stricte.
2. **Épique 2** : Connectivité Base de Données (ORM SQLAlchemy / asyncpg).
3. **Épique 3** : Câblage intelligent ADK / Outils Pydantic (Logiques métier, Fail-Fast, Anti-hallucination).
4. **Épique 4** : Déploiement des tests automatisés (Mock absolu des I/O réseau).
