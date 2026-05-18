# Story 3.4 : Documentation README Agent

Status: review

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

---

## Story Details

- **Status:** ready-for-dev
- **Epic:** 3 — Résilience, Observabilité et Intégration Écosystème
- **Story ID:** 3.4
- **Story Key:** `3-4-documentation-readme-agent`

## 📖 Story Foundation

### User Story
**As a** développeur de l'écosystème Tegmen,
**I want** que l'Agent Gourmet dispose d'un README complet et conforme au template,
**So that** tout contributeur puisse comprendre, lancer et tester l'agent rapidement.

### Acceptance Criteria (BDD)
- **Given** le template `docs/templates/README-agent.template.md`
- **When** le README est généré pour Gourmet
- **Then** le fichier `src/agent_gourmet/README.md` existe et suit la structure du template
- **And** il documente : description, périmètre métier, endpoints A2A, schémas Pydantic (implicitement via les skills), configuration (variables `.env`), commandes de lancement (`uv run`), commandes de test
- **And** les skills exposées (`search_recipes`, `get_recipe_details`, `message/send`) sont listées avec leurs paramètres
- **And** le diagramme Mermaid reflète l'architecture réelle de Gourmet (A2A Server -> Recipe Service -> Mock DB)

---

## 👨‍💻 Developer Context

> **⚠️ CRITICAL RULES & GUARDRAILS ⚠️**
> - **TECHNICAL ACCURACY**: The README must reflect the current state of the codebase (e.g., port 8002, use of `uv`, current skills, etc.).
> - **STANDALONE FOCUS**: Emphasize that Gourmet is a standalone A2A service that can be tested independently of Maestro.

### Technical Requirements
- Fill out all placeholders `{...}` in the template.
- **Port**: 8002 (standard for Gourmet).
- **Service Name**: `agent_gourmet`.
- **Docker Profile**: `gourmet`.
- **Environment Variables**: Document `GOURMET_ARTIFICIAL_DELAY_MS`, `GOURMET_PERSISTENCE_TIMEOUT_MS`, `OTEL_ENABLED`, etc.
- **Skills Documentation**:
    - `search_recipes`: query (str), tags_include (list[str]), tags_exclude (list[str]), ingredients_exclude (list[str]), max_prep_time (int), limit (int), offset (int).
    - `get_recipe_details`: recipe_id (str).
    - `message/send`: message (Message object).

### Architecture Compliance
- Diagramme Mermaid :
    - Maestro Gateway -> Gourmet (A2A Server)
    - Gourmet -> Recipe Service
    - Recipe Service -> Mock Database (RECIPES_DB)

### File Structure Requirements
- Output file: `src/agent_gourmet/README.md`.

---

### 🧠 Previous Story Intelligence
- **Story 3.1**: Added timeout and delay configuration variables.
- **Story 3.2 & 3.3**: Added observability (Correlation ID, Traces, JSON Logging). Mention these in the "Observabilité" or "Architecture" section if relevant.

### Project Context Reference
- `_bmad-output/project-context.md` for naming conventions and ecosystem role.

---

## Tasks / Subtasks

- [x] Task 1 : Préparation du contenu
  - [x] Recenser tous les endpoints et paramètres réels de Gourmet.
  - [x] Identifier toutes les variables d'environnement actives.
- [x] Task 2 : Rédaction du README
  - [x] Copier le template dans `src/agent_gourmet/README.md`.
  - [x] Remplacer tous les placeholders par les informations de Gourmet.
  - [x] Adapter le diagramme Mermaid.
- [x] Task 3 : Validation
  - [x] Vérifier que tous les liens et commandes sont fonctionnels.
  - [x] S'assurer que le rendu Markdown est propre.
