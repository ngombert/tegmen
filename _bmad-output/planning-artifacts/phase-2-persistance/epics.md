---
stepsCompleted: ['step-01-validate-prerequisites.md', 'step-02-design-epics.md', 'step-03-create-stories.md']
inputDocuments: ['_bmad-output/planning-artifacts/phase-2-persistance/prd.md', '_bmad-output/planning-artifacts/phase-2-persistance/architecture.md']
---

# tegmen - Epic Breakdown

## Overview

This document provides the complete epic and story breakdown for tegmen, decomposing the requirements from the PRD, UX Design if it exists, and Architecture requirements into implementable stories.

## Requirements Inventory

### Functional Requirements

- FR1: L'utilisateur peut poser une question au système global qui la dirige automatiquement vers l'agent expert approprié.
- FR2: L'utilisateur peut invoquer explicitement un agent par son nom pour forcer le routage.
- FR3: L'utilisateur peut corriger manuellement une erreur de routage a posteriori.
- FR4: Le système peut solliciter plusieurs agents simultanément (Party Mode) et en synthétiser les résultats.
- FR5: Le système pose une question de clarification en cas d'ambiguïté sur le domaine visé.
- FR6: L'agent expert peut détecter une requête hors-domaine et rendre la main.
- FR7: Le système peut suspendre et mémoriser l'état d'une session spécialisée lors d'une digression.
- FR8: Le système peut relancer automatiquement la session de l'agent au point exact où elle a été suspendue.
- FR8b: Le système nettoie silencieusement la pile de contextes si l'interruption s'éternise au-delà d'un délai défini ou d'un volume d'échanges (Garbage Collection).
- FR8c: L'utilisateur peut explicitement indiquer à Maestro d'annuler ou de clore un contexte suspendu.
- FR9: L'agent expert peut extraire de nouveaux "Faits" et évaluer leur importance.
- FR10: Le système stocke et retrouve sémantiquement les faits consolidés.
- FR11: Le système croise ses connaissances directes (agenda) avec la requête pour contraindre la réponse de l'agent expert.
- FR12: L'administrateur système déploie ou met à jour la base de données d'un agent de manière totalement isolée.
- FR13: L'utilisateur peut interroger le système même si des agents spécialistes sont hors ligne.
- FR14: Maestro doit stocker et associer chaque état de session (notamment l'affinité avec l'agent actif `active_agent`) directement au couple `(family_id, user_id)` en base de données.
- FR15: Lorsqu'un utilisateur se connecte à partir d'un nouvel appareil ou rafraîchit son client web, Maestro doit charger automatiquement la session active correspondante depuis la base de données.
- FR16: L'action d'escape (ex: "Laisse tomber ce sujet", "annuler") doit purger l'état de session dans la base de données pour l'utilisateur concerné.
- FR17: Conserver en base de données un résumé ou les derniers messages échangés pour permettre le re-chargement du prompt de contexte sans dépendre uniquement de l'état en mémoire.

### NonFunctional Requirements

- NFR1 (Latence Party Mode): Le Time-To-First-Token (TTFT) global pour une requête complexe nécessitant le Party Mode ne doit pas dépasser 15 secondes.
- NFR2 (Latence Tunnel Mode): Le TTFT pour une requête simple traitée par un seul agent ne doit pas dépasser 5 secondes.
- NFR3 (Feedback UX): L'interface utilisateur doit afficher un indicateur de traitement ("Maestro consulte la famille...") dans les 500ms suivant la requête pour masquer la latence.
- NFR4 (Isolation de la Persistance): Chaque agent possède sa propre base de données indépendante (schéma PostgreSQL dédié, migrations Alembic).
- NFR5 (Stockage Hybride): Les "Hard-Facts" utilisent des tables relationnelles strictes (SQL), tandis que les "Soft-Facts" sont vectorisés via `pgvector` pour la recherche sémantique.
- NFR6 (Zero Downtime Mutuel): L'indisponibilité d'un agent ne provoque aucune interruption de service sur Maestro ni sur les autres agents.
- NFR7 (Intégrité des Données): 100% des payloads `State Update` transitent validés strictement par un schéma Pydantic.
- NFR8: Si un agent spécialiste met plus de 10 secondes à répondre, Maestro reprend la main (Timeout) pour notifier l'utilisateur.
- NFR9: Maestro traite sans erreur les réponses d'un agent obsolète de la Phase 1.
- NFR10 (Isolation Maestro): L'état de session utilisateur est géré exclusivement par Maestro dans la base `maestro` (conforme au NFR4).
- NFR11 (Performance Écriture/Lecture BDD): Le temps d'écriture/lecture de l'état de session en BDD lors d'un message ne doit pas ajouter plus de 50ms de latence au traitement de la requête.

