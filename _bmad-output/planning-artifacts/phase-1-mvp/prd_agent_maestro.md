---
stepsCompleted: ["step-01-init.md", "step-02-discovery.md", "step-02b-vision.md", "step-02c-executive-summary.md", "step-03-success.md", "step-04-journeys.md", "step-05-domain.md", "step-06-innovation.md", "step-07-project-type.md", "step-08-scoping.md", "step-09-functional.md", "step-10-nonfunctional.md", "step-11-polish.md"]
inputDocuments: ["_bmad-output/project-context.md", "docs/A2A.md", "_bmad-output/planning-artifacts/prd_agent_gourmet.md"]
workflowType: 'prd'
documentCounts:
  briefCount: 1
  researchCount: 0
  brainstormingCount: 0
  projectDocsCount: 2
classification:
  projectType: api_backend
  domain: general
  complexity: medium
  projectContext: brownfield
---

# Product Requirements Document - tegmen Maestro

**Author:** Nicolas
**Date:** 2026-04-16

## Executive Summary

Maestro est le Majordome Numérique de l'écosystème Tegmen. Agissant comme passerelle (API Gateway) asynchrone, il qualifie l'intention de la famille et route les requêtes vers les microservices spécialisés via le protocole Agent-to-Agent (A2A). Cette refonte *brownfield* élimine la dette du monolithe et sécurise un modèle de permissions asymétrique via un **Bouclier Actif de Contexte**. Maestro hydrate chaque requête du profil utilisateur approprié avant de la relayer, déchargeant intégralement les sous-agents des logiques d'autorisation, tout en garantissant un anonymat PII absolu.

## Project Classification

- **Project Type:** API Backend (Gateway A2A / Semantic Router)
- **Domain:** Family-Tech / General
- **Complexity:** Medium (RBAC, Fail-Fast network policy)
- **Context:** Brownfield (Migration vers A2A pur)

## Success Criteria

### User Success
- **Fluidité:** Reconnaissance implicite des utilisateurs sans déclaration manuelle.
- **Transparence:** Retour immédiat et explicite en cas d'indisponibilité d'un sous-agent (zero-hallucination).

### Business Success
- **Indépendance des agents:** Les sous-agents spécialisés opèrent sous forme de microservices purs sans logique RBAC (Role-Based Access Control).
- **Gouvernance:** 100% des PII (données personnelles) sont masquées dans les journaux système (logs).
- **Efficience:** Diminution immédiate des coûts en tokens LLM par l'utilisation de routages sémantiques locaux.

### Technical & Measurable Success
- **Latence:** Délai additionnel injecté par Maestro < 100ms (P95) sur hardware M-Series/GPU ou < 300ms sur CPU ARM/générique.
- **Asynchronisme:** Zéro appel I/O bloquant. Maintien de 50 requêtes simultanées en attente (FastAPI).
- **Testabilité:** Zéro fuite de PII validée par analyse CI sur dictionnaire poison (Mock).

## Product Scope & Phased Development

