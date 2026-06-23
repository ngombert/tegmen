# Deferred Work

## Deferred from: code review de 1-1-provisionnement-de-l-infrastructure-postgresql-hybride (2026-05-20)

- **Credentials faibles user=password** — `scripts/init-multiple-dbs.sh:13` — Chaque utilisateur de base de données a un mot de passe identique à son nom (`gourmet:gourmet`, `maestro:maestro`, etc.). Pattern pré-existant avant cette story, acceptable pour dev local mais sans commentaire explicite ni garde empêchant une réutilisation en staging/prod. À adresser dans un epic sécurité ou avant tout déploiement hors dev.

## Deferred from: code review de focus sur input de ChatLayout (2026-06-23)

- **Anti-pattern : index de tableau comme clé React** — `src/web-client/src/components/ChatLayout.tsx:39` — L'affichage des messages utilise l'index de tableau comme clé `key={idx}`, ce qui peut causer des problèmes de rendu et de performance si l'ordre des messages change.
