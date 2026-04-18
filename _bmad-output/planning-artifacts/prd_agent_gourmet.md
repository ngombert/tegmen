---
project_name: 'Tegmen (Family-Agents)'
document_type: 'Product Requirements Document'
module: 'Agent Gourmet'
status: 'Draft'
author: 'Chef de Produit (IA)'
stepsCompleted: ["step-04-journeys.md", "step-05-domain.md", "step-06-innovation.md", "step-07-project-type.md", "step-08-scoping.md", "step-09-functional.md", "step-10-nonfunctional.md", "step-11-polish.md"]
---

# PRD : Agent Gourmet

## 1. Vision et Objectifs
L'**Agent Gourmet** est un microservice spécialisé (serveur A2A) au sein de l'écosystème Tegmen. Son rôle est d'agir en tant qu'expert en cuisine familiale, fournissant la recherche de recettes et l'accès à leurs détails (ingrédients, étapes). À terme, il gérera la planification complète des repas. 
Conçu pour être interrogé sans interface graphique, il délègue l'autorisation et l'intention utilisateur à l'agent fédérateur **Maestro** (Gateway A2A).

## 2. État Actuel de l'Implémentation (As-Is)
L'infrastructure de base est opérationnelle mais s'appuie sur des composants de test non adaptés à la production (dette technique bloquante).

### 2.1 Capacités Implémentées (Skills ADK)
*   **`search_recipes`** : Recherche textuelle dans une base de recettes par mots-clés ou "tags".
*   **`get_recipe_details`** : Récupère les détails structurels d'une recette via un identifiant unique (`recipe_id`).

### 2.2 Stack Technique Actuelle
*   FastAPI orchestré par `uvicorn`.
*   Protocole d'Échange : SDK A2A (`a2a-sdk`) monté sur la racine (`/`).
*   LlmAgent de `google-adk` alimenté par `LiteLLM`.
*   Persistance : **Mock local vulnérable** (`RECIPES_DB`).

## 3. Axes d'Amélioration Architecturale
Pour se conformer aux standards du projet (réf : `project-context.md`), les migrations suivantes sont impératives :

*   **Migration Asynchrone (Critique)** : Refactoriser les appels réseau en `async def` pour ne pas bloquer l'Event Loop de FastAPI.
*   **Implémentation Pydantic (Haute Priorité)** : Migrer les types primitifs vers des schémas Pydantic v2 (ex: `RecipeSchema`) placés dans `src/agent_gourmet/schemas/`.
*   **Fail-Fast & Erreurs (Haute Priorité)** : Remplacer les erreurs silencieuses par des levées d'exceptions explicites (ex: erreur RPC formatée équivalente à HTTP 404) pour alerter Maestro proprement.
*   **Migration Data (Moyenne)** : Remplacer le mock par une base PostgreSQL via `asyncpg` et SQLAlchemy.
*   **Sémantique de Triage** : Réviser les docstrings des algorithmes (skills) pour faciliter le routage via LLM chez Maestro.
*   **Couverture Automatisée** : Mettre en place `pytest-asyncio` avec un blocage formel de tous les flux I/O réseaux durant la CI (`pytest-httpx`).

## 4. Parcours Utilisateurs (User Journeys)

### 4.1 "Happy Path" : La Famille cherche l'inspiration
*   **Situation :** Nicolas rentre avec les enfants, il lui reste des courgettes et des pâtes. Il demande une recette végétarienne à Maestro.
*   **Déroulement :** Maestro sollicite l'Agent Gourmet via une sous-requête A2A anonymisée. Grâce à son asynchronisme natif (`asyncpg`), Gourmet interroge la base de données de manière sub-milliseconde.
*   **Résolution :** Gourmet retourne directement une structure typée Pydantic de la recette "Pâtes aux courgettes rôties". Nicolas est servi instantanément.

### 4.2 "Edge Case" : Résilience Fail-Fast
*   **Situation :** L'identifiant d'une recette demandée a été accidentellement supprimé. Maestro interroge Gourmet.
*   **Déroulement :** Gourmet ne trouve rien. Au lieu de faire patienter Maestro jusqu'au timeout, Gourmet lève immédiatement une exception RPC "Recette non trouvée".
*   **Résolution :** Maestro capte l'exception et prévient explicitement la famille (anti-hallucination).

### 4.3 "Admin Path" : Testabilité CI/CD
*   **Situation :** Le développeur modifie les schémas de base de données. 
*   **Déroulement :** Il exécute la suite de tests `pytest-asyncio` sur un environnement totalement mocké (sans accès PostgreSQL physique).
*   **Résolution :** Les tests valident instantanément la conformité des schémas Pydantic v2 sans nécessiter d'infrastructure réseau en CI.

## 5. Spécificités API Backend (Architecture & Contrats)

*   **Délégation Auth (Context Shield)** : L'Agent Gourmet délègue totalement l'authentification et l'autorisation (RBAC) des utilisateurs finaux à Maestro. L'authentification technique inter-services s'appuie sur la validation d'un *Trust Token* (ex: en-tête `X-A2A-Secret`) intercepté localement par Gourmet.
*   **Contract Testing** : La stabilité du payload A2A est couverte par du *Consumer-Driven Contract Testing* (ex: Pact) pour s'assurer qu'aucune modification de l'unanimité des structs Pydantic ne casse le contrat avec Maestro en production.

## 6. Stratégie de Déploiement et Périmètre (Scoping)

