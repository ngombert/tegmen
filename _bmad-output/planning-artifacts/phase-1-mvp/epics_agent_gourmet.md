---
stepsCompleted:
  - step-01-validate-prerequisites.md
  - step-02-design-epics.md
  - step-03-create-stories.md
  - step-04-final-validation.md
inputDocuments:
  - _bmad-output/planning-artifacts/prd_agent_gourmet.md
  - _bmad-output/planning-artifacts/architecture.md
  - docs/A2A.md
---

# tegmen - Epic Breakdown (Agent Gourmet)

## Overview

This document provides the complete epic and story breakdown for the Agent Gourmet module of tegmen, decomposing the requirements from the PRD, Architecture decisions, and lessons learned from the Maestro agent implementation into implementable stories.

## Requirements Inventory

### Functional Requirements

FR1: L'API Gateway (Maestro) peut rechercher des recettes à partir de mots-clés simples et/ou d'ingrédients spécifiques.
FR2: Maestro peut filtrer positivement les résultats en incluant des tags structurés (ex: plat, dessert).
FR3: Maestro peut filtrer négativement (exclure) des tags ou des ingrédients spécifiques (ex: allergènes traduits par son Context Shield).
FR4: Maestro peut limiter et paginer les résultats de recherche (Volume max) pour protéger le LLM.
FR5: Maestro peut restreindre les résultats d'une recherche en fonction d'un temps de préparation spécifié.
FR6: Maestro est informé de manière formelle et explicite s'il n'y a aucun résultat correspondant à la recherche.
FR7: Maestro peut extraire toutes les métadonnées d'une recette complète en fournissant son identifiant unique.
FR8: Maestro peut obtenir la liste distincte et quantifiée des ingrédients nécessaires pour une recette donnée.
FR9: Maestro est notifié instantanément par une erreur structurée (Fail-Fast) si l'identifiant de la recette demandée n'existe pas.
FR10: Maestro peut obtenir les instructions séquentielles de préparation (pas-à-pas) pour une recette.
FR11: *(Phase 2)* Maestro peut demander le calcul proportionnel (rescale) des quantités des ingrédients d'une recette en renseignant un nombre de portions cible.
FR12: *(Phase 3)* Maestro peut demander la suggestion d'un menu de repas couvrant une période calendaire spécifique.
FR13: *(Phase 3)* L'Agent Gourmet peut évaluer les recettes réalisables en fonction d'un inventaire d'ingrédients fourni.
FR14: *(Phase 3)* Maestro peut transmettre une collection d'identifiants de recettes à Gourmet pour déclencher la génération d'une liste de courses (ingrédients agrégés).
FR15: Tout système consommateur peut obtenir formellement la description sémantique détaillée de la compétence (skill) offerte par l'agent.
FR16: Le système rejette automatiquement à l'entrée toute requête envoyée par Maestro ne respectant pas strictement le modèle de données attendu.

### NonFunctional Requirements

NFR-PERF-1 (Latence IO): L'Agent Gourmet doit traiter une requête SQL de `search_recipes` en base de données asynchrone en moins de 50ms (P95) pour prévenir tout goulot d'étranglement ou silence prolongé avec le LLM Maestro.
NFR-PERF-2 (Concurrence Domestique): Le système doit pouvoir supporter un micro-pic domestique allant jusqu'à 5 requêtes concurrentes sans blocage en s'appuyant sur un pool de base de données asynchrone minime (ex: max 10 connexions).
NFR-REL-1 (Crash Recovery): Le redémarrage à froid du service doit être pleinement opérationnel en moins de 3 secondes, favorisant une tolérance aux redémarrages rapides du serveur domestique.
NFR-REL-2 (Fail-Fast Timeout & Chaos Testing): Toute requête vers la persistance dépassant un délai critique de 3000ms doit interrompre la coroutine asynchrone et renvoyer une erreur explicite. L'application supporte par ailleurs l'injection par variable d'environnement (`.env`) d'un délai artificiel pour éprouver mécaniquement la solidité de ce timeout.
NFR-INT-1 (Type Safety Strict): 100% des objets A2A d'entrée et de sortie s'appuient sur des modèles Pydantic v2 paramétrés en `strict=True`. Tout cast implicite induit par une anomalie réseau provoquera un échec structurel.
NFR-SEC-1 (Zero-Trust Local Logging): L'Agent Gourmet doit produire des journaux de logs via un système "Structured JSON Logging" qui ne laisse transparaître en clair que les variables d'état ou identifiants (ex: `recipe_id`), excluant formellement toute donnée textuelle saisie par la famille.

