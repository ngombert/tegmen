# Plan de Stabilisation Maestro (Phase 2)

Ce document détaille les actions prioritaires pour stabiliser les fondations du Gateway Maestro avant l'intégration de nouveaux agents (Acadomie, etc.). L'objectif est de transformer le MVP en un socle "Gold Standard" robuste, prévisible et scalable.

---

## 1. Objectifs Stratégiques
*   **Fiabilité du Routage :** Unifier la logique de classification d'intention pour éviter les comportements divergents.
*   **Gestion des Ressources :** Éliminer les fuites de mémoire potentielles par un nettoyage actif des sessions.
*   **Confiance Industrielle :** Stabiliser l'infrastructure de test pour garantir un feedback 100% fiable.

---

## 2. Architecture & Design (🏗️ Winston)

Pour garantir la pérennité de Maestro, les composants critiques seront refactorisés selon des principes de design "Lean" et de robustesse asynchrone.

### 2.1 Unification du Pipeline d'Intention
Le dualisme actuel de la logique `classify_intent` crée une dette technique.
*   **Action :** Centralisation au sein d'un `IntentOrchestrator`.
*   **Détail :** Chaque requête passera par un pipeline unique : `Analyse du Contexte -> Classification (Semantic Router) -> Dispatch`.
*   **Optimisation :** Utilisation d'un mécanisme de "Fast-Track" pour le *sticky routing* sans perdre la capacité d'évasion sémantique (Escape Hatch).

### 2.2 Gestion Active du Cycle de Vie des Sessions
La suppression "lazy" actuelle est insuffisante pour la production.
*   **Action :** Implémentation d'un `ActiveCleanupWorker`.
*   **Détail :** Injection d'une tâche de fond `asyncio` dans `InMemorySessionStore` qui purge périodiquement les sessions expirées.
*   **Sécurité :** Utilisation de verrous asynchrones (`asyncio.Lock`) pour garantir l'intégrité lors des accès concurrents.

---

## 3. Implémentation (💻 Amelia)

La liste des fichiers et actions atomiques pour la stabilisation :

### 3.1 Unification de l'Intention
*   **Fichier :** `src/agent_maestro/router.py`
    *   Refactoriser `classify_intent` pour utiliser systématiquement `get_all_scores`.
    *   Supprimer la bifurcation de logique entre le chemin avec et sans `active_agent`.
    *   S'assurer que le `THRESHOLD_ESCAPE_HATCH` est respecté uniformément.

### 3.2 Correction Mémoire (Sessions)
*   **Fichier :** `src/agent_maestro/session.py` (ou `src/common/session.py` si centralisé)
    *   Ajouter une méthode `start_cleanup_task()` déclenchée au démarrage de l'application (lifespan).
    *   Implémenter la boucle de purge asynchrone.

### 3.3 Infrastructure de Test
*   **Fichier :** `tests/conftest.py` & `tests/agent_maestro/test_gateway.py`
    *   Migration complète vers `httpx.AsyncClient`.
    *   Isolation des fixtures pour garantir un `SessionStore` vierge par test.

---

## 4. Qualité & Tests (🧪 Murat)

La qualité n'est pas une option, c'est la condition de survie du projet multi-agents.

### 4.1 Éradication de la "Flakiness"
*   **Audit :** Isolation et correction des tests intermittents dans `tests/test_maestro_*`.
*   **Validation :** 30 exécutions consécutives réussies en environnement CI/CD.

### 4.2 Portes de Sécurité (Quality Gates)
*   **Couverture :** Blocage si la couverture sur `src/agent_maestro/` descend sous **85%**.
*   **Résilience :** Injection systématique de latences simulées pour valider le *Fail-Fast*.

---

## 5. Critères de Succès "Gold Standard"
Maestro sera déclaré prêt pour Acadomie lorsque :
1.  **Fiabilité :** 100% de succès sur les 20 dernières builds.
2.  **Performance :** Latence de routage P95 < 200ms (hors LLM).
3.  **Stabilité :** Zéro fuite mémoire identifiée sous test de charge (15 min).
4.  **Clarté :** Zéro "TODO/FIXME" critique dans le cœur du routeur.