### Additional Requirements

- Starter Template: Base de Code Phase 1 (Existant) sous `src/` avec Python 3.13 géré par `uv`. Architecture microservices existante.
- Infrastructure: Conteneur Postgres unique avec des bases logiques séparées initialisées par `init-multiple-dbs.sh`. L'image Docker doit supporter `pgvector` (ex: `pgvector/pgvector:pg18`).
- Integration: Extension du Protocole A2A (JSON-RPC) pour supporter `new_facts_payload` et `Context Stack` de manière optionnelle.
- Security: Validation Pydantic stricte des schémas d'état inter-agents, utilisation de `X-A2A-Secret`.
- Architecture Pattern: Propriété exclusive du Context Stack par Maestro. Agents spécialisés "Stateless".
- Pattern 2B: Isolation stricte des migrations Alembic par agent.
- Pattern 3B: Le Yield est retourné comme un objet Pydantic standard imbriqué dans la propriété `result` du JSON-RPC. Pas d'exceptions Python pour le flux métier.

### UX Design Requirements

Aucune exigence de design UX pour ce projet backend.

### FR Coverage Map

FR1: Epic 2 - Routage automatique
FR2: Epic 2 - Invocation explicite
FR3: Epic 2 - Correction manuelle du routage
FR4: Epic 2 - Party Mode
FR5: Epic 2 - Clarification d'ambiguïté
FR6: Epic 3 - Détection requête hors-domaine (Yield)
FR7: Epic 3 - Suspension et mémorisation de l'état
FR8: Epic 3 - Relance automatique
FR8b: Epic 3 - Nettoyage de la pile (Garbage Collection)
FR8c: Epic 3 - Clôture explicite par l'utilisateur
FR9: Epic 4 - Extraction et évaluation des Faits
FR10: Epic 4 - Stockage et recherche sémantique
FR11: Epic 4 - Croisement des connaissances avec agenda
FR12: Epic 1 - Déploiement isolé des BDD (Migrations)
FR13: Epic 2 - Interrogation résiliente (Agents hors ligne)
FR14, FR15, FR16, FR17: Epic 5 - Persistance de Session et Historique Conversationnel

### NFR Coverage Map

NFR1, NFR2, NFR3: Epic 2 - Latence et Feedback UX
NFR4: Epic 1 - Isolation de la Persistance
NFR5: Epic 4 - Stockage Hybride (pgvector)
NFR6: Epic 1 - Zero Downtime Mutuel
NFR7: Epic 2 - Intégrité Pydantic à 100%
NFR8: Epic 2 - Dégradation Gracieuse (Timeout 10s)
NFR9: Epic 2 - Rétrocompatibilité A2A
NFR10, NFR11: Epic 5 - Persistance de Session et Historique Conversationnel

## Epic List

### Epic 1: Fondation de Persistance et Isolation
Mettre en place l'infrastructure décentralisée de base de données (PostgreSQL + pgvector) avec isolation stricte des migrations (Alembic) par agent, garantissant le Zero Downtime mutuel.
**FRs covered:** FR12
**NFRs covered:** NFR4, NFR6