### 6.1 Phase 1 : MVP "Technical Robustness"
L'objectif est d'assurer une intégration A2A irréprochable avec Maestro. La richesse fonctionnelle de la base de données est secondaire face à la solidité du pipeline et des types.
*   **Must-Haves** : Endpoints `search_recipes` et `get_recipe_details` via le SDK A2A ; couche de schémas stricts Pydantic v2 ; mécanique de Fail-Fast (`A2AReceiverException`) ; base mockée minimale (`RECIPES_DB`).

### 6.2 Phase 2 : Croissance (Growth)
*   **Déploiement SQL** : Connexion PostgreSQL de production via `asyncpg`.
*   **Recherche avancée** : Filtrage par mots-clés, temps de préparation.
*   **Optimisation Locale** : Mise en cache en mémoire des requêtes classiques.

### 6.3 Phase 3 : Planification et Expansion
*   API de Planification de Repas (`generate_weekly_plan`).
*   Interconnexion (ou mock) avec l'inventaire du réfrigérateur (Fridge API interface).

### 6.4 Atténuation des Risques
*   **Risque de Désynchronisation JSON-RPC :** Traité par le Consumer-Driven Contract Testing.
*   **Lenteur de la Gateway (Latence P95) :** Cadré par des exigences de temps de réponse non-fonctionnelles strictes.

## 7. Exigences Fonctionnelles (Functional Requirements)

### Découverte et Extraction
*   **FR1** : L'API Gateway (Maestro) peut rechercher des recettes à partir de mots-clés simples et/ou d'ingrédients spécifiques.
*   **FR2** : Maestro peut filtrer positivement les résultats en incluant des tags structurés (ex: plat, dessert).
*   **FR3** : Maestro peut filtrer négativement (exclure) des tags ou des ingrédients spécifiques (ex: allergènes traduits par son *Context Shield*).
*   **FR4** : Maestro peut limiter et paginer les résultats de recherche (Volume max) pour protéger le LLM.
*   **FR5** : Maestro peut restreindre les résultats d'une recherche en fonction d'un temps de préparation spécifié.
*   **FR6** : Maestro est informé de manière formelle et explicite s'il n'y a aucun résultat correspondant à la recherche.
*   **FR7** : Maestro peut extraire toutes les métadonnées d'une recette complète en fournissant son identifiant unique.
*   **FR8** : Maestro peut obtenir la liste distincte et quantifiée des ingrédients nécessaires pour une recette donnée.
*   **FR9** : Maestro est notifié instantanément par une erreur structurée (Fail-Fast) si l'identifiant de la recette demandée n'existe pas.
*   **FR10** : Maestro peut obtenir les instructions séquentielles de préparation (pas-à-pas) pour une recette.
*   **FR11** : *(Phase 2)* Maestro peut demander le calcul proportionnel (rescale) des quantités des ingrédients d'une recette en renseignant un nombre de portions cible.

### Planification Culinaire (Phase 3)
*   **FR12** : Maestro peut demander la suggestion d'un menu de repas couvrant une période calendaire spécifique.
*   **FR13** : L'Agent Gourmet peut évaluer les recettes réalisables en fonction d'un inventaire d'ingrédients fourni.
*   **FR14** : Maestro peut transmettre une collection d'identifiants de recettes à Gourmet pour déclencher la génération d'une liste de courses (ingrédients agrégés).

### Intégrité et Déclaration
*   **FR15** : Tout système consommateur peut obtenir formellement la description sémantique détaillée de la compétence (skill) offerte par l'agent.
*   **FR16** : Le système rejette automatiquement à l'entrée toute requête envoyée par Maestro ne respectant pas strictement le modèle de données attendu.

## 8. Exigences Non-Fonctionnelles (Non-Functional Requirements)

### 8.1 Performance
*   **NFR-PERF-1 (Latence IO)** : L'Agent Gourmet doit traiter une requête SQL de `search_recipes` en base de données asynchrone en moins de 50ms (P95) pour prévenir tout goulot d'étranglement ou silence prolongé avec le LLM Maestro.
*   **NFR-PERF-2 (Concurrence Domestique)** : Le système doit pouvoir supporter un micro-pic domestique allant jusqu'à 5 requêtes concurrentes sans blocage en s'appuyant sur un pool de base de données asynchrone minime (ex: max 10 connexions). 

### 8.2 Fiabilité (Reliability)
*   **NFR-REL-1 (Crash Recovery)** : Le redémarrage à froid du service doit être pleinement opérationnel en moins de 3 secondes, favorisant une tolérance aux redémarrages rapides du serveur domestique.
*   **NFR-REL-2 (Fail-Fast Timeout & Chaos Testing)** : Toute requête vers la persistance dépassant un délai critique de 3000ms doit interrompre la coroutine asynchrone et renvoyer une erreur explicite. L'application supporte par ailleurs l'injection par variable d'environnement (`.env`) d'un délai artificiel pour éprouver mécaniquement la solidité de ce timeout.

### 8.3 Sécurité et Intégration
*   **NFR-INT-1 (Type Safety Strict)** : 100% des objets A2A d'entrée et de sortie s'appuient sur des modèles `Pydantic v2` paramétrés en `strict=True`. Tout cast implicite induit par une anomalie réseau provoquera un échec structurel.
*   **NFR-SEC-1 (Zero-Trust Local Logging)** : Fini les `print` génériques. L'Agent Gourmet doit produire des journaux de logs via un système "Structured JSON Logging" qui ne laisse transparaître en clair que les variables d'état ou identifiants (ex: `recipe_id`), excluant formellement toute donnée textuelle saisie par la famille.
