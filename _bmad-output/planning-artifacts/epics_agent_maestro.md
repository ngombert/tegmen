---
stepsCompleted:
  - step-01-validate-prerequisites.md
  - step-02-design-epics.md
  - step-03-create-stories.md
inputDocuments:
  - _bmad-output/planning-artifacts/prd_agent_maestro.md
  - _bmad-output/planning-artifacts/architecture.md
  - docs/A2A.md
---

# tegmen - Epic Breakdown

## Overview

This document provides the complete epic and story breakdown for tegmen, decomposing the requirements from the PRD, UX Design if it exists, and Architecture requirements into implementable stories.

## Requirements Inventory

### Functional Requirements

FR1: Le système peut recevoir une intention textuelle non-structurée.
FR2: Le système identifie localement (sans LLM distant) l'agent spécialisé compétent.
FR3: Le système transmet la demande à l'agent cible via le protocole A2A.
FR4: Le système notifie son incompétence si l'intention ne correspond à aucun domaine répertorié.
FR5: Le système identifie l'émetteur de la demande (authentification).
FR6: Le système modifie automatiquement la requête pour y greffer les spécificités du profil de l'émetteur.
FR7: Le système applique et transmet les restrictions parentales (RBAC implicite) bloquantes.
FR8: Le système expurge ou masque irréversiblement toute PII avant écriture en journal/stdout.
FR9: Le système conserve des journaux de télémétrie exploitables pour le debugging (latence, échec) exempts de contenu privé.
FR10: Le système applique un délai SLA aux requêtes sortantes avant neutralisation.
FR11: Le système notifie instantanément l'utilisateur d'un échec de jonction A2A (Fail-Fast).
FR12: Le système émet une erreur structurée (ex. HTTP 422) si un agent tiers ne respecte pas le schéma Pydantic entendu.
FR13: Le système maintient un unique endpoint façade pour les applications front-end.
FR14: Le système expose sa topologie JSON-RPC de façon lisible via la documentation OpenAPI générée par FastAPI.

### NonFunctional Requirements