### Epic 2: Routage Intelligent et Résilient
Permettre au système central de distribuer intelligemment les requêtes (en unitaire ou Party Mode) tout en garantissant des temps de réponse stricts, la rétrocompatibilité et l'intégrité des messages via Pydantic.
**FRs covered:** FR1, FR2, FR3, FR4, FR5, FR13
**NFRs covered:** NFR1, NFR2, NFR3, NFR7, NFR8, NFR9

### Epic 3: Fluidité Conversationnelle (Gestion des Interruptions)
Dotter les agents de la capacité à rendre la main (Yield) et permettre à Maestro de suspendre, stocker et restaurer le contexte conversationnel sans perturber l'expérience utilisateur.
**FRs covered:** FR6, FR7, FR8, FR8b, FR8c

### Epic 4: Mémoire Personnalisée et Raisonnement Croisé
Implémenter l'extraction asynchrone, le stockage hybride (SQL/Vector) et le croisement sémantique des Soft/Hard Facts pour rendre l'assistant proactif et ultra-personnalisé.
**FRs covered:** FR9, FR10, FR11
**NFRs covered:** NFR5

### Epic 5: Persistance de Session et Historique Conversationnel
Rendre la session de discussion persistante en base de données PostgreSQL pour permettre la reprise multi-appareil et résister aux redémarrages de l'application ou du serveur.
**FRs covered:** FR14, FR15, FR16, FR17
**NFRs covered:** NFR10, NFR11

### Epic 6: Gestion de Contexte & Isolation Utilisateur (Claim Check)
Industrialiser la gestion de la mémoire à court terme par le pattern Claim Check en introduisant un stockage découplé (Postgres/Redis) et en sécurisant l'accès aux contextes par des listes d'autorisations utilisateur-centriques (ACLs), résolvant les cas d'usage d'intimité intra-foyer et de surprises parentales.
**FRs covered:** FR7, FR8, FR8b, FR8c, FR14
**NFRs covered:** NFR10, NFR11

## Epic 1: Fondation de Persistance et Isolation

Mettre en place l'infrastructure décentralisée de base de données (PostgreSQL + pgvector) avec isolation stricte des migrations (Alembic) par agent, garantissant le Zero Downtime mutuel.

### Story 1.1: Provisionnement de l'infrastructure PostgreSQL Hybride

As a administrateur système,
I want disposer d'un conteneur PostgreSQL supportant `pgvector` et initialisant automatiquement des bases logiques séparées au démarrage,
So that je puisse préparer le terrain pour la persistance isolée et sémantique de chaque agent.

**Acceptance Criteria:**

**Given** un environnement Docker vierge
**When** je lance la commande de démarrage (ex: `docker compose up db`)
**Then** une image de type `pgvector/pgvector` est téléchargée et démarrée
**And** le script d'initialisation crée automatiquement les bases de données distinctes (`maestro`, `gourmet`, `acadomie`, `explorer`) et active l'extension `vector` sur chacune.

### Story 1.2: Configuration de l'ORM et des Migrations Isolées (Pattern 2B)

As a administrateur système,
I want configurer SQLAlchemy asynchrone et Alembic de manière indépendante pour chaque microservice existant,
So that je puisse déployer chaque agent avec un Zero Downtime contrôlé sans risque de conflit avec le reste de l'écosystème.

**Acceptance Criteria:**

**Given** les microservices de la plateforme (`agent_maestro`, `agent_gourmet`, etc.)
**When** j'initialise l'environnement de base de données
**Then** chaque agent possède son propre environnement Alembic isolé (ex: `src/agent_maestro/app/db/alembic/`)
**And** chaque agent possède une connexion asynchrone pointant vers sa propre base logique via les variables d'environnement
**And** l'exécution d'une migration dans un agent n'impacte en rien la structure des autres bases.

## Epic 2: Routage Intelligent et Résilient

Permettre au système central de distribuer intelligemment les requêtes (en unitaire ou Party Mode) tout en garantissant des temps de réponse stricts, la rétrocompatibilité et l'intégrité des messages via Pydantic.

