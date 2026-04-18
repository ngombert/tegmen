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

FR1: Epic 3 - Classification de l'intention textuelle
FR2: Epic 3 - Analyse sémantique locale In-Memory
FR3: Epic 3 - Transport vers l'agent spécialiste via A2A
FR4: Epic 3 - Notification conversationnelle en cas de domaine non géré
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
**FRs covered:** FR1, FR2, FR3, FR4

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

### Story 3.1: Intégration Modèle Vectoriel In-Memory

As a Architecte Système,
I want charger un modèle d'encodage léger en mémoire via `ThreadPoolExecutor` dans `semantic_router.py`,
So that je puisse classifier les requêtes sans Cloud LLM de tierce partie et sans bloquer l'Event Loop asynchrone Python.

**Acceptance Criteria:**

**Given** la phase de démarrage de FastAPI
**When** l'initialisation du Routeur Sémantique démarre
**Then** l'espace vectoriel des "Cartes d'identité des Agents" est chargé 
**And** cela est exécuté via l'offload asynchrone sans monopoliser le fil conducteur principal (Testé et certifié).

### Story 3.2: Réception et Routage de l'Intention (Dispatch A2A)

As a Application Front-end (Utilisateur),
I want soumettre une intention en texte libre,
So that Maestro identifie l'agent spécialiste et transmette la réponse via le réseau interne.

**Acceptance Criteria:**

**Given** une requête autorisée, profilée et traitée sémantiquement
**When** le score match avec un agent précis (Gourmet, Acadomie)
**Then** Maestro exécute l'appel `A2AClient` vers l'endpoint JSON-RPC de ce sous-réseau
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