NFR-PERF-1 (Overhead Latency): Temps additionnel du routage restreint à 100ms (P95) sur hardware accéléré, ou 300ms sur CPU ARM standard.
NFR-PERF-2 (Zero-Blocking): API asynchrone maintenant l'Event Loop accessible à 100%. L'interface supporte 50 requêtes simultanées ; inférence dans ThreadPoolExecutor.
NFR-SEC-1 (Sanitization Assurance): Validation du caviardage PII en CI par dictionnaire Mock empoisonné.
NFR-SEC-2 (Data Localization): 100% de la chaîne de décision exécutée local-first.
NFR-REL-1 (Crash Recovery): Auto-reboot du conteneur en < 10 secondes.
NFR-REL-2 (Type Safety Contract): Tolérance zéro sur erreur A2A (Graceful Degradation interceptant l'erreur).

### Additional Requirements

- Implémentation du Starter Template Standardized Lean FastAPI via src/common/ partagé en Epic 1.
- Tous les échanges JSON-RPC sont en snake_case. Le client gèrera la transformation vers le camelCase.
- Dépendances réseau (httpx) et services d'inférence (litellm) explicitement injectables pour valider un CI Zéro Réseau.
- Stratégie en mémoire (In-Memory) pour le routeur sémantique (Pas de base de données vectorielle complexe pour le routing).
- Les modèles Pydantic doivent être stricts, en PascalCase, et toute erreur de validation lève une A2ARPCError.
- Architecture stateless interdisant l'usage d'un orchestrateur LLM persistant local.

### UX Design Requirements

(Aucun document UX Design formel n'est présent)

### FR Coverage Map

FR1: Epic 3 (Story 3.1) - Classification de l'intention textuelle
FR2: Epic 3 (Story 3.1) - Analyse sémantique locale In-Memory
FR3: Epic 3 (Story 3.2) - Transport vers l'agent spécialiste via A2A
FR4: Epic 3 (Story 3.3) - Notification conversationnelle en cas de domaine non géré
ADR-REGISTRY: Epic 3 (Story 3.0) - Registre config-driven des agents (config/agents.yaml). Suppression du couplage direct (agents.py) et du mode monolithe. Décision issue du Party Mode 2026-04-18.
FR5: Epic 2 - Authentification de l'émetteur via JWT
FR6: Epic 2 - Modification du payload avec le profil utilisateur
FR7: Epic 2 - Respect des permissions/contrôle parental (RBAC)
FR8: Epic 2 - Effacement des PII avant tous les journaux logs
FR9: Epic 2 - Conservation de l'Audit asynchrone technique
FR10: Epic 4 - Politique temporelle (SLA Timeouts) pour les requêtes A2A
FR11: Epic 4 - Communication instantanée à l'utilisateur des échecs (Fail-Fast)
FR12: Epic 4 - Interception structurelle réseau des exceptions Pydantic 
FR13: Epic 1 - Stabilisation du Endpoint racine public FastAPI
FR14: Epic 1 - Auto-génération documentaire JSON-RPC / Swagger

## Epic List

### Epic 1: Fondation d'Accès et Couche d'Échange A2A
L'utilisateur (Front-end ou Dev) peut se connecter à Maestro via une API documentée et un protocole JSON-RPC standardisé.
**FRs covered:** FR13, FR14

### Epic 2: Bouclier de Contexte Actif et Confidentialité (Privacy)
La famille interagit de manière sécurisée ; les utilisateurs sont authentifiés, les permissions parentales sont appliquées et la vie privée (PII) est garantie dans les logs.
**FRs covered:** FR5, FR6, FR7, FR8, FR9

### Epic 3: Routage Sémantique Intelligent In-Memory
L'utilisateur voit ses demandes comprises et automatiquement redirigées vers l'agent spécialiste compétent, sans délai perceptible.
**FRs covered:** FR1, FR2, FR3, FR4, ADR-REGISTRY

> **ADR (Party Mode 2026-04-18) :** Cet Epic inclut une Story 3.0 de fondation qui introduit un registre d'agents config-driven (`config/agents.yaml` + `src/common/agent_registry.py`). Cette story supprime le fichier `src/agent_maestro/agents.py` (imports directs violant l'indépendance A2A), élimine le mode monolithe (`MICROSERVICES_MODE`), et nettoie les URLs hardcodées dans `config.py` et `a2a_client.py`. Le routeur sémantique (Story 3.1) et le dispatch A2A (Story 3.2) consomment ce registre comme source de vérité unique.

### Epic 4: Résilience Absolue et Dégradation Gracieuse
L'utilisateur n'est jamais bloqué ou face à une erreur obscure ; le système gère instantanément les pannes internes par un retour clair (Zero-Blocking/Fail-Fast).
**FRs covered:** FR10, FR11, FR12

<!-- Repeat for each epic in epics_list (N = 1, 2, 3...) -->

## Epic 1: Fondation d'Accès et Couche d'Échange A2A

L'utilisateur (Front-end ou Dev) peut se connecter à Maestro via une API documentée et un protocole JSON-RPC standardisé.

### Story 1.1: Librairie Commune A2A (Starter Template)

As a Développeur de l'écosystème Tegmen,
I want disposer des classes de base FastAPI et Pydantic pour le serveur et client A2A dans `src/common/`,
So that tous les agents actuels et futurs utilisent les mêmes exceptions et structures JSON-RPC.

**Acceptance Criteria:**

**Given** qu'un nouveau microservice est créé (ex. Maestro)
**When** le développeur importe `A2AServer` depuis `src.common`
**Then** le serveur est prêt à recevoir du JSON-RPC 2.0 validé par Pydantic
**And** la logique gère naturellement le snake_case et implémente la classe technique `A2ARPCError` prête à lever des exceptions formelles.

### Story 1.2: Création du Gateway Endpoint Public Maestro

As a Application Front-end,
I want un endpoint POST public unique exposé par Maestro (`/api/v1/routing`),
So that je puisse envoyer mes requêtes sans exposer les sous-réseaux Docker des autres agents.

**Acceptance Criteria:**

**Given** que le serveur `agent_maestro` est en cours d'exécution
**When** je soumets un appel POST valide JSON-RPC à la racine
**Then** l'API FastAPI intercepte la requête sans erreur de type
**And** je reçois une réponse asynchrone valide sans blocage CPU (vérifié par tests `pytest-asyncio` sans réseau avec Mock).

### Story 1.3: Auto-Documentation OpenAPI (Swagger)

As a Intégrateur système,
I want visiter l'accès Swagger généré de FastAPI (`/docs`),
So that je puisse lire la topologie et la signature exacte du requêtage JSON-RPC attendu.

**Acceptance Criteria:**

**Given** le serveur Maestro déployé localement
**When** un utilisateur accède au path `/docs` via un navigateur
**Then** les schémas d'entrée et les valeurs textuelles de JSON-RPC s'affichent correctement
**And** les structures de réponse (incluant erreurs de schémas) sont clairement listées avec leurs attributs.

<!-- Repeat for each epic in epics_list (N = 1, 2, 3...) -->

## Epic 2: Bouclier de Contexte Actif et Confidentialité (Privacy)

La famille interagit de manière sécurisée ; les utilisateurs sont authentifiés, les permissions parentales sont appliquées et la vie privée (PII) est garantie dans les logs.

### Story 2.1: Authentification Stricte et Validation JWT

As a Administrateur de Sécurité,
I want que Maestro exige et valide un token JWT valide (Bearer Token) pour toute requête,
So that les appels non autorisés soient rejetés avant d'utiliser la mémoire LLM ou le réseau.

**Acceptance Criteria:**

**Given** une requête entrante vers Maestro
**When** le payload ne contient pas un JWT valide
**Then** Maestro intercepte l'appel via un middleware ou `Depends` FastAPI et émet une erreur HTTP 401
**And** si le JWT est valide, l'identité (ex: `family_id`) est décodée en mémoire et attachée au contexte.

### Story 2.2: Filtre PII et Télémétrie d'Audit

As a Développeur chargé du support,
I want disposer de logs de latence et performance propres, sans PII,
So that l'audit système soit possible sans violer la Privacy de la famille.

**Acceptance Criteria:**

**Given** une requête contenant une donnée sensible (selon dictionnaire Mock poison)
**When** FastAPI journalise le suivi asynchrone (Stdout)
**Then** l'information sensible est remplacée irréversiblement par `***`
**And** un test `pytest` (CI) échoue si ce caviardage ne s'applique pas strictement.

### Story 2.3: Hydratation du Contexte et Contrôle Parental (RBAC)

As a Parent (Administrateur),
I want que les requêtes soient automatiquement enrichies du profil utilisateur et que les restrictions parentales soient appliquées sans intervention manuelle,
So that les agents spécialistes reçoivent un contexte complet et que les demandes hors-limites soient bloquées dès le Gateway.

**Acceptance Criteria:**

**Scénario 1 — Hydratation du profil (FR6) :**

**Given** une requête authentifiée et validée par JWT
**When** Maestro prépare la transmission vers l'agent spécialiste
**Then** le payload JSON-RPC sortant est automatiquement enrichi des métadonnées de profil de l'utilisateur (ex: `family_id`, `preferences`, `language`)
**And** aucune saisie manuelle de l'utilisateur n'est requise pour ce processus.

**Scénario 2 — Application des restrictions parentales (FR7) :**

**Given** une requête authentifiée pour un utilisateur soumis à des restrictions parentales (ex: Léo, 10 ans)
**When** Maestro évalue la requête contre le profil de restrictions de l'utilisateur
**Then** si la requête viole une restriction active (ex: accès hors plage horaire autorisée), l'envoi vers l'agent spécialiste est immédiatement bloqué
**And** l'utilisateur reçoit une réponse conversationnelle explicite (ex: "Désolé, cette fonctionnalité n'est pas disponible pour toi en ce moment.") sans qu'aucune erreur HTTP brute ne soit exposée.

<!-- Repeat for each epic in epics_list (N = 1, 2, 3...) -->

## Epic 3: Routage Sémantique Intelligent In-Memory

L'utilisateur voit ses demandes comprises et automatiquement redirigées vers l'agent spécialiste compétent, sans délai perceptible.

> **ADR (Party Mode 2026-04-18) :** Cet Epic introduit le registre config-driven (`config/agents.yaml`) comme source de vérité unique pour le catalogue d'agents. Il supprime le couplage in-process hérité (imports directs dans `agents.py`, mode monolithe `MICROSERVICES_MODE`) au profit d'une architecture 100% microservices A2A.

### Story 3.0: Registre d'Agents Config-Driven et Nettoyage du Couplage

As a Développeur de l'écosystème Tegmen,
I want un registre centralisé des agents chargé depuis un fichier de configuration externe (`config/agents.yaml`),
So that l'ajout ou la suppression d'un agent ne nécessite aucune modification du code source de Maestro.

**Contexte (ADR Party Mode 2026-04-18) :**
L'implémentation actuelle de l'Epic 1 a introduit un couplage in-process direct (`src/agent_maestro/agents.py` importait les modules Python des sous-agents), violant la règle topologique A2A. Le mode `MICROSERVICES_MODE` toggle et le dictionnaire `AGENT_URLS` hardcodé dans `a2a_client.py` encodaient en dur la liste des agents dans le code source. Cette story corrige ces violations en introduisant un registre config-driven comme fondation de l'Epic 3.

**Acceptance Criteria:**

**Scénario 1 — Chargement du registre :**

**Given** le fichier `config/agents.yaml` contenant la définition d'au moins un agent (nom, description, URL, utterances sémantiques)
**When** Maestro démarre
**Then** `src/common/agent_registry.py` charge et valide la configuration via un modèle Pydantic `AgentConfig`
**And** expose les fonctions `get_agent_url(route)`, `list_agents()` et `get_agent_utterances(route)` consommables par le routeur et le client A2A.

**Scénario 2 — Fail-Fast sur config invalide :**

**Given** un fichier `config/agents.yaml` absent, vide ou contenant un schéma invalide (ex: URL manquante, utterances vides)
**When** Maestro tente de démarrer
**Then** le démarrage échoue immédiatement avec un message d'erreur explicite indiquant le problème de configuration
**And** aucun trafic n'est servi avant validation complète.

**Scénario 3 — Override par variable d'environnement :**

**Given** le YAML définit `url: http://localhost:8001` pour l'agent gourmet
**When** la variable d'environnement `AGENT_GOURMET_URL` est définie à `http://agent-gourmet:8000`
**Then** l'URL effective utilisée par le registre est celle de la variable d'environnement (priorité env > YAML).

**Scénario 4 — Nettoyage du code hérité :**

**Given** le registre config-driven opérationnel
**When** la story est terminée
**Then** le fichier `src/agent_maestro/agents.py` est supprimé (code mort)
**And** les variables `GOURMET_URL`, `ACADOMIE_URL`, `EXPLORER_URL` sont retirées de `src/common/config.py`
**And** le dictionnaire `AGENT_URLS` hardcodé est retiré de `src/common/a2a_client.py` au profit d'un appel au registre
**And** le toggle `MICROSERVICES_MODE` et la logique de branchement associée sont retirés de `src/agent_maestro/main.py`
**And** l'endpoint `/routes` de `main.py` consomme le registre pour lister dynamiquement les agents.

### Story 3.1: Intégration Modèle Vectoriel In-Memory

As a Architecte Système,
I want charger un modèle d'encodage léger en mémoire via `ThreadPoolExecutor` dans `semantic_router.py`,
So that je puisse classifier les requêtes sans Cloud LLM de tierce partie et sans bloquer l'Event Loop asynchrone Python.

**Acceptance Criteria:**

**Given** la phase de démarrage de FastAPI
**When** l'initialisation du Routeur Sémantique démarre
**Then** les routes sémantiques sont construites **dynamiquement** à partir des utterances fournies par le registre d'agents (`agent_registry.get_agent_utterances()`)
**And** l'espace vectoriel est chargé en mémoire via l'offload asynchrone sans monopoliser le fil conducteur principal (Testé et certifié)
**And** aucune utterance n'est hardcodée dans le code source de `router.py`.

### Story 3.2: Réception et Routage de l'Intention (Dispatch A2A)

As a Application Front-end (Utilisateur),
I want soumettre une intention en texte libre,
So that Maestro identifie l'agent spécialiste et transmette la réponse via le réseau interne.

**Acceptance Criteria:**

**Given** une requête autorisée, profilée et traitée sémantiquement
**When** le score match avec un agent précis
**Then** Maestro résout l'URL de l'agent via le registre (`agent_registry.get_agent_url()`) et exécute l'appel `A2AClient` vers l'endpoint JSON-RPC correspondant
**And** transmet de manière transparente le résultat conversationnel de fin vers l'utilisateur.

### Story 3.3: Gestion d'Incompétence et Fallback Local

As a Utilisateur (Famille),
I want que les requêtes hors du domaine ne soient pas envoyées à des agents incohérents,
So that le système soit honnête sur ses limites plutôt que de risquer une hallucination.

**Acceptance Criteria:**

**Given** un message d'utilisateur lointain aux compétences des agents existants
**When** la validation mathématique In-Memory attribue un score très bas à tous
**Then** l'API FastAPI intercepte l'action avant le départ réseau
**And** compile localement et retourne une réponse de politesse refusant de traiter le sujet inadapté.

## Epic 4: Résilience Absolue et Dégradation Gracieuse

L'utilisateur n'est jamais bloqué ou face à une erreur obscure ; le système gère instantanément les pannes internes par un retour clair (Zero-Blocking/Fail-Fast).

### Story 4.1: Disjoncteur Temporel "Fail-Fast"

As a Maestro Gateway,
I want imposer un délai critique (SLA Timeout) sur tout échange A2A sortant vers un spécialiste,
So that je ne gèle jamais l'application si un agent tiers tombe en panne.

**Acceptance Criteria:**

**Given** une requête JSON-RPC asynchrone sortante
**When** l'agent ciblé ne répond pas dans le délai strict (ex: 5 secondes)
**Then** l'attente s'interrompt instantanément
**And** une exception technique `A2ARPCError(Timeout)` est levée localement.

### Story 4.2: Interception "Gracieuse" et Conversationnelle

As a Utilisateur (Famille),
I want qu'en cas de panne système, l'erreur soit interceptée pour prévenir le crash avec un code technique (500),
So that je reçoive une phrase d'explication douce de la part du bot.

**Acceptance Criteria:**

**Given** une exception technique du routeur (Time-out de Story 4.1 ou Exception de Schéma Pydantic)
**When** le système cherche à retourner l'erreur au client appelant
**Then** un exception_handler global FastAPI capture l'erreur
**And** substitue le code d'erreur standard 500 par une réponse JSON-RPC contextuelle courtoise expliquant momentanément l'indisponibilité.

### Story 4.3: Instrumentation OpenTelemetry

As a Ingénieur SRE / Architecte,
I want instrumenter Maestro et ses clients A2A avec le standard OpenTelemetry,
So that toutes les requêtes puissent être tracées de bout en bout avec des standards du marché.

**Acceptance Criteria:**

**Given** une requête entrante sur Maestro
**When** le système traite la requête
**Then** des spans OpenTelemetry sont générées pour chaque étape clé (Auth, Privacy, Routing, A2A Call)
**And** le contexte de trace (trace_id) est propagé dans les headers JSON-RPC vers les agents spécialistes.

### Story 4.4: Diagnostic Trace Path

As a Administrateur (Nicolas),
I want visualiser le chemin détaillé d'une requête (Trace Path) dans la réponse API (en mode debug),
So that je puisse comprendre exactement pourquoi un agent a été choisi et quels outils ont été utilisés.

**Acceptance Criteria:**

**Given** une requête effectuée par un administrateur avec un flag de debug/trace activé
**When** Maestro retourne la réponse
**Then** la réponse contient un bloc `debug_info` ou `trace_path` détaillant les scores de confiance, l'agent cible et les éventuels échecs de routage.

### Story 4.5: Optimisation Linguistique French-First

As a Famille Francophone,
I want un routage sémantique optimisé pour la langue française,
So that mes intentions soient mieux comprises sans ambiguïté linguistique.

**Acceptance Criteria:**

**Given** une intention exprimée en français avec des nuances ou des termes familiers
**When** le routeur sémantique évalue la requête
**Then** le score de confiance pour l'agent approprié est significativement supérieur à celui obtenu avec un modèle purement anglais
**And** le système utilise un modèle d'embedding optimisé pour le français (ex: MiniLM-L12 multilingue ou E5-multilingual).