### Story 2.1: Intégrité du Protocole A2A et Rétrocompatibilité

As a agent système (Maestro),
I want que mon protocole A2A supporte les nouveaux champs (Yield, ContextStack, NewFacts) tout en gardant une validation Pydantic stricte,
So that je puisse communiquer avec les agents Phase 2 sans casser la communication avec les agents Phase 1 existants.

**Acceptance Criteria:**

**Given** les schémas partagés dans `src/common/schemas.py`
**When** je reçois une réponse d'un agent sans les champs Phase 2 (ex: pas de `new_facts_payload`)
**Then** la validation Pydantic réussit (Rétrocompatibilité - NFR9)
**And** si un payload mal formé est envoyé, une erreur stricte est levée avant le transfert réseau (Intégrité - NFR7).

### Story 2.2: Routage Unitaire et Clarification

As a utilisateur de la famille,
I want que Maestro me dirige vers le bon expert (ou me demande des précisions si ambigu), ou me laisse l'invoquer par son nom,
So that j'aie une réponse précise en moins de 5 secondes.

**Acceptance Criteria:**

**Given** une requête utilisateur via l'API Gateway
**When** le domaine est clair ou l'agent est invoqué par son nom
**Then** la requête est routée vers l'expert de manière transparente
**And** le premier token de la réponse (TTFT) est reçu en moins de 5 secondes
**And** si le domaine est ambigu, Maestro pose une question de clarification sans interroger d'expert
**And** je peux corriger le routage si Maestro s'est trompé.

### Story 2.3: Routage Parallèle Automatique (Party Mode) et Résilience

As a utilisateur de la famille,
I want que Maestro détecte automatiquement quand ma requête nécessite l'expertise croisée de plusieurs agents et les interroge simultanément,
So that j'obtienne une réponse synthétisée robuste, sans que le système ne s'effondre si l'un des agents est lent ou indisponible.

**Acceptance Criteria:**

**Given** une requête utilisateur complexe touchant à plusieurs domaines
**When** Maestro analyse la requête (Semantic Routing)
**Then** il déduit automatiquement la nécessité d'invoquer plusieurs agents pertinents en parallèle
**And** je reçois un indicateur UX "Maestro consulte la famille..." en moins de 500ms
**And** si l'un des agents appelés met plus de 10s à répondre ou est hors ligne, Maestro l'ignore silencieusement sans crasher
**And** la synthèse finale est générée avec les agents ayant répondu à temps, avec un TTFT global inférieur à 15 secondes.

## Epic 3: Fluidité Conversationnelle (Gestion des Interruptions)

Dotter les agents de la capacité à rendre la main (Yield) et permettre à Maestro de suspendre, stocker et restaurer le contexte conversationnel sans perturber l'expérience utilisateur.

### Story 3.1: Détection Hors-Domaine (Pattern Yield)

As a agent spécialiste,
I want détecter quand la question sort de mon domaine d'expertise et retourner une réponse structurée `YieldResponse` au lieu d'halluciner,
So that Maestro sache qu'il doit déclencher la Trappe de Sortie.

**Acceptance Criteria:**

**Given** un agent spécialiste (ex: Acadomie) interrogé sur un sujet hors-scope
**When** le modèle LLM interne à l'agent analyse l'intention
**Then** il ne tente pas de générer une réponse texte standard
**And** il retourne un objet Pydantic de type `YieldResponse`
**And** l'objet inclut l'explication optionnelle de l'abandon pour aider Maestro.

### Story 3.2: Pile de Contexte (Suspend & Resume)

As a utilisateur de la famille,
I want pouvoir poser une question "hors-sujet" en pleine tâche, et que l'assistant mémorise ma tâche initiale pour m'y ramener naturellement,
So that je ne perde pas le fil de mes activités.

**Acceptance Criteria:**

