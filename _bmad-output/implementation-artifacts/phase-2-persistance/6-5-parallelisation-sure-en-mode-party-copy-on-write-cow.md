# Story 6.5: Parallélisation Sûre en Mode "Party" (Copy-on-Write CoW)

Status: ready-for-dev

## Story

As a agent système (Maestro),
I want cloner le contexte de départ lors d'un appel parallèle à plusieurs agents (Party Mode) et fusionner leurs retours,
So that nous évitions les conditions de concurrence et les pertes d'écriture sur le contexte partagé.

## Contexte

**FRs couvertes :** FR4 (Party Mode - solliciter plusieurs agents et synthétiser les résultats)
**NFRs couvertes :** NFR1 (Latence Party Mode < 15s), NFR7 (Intégrité des données)

## Acceptance Criteria

### AC1 — Passage en Lecture Seule des Contextes Partagés
- **Given** une requête utilisateur complexe déclenchant le Party Mode (ex: Gourmet + Acadomie interrogés en parallèle)
- **When** Maestro transmet le `claim_check_id` de session aux agents enfants
- **Then** il marque ce contexte de départ comme en "Lecture Seule" (Read-Only) via un paramètre ou un en-tête HTTP.

### AC2 — Copy-on-Write (CoW) des modifications
- **Given** un agent spécialiste traitant une requête avec un contexte en lecture seule
- **When** cet agent décide de modifier le contexte (ex: extraire de nouveaux faits ou changer l'état de session locale)
- **Then** il ne modifie pas l'enregistrement d'origine en base de données
- **And** le système crée automatiquement un nouveau clone du contexte (Copy-on-Write), génère un nouveau `claim_check_id` UUID unique, et applique les modifications sur cette nouvelle ligne
- **And** l'agent retourne ce nouveau `claim_check_id` dans sa réponse JSON-RPC à Maestro.

### AC3 — Résolution et Fusion Déterministe
- **Given** les réponses parallèles de multiples agents contenant chacun potentiellement un nouveau `claim_check_id` modifié
- **When** Maestro reçoit toutes les réponses (ou après l'expiration de la timebox de 10s)
- **Then** il exécute une fonction de fusion déterministe (`merge_contexts`) qui combine :
  - Les nouveaux faits extraits par chaque agent (union sans doublons sémantiques)
  - Les modifications d'état de session non conflictuelles
- **And** il écrit le contexte fusionné final sous une nouvelle version principale, mettant à jour la session utilisateur en base de données.

---

## Tasks / Subtasks

### Task 1: Implémentation du Copy-on-Write (CoW) (AC1, AC2)
- [ ] Modifier les schémas d'en-tête et d'API A2A pour supporter un flag `read_only: bool = False` ou un header HTTP `X-Context-Read-Only: true`
- [ ] Dans le repository de contexte (`PostgresContextRepository`), adapter `save_context` :
  - [ ] Si la clé d'origine est marquée ou configurée en lecture seule, interdire sa modification directe
  - [ ] Générer un nouvel UUID pour le clone, copier le contenu existant, y appliquer les modifications, l'enregistrer et retourner ce nouvel identifiant à l'appelant
- [ ] Configurer les agents pour intercepter et retourner ce nouvel ID modifié au format JSON-RPC `result.claim_check_id`

### Task 2: Logique de Fusion Déterministe dans Maestro (AC3)
- [ ] Implémenter la fonction asynchrone `merge_contexts(parent_context_id: str, child_context_ids: list[str]) -> str` dans `src/agent_maestro/app/services/context_service.py` (ou dans Maestro)
  - [ ] Récupérer le contexte parent et tous les contextes enfants modifiés
  - [ ] Fusionner les listes de faits (éviter les doublons de clés identiques, prioriser par `importance_score` ou date de mise à jour)
  - [ ] Fusionner les dictionnaires d'état de session (si deux clés sont en conflit, définir une règle déterministe comme "la dernière écriture l'emporte" ou fusionner les sous-structures)
  - [ ] Enregistrer le résultat fusionné sous un nouvel identifiant final et le lier à la session de l'utilisateur
  - [ ] Supprimer ou marquer comme obsolètes les contextes temporaires de travail des enfants pour éviter l'accumulation de données (Garbage Collection)

### Task 3: Test de Concurrence et de Fusion (AC1, AC2, AC3)
- [ ] Créer les tests unitaires et d'intégration dans `tests/agent_maestro/test_party_mode_cow.py`
  - [ ] Simuler deux agents spécialistes s'exécutant en parallèle et modifiant chacun leur copie du contexte initial
  - [ ] Vérifier qu'aucune exception de conflit d'écriture en base de données n'est générée
  - [ ] Valider que la fonction `merge_contexts` produit bien un résultat combiné propre, déterministe, et sans perte d'information
  - [ ] Valider le comportement si un agent échoue ou s'il y a un timeout (fusionner uniquement les réponses reçues à temps - dégradation gracieuse)

---

## Dev Notes

- **Concurrence sans verrou :** Le pattern Copy-on-Write est une alternative extrêmement élégante aux verrous pessimistes (locks) en base de données dans un système distribué. Il garantit qu'aucune transaction parallèle ne bloque une autre, ce qui est crucial pour maintenir le TTFT global sous les 15 secondes en Party Mode (NFR1).
- **Timebox :** Se rappeler que Maestro utilise une timebox stricte de 10s (NFR8). Les contextes des agents qui répondent après ce délai ne doivent pas être intégrés à la fusion finale.

### Project Structure Notes

- La logique de fusion doit résider dans Maestro car il est le chef d'orchestre exclusif et le propriétaire de l'état global.
- La prise en charge du header Read-Only doit être intégrée dans `src/common/a2a_server.py`.

### References

- [Architecture: docs/architecture.md#Implementation Patterns & Consistency Rules]
- [Source: _bmad-output/planning-artifacts/phase-2-persistance/epics.md#Story 6.5]

## Dev Agent Record

### Agent Model Used

{{agent_model_name_version}}

### Debug Log References

### Completion Notes List

### File List
