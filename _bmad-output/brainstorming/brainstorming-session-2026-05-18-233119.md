---
stepsCompleted: [1, 2, 3, 4]
inputDocuments: ["_bmad-output/project-context.md", "_bmad-output/planning-artifacts/phase-1-mvp/"]
session_topic: 'Conception de la Phase 2 : Persistance, Mémoire et Contexte'
session_goals: 'Définir l''architecture de la mémoire à long terme, le choix de la base de données asynchrone, et la gestion du contexte des agents'
selected_approach: 'progressive-flow'
techniques_used: ['First Principles Thinking', 'Constraint Mapping', 'Solution Matrix', 'Decision Tree Mapping']
ideas_generated: []
context_file: ''
---

# Brainstorming Session Results

**Facilitator:** Nicolas
**Date:** 2026-05-18

## Session Overview

**Topic:** Conception de la Phase 2 : Persistance, Mémoire et Contexte
**Goals:** Définir l'architecture de la mémoire à long terme, le choix de la base de données asynchrone, et la gestion du contexte des agents

### Context Guidance

_La Phase 1 (MVP) a posé les bases de l'architecture microservices A2A (Tegmen) avec des bouchons en mémoire. La Phase 2 doit traiter la gestion de la persistance, des contextes d'agents et de leur mémoire à long terme, en s'appuyant sur le Project Context et les artefacts MVP existants._

### Session Setup

_Session configurée pour explorer les différentes options d'architecture pour la persistance des données et la mémoire à long terme (SQL, Vectorielle, GraphDB, etc.) ainsi que les stratégies d'hydratation du contexte pour les agents spécialisés._

## Technique Selection

**Approach:** Progressive Technique Flow
**Journey Design:** Développement systématique de l'exploration à l'action.