**Given** une session experte en cours (Tunnel Mode)
**When** je pose une question entraînant un "Yield" de l'expert
**Then** Maestro enregistre l'état de la session dans la table `context` de sa base de données
**And** Maestro traite ma digression
**And** une fois la digression résolue, Maestro dépile le contexte et restaure la session initiale avec l'agent expert.

### Story 3.3: Nettoyage et Clôture du Contexte (Garbage Collection)

As a utilisateur,
I want que le système "oublie" un sujet suspendu si l'interruption devient la nouvelle conversation principale, ou pouvoir lui demander explicitement d'abandonner,
So that l'IA ne me relance pas sur un sujet "zombie" obsolète.

**Acceptance Criteria:**

**Given** un contexte suspendu stocké en base
**When** l'interruption dépasse un certain seuil (délai ou volume de messages)
**Then** Maestro nettoie silencieusement la pile en base de données
**And** **When** je dis explicitement "Laisse tomber ce sujet"
**Then** Maestro supprime immédiatement le contexte de la pile.

## Epic 4: Mémoire Personnalisée et Raisonnement Croisé

Implémenter l'extraction asynchrone, le stockage hybride (SQL/Vector) et le croisement sémantique des Soft/Hard Facts pour rendre l'assistant proactif et ultra-personnalisé.

### Story 4.1: Extraction et Évaluation des Nouveaux Faits

As a agent spécialiste,
I want extraire de la conversation des informations potentiellement utiles pour l'avenir et en évaluer l'importance,
So that Maestro puisse les consolider dans la mémoire globale de la famille.

**Acceptance Criteria:**

**Given** une conversation contenant une nouvelle information
**When** l'agent spécialiste génère sa réponse
**Then** il inclut un bloc `new_facts_payload` validé par Pydantic dans son retour JSON-RPC
**And** chaque fait est accompagné d'un `importance_score` pour aider Maestro à filtrer le bruit.

### Story 4.2: Stockage Hybride (SQL & Vector)

As a agent système responsable des données,
I want stocker les "Hard-Facts" dans des tables SQL classiques et les "Soft-Facts" sous forme d'embeddings via l'extension `pgvector`,
So that je puisse les retrouver instantanément par requêtes sémantiques.

**Acceptance Criteria:**

**Given** un payload de faits validé
**When** le système procède à l'insertion en base
**Then** les faits structurés stricts vont dans les champs SQL relationnels appropriés
**And** les faits souples sont vectorisés via un modèle d'embedding et insérés dans la table `soft_facts` via `pgvector`
**And** je peux exécuter une recherche de similarité cosinus pour retrouver les faits pertinents d'une requête.

### Story 4.3: Intégration par le Prompt (Croisement des Connaissances)

As a utilisateur de la famille,
I want que l'assistant croise spontanément ce qu'il sait de moi avec ma question,
So that j'obtienne une réponse de l'expert qui soit déjà contrainte par ma réalité (ex: agenda, goûts).

**Acceptance Criteria:**

**Given** une requête utilisateur
**And** un fait connu stocké en mémoire
**When** Maestro décide d'invoquer l'agent Gourmet
**Then** Maestro recherche et injecte les faits pertinents directement dans le contexte du prompt envoyé à Gourmet
**And** la réponse de Gourmet tient compte de cette contrainte.

### Story 4.4: Résolution de Conflits Sémantiques (Mise à jour des Faits)

As a utilisateur,
I want que le système comprenne quand je change d'avis ou que ma situation évolue, et qu'il mette à jour ses connaissances au lieu d'accumuler des faits contradictoires,
So that l'assistant reste pertinent dans le temps.

**Acceptance Criteria:**

**Given** un fait existant en mémoire (ex: "Nicolas aime les épinards")
**When** une nouvelle conversation indique le contraire ("Je déteste les épinards maintenant")
**Then** le processus d'extraction génère un nouveau fait
**And** le système identifie le conflit sémantique avec le fait précédent lors de l'insertion
**And** l'ancien fait est soit invalidé (marqué comme obsolète) soit écrasé par le nouveau.

### Story 4.5: Découverte Sémantique et Retrieval (Top-K)

