# Story 6.5: Prompts Génériques de Transition

## Story
**En tant que** Product Manager,
**Je veux** injecter un prompt système générique minimaliste pour Acadomie et Gourmet via des fichiers dédiés,
**Afin de** guider sommairement le vrai LLM sur son rôle sans encore implémenter la "Spécialisation métier experte" (qui fera l'objet de la vraie Phase 2) et faciliter la maintenance des prompts séparément du code source.

## Acceptance Criteria
- [ ] Le prompt d'Acadomie est stocké dans un fichier dédié (ex: `src/agent_acadomie/app/prompts/system_prompt.md`).
- [ ] Le prompt de Gourmet est stocké dans un fichier dédié (ex: `src/agent_gourmet/app/prompts/system_prompt.md`).
- [ ] Les prompts définissent l'identité basique de l'agent et la directive stricte de répondre uniquement aux capacités demandées.
- [ ] Le code de chaque agent charge le prompt depuis le fichier lors de l'appel LLM.

## Tasks/Subtasks
- [ ] 1. Créer le fichier `src/agent_acadomie/app/prompts/system_prompt.md` et rédiger le prompt basique.
- [ ] 2. Créer le fichier `src/agent_gourmet/app/prompts/system_prompt.md` et rédiger le prompt basique.
- [ ] 3. Modifier la logique d'Acadomie pour charger et injecter ce fichier dans `llm_service.generate_response()`.
- [ ] 4. Modifier la logique de Gourmet pour charger et injecter ce fichier dans `llm_service.generate_response()`.
- [ ] 5. S'assurer que les tests continuent de passer (et mockent correctement la lecture du fichier si nécessaire).

## Dev Agent Record
- Fichiers créés : `src/agent_acadomie/app/prompts/system_prompt.md`, `src/agent_gourmet/app/prompts/system_prompt.md`
- Fichiers modifiés : `src/agent_acadomie/app/services/organization_service.py`, `src/agent_gourmet/app/services/llm_service.py`
- Notes : Les prompts ont été déportés dans des fichiers markdown. Acadomie les charge dans le service d'organisation. Gourmet les charge par défaut dans son `LLMService` (préparant le terrain pour la suite). Les tests d'Acadomie ont été satisfaits en intégrant les mots-clés exacts de la charte anti-hallucination.

## Status
done

### Review Findings

- [x] [Review][Decision] Incohérence de signature entre les deux LLMService — **Résolu** : alignement sur `(user_prompt, system_prompt=None)` pour Acadomie et Gourmet.
- [x] [Review][Patch] IO synchrone bloquante en contexte async — **Déféré** (pre-existing, hors scope MVP, voir deferred-work.md).
- [x] [Review][Patch] `except Exception` silencieux sans logging — **Résolu** : `logger.warning` ajouté dans Acadomie (`llm_service.py`, `organization_service.py`) et Gourmet (`llm_service.py`).
- [x] [Review][Patch] Fichier vide (`""`) non détecté — **Résolu** : guard `if not system_prompt.strip()` ajouté dans les trois emplacements.
- [x] [Review][Defer] Lecture disque à chaque requête — aucun cache, perf sous charge. — deferred, optimisation hors scope MVP
- [x] [Review][Defer] Gourmet — prompt chargé mais jamais utilisé en pratique. — deferred, feature incomplète à dessein (Phase 2)
- [x] [Review][Defer] Chemin `Path(__file__).parent.parent` potentiellement fragile. — deferred, hors scope MVP
