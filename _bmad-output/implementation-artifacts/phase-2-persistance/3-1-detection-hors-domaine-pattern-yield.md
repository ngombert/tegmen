# Story 3.1: Détection Hors-Domaine (Pattern Yield)

Status: done

## Story

As a agent spécialiste,
I want détecter quand la question sort de mon domaine d'expertise et retourner une réponse structurée `YieldResponse` au lieu d'halluciner,
So that Maestro sache qu'il doit déclencher la Trappe de Sortie.

## Acceptance Criteria

### AC1 — Détection de hors-domaine par l'agent spécialiste
- **Given** un agent spécialiste (ex: Acadomie ou Gourmet) interrogé sur un sujet hors-scope
- **When** l'agent ou le modèle LLM interne analyse l'intention
- **Then** il ne tente pas de générer une réponse texte standard
- **And** il retourne un objet de type `YieldResponse` (status="yield")
- **And** l'objet inclut le message d'abandon explicatif pour Maestro.

---

## Tasks / Subtasks

- [x] Mettre à jour les prompts système pour Gourmet et Acadomie avec les instructions de Yield
- [x] Modifier la logique A2A de Gourmet et Acadomie pour mapper le token `[YIELD]` vers un `YieldResponse`
- [x] Ajouter un support de détection heuristique dans le Mock LLM pour les tests de non-régression

## Implementation Notes

### Files Modified
- `src/agent_gourmet/app/prompts/system_prompt.md` — Ajout de l'instruction `[YIELD]` pour réponses hors-domaine
- `src/agent_acadomie/app/prompts/system_prompt.md` — Ajout de l'instruction `[YIELD]` pour réponses hors-domaine
- `src/agent_gourmet/app/api/routers/a2a.py` — Handler A2A avec détection du token `[YIELD]`
- `src/agent_acadomie/app/api/routers/a2a.py` — Handler A2A avec détection du token `[YIELD]`
- `src/agent_gourmet/app/services/llm_service.py` — Mock LLM heuristique hors-domaine
- `src/agent_acadomie/app/services/llm_service.py` — Mock LLM heuristique hors-domaine

### Test Coverage
- `tests/common/test_epic_3.py::test_specialist_yield_detection` — Vérifie la détection Yield pour Gourmet et Acadomie en mode Mock LLM