As a agent système (Maestro),
I want pouvoir interroger efficacement la base de données décentralisée pour retrouver les faits les plus pertinents sans saturer la latence ni le contexte du LLM,
So that je puisse fournir un prompt enrichi mais concis aux agents spécialistes.

**Acceptance Criteria:**

**Given** une requête utilisateur nécessitant du contexte
**When** Maestro cherche des faits associés
**Then** Maestro utilise un mécanisme optimisé (ex: Fan-out en parallèle vers les bases vectorielles des agents ou consultation d'un index léger)
**And** seuls les Top-K faits les plus pertinents (score sémantique le plus haut) sont récupérés et intégrés au prompt final.

## Epic 5: Persistance de Session et Historique Conversationnel

Rendre la session de discussion persistante en base de données PostgreSQL pour permettre la reprise multi-appareil et résister aux redémarrages de l'application ou du serveur.

### Story 5.1: Migration et Schéma de Persistance de Session (Alembic)

As a développeur backend,
I want définir une table `user_sessions` dans la base Maestro et configurer sa migration via Alembic,
So that les sessions utilisateurs soient associées de manière unique et persistantes en base de données.

**Acceptance Criteria:**

**Given** la base de données PostgreSQL de Maestro
**When** j'applique la migration Alembic sous `src/agent_maestro/app/db/alembic/`
**Then** la table `user_sessions` est créée avec les champs `family_id`, `user_id`, `session_id`, `active_agent`, `active_claim_check_id`, `updated_at` et une contrainte d'unicité sur le couple `(family_id, user_id)`
**And** le champ `active_claim_check_id` est un UUID optionnel pointant vers le claim de contexte actif dans le `ContextStore`.

### Story 5.2: Implémentation du PostgresSessionStore

As a agent système (Maestro),
I want utiliser un adaptateur `PostgresSessionStore` implémentant l'interface `BaseSessionStore`,
So that je puisse enregistrer et charger l'état de session de l'utilisateur de manière asynchrone et transparente.

**Acceptance Criteria:**

**Given** un utilisateur connecté avec un `family_id` et un `user_id`
**When** il envoie un message ou se reconnecte depuis un autre appareil
**Then** Maestro récupère ou met à jour sa session (incluant l'affinité d'agent et le pointeur de contexte `active_claim_check_id`) via `PostgresSessionStore` en moins de 50ms
**And** en cas d'action d'annulation ("Laisse tomber"), l'état de la session et le claim de contexte associé en BDD sont correctement purgés.

## Epic 6: Gestion de Contexte & Isolation Utilisateur (Claim Check)

Industrialiser la gestion de la mémoire à court terme par le pattern Claim Check en introduisant un stockage découplé (Postgres/Redis) et en sécurisant l'accès aux contextes par des listes d'autorisations utilisateur-centriques (ACLs), résolvant les cas d'usage d'intimité intra-foyer et de surprises parentales.

### Story 6.1: Interface d'Abstraction du Stockage Contextuel (BaseContextRepository)

As a développeur backend,
I want définir une interface abstraite pour le stockage du contexte,
So that je puisse découpler la logique d'hydratation A2A de la base de données sous-jacente et permettre une transition future vers Redis.

**Acceptance Criteria:**

**Given** le fichier `src/common/context_repository.py`
**When** je définis la classe abstraite `BaseContextRepository`
**Then** elle expose les méthodes asynchrones `save_context(claim_key, payload, ttl_seconds)` et `get_context(claim_key)`
**And** elle est documentée pour forcer les implémentations concrètes à respecter ce contrat.

### Story 6.2: Implémentation du PostgresContextRepository et Gestion du TTL

As a développeur backend,
I want implémenter le repository pour PostgreSQL avec gestion automatique de la péremption,
So that les contextes de discussion à court terme soient persistés de manière performante et automatiquement purgés après expiration.

**Acceptance Criteria:**

**Given** la base de données Postgres de Maestro
**When** j'implémente `PostgresContextRepository` dans `src/infrastructure/postgres_context_repository.py`
**Then** les claims de contexte sont écrits dans une table `context_store` indexée sur `claim_check_id` et `expires_at`
**And** la méthode `get_context` filtre les résultats pour ignorer les contextes dont le TTL est expiré (`expires_at < NOW()`)
**And** un mécanisme de nettoyage périodique élimine les enregistrements obsolètes en arrière-plan.

### Story 6.3: Sécurité de Contexte User-Centric et ACL (Validation de Visibilité)

As a utilisateur de la famille,
I want que mes contextes de discussion privés (notes personnelles, surprises) soient inaccessibles aux autres membres de la famille,
So that mon intimité et le secret de mes actions soient garantis.

**Acceptance Criteria:**

**Given** un contexte stocké avec les métadonnées `owner_id` (propriétaire) et `authorized_users` (liste d'identifiants autorisés)
**When** un utilisateur (`requester_user_id`) tente d'accéder à ce contexte via le service
**Then** le système autorise l'accès si l'utilisateur est le propriétaire ou fait partie des utilisateurs autorisés
**And** il lève une exception de sécurité stricte (`PermissionError`) avec rejet 403 si l'utilisateur n'est pas autorisé (ex: un enfant accédant aux préparatifs d'un week-end surprise des parents, ou un enfant accédant aux devoirs d'un autre enfant).

### Story 6.4: Hydratation Automatique et Interception A2A (FastAPI & Header)

As a agent spécialiste,
I want recevoir automatiquement mon contexte hydraté et sécurisé sans écrire de code d'accès à la base de données,
So that je puisse me concentrer uniquement sur ma logique métier de traitement.

**Acceptance Criteria:**

**Given** une requête JSON-RPC arrivant sur un serveur A2A
**When** le header `X-Claim-Check-ID` est intercepté par le serveur FastAPI
**Then** la dépendance FastAPI `get_hydrated_context` dans `src/common/a2a_server.py` valide le token d'identité de l'appelant
**And** elle charge le contexte associé depuis le repository et applique le contrôle ACL de la Story 6.3
**And** elle injecte le `RequestContext` entièrement hydraté directement dans les paramètres de la fonction de l'agent.

### Story 6.5: Parallélisation Sûre en Mode "Party" (Copy-on-Write CoW)

As a agent système (Maestro),
I want cloner le contexte de départ lors d'un appel parallèle à plusieurs agents (Party Mode) et fusionner leurs retours,
So that nous évitions les conditions de concurrence et les pertes d'écriture sur le contexte partagé.

**Acceptance Criteria:**

**Given** une requête nécessitant le mode "Party" avec plusieurs agents spécialistes
**When** Maestro distribue la tâche en parallèle
**Then** il partage le même `claim_check_id` en lecture seule aux agents enfants
**And** si un agent enfant modifie son contexte, il écrit une nouvelle version (Copy-on-Write) retournant un nouveau claim check ID
**And** à la fin de la parallélisation, Maestro fusionne de manière déterministe les nouveaux faits et modifications dans une nouvelle version du contexte parent.

### Story 6.6: Fixtures InMemory et Tests de Voyage dans le Temps (Time-Travel Testing)

As a ingénieur QA,
I want tester le comportement de la pile de contexte et l'expiration du TTL de manière ultra-rapide et déterministe,
So that la CI/CD reste performante et exempte de tests instables.

**Acceptance Criteria:**

**Given** la suite de tests `tests/test_context_security.py`
**When** j'exécute les tests unitaires
**Then** le système utilise un double de test `InMemoryContextRepository` thread-safe sans dépendance réseau
**And** j'utilise une abstraction d'horloge (`TimeProvider`/`Clock`) pour simuler le passage du temps (avancer de `TTL + 1 seconde`) sans effectuer de `sleep()` réel
**And** la suite de tests valide à 100% les scénarios limites d'expiration du TTL et d'usurpation d'identité (tests d'intrusion automatisés).