**Progressive Techniques:**
- **Phase 1 - Exploration:** First Principles Thinking (déconstruire les hypothèses)
- **Phase 2 - Reconnaissance de motifs:** Constraint Mapping (identifier les limitations réelles)
- **Phase 3 - Développement:** Solution Matrix (croiser besoins et technologies)
- **Phase 4 - Planification:** Decision Tree Mapping (créer un plan d'action concret)

**Journey Rationale:** Concevoir l'architecture optimale pour la Phase 2 en détruisant les idées reçues sur la mémoire des agents, pour reconstruire sur des bases techniques saines adaptées à Tegmen.

## Technique Execution Results

### Phase 1: First Principles Thinking

**[Architecture]**: Mémoire Asymétrique (Maestro vs Spécialistes)
_Concept_: Le routeur (Maestro) monopolise la gestion du contexte relationnel, des habitudes et des "sujets en cours". Les sous-agents (Gourmet, Explorer, Acadomie) stockent et gèrent les faits propres à leur domaine.
_Novelty_: Empêche les agents spécialisés d'être surchargés par le relationnel familial, simplifiant leurs prompts et garantissant l'identité unique de l'IA via Maestro.

**[Architecture]**: Souveraineté de la Donnée et Échange Croisé (Cross-Pollination)
_Concept_: Les agents ont le contrôle total et le droit d'écriture sur leur propre base de données. Pour un événement complexe (ex: Pique-nique), l'orchestrateur (Maestro) gère "l'Event" et assure l'échange d'informations pertinentes entre les agents (ex: croiser le menu de Gourmet avec le lieu d'Explorer).
_Novelty_: Base de données totalement décentralisée par domaine. L'intégration se fait dynamiquement dans le "Contexte" injecté par Maestro, plutôt que par un monolithe SQL complexe.

**[Inspiration/Analogie]**: Le Modèle "Party Mode" (Orchestration LLM séquentielle)
_Concept_: S'inspirer du Party Mode de BMad pour le workflow A2A. Maestro agit comme le facilitateur principal qui appelle explicitement chaque expert (Gourmet, Acadomie) dans une "salle de discussion virtuelle". Chaque expert apporte son savoir (sa base de données) à la conversation globale, gérée et compilée par Maestro pour la famille.
_Novelty_: Offre un framework conversationnel naturel pour l'échange de données inter-agents, rendant l'orchestration transparente et hautement asynchrone, tout en s'appuyant sur des identités fortes.

### Phase 2: Constraint Mapping

**[Contrainte Neutralisée]**: Latence I/O et Over-Engineering
_Concept_: La latence des requêtes en base de données (asyncpg) est négligeable face au temps d'inférence LLM. Le choix d'une UX asynchrone (messagerie texte type WhatsApp ou Web Chat) permet d'absorber naturellement les délais.
_Action_: Pas besoin de développer des couches de cache prédictif ou des optimisations réseaux complexes pour la Phase 2. L'architecture doit rester simple et directe avec la BDD.

**[Architecture]**: Déploiement BDD Découplé (Microservices Purs)
_Concept_: Chaque agent embarque sa propre logique de migration de base de données (ex: Alembic). Le déploiement et la mise à jour d'un agent incluent la mise à jour de son propre schéma de données de manière totalement autonome.
_Décision_: Garantit l'indépendance totale des agents. Une mise à jour de la mémoire de Gourmet n'impactera jamais le déploiement d'Acadomie ou de Maestro.

### Phase 3: Solution Matrix

**[Architecture]**: Mémoire Hybride (SQL + JSONB/Vectoriel)
_Concept_: Utiliser une base de données relationnelle (PostgreSQL) comme fondation unique. Les "Hard Facts" (composition familiale, liste de recettes, dates) sont modélisés en SQL strict. Les "Soft Facts" (préférences floues, habitudes, personnalité) sont stockés sous forme de vecteurs (via `pgvector`) ou de schémas flexibles (`JSONB`) au sein de la même base.
_Décision_: Évite la complexité de maintenir deux systèmes de bases de données séparés, tout en tirant parti de la puissance sémantique des LLMs pour les recherches de préférences.

### Phase 4: Decision Tree Mapping

**[Architecture]**: Routage Bifurqué (Party Mode vs Tunnel Mode)
_Concept_: L'orchestrateur (Maestro) analyse l'intention initiale de la session et décide du mode de routage. 
- *Branche A (Multi-Domaines)* : Si la requête touche plusieurs agents (ex: Pique-nique = Explorer + Gourmet), Maestro active le "Party Mode asynchrone" et orchestre les retours.
- *Branche B (Tunnel Mode / Focus)* : Si la requête est ultra-spécifique (ex: devoirs de maths), Maestro ouvre un tunnel direct vers l'agent concerné (Acadomie). L'agent interagit avec l'utilisateur (avec son propre contexte) sans subir l'orchestration lourde de Maestro à chaque message.
_Décision_: Optimise les performances et la fluidité UX en réservant l'orchestration complexe uniquement aux cas qui le nécessitent.

## Idea Organization and Prioritization

**Thematic Organization:**
- **Thème 1 : Architecture Décentralisée (Souveraineté)**
  - Mémoire Asymétrique (Maestro = Contexte vs Agents = Faits)
  - Déploiement BDD Découplé (Microservices purs avec migrations autonomes via Alembic)
- **Thème 2 : Infrastructure de la Donnée**
  - Mémoire Hybride PostgreSQL (SQL strict + JSONB/pgvector pour les faits flous)
  - Échange Croisé via Context injection (Analogie Party Mode)
- **Thème 3 : Stratégie de Routage et Latence**
  - UX asynchrone (messagerie) pour masquer la latence I/O
  - Routage Bifurqué (Party Mode vs Tunnel Mode focus)

**Prioritization Results:**
- **Top Priority Ideas:**
  - Implémenter la logique "Tunnel Mode" vs "Party Mode" dans Maestro pour optimiser les appels LLM.
  - Initialiser PostgreSQL avec un schéma Hybride (SQL/JSONB) pour le Profil familial.
- **Quick Win Opportunities:**
  - Déployer l'infrastructure de DB isolée avec un outil de migration indépendant (Alembic) par agent.

**Action Planning (Next Steps):**
1. Rédiger le PRD de la Phase 2 en détaillant ces architectures (utilisation de `bmad-create-prd`).
2. Mettre à jour l'architecture système globale (`project-context.md`).
3. Démarrer les Epics/Stories d'implémentation pour la BDD (SQLAlchemy, Alembic, asyncpg) pour Maestro en priorité.

## Session Summary and Insights

**Key Achievements:**
- Définition complète de l'architecture de persistance et de contexte pour la Phase 2.
- Alignement sur des best-practices modernes (Hybride DB, Microservices).
- Résolution pragmatique des problèmes de latence réseau et d'engorgement de Maestro.

**Session Reflections:**
L'utilisation de la réflexion par "Principes Premiers" a permis d'éliminer la complexité superflue (sur-ingénierie des caches, DB unique synchronisée) pour aboutir à un système asymétrique élégant où l'intégration se fait par le prompt du LLM (contexte) plutôt que par un schéma de données rigide.
