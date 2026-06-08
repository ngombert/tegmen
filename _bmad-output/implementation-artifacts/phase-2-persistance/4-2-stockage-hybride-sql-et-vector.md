# Story 4.2: Stockage Hybride (SQL & Vector)

Status: done

## Story

As a agent système responsable des données,
I want stocker les "Hard-Facts" dans des tables SQL classiques et les "Soft-Facts" sous forme d'embeddings via l'extension `pgvector`,
So that je puisse les retrouver instantanément par requêtes sémantiques.

## Acceptance Criteria

1. **Given** un payload de faits validé
2. **When** le système procède à l'insertion en base
3. **Then** les faits structurés stricts vont dans les champs SQL relationnels appropriés
4. **And** les faits souples sont vectorisés via un modèle d'embedding et insérés dans la table `soft_facts` via `pgvector`
5. **And** je peux exécuter une recherche de similarité cosinus pour retrouver les faits pertinents d'une requête.

## Tasks / Subtasks

- [x] Installer la dépendance pgvector (AC: 4)
  - [x] Ajouter `pgvector` dans `pyproject.toml`
  - [x] Exécuter `uv sync` ou installer le package dans le venv
- [x] Créer les modèles HardFact et SoftFact dans Maestro (AC: 3, 4)
  - [x] Créer `src/agent_maestro/app/db/models/hard_fact.py`
  - [x] Créer `src/agent_maestro/app/db/models/soft_fact.py`
  - [x] Importer et enregistrer les modèles dans `src/agent_maestro/app/db/models/__init__.py`
- [x] Générer et appliquer la migration Alembic pour Maestro (AC: 3, 4)
  - [x] Générer la migration Alembic pour Maestro contenant les tables `hard_facts` et `soft_facts`
  - [x] Activer explicitement l'extension `vector` dans le script de migration (`op.execute("CREATE EXTENSION IF NOT EXISTS vector")`)
  - [x] Appliquer la migration de base de données
- [x] Implémenter le service de stockage dans Maestro (AC: 3, 4, 5)
  - [x] Implémenter `store_facts` dans `src/agent_maestro/app/services/fact_service.py` avec injection de session dynamique (sans import de session globale)
  - [x] Implémenter la recherche de similarité sémantique
- [x] Connecter le stockage asynchrone dans le router principal (AC: 2)
  - [x] Modifier `main.py` de Maestro pour intercepter `new_facts_payload` après retour d'un agent spécialiste
  - [x] Persister de manière non-bloquante (tâche asynchrone en arrière-plan)
- [x] Créer et exécuter les tests (AC: 3, 4, 5)
  - [x] Créer `test_hard_fact_storage` et `test_soft_fact_storage_synthetic` dans `tests/common/test_epic_4.py`
  - [x] S'assurer que tous les tests passent sans charger le modèle d'embedding réel en CI

## Dev Notes

- Recommandation Winston : centraliser dans Maestro.
- Recommandation Amelia : injecter `AsyncSession` dynamiquement dans le service de faits. Ne pas créer de session globale pour éviter de casser les fixtures.
- Recommandation Murat : mock l'embedding dans les tests et utiliser des vecteurs synthétiques en dur.
- Recommandation John : simple et direct.

### Project Structure Notes

- `src/agent_maestro/app/db/models/` pour les modèles.
- `src/agent_maestro/app/services/` pour les services de base de données.

### References

- [Source: epics.md#Story 4.2]

## Dev Agent Record

### Agent Model Used

Gemini 3.5 Flash (Low)

### Debug Log References

- [Tests Log](file:///home/ngombert/.gemini/antigravity/brain/d608644b-0081-4ad3-8006-304237256ba5/.system_generated/tasks/task-1178.log)

### Completion Notes List

- Implémentation des modèles `HardFact` et `SoftFact`.
- Installation de `pgvector` et écriture de la migration Alembic activant l'extension `vector`.
- Implémentation du `fact_service.py` pour sauvegarder et requêter les faits.
- Liaison de la capture asynchrone de `new_facts_payload` dans `main.py` de Maestro.
- Ajout et réussite des tests unitaires/intégration avec vecteurs synthétiques.

### File List

- `pyproject.toml`
- `src/agent_maestro/app/db/models/hard_fact.py`
- `src/agent_maestro/app/db/models/soft_fact.py`
- `src/agent_maestro/app/db/models/__init__.py`
- `src/agent_maestro/app/db/alembic/versions/2d9490624fda_create_facts_tables.py`
- `src/agent_maestro/app/services/fact_service.py`
- `src/agent_maestro/main.py`
- `src/common/embedding_service.py`
- `tests/common/test_epic_4.py`
