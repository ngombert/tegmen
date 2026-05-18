---
stepsCompleted: ['step-01-init.md', 'step-02-discovery.md', 'step-02b-vision.md', 'step-02c-executive-summary.md', 'step-03-success.md', 'step-04-journeys.md', 'step-05-domain.md', 'step-06-innovation.md', 'step-07-project-type.md', 'step-08-scoping.md', 'step-09-functional.md', 'step-10-nonfunctional.md', 'step-11-polish.md']
inputDocuments: ['_bmad-output/brainstorming/brainstorming-session-2026-05-18-233119.md', '_bmad-output/project-context.md', 'docs/A2A.md', 'docs/adk.md']
classification:
  projectType: api_backend
  domain: general
  complexity: medium
  projectContext: brownfield
workflowType: 'prd'
---

# Product Requirements Document - tegmen

**Author:** Nicolas
**Date:** 2026-05-18

## Executive Summary

La Phase 2 de Tegmen vise à doter l'assistant familial d'une mémoire à long terme résiliente et d'une fluidité conversationnelle naturelle. Le système dépasse le cadre d'un chatbot standard en offrant une intelligence unifiée qui grandit avec la famille. Il orchestre de manière transparente un routeur principal (Maestro) chargé du contexte relationnel, et des microservices experts (Gourmet, Acadomie, Explorer) responsables de leurs domaines respectifs. Le ressenti global s'apparente à une messagerie asynchrone familiale (type WhatsApp), ce qui permet d'absorber naturellement les délais inhérents à l'orchestration de multiples LLMs.

### What Makes This Special

L'innovation centrale repose sur une **mémoire asymétrique** et un **routage bifurqué** :
*   **Pile de Contextes et Trappe de Sortie :** Les agents spécialisés travaillent en "Tunnel Mode" pour maximiser l'efficacité. Lorsqu'une intention hors-domaine est détectée, le contexte est suspendu (mis en pile) et Maestro reprend la main, permettant un retour fluide au sujet initial une fois l'interruption traitée.
*   **Base de données Décentralisée et Hybride :** Chaque agent gère sa propre base PostgreSQL (SQL strict + JSONB/pgvector) de manière autonome (via Alembic). L'intégration des données se fait directement par le prompt du LLM (contexte) plutôt que par un schéma de jointures SQL rigide et monolithique. 
*   **Orchestration Multi-Agents (Party Mode) :** Une capacité asynchrone encadrée par une dégradation gracieuse stricte (Timebox), permettant de croiser plusieurs expertises sans sacrifier l'expérience utilisateur globale.

## Project Classification

*   **Project Type:** Backend API / Architecture Microservices (Protocole A2A)
*   **Domain:** IA / Assistance Familiale
*   **Complexity:** Moyenne à Élevée (Système distribué, orchestration asynchrone et persistance hybride)
*   **Context:** Brownfield (Évolution de l'architecture MVP de la Phase 1)

## Success Criteria

### User Success
L'utilisateur perçoit le système comme une entité omnisciente, capable de croiser les savoirs spécialisés. Le succès ultime est atteint lors de requêtes quotidiennes comme "On mange quoi ce soir ?" : l'IA propose un repas cohérent avec l'historique des derniers jours, les goûts (Soft-Facts) et l'agenda de la famille (ex: proposer un repas rapide car un cours de danse est prévu à 19h).

### Business Success
Adoption quotidienne et naturelle de l'assistant. L'absence de friction lors des interruptions (via la Trappe de sortie) et la richesse du contexte (intégration des soft-facts) garantissent une forte rétention de l'outil dans l'écosystème domestique.

### Technical Success
- **Gestion de la Latence (TTFT Assumé) :** Tolérance d'un Time-To-First-Token plus long (jusqu'à 10-15 secondes pour les requêtes Party Mode complexes) sans mécanisme de streaming A2A, compensée par une UX d'attente type "Messagerie de groupe".
- **Autonomie de la Persistance :** Le déploiement, la maintenance et les migrations (Alembic) des bases de données de chaque microservice se font en totale isolation.

### Measurable Outcomes
- Validation déterministe en CI du passage des contraintes d'un agent à l'autre.
- En cas de perte de contexte ou de timeout, l'IA ne génère pas d'erreur technique mais pose une question de clarification gracieuse (Dégradation gracieuse testée à 100%).