### Additional Requirements

- **Migration Asynchrone (Critique)** : Refactoriser toutes les fonctions I/O (tools) en `async def` pour ne pas bloquer l'Event Loop de FastAPI.
- **Restructuration Architecturale** : Réorganiser le module en `app/api/routers/`, `app/schemas/`, `app/services/` conformément à la structure définie dans l'architecture.
- **Remplacement des Erreurs Silencieuses** : Les retours `{"error": "..."}` actuels doivent être remplacés par des levées d'exceptions `A2ARPCError` avec des codes spécifiques au domaine (ex: `RECIPE_NOT_FOUND = -32010`).
- **Injection de Dépendances (CI Zéro Réseau)** : Les clients réseau/LLM doivent être explicitement injectables via `FastAPI Depends()` ou en paramètres d'objets pour garantir un mocking complet en CI.
- **Typage Strict Python 3.13+** : Utilisation des built-ins natifs (`list`, `dict`, `X | None`), interdiction de `typing.List`, `typing.Optional`. Annotation de retour obligatoire sur chaque fonction (`-> None:`).
- **`snake_case` exclusif** dans les payloads JSON-RPC (pas de conversion d'alias Pydantic).
- **`correlation_id` obligatoire** : Propager le `correlation_id` du `RequestContext` dans les logs et les réponses d'erreur pour la traçabilité distribuée (leçon Maestro Story 4.3/4.4).
- **Docstrings Exhaustives sur les Skills** : Les skills exposées au LLM via l'ADK doivent avoir des docstrings exhaustives (description, arguments, objectif) servant de prompt de décision au routeur sémantique de Maestro.
- **Couverture Tests Automatisée** : `pytest-asyncio` (`asyncio_mode="auto"`) avec blocage formel de tous les flux I/O réseau en CI. Scénarios nominaux + cas de défaillance (timeouts, payloads invalides).
- **OpenTelemetry (Héritage Transverse)** : L'instrumentation OTel est automatiquement activée via `common/a2a_server.py` (`config.OTEL_ENABLED`). Gourmet doit s'assurer de propager le `trace_id` dans ses réponses d'erreur pour le `debug_info` de Maestro.
- **Structured JSON Logging** : Le `common/logger.py` actuel utilise un format texte simple. Le NFR-SEC-1 exige du JSON structuré — nécessite une migration du handler logging.
- **README Agent Obligatoire** : Chaque agent doit disposer d'un `README.md` conforme au template `docs/templates/README-agent.template.md` (exigence `project-context.md`). Critère bloquant pour la validation d'un epic.
- **Chaos Testing côté Serveur** : Le PRD NFR-REL-2 exige l'injection de délai artificiel côté Gourmet (variable `.env`) — complémentaire au timeout côté client Maestro.
- **Correction Intégration A2A (Audit)** : Le `A2AServer` dans `common/a2a_server.py` ne connecte pas l'agent ADK au handler `message/send` — aucune requête n'est dispatchée. Correction rétro-compatible nécessaire. Le `RequestContext` (family_id, correlation_id, restrictions) n'est pas transmis par `common/a2a_client.py` aux sous-agents — ajout d'un paramètre optionnel `context` rétro-compatible.

### UX Design Requirements

(Système backend A2A pur — pas d'interface graphique)

### FR Coverage Map

FR1:  Epic 1 (Story 1.2) — Recherche par mots-clés et ingrédients
FR2:  Epic 1 (Story 1.3) — Filtrage positif par tags structurés
FR3:  Epic 1 (Story 1.3) — Filtrage négatif (exclusion tags/ingrédients)
FR4:  Epic 1 (Story 1.3) — Limitation et pagination des résultats
FR5:  Epic 1 (Story 1.3) — Restriction par temps de préparation
FR6:  Epic 1 (Story 1.2) — Notification formelle si aucun résultat
FR7:  Epic 2 (Story 2.1) — Extraction des métadonnées complètes d'une recette
FR8:  Epic 2 (Story 2.1) — Liste quantifiée des ingrédients
FR9:  Epic 2 (Story 2.2) — Fail-Fast si ID recette inexistant
FR10: Epic 2 (Story 2.1) — Instructions séquentielles de préparation
FR11: (Phase 2 — Hors scope MVP)
FR12: (Phase 3 — Hors scope MVP)
FR13: (Phase 3 — Hors scope MVP)
FR14: (Phase 3 — Hors scope MVP)
FR15: Epic 1 (Story 1.1) — Exposition de l'Agent Card A2A et dispatch A2A fonctionnel
FR16: Epic 1 (Story 1.1) — Rejet des requêtes non conformes (validation Pydantic strict)

## Epic List

### Epic 1: Recherche et Découverte de Recettes
Maestro peut rechercher des recettes pour la famille avec des filtres avancés (tags, ingrédients, exclusions, temps de préparation) et reçoit des résultats structurés et paginés. Inclut la refactorisation fondatrice (async, Pydantic, restructuration `app/`, correction intégration A2A).
**FRs covered:** FR1, FR2, FR3, FR4, FR5, FR6, FR15, FR16

### Epic 2: Consultation Détaillée d'une Recette
Maestro peut extraire les métadonnées complètes, les ingrédients quantifiés et les instructions pas-à-pas d'une recette spécifique, avec un retour d'erreur immédiat si la recette n'existe pas.
**FRs covered:** FR7, FR8, FR9, FR10

### Epic 3: Résilience, Observabilité et Intégration Écosystème
L'agent Gourmet est robuste en production : timeout sur la persistance avec chaos testing, propagation du correlation_id et du trace_id OpenTelemetry, structured JSON logging, et documentation complète (README).
**NFRs covered:** NFR-PERF-1, NFR-PERF-2, NFR-REL-1, NFR-REL-2, NFR-SEC-1

---

## Epic 1: Recherche et Découverte de Recettes

### Story 1.1: Fondation A2A et Structure Agent Gourmet

As a développeur Tegmen,
I want que l'Agent Gourmet soit restructuré selon l'architecture standardisée et que le serveur A2A dispatch correctement les requêtes,
So that les futurs endpoints Gourmet soient opérationnels de bout en bout via le protocole A2A.

**Acceptance Criteria:**

**Given** le module `agent_gourmet/` actuel avec des fonctions synchrones et une structure flat
**When** la restructuration est appliquée
**Then** le module est organisé en `app/schemas/`, `app/services/`, `app/api/` avec des imports fonctionnels
**And** tous les modèles Pydantic utilisent `ConfigDict(strict=True)` et le typage Python 3.13+
**And** `common/a2a_server.py` est corrigé pour dispatcher la méthode `message/send` vers l'agent ADK (correction rétro-compatible)
**And** `common/a2a_client.py` accepte un paramètre optionnel `context: RequestContext | None = None` pour la propagation du contexte (rétro-compatible)
**And** un test d'intégration A2A automatisé valide le flux client → serveur → handler → réponse
**And** les 84 tests existants passent sans régression
**And** FR15 : l'endpoint `/a2a/AgentCard` retourne les métadonnées enrichies de l'agent
**And** FR16 : une requête JSON-RPC mal formée est rejetée avec une erreur Pydantic structurée

### Story 1.2: Recherche de Recettes Basique

As a famille utilisant Tegmen,
I want pouvoir chercher des recettes par mots-clés ou ingrédients,
So that je puisse trouver des idées de repas rapidement.

**Acceptance Criteria:**

**Given** une base de recettes en mémoire (mock `RECIPES_DB`, migration DB hors scope MVP)
**When** Maestro envoie une requête `search_recipes` avec un mot-clé
**Then** Gourmet retourne une liste de recettes correspondantes avec `name`, `id`, `tags`, `prep_time`
**And** la fonction est `async def` et utilise des schémas Pydantic (`SearchRequest`, `SearchResponse`)
**And** FR1 : la recherche fonctionne par nom de recette et par nom d'ingrédient
**And** FR6 : si aucun résultat ne correspond, la réponse contient un payload structuré explicite (`results: [], total_count: 0`)
**And** les résultats sont vérifiés par des tests `pytest-asyncio` sans I/O réseau

### Story 1.3: Filtres Avancés et Pagination

As a famille utilisant Tegmen,
I want pouvoir affiner ma recherche de recettes avec des filtres (tags, exclusions, temps, pagination),
So that je reçoive des résultats ciblés et en volume contrôlé.

**Acceptance Criteria:**

**Given** le service de recherche de la Story 1.2
**When** Maestro envoie une requête avec des paramètres de filtrage
**Then** FR2 : les résultats sont filtrables par tags inclusifs (ex: `tags_include: ["plat", "rapide"]`)
**And** FR3 : les résultats excluent les recettes contenant des tags ou ingrédients spécifiques (ex: `tags_exclude: ["arachide"]`, `ingredients_exclude: ["gluten"]`)
**And** FR4 : les résultats sont paginables via `limit` et `offset`, avec un `total_count` dans la réponse
**And** FR5 : les résultats sont filtrables par `max_prep_time` en minutes
**And** les filtres sont cumulatifs (AND logic)
**And** les paramètres de filtrage sont validés par un schéma Pydantic strict (`SearchFilters`)
**And** les cas limites (filtres vides, limit=0) sont couverts par des tests

---

## Epic 2: Consultation Détaillée d'une Recette

### Story 2.1: Extraction Complète d'une Recette

As a famille utilisant Tegmen,
I want pouvoir consulter les détails complets d'une recette (métadonnées, ingrédients, instructions),
So that je puisse suivre la recette pas-à-pas pour préparer le repas.

**Acceptance Criteria:**

**Given** un identifiant de recette existant dans la base
**When** Maestro envoie une requête `get_recipe_details` avec le `recipe_id`
**Then** FR7 : Gourmet retourne un schéma Pydantic complet contenant les métadonnées (`name`, `tags`, `prep_time`, `servings`, `difficulty`)
**And** FR8 : la réponse inclut la liste distincte et quantifiée des ingrédients (`name`, `quantity`, `unit`)
**And** FR10 : la réponse inclut les instructions séquentielles de préparation (liste ordonnée de `steps`)
**And** le schéma de réponse (`RecipeDetailResponse`) utilise `ConfigDict(strict=True)`

### Story 2.2: Fail-Fast sur Recette Inexistante

As a Maestro (API Gateway),
I want recevoir une erreur structurée immédiate si l'identifiant de recette demandé n'existe pas,
So that je puisse informer la famille sans halluciner ni patienter inutilement.

**Acceptance Criteria:**

**Given** un identifiant de recette inexistant (ex: `recipe_id="999"`)
**When** Maestro envoie une requête `get_recipe_details`
**Then** FR9 : Gourmet lève une `A2ARPCError` avec un code spécifique au domaine (ex: `RECIPE_NOT_FOUND = -32010`)
**And** l'erreur contient un `message` explicite en français et un champ `data` avec le `recipe_id` invalide
**And** le pattern `{"error": "Recette non trouvée"}` (retour actuel de `tools.py`) est supprimé
**And** un test vérifie que Maestro reçoit bien une `JsonRpcResponse` avec un `error` structuré (pas un `result`)
**And** un test vérifie qu'un `recipe_id` de type invalide (ex: non-string) est rejeté par validation Pydantic

---

## Epic 3: Résilience, Observabilité et Intégration Écosystème

### Story 3.1: Timeout Persistance et Chaos Testing

As a opérateur du serveur domestique Tegmen,
I want que l'Agent Gourmet interrompe immédiatement toute requête de persistance dépassant un délai critique et supporte l'injection de latence artificielle,
So that le système ne reste jamais bloqué et que je puisse tester sa robustesse.

**Acceptance Criteria:**

**Given** un service de persistance (mock ou futur asyncpg)
**When** une requête de données dépasse 3000ms
**Then** NFR-REL-2 : la coroutine est interrompue via `asyncio.wait_for` et une `A2ARPCError(TIMEOUT)` est levée
**And** NFR-REL-2 : la variable d'environnement `GOURMET_ARTIFICIAL_DELAY_MS` injecte un délai artificiel dans le service de persistance pour simuler la lenteur
**And** un test vérifie que le timeout déclenche l'erreur en < 3100ms
**And** un test vérifie que le chaos testing (délai injecté > seuil) produit bien une `A2ARPCError(TIMEOUT)`
**And** NFR-REL-1 : le démarrage à froid du service est opérationnel en moins de 3 secondes (test de lifespan)
**And** NFR-PERF-2 : 5 requêtes concurrentes s'exécutent sans blocage (test `asyncio.gather`)

### Story 3.2: Observabilité — Correlation ID et Traces

As a développeur déboguant un flux Maestro → Gourmet,
I want que le `correlation_id` et le `trace_id` OpenTelemetry soient propagés dans les logs et les réponses d'erreur de Gourmet,
So that je puisse tracer une requête de bout en bout dans le système distribué.

**Acceptance Criteria:**

**Given** une requête A2A reçue par Gourmet contenant un `RequestContext` avec `correlation_id`
**When** Gourmet traite la requête
**Then** le `correlation_id` apparaît dans chaque ligne de log émise pendant le traitement
**And** en cas d'erreur, le `correlation_id` est inclus dans le champ `data` de la `JsonRpcError`
**And** si `OTEL_ENABLED=true`, le `trace_id` du span courant est inclus dans les réponses d'erreur (pour le `debug_info` de Maestro)
**And** un test vérifie la propagation du `correlation_id` dans les logs (mock logger)
**And** un test vérifie la présence du `correlation_id` dans les erreurs structurées

### Story 3.3: Structured JSON Logging et Zero-Trust

As a opérateur du serveur domestique Tegmen,
I want que les logs de l'Agent Gourmet soient au format JSON structuré et n'exposent jamais les données textuelles de la famille,
So that les logs soient exploitables par des outils d'analyse et respectent la vie privée.

**Acceptance Criteria:**

**Given** le handler logging actuel (`common/logger.py`) en format texte
**When** Gourmet émet un log
**Then** NFR-SEC-1 : le format de sortie est JSON structuré (un objet JSON par ligne) avec les clés `timestamp`, `level`, `service`, `correlation_id`, `message`
**And** NFR-SEC-1 : les données textuelles de la famille (message utilisateur, contenu de recette) ne sont jamais loguées en clair — seuls les identifiants (`recipe_id`, `user_id`, `family_id`) apparaissent
**And** la migration est implémentée comme un handler local Gourmet (pas de modification de `common/logger.py` pour éviter les régressions transverses)
**And** un test vérifie que la sortie log est un JSON parseable
**And** un test vérifie qu'un message contenant du texte utilisateur n'apparaît pas dans les logs

### Story 3.4: Documentation README Agent

As a développeur de l'écosystème Tegmen,
I want que l'Agent Gourmet dispose d'un README complet et conforme au template,
So that tout contributeur puisse comprendre, lancer et tester l'agent rapidement.

**Acceptance Criteria:**

**Given** le template `docs/templates/README-agent.template.md`
**When** le README est généré pour Gourmet
**Then** le fichier `src/agent_gourmet/README.md` existe et suit la structure du template
**And** il documente : description, endpoints A2A, schémas Pydantic, configuration (variables `.env`), commandes de lancement (`uv run`), commandes de test
**And** les skills exposées (search_recipes, get_recipe_details) sont listées avec leurs paramètres



