# Story 6.6: Fixtures InMemory et Tests de Voyage dans le Temps (Time-Travel Testing)

Status: ready-for-dev

## Story

As a ingénieur QA,
I want tester le comportement de la pile de contexte et l'expiration du TTL de manière ultra-rapide et déterministe,
So that la CI/CD reste performante et exempte de tests instables.

## Contexte

**FRs couvertes :** FR8b (Nettoyage automatique du contexte - Garbage Collection)
**NFRs couvertes :** NFR8 (Dégradation gracieuse), NFR11 (Performance et testabilité sans dépendances lourdes)

## Acceptance Criteria

### AC1 — Double de Test InMemory thread-safe
- **Given** la suite de tests unitaires du projet
- **When** j'exécute des tests nécessitant le stockage de contexte sans vouloir démarrer une base de données PostgreSQL réelle
- **Then** je peux utiliser un double de test `InMemoryContextRepository` qui implémente fidèlement l'interface `BaseContextRepository`
- **And** ce repository en mémoire utilise des verrous thread-safe (`asyncio.Lock`) et un dictionnaire interne pour simuler le comportement de la BDD.

### AC2 — Voyage dans le Temps (Time-Travel Testing)
- **Given** un contexte enregistré avec un TTL défini (ex: 60 secondes)
- **When** je veux tester la péremption de ce contexte dans mes tests unitaires
- **Then** je n'utilise aucun `time.sleep` ou `asyncio.sleep` bloquant (ce qui ralentirait la CI)
- **And** j'utilise un composant d'horloge injectable (`TimeProvider` ou `Clock`) dont je peux modifier l'heure actuelle de manière programmatique
- **And** en avançant l'horloge virtuelle de `TTL + 1 seconde`, le test constate immédiatement l'expiration du contexte comme si le temps s'était réellement écoulé.

### AC3 — Scénarios Limites et Robustesse
- **Given** la suite de tests unitaires `tests/test_context_security.py` (ou `tests/agent_maestro/test_context_expiry.py`)
- **When** j'exécute la suite de tests de bout en bout
- **Then** elle valide à 100% les cas limites d'expiration du TTL, d'usurpation d'identité (ACL) et de nettoyage automatique en arrière-plan sans aucune instabilité (flakiness).

---

## Tasks / Subtasks

### Task 1: Implémentation du Fournisseur de Temps (Clock Abstraction) (AC2)
- [ ] Créer une abstraction de temps `TimeProvider` dans `src/common/utils.py` (ou directement dans `src/common/context_repository.py`) :
  ```python
  class TimeProvider:
      def now(self) -> datetime:
          return datetime.now(timezone.utc)
  ```
- [ ] Adapter `PostgresContextRepository` pour utiliser `TimeProvider` injecté (par défaut une instance réelle de l'horloge système) lors du calcul des dates d'expiration et des requêtes.

### Task 2: Création de la Version InMemory (AC1, AC2)
- [ ] Implémenter la classe `InMemoryContextRepository` héritant de `BaseContextRepository` dans `tests/common/mocks.py` (ou dans le module partagé de test)
  - [ ] Utiliser un dictionnaire en mémoire pour stocker les enregistrements
  - [ ] Permettre l'injection d'un `TimeProvider` mockable pour simuler le voyage dans le temps
  - [ ] Appliquer les contrôles de sécurité ACL lors du chargement des données
  - [ ] Implémenter le filtrage du TTL basé sur l'horloge virtuelle

### Task 3: Écriture de la Suite de Tests Temporels et de Sécurité (AC2, AC3)
- [ ] Écrire la suite de tests dans `tests/agent_maestro/test_context_time_travel.py` ou `tests/test_context_security.py` :
  - [ ] Tester la création d'un contexte avec un TTL court (ex: 5s)
  - [ ] Vérifier que le contexte est accessible immédiatement
  - [ ] Simuler l'avancement de l'horloge de 6 secondes (via un mock de `TimeProvider` qui retourne `maintenant + 6 secondes`)
  - [ ] Tenter de récupérer le contexte et valider qu'il retourne bien `None` (expiré)
  - [ ] Valider que le Garbage Collector de test supprime bien l'enregistrement en mémoire de manière instantanée sans bloquer
  - [ ] S'assurer du respect des principes du document `.agent/rules/test-writing.md` (indépendance des tests, clarté, AAA pattern, pas de flakiness)

---

## Dev Notes

- **Rapidité de la CI/CD :** Les tests impliquant du temps sont la source numéro un de lenteurs et d'instabilités (flakiness) dans les pipelines de déploiement. L'utilisation d'une horloge virtuelle mockée est une obligation absolue pour garantir des tests performants s'exécutant en quelques millisecondes.
- **Thread-Safety :** L'implémentation en mémoire doit être thread-safe et asynchrone pour éviter tout conflit d'accès si plusieurs coroutines de test s'exécutent en parallèle.

### Project Structure Notes

- Le code de test réside dans `tests/test_context_security.py`.
- L'abstraction de temps doit être exportable pour pouvoir être réutilisée par d'autres modules nécessitant des assertions temporelles (ex: les jetons JWT ou les sessions de connexion).

### References

- [Architecture: docs/architecture.md#Testing Standards]
- [Source: _bmad-output/planning-artifacts/phase-2-persistance/epics.md#Story 6.6]
- [Rules: .agent/rules/test-writing.md]

## Dev Agent Record

### Agent Model Used

{{agent_model_name_version}}

### Debug Log References

### Completion Notes List

### File List
