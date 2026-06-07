# Deferred Work

## Deferred from: code review de 1-1-provisionnement-de-l-infrastructure-postgresql-hybride (2026-05-20)

- **Credentials faibles user=password** — `scripts/init-multiple-dbs.sh:13` — Chaque utilisateur de base de données a un mot de passe identique à son nom (`gourmet:gourmet`, `maestro:maestro`, etc.). Pattern pré-existant avant cette story, acceptable pour dev local mais sans commentaire explicite ni garde empêchant une réutilisation en staging/prod. À adresser dans un epic sécurité ou avant tout déploiement hors dev.
