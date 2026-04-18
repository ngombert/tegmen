# Story 2.1: Anonymisation PII et Audit Trail

Status: done

## Story

As a Chef de Famille,
I want que mes données personnelles (noms, téléphones) soient filtrées par Maestro avant d'être envoyées aux agents spécialisés,
so that ma vie privée soit protégée.

## Acceptance Criteria

1. `src/common/privacy.py` existe et contient une fonction `sanitize_message(text: str)`.
2. Le filtrage identifie et remplace les motifs sensibles (Téléphones FR, Emails, Noms propres simples) par `[FILTERED]`.
3. `log_audit_trail` enregistre chaque action dans `logs/audit.log` sans stocker le contenu brut des messages.
4. Les endpoints de Maestro (`/chat` et `/api/v1/routing`) appliquent systématiquement `sanitize_message`.

## Tasks / Subtasks

- [x] Task 1 : Créer `src/common/privacy.py` (AC: #1, #2)
- [x] Task 2 : Implémenter `log_audit_trail` (AC: #3)
- [x] Task 3 : Intégrer le filtrage dans `main.py` de Maestro (AC: #4)
- [x] Task 4 : Valider avec des tests unitaires (`tests/common/test_privacy.py`)

## Dev Agent Record

### Agent Model Used
Gemini 2.0 Flash (Antigravity)

### Completion Notes
- ✅ AC #1, #2, #3, #4 satisfied.
- ✅ Regex pour téléphones FR et emails implémentées.
- ✅ Audit log JSON-formatted pour faciliter le parsing futur.
