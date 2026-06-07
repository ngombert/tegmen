# Story 2.3: Routage Parallèle Automatique (Party Mode) et Résilience

Status: done

## Story

As a utilisateur de la famille,
I want que Maestro détecte automatiquement quand ma requête nécessite l'expertise croisée de plusieurs agents et les interroge simultanément,
So that j'obtienne une réponse synthétisée robuste, sans que le système ne s'effondre si l'un des agents est lent ou indisponible.

## Contexte

**FRs couvertes :** FR4 (Party Mode), FR13 (Interrogation résiliente / Agents hors ligne)
**NFRs couvertes :** NFR1 (Latence Party Mode), NFR3 (Feedback UX), NFR8 (Dégradation gracieuse / Timeout 10s)

## Acceptance Criteria

### AC1 — Détection du Party Mode
- **Given** une requête nécessitant une expertise croisée ou mentionnant explicitement d'interroger tout le monde
- **When** Maestro analyse la requête
- **Then** il déclenche le Party Mode et contacte les agents concernés en parallèle

### AC2 — Résilience et dégradation gracieuse
- **Given** plusieurs agents contactés
- **When** l'un d'eux met plus de 10s à répondre ou est hors-ligne
- **Then** il est ignoré silencieusement, et la réponse finale est générée à partir des agents opérationnels

---

## Tasks / Subtasks

### Task 1: Implémenter la détection du Party Mode dans le routeur sémantique
- [x] Modifier `classify_intent` dans `router.py` pour détecter le chevauchement sémantique des scores (écart <= 0.01) ou par mots-clés.

### Task 2: Implémenter l'orchestration parallèle dans Maestro
- [x] Utiliser `asyncio.gather` pour appeler les agents en parallèle.
- [x] Appliquer une limite de temps stricte (10.0 secondes).
- [x] Filtrer la liste des agents par RBAC (sécurité enfant).

### Task 3: Synthétiser les résultats
- [x] Créer `generate_synthesis` avec LiteLLM pour fusionner les réponses reçues.

---

## Dev Agent Record

### Agent Model Used
Gemini 3.5 Flash (Low)

### Completion Notes
- Ajout d'une gestion de timeout robuste par agent et intégration d'un LLM de synthèse.
