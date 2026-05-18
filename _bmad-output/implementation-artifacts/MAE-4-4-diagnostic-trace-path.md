# Story 4.4: Diagnostic Trace Path

Status: done

## Story

As a Administrateur (Nicolas),
I want visualiser le chemin détaillé d'une requête (Trace Path) dans la réponse API (en mode debug),
so that je puisse comprendre exactement pourquoi un agent a été choisi et quels outils ont été utilisés.

## Acceptance Criteria

1. **Données de Trace** : Le système collecte les scores de similarité, les utterances matchées et l'agent sélectionné.
2. **Champ Debug** : Un champ `debug_info` ou `trace_path` est ajouté à la réponse JSON-RPC.
3. **Contrôle d'Accès** : Ce champ n'est visible que si l'utilisateur possède le rôle `parent` (Administrateur) et qu'un flag `debug=true` est passé (`config.DEBUG` est activé).
4. **Zéro PII** : Les données de trace ne doivent pas refléter le contenu original s'il a été filtré (utiliser les versions sanitisées).

## Tasks / Subtasks

- [ ] Task 1 : Modifier `router.py` pour retourner le détail des scores calculés.
- [ ] Task 2 : Enrichir le processus de routage dans `main.py` pour compiler les étapes.
- [ ] Task 3 : Ajouter la logique de filtrage du champ debug selon le rôle utilisateur.
- [ ] Task 4 : Valider avec des tests d'intégration.

## Dev Notes

### Architecture & Contraintes
- Utiliser le `RequestContext` pour identifier le rôle de l'utilisateur.
- Les données de trace peuvent être volumineuses, s'assurer que le format JSON est clair.
- Pas d'impact sur la latence en mode normal.

## Dev Agent Record

### Agent Model Used
N/A

### Completion Notes
- Ajout de `get_all_scores` dans `router.py` pour extraire les scores de toutes les routes de l'index interne.
- Modification de `main.py` pour intercepter le flag `debug` dans les paramètres JSON-RPC.
- Restriction RBAC : le bloc `_debug` n'est injecté que pour le rôle `parent`.
- Inclusion des scores, des seuils, de la route choisie et du `trace_id` OpenTelemetry.
- Validation via `tests/test_maestro_trace.py`.