## Product Scope

### MVP - Minimum Viable Product
- **Routage Bifurqué Complet :** Implémentation simultanée du *Tunnel Mode* (avec Pile de contextes) ET du *Party Mode* asynchrone.
- **Bases de Données Indépendantes Hybrides :** Déploiement de bases PostgreSQL par agent gérées par Alembic.
- **Gestion Complète des Faits (Hard & Soft) :** Intégration de `pgvector` **dès le MVP** pour la recherche sémantique des Soft-Facts (préférences, habitudes), en complément du SQL pour les Hard-Facts (dates, composition familiale).
- **State Update Payload :** Mécanisme permettant aux agents d'évaluer et remonter l'importance de nouveaux faits vers la mémoire globale.

### Growth Features (Post-MVP)
- Intégration du Streaming A2A (SSE/WebSockets) pour réduire drastiquement le TTFT perçu.
- Mécanismes proactifs avancés (agents qui déclenchent d'eux-mêmes des notifications sans prompt utilisateur).

### Vision (Future)
- Un système prédictif complet où le réseau A2A s'auto-optimise en continu pour anticiper les besoins.

## User Journeys

### 1. Sarah, la mère de famille (Croisement Contexte Global / Expertise)
*   **Situation :** Il est 18h, Sarah rentre fatiguée et demande : *"Qu'est-ce qu'on mange ce soir ?"*
*   **Action :** Maestro consulte l'agenda et détecte un cours de danse à 19h. Il invoque Gourmet en lui transmettant cette contrainte temporelle et les préférences familiales.
*   **Climax :** L'assistant répond : *"Gourmet suggère des pâtes au pesto express prêtes en 15 minutes, ce qui laisse le temps de manger avant le cours de danse de Léo à 19h."*
*   **Résolution :** La charge mentale de Sarah est allégée grâce au croisement des contextes (Temps + Cuisine).

### 2. Léo, le fils (Le cas complexe - Trappe de sortie & Pile de contextes)
*   **Situation :** Léo révise sa géométrie avec Acadomie (Tunnel Mode).
*   **Action :** Il interrompt l'agent scolaire : *"Au fait, c'est quoi déjà l'adresse de la fête de samedi ?"*
*   **Climax :** Acadomie active la *Trappe de Sortie* et suspend sa session. Maestro prend le relais, donne l'adresse issue de l'agenda, puis **dépile le contexte** : *"C'est au 12 rue Victor Hugo. Bref, on en était à la question 3 de ton exercice de géométrie."*
*   **Résolution :** Léo reprend son travail naturellement sans perte de fil.

### 3. Nicolas, l'administrateur système (Ops & Isolation)
*   **Situation :** Nicolas déploie une mise à jour sur Gourmet nécessitant une migration de BDD (Alembic).
*   **Action :** Pendant cette maintenance isolée, Sarah demande à Maestro de noter un rappel.
*   **Climax :** Maestro enregistre l'information dans sa propre BDD instantanément.
*   **Résolution :** L'écosystème familial ne s'arrête jamais complètement grâce au découplage (Zero Downtime Mutuel).

## Innovation & Risk Mitigation

### Architectural Innovations
- **Protocole A2A et Context Stack :** L'agent spécialisé rend la main de son propre chef ("Yield") s'il détecte une intention hors-domaine. Maestro gère l'interruption via une pile de contextes (Context Stack) pour reprendre la discussion initiale plus tard.
- **Persistance Distribuée par Auto-évaluation :** La charge cognitive d'extraction mémorielle est décentralisée. Les agents génèrent un `State Update Payload` après une transaction pour notifier Maestro des nouveaux Faits à mémoriser, favorisant une "intégration par le prompt".

### Risk Mitigation Strategy
- **Risque d'Hallucination au Routage :** Maestro pourrait déclencher le mauvais agent.
  *Mitigation :* **Invocation Directe et Correction.** L'utilisateur peut forcer le routage ("Demande à Gourmet...") ou le corriger a posteriori ("Non, c'était pour Acadomie").
- **Timeouts Réseau :** Latence excessive lors d'une requête Party Mode.
  *Mitigation :* Tolérance assumée au TTFT compensée par une interface type messagerie asynchrone, soutenue par une dégradation gracieuse stricte (Timeout coupé à 10s).
- **Corruptions de BDD :** Risque lié au transfert inter-agents.
  *Mitigation :* Validation Pydantic systématique des payloads avant tout transfert réseau.

## API Backend Specific Requirements (Phase 2 Updates)

### Technical Architecture Considerations
L'architecture A2A de la Phase 1 est conservée. Le `a2a-sdk` (v2.0) est étendu pour supporter les nouveaux schémas de données du routage bifurqué.

### Extension du Protocole JSON-RPC (Data Schemas)
1. **Support du "Yield" (Trappe de sortie) :** Renvoi d'un statut `yield_action: true` avec une explication optionnelle.
2. **State Update Payload :** Ajout d'un bloc `new_facts_payload` contenant les faits extraits et leur `importance_score`.
3. **Transmission du Context Stack :** Injection de la Pile de Contextes via `params.context`.

### Implementation Considerations
- **Validation Stricte des Faits (Pydantic) :** Les modèles `FactSchema` sont centralisés dans le SDK. La validation est locale côté agent avant envoi réseau. Un payload mal formaté lève une exception locale.
- **Rétrocompatibilité :** Les requêtes A2A standards de la Phase 1 continuent de fonctionner si aucun `new_facts_payload` n'est fourni.

## Functional Requirements

### Orchestration & Routage
- FR1: L'utilisateur peut poser une question au système global qui la dirige automatiquement vers l'agent expert approprié.
- FR2: L'utilisateur peut invoquer explicitement un agent par son nom pour forcer le routage.
- FR3: L'utilisateur peut corriger manuellement une erreur de routage a posteriori.
- FR4: Le système peut solliciter plusieurs agents simultanément (Party Mode) et en synthétiser les résultats.
- FR5: Le système pose une question de clarification en cas d'ambiguïté sur le domaine visé.

### Gestion des Interruptions (Context Stack)
- FR6: L'agent expert peut détecter une requête hors-domaine et rendre la main.
- FR7: Le système peut suspendre et mémoriser l'état d'une session spécialisée lors d'une digression.
- FR8: Le système peut relancer automatiquement la session de l'agent au point exact où elle a été suspendue.

### Mémoire Distribuée (Hard & Soft Facts)
- FR9: L'agent expert peut extraire de nouveaux "Faits" et évaluer leur importance.
- FR10: Le système stocke et retrouve sémantiquement les faits consolidés.
- FR11: Le système croise ses connaissances directes (agenda) avec la requête pour contraindre la réponse de l'agent expert.

### Résilience de l'Écosystème
- FR12: L'administrateur système déploie ou met à jour la base de données d'un agent de manière totalement isolée.
- FR13: L'utilisateur peut interroger le système même si des agents spécialistes sont hors ligne.

## Non-Functional Requirements

### Performance & Latency
- NFR1 (Latence Party Mode) : Le Time-To-First-Token (TTFT) global pour une requête complexe nécessitant le Party Mode ne doit pas dépasser 15 secondes.
- NFR2 (Latence Tunnel Mode) : Le TTFT pour une requête simple traitée par un seul agent ne doit pas dépasser 5 secondes.
- NFR3 (Feedback UX) : L'interface utilisateur doit afficher un indicateur de traitement ("Maestro consulte la famille...") dans les 500ms suivant la requête pour masquer la latence.

### Data Architecture & Storage
- NFR4 (Isolation de la Persistance) : Chaque agent possède sa propre base de données indépendante (schéma PostgreSQL dédié, migrations Alembic).
- NFR5 (Stockage Hybride) : Les "Hard-Facts" utilisent des tables relationnelles strictes (SQL), tandis que les "Soft-Facts" sont vectorisés via `pgvector` pour la recherche sémantique.

### Reliability & Resilience
- NFR6 (Zero Downtime Mutuel) : L'indisponibilité d'un agent ne provoque aucune interruption de service sur Maestro ni sur les autres agents.
- NFR7 (Intégrité des Données) : 100% des payloads `State Update` transitent validés strictement par un schéma Pydantic.
- NFR8 (Dégradation Gracieuse) : Si un agent spécialiste met plus de 10 secondes à répondre, Maestro reprend la main (Timeout) pour notifier l'utilisateur.

### Integration
- NFR9 (Rétrocompatibilité A2A) : Maestro traite sans erreur les réponses d'un agent obsolète de la Phase 1.