### MVP Strategy (Phase 1)
**Objectif:** Platform MVP asynchrone résilient sans régression fonctionnelle. Équipe resserrée (1 Lead Dev / 1 Architect).
**Fonctionnalités Clés:**
- Routage sémantique local `semantic-router`.
- Bouclier de contexte (Hydratation des privilèges et données d'identité).
- Interception asynchrone Fail-Fast (JSON-RPC) et filtrage strict des PII.

### Growth Strategy (Phase 2)
- Disjoncteur réseau "Smart Retry" asynchrone pour les micro-pannes.
- Cache sémantique proactif (réponses instantanées aux requêtes identiques).
- Gestion persistante du contexte multi-tours intra-session.

### Expansion (Phase 3)
- Agrégation composite native (1 requête -> N sous-agents -> compilation).
- Streaming temps réel audio bidirectionnel (WebSockets/gRPC).
- Analyse d'usage pour auto-ajustement des contextes.

### Risk Management
- **Hardware RAM (Tech):** Surcharge provoquée par l'inférence. **M:** Exploitation exclusive de micro-modèles onnx (`all-MiniLM-L6-v2`) offloadés dans un `ThreadPoolExecutor`.
- **Rupture de Contrats (Market):** Désynchronisation temporelle entre les microservices. **M:** Tests de contrats orientés consommateur (Consumer-Driven Contract Testing) via Pydantic en CI.
- **Développement Locus:** Dépendance réseau pendant le dev local. **M:** "Zéro réseau en CI" (mock obligatoire `pytest-httpx`).

## User Journeys

### 1. Parcours Nominal : Léo et le Bouclier (Routing)
Léo (10 ans) interroge le système pour un exercice. Maestro capte l'intention, l'identifie formellement, et hydrate la requête de ses permissions (ex: "Pas de triche"). Le routeur redirige l'appel structuré A2A vers l'Agent Acadomie qui obéit au contexte sans poser de questions supplémentaires.

### 2. Parcours Résilience : Marie et le Fail-Fast (Error)
Marie cherche une recette, mais l'Agent Gourmet subit un *timeout*. Au lieu d'attendre 60s ou d'halluciner, Maestro capte l'exception HTTP locale et coupe la requête en retournant un message explicatif sur la panne. La confiance est maintenue.

### 3. Parcours Administrateur : Nicolas et l'Audit (Security)
Nicolas explore les logs pour identifier le goulot d'étranglement du week-end. Il visualise les temps de traitement TCP et le routage (ex: 42ms vars Acadomie), mais aucune information personnelle (PII/Prompts) n'est traçable par effraction.

## Architectural Constraints (Domain & Technical)

- **Protocole:** JSON-RPC 2.0 asynchrone via `a2a-sdk` sur HTTP.
- **Localisation des Données:** Zéro requête cloud LLM utilisée pour la décision de routage.
- **Conformité & Intégrité:** Rejet inconditionnel (HTTP 422) de tout payload non certifié par les schémas stricts Pydantic.
- **Recouvrement:** Redémarrage système à froid (modèles ML inclus) opérationnel en < 10 secondes.

## Functional Requirements

### F1. Routage et Orchestration Sémantique
- **FR1:** Le système peut recevoir une intention textuelle non-structurée.
- **FR2:** Le système identifie localement (sans LLM distant) l'agent spécialisé compétent.
- **FR3:** Le système transmet la demande à l'agent cible via le protocole A2A.
- **FR4:** Le système notifie son incompétence si l'intention ne correspond à aucun domaine répertorié.

### F2. Gouvernance de Contexte (Context Shield)
- **FR5:** Le système identifie l'émetteur de la demande (authentification).
- **FR6:** Le système modifie automatiquement la requête pour y greffer les spécificités du profil de l'émetteur.
- **FR7:** Le système applique et transmet les restrictions parentales (RBAC implicite) bloquantes.

### F3. Protection de la Vie Privée et Audit
- **FR8:** Le système expurge ou masque irréversiblement toute PII avant écriture en journal/stdout.
- **FR9:** Le système conserve des journaux de télémétrie exploitables pour le debugging (latence, échec) exempts de contenu privé.

### F4. Résilience Réseau
- **FR10:** Le système applique un délai SLA aux requêtes sortantes avant neutralisation.
- **FR11:** Le système notifie instantanément l'utilisateur d'un échec de jonction A2A (Fail-Fast).
- **FR12:** Le système émet une erreur structurée (ex. HTTP 422) si un agent tiers ne respecte pas le schéma Pydantic entendu.

### F5. Accessibilité
- **FR13:** Le système maintient un unique endpoint façade pour les applications front-end.
- **FR14:** Le système expose sa topologie JSON-RPC de façon lisible via la documentation OpenAPI générée par FastAPI.

## Non-Functional Requirements

### Performance
- **NFR-PERF-1 (Overhead Latency):** Temps additionnel du routage (déduction sémantique + hydratation) restreint à 100ms (P95) sur hardware accéléré, ou 300ms sur CPU ARM standard.
- **NFR-PERF-2 (Zero-Blocking):** API asynchrone maintenant l'Event Loop accessible à 100%. L'interface supporte 50 requêtes simultanées ; l'inférence vectorielle est déchargée par `ThreadPoolExecutor`.

### Security
- **NFR-SEC-1 (Sanitization Assurance):** Validation du caviardage PII en CI par application d'un dictionnaire Mock empoisonné ; toute fuite repérée par regex entraîne l'échec du pipeline.
- **NFR-SEC-2 (Data Localization):** 100% de la chaîne de décision de triage exécutée local-first.

### Reliability
- **NFR-REL-1 (Crash Recovery):** Auto-reboot du conteneur en < 10 secondes incluant charge ML à froid en RAM.
- **NFR-REL-2 (Type Safety Contract):** Tolérance zéro face à une erreur structurelle A2A, avec interception totale pour prévenir le plantage fatal de l'Event Loop.
